"""Flash the bundled production release for the connected LKBX's R2/R8 hardware."""

import fnmatch
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile


def select_port(configured, ports):
    configured = (configured or "").strip()
    if configured and not any(char in configured for char in "*?[]"):
        return configured
    matches = sorted({
        item["port"] for item in ports
        if (fnmatch.fnmatch(item["port"], configured) if configured else
            "303A:1001" in item.get("hwid", "").upper())
    })
    if len(matches) != 1:
        raise ValueError(
            "Connect one LKBX with a USB data cable, or select its port with "
            "pio run --upload-port PORT. "
            f"Matching ports: {', '.join(matches) or 'none'}."
        )
    return matches[0]


def hardware_variant(data):
    # Same factory eFuse mapping used by lkbx's production auto-detection.
    # The dump starts at ESP32-S3 EFUSE_RD_REPEAT_DATA3_REG (0x6000703c).
    if len(data) != 32:
        raise ValueError("Incomplete hardware identity; no firmware was written.")
    repeat_data3 = struct.unpack_from("<I", data, 0)[0]
    word4, word5 = struct.unpack_from("<II", data, 0x18)
    capacity = (((word5 >> 19) & 1) << 2) | ((word4 >> 3) & 3)
    pin_power = (repeat_data3 >> 8) & 1
    if pin_power == 0 and capacity in (1, 2):
        return "r2"
    if pin_power == 1 and capacity == 1:
        return "r8"
    raise ValueError(
        f"Unsupported hardware (PSRAM code {capacity}, pin power {pin_power}); "
        "no firmware was written."
    )


def verify_firmware(directory, variant):
    manifest = json.loads((directory / "manifest.json").read_text())
    if (manifest["deviceType"], manifest["track"], manifest["hardwareVariant"]) != (
        "lkbx", "main", variant
    ):
        raise ValueError("Firmware manifest does not match this LKBX.")
    artifacts = {item["filename"]: item for item in manifest["artifacts"]}
    for name in ("bootloader.bin", "partitions.bin", "firmware.bin"):
        data = (directory / name).read_bytes()
        expected = artifacts[name]
        if (len(data) != expected["sizeBytes"] or
                hashlib.sha256(data).hexdigest() != expected["sha256"]):
            raise ValueError(f"{variant}/{name} is damaged; download this repository again.")
    return manifest["version"]


def recover(project, python, esptool, port, baud):
    command = [python, str(esptool), "--chip", "esp32s3", "--port", port]
    with tempfile.TemporaryDirectory(prefix="lkbx-recovery-") as temporary:
        dump = Path(temporary) / "efuse.bin"
        print(f"Detecting LKBX hardware on {port}...", flush=True)
        subprocess.run(
            command + ["--after", "hard_reset", "dump_mem", "0x6000703c", "32", str(dump)],
            check=True, timeout=30,
        )
        variant = hardware_variant(dump.read_bytes())
        directory = Path(project) / "firmware" / variant
        version = verify_firmware(directory, variant)

        # Erased OTA metadata makes the bootloader select the freshly written app0.
        # Separate segments preserve NVS (settings) and the filesystem.
        otadata = Path(temporary) / "otadata.bin"
        otadata.write_bytes(b"\xff" * 0x2000)
        print(f"Recovering LKBX {variant.upper()} with firmware {version}...", flush=True)
        subprocess.run(
            command + [
                "--baud", str(baud), "--after", "hard_reset", "write_flash", "-z",
                "--flash_mode", "keep", "--flash_freq", "keep", "--flash_size", "keep",
                "0x0", str(directory / "bootloader.bin"),
                "0x8000", str(directory / "partitions.bin"),
                "0xe000", str(otadata),
                "0x10000", str(directory / "firmware.bin"),
            ],
            check=True,
        )
    print(f"Done. LKBX {variant.upper()} is restarting with firmware {version}.")


def platformio_recover(env, targets):
    # Cleaning must never connect to a device or delete the bundled firmware.
    if env.IsCleanTarget():
        return
    if "upload" not in targets or set(targets) - {"upload", "nobuild"}:
        sys.stderr.write("This recovery tool supports pio run (upload) and pio run -t clean.\n")
        env.Exit(1)
        return

    from platformio.device.list.util import list_serial_ports

    try:
        port = select_port(env.subst("$UPLOAD_PORT"), list_serial_ports())
        tool_dir = env.PioPlatform().get_package_dir("tool-esptoolpy")
        if not tool_dir or not (Path(tool_dir) / "esptool.py").is_file():
            raise ValueError("PlatformIO's esptool package is missing; reinstall the platform.")
        recover(
            env.subst("$PROJECT_DIR"), env.subst("$PYTHONEXE"),
            Path(tool_dir) / "esptool.py", port, env.GetProjectOption("upload_speed"),
        )
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        sys.stderr.write(f"Recovery failed: {error}\n")
        env.Exit(1)
        return
    # The release is already built. Never compile or upload a replacement program.
    env.Exit(0)


if "Import" in globals():
    Import("env")
    from SCons.Script import COMMAND_LINE_TARGETS

    platformio_recover(env, [str(target) for target in COMMAND_LINE_TARGETS])
