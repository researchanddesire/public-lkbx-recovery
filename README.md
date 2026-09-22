# LKBX Recovery

Recover an **R2 or R8 LKBX** with production firmware **1.21.51**.
The tool detects your hardware and flashes the matching firmware automatically.

## Recover

You need [PlatformIO](https://docs.platformio.org/en/latest/core/installation/index.html),
[Git](https://git-scm.com/downloads), and a USB-C **data** cable. Windows, macOS,
and Linux are supported.

Clone this repository, connect one LKBX, and run this from the repository folder:

```sh
pio run
```

Or, for a fresh download and recovery in one line:

```sh
git clone https://github.com/researchanddesire/public-lkbx-recovery.git && cd public-lkbx-recovery && pio run
```

Wait for “Done” and let the device restart. Recovery installs the matching
bootloader, partition table, and firmware, including on an erased device.
It resets the boot-slot selection while preserving saved settings and the filesystem.
No separate bootloader step or R2/R8 selection is needed.

## Trouble connecting?

- Close serial monitors, browser device connections, and other programs using the LKBX.
- Try a different USB data cable or port, then unplug and reconnect the device.
- If several devices are connected, choose the LKBX's port explicitly:
  `pio run --upload-port COM3` (Windows) or
  `pio run --upload-port /dev/cu.usbmodem1101` (macOS example).
  Run `pio device list` to find your port.
- Unknown hardware or a damaged firmware file stops recovery before anything is written.
- You can rerun `pio run`; cleaning with `pio run -t clean` also leaves the firmware intact.

Still stuck? Contact [Support@ResearchAndDesire.com](mailto:Support@ResearchAndDesire.com).

## Bundled release

`firmware/r2/` and `firmware/r8/` contain the original production binaries and
release manifests for **1.21.51**, build
`20a46d19361fa7ed1e57b905b36b53520828bf9e`. The tool verifies each binary's
SHA-256 checksum before flashing. The manifests also describe the web installer;
this tool uses only the three separate binaries to preserve device settings.

For a future release, replace each variant's `firmware.bin`, `bootloader.bin`,
`partitions.bin`, and `manifest.json` together, then update the version here.
Run the hardware-free checks with `python -m unittest discover -s tests`.
