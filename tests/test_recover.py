import contextlib
import io
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from scripts import recover


ROOT = Path(__file__).resolve().parents[1]


def efuses(capacity, power):
    data = bytearray(32)
    struct.pack_into("<I", data, 0, power << 8)
    struct.pack_into("<II", data, 0x18, (capacity & 3) << 3, (capacity >> 2) << 19)
    return data


class HardwareTests(unittest.TestCase):
    def test_all_efuse_combinations(self):
        supported = {(1, 0): "r2", (2, 0): "r2", (1, 1): "r8"}
        for capacity in range(8):
            for power in range(2):
                with self.subTest(capacity=capacity, power=power):
                    if (capacity, power) in supported:
                        self.assertEqual(recover.hardware_variant(efuses(capacity, power)),
                                         supported[capacity, power])
                    else:
                        with self.assertRaises(ValueError):
                            recover.hardware_variant(efuses(capacity, power))

    def test_incomplete_identity(self):
        with self.assertRaises(ValueError):
            recover.hardware_variant(bytes(28))

    def test_port_selection(self):
        ports = [
            {"port": "COM3", "hwid": "USB VID:PID=303A:1001"},
            {"port": "COM4", "hwid": "USB VID:PID=1234:5678"},
        ]
        self.assertEqual(recover.select_port(None, ports), "COM3")
        self.assertEqual(recover.select_port("COM4", ports), "COM4")
        self.assertEqual(recover.select_port("COM3*", ports), "COM3")
        with self.assertRaises(ValueError):
            recover.select_port(None, [])
        with self.assertRaises(ValueError):
            recover.select_port("COM*", ports)
        with self.assertRaises(ValueError):
            recover.select_port(None, ports + [{"port": "COM5", "hwid": "303A:1001"}])


class ReleaseTests(unittest.TestCase):
    def test_bundled_releases_and_flash_layout(self):
        versions = set()
        for variant in ("r2", "r8"):
            directory = ROOT / "firmware" / variant
            versions.add(recover.verify_firmware(directory, variant))
            for name in ("bootloader.bin", "firmware.bin"):
                data = (directory / name).read_bytes()
                self.assertEqual(data[0], 0xE9)
                self.assertEqual(struct.unpack_from("<H", data, 12)[0], 9)  # ESP32-S3
            self.assertLess((directory / "bootloader.bin").stat().st_size, 0x8000)
            self.assertLessEqual((directory / "partitions.bin").stat().st_size, 0x1000)
            partitions = (directory / "partitions.bin").read_bytes()
            entries = {}
            for offset in range(0, len(partitions), 32):
                magic, kind, subtype, address, size, name, flags = struct.unpack_from(
                    "<HBBII16sI", partitions, offset)
                if magic != 0x50AA:
                    break
                entries[name.rstrip(b"\0")] = (address, size)
            self.assertEqual(entries[b"otadata"], (0xE000, 0x2000))
            self.assertEqual(entries[b"app0"][0], 0x10000)
            self.assertLessEqual((directory / "firmware.bin").stat().st_size,
                                 entries[b"app0"][1])
        self.assertEqual(len(versions), 1)

    def test_corrupt_missing_or_wrong_variant_bundle(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "r2"
            shutil.copytree(ROOT / "firmware" / "r2", directory)
            with self.assertRaises(ValueError):
                recover.verify_firmware(directory, "r8")
            firmware = directory / "firmware.bin"
            data = bytearray(firmware.read_bytes())
            data[-1] ^= 1
            firmware.write_bytes(data)
            with self.assertRaises(ValueError):
                recover.verify_firmware(directory, "r2")
            firmware.unlink()
            with self.assertRaises(FileNotFoundError):
                recover.verify_firmware(directory, "r2")


class RecoveryTests(unittest.TestCase):
    def run_recovery(self):
        with contextlib.redirect_stdout(io.StringIO()):
            recover.recover(ROOT, sys.executable, Path("esptool.py"), "COM3", 460800)

    def test_each_variant_flashes_correct_images_and_resets_ota(self):
        for capacity, power, variant in ((1, 0, "r2"), (2, 0, "r2"), (1, 1, "r8")):
            with self.subTest(variant=variant, capacity=capacity):
                def esptool(command, **kwargs):
                    self.assertEqual(command[2:6], ["--chip", "esp32s3", "--port", "COM3"])
                    self.assertTrue(kwargs["check"])
                    if "dump_mem" in command:
                        self.assertEqual(command[-3:-1], ["0x6000703c", "32"])
                        Path(command[-1]).write_bytes(efuses(capacity, power))
                    else:
                        self.assertIn("write_flash", command)
                        self.assertNotIn("erase_flash", command)
                        self.assertEqual(command[-8::2], ["0x0", "0x8000", "0xe000", "0x10000"])
                        self.assertEqual(Path(command[-3]).read_bytes(), b"\xff" * 0x2000)
                        directory = ROOT / "firmware" / variant
                        self.assertEqual(command[-7], str(directory / "bootloader.bin"))
                        self.assertEqual(command[-5], str(directory / "partitions.bin"))
                        self.assertEqual(command[-1], str(directory / "firmware.bin"))
                with patch.object(recover.subprocess, "run", side_effect=esptool) as run:
                    self.run_recovery()
                    self.assertEqual(run.call_count, 2)

    def test_unknown_hardware_never_writes(self):
        def probe(command, **kwargs):
            Path(command[-1]).write_bytes(efuses(7, 1))
        with patch.object(recover.subprocess, "run", side_effect=probe) as run:
            with self.assertRaises(ValueError):
                self.run_recovery()
            self.assertEqual(run.call_count, 1)

    def test_failed_probe_never_writes(self):
        with patch.object(recover.subprocess, "run",
                          side_effect=subprocess.CalledProcessError(2, "probe")) as run:
            with self.assertRaises(subprocess.CalledProcessError):
                self.run_recovery()
            self.assertEqual(run.call_count, 1)

    def test_damaged_bundle_never_writes(self):
        def probe(command, **kwargs):
            Path(command[-1]).write_bytes(efuses(1, 0))
        with patch.object(recover.subprocess, "run", side_effect=probe) as run:
            with patch.object(recover, "verify_firmware", side_effect=ValueError("bad hash")):
                with self.assertRaises(ValueError):
                    self.run_recovery()
            self.assertEqual(run.call_count, 1)

    def test_failed_flash_does_not_report_success(self):
        def esptool(command, **kwargs):
            if "dump_mem" in command:
                Path(command[-1]).write_bytes(efuses(1, 1))
            else:
                raise subprocess.CalledProcessError(2, command)
        output = io.StringIO()
        with patch.object(recover.subprocess, "run", side_effect=esptool):
            with contextlib.redirect_stdout(output), self.assertRaises(subprocess.CalledProcessError):
                recover.recover(ROOT, sys.executable, Path("esptool.py"), "COM3", 460800)
        self.assertNotIn("Done.", output.getvalue())

    def test_clean_never_connects(self):
        env = Mock()
        env.IsCleanTarget.return_value = True
        with patch.object(recover, "recover") as flash:
            recover.platformio_recover(env, ["clean"])
        flash.assert_not_called()
        env.subst.assert_not_called()

    def test_non_upload_target_never_connects(self):
        env = Mock()
        env.IsCleanTarget.return_value = False
        with patch.object(recover, "recover") as flash, contextlib.redirect_stderr(io.StringIO()):
            recover.platformio_recover(env, ["nobuild"])
        flash.assert_not_called()
        env.subst.assert_not_called()
        env.Exit.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()
