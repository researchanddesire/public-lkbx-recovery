# LKBX Recovery

If you're reading this, then for some reason you're need to flash your device with fresh firmware.
Maybe your device is bricked, or you just want to start fresh.

Don't worry, it's not the end of the world. This guide will help you recover your LKBX.

In this simple repository, there's a functioning LKBX firmware that you can flash to your LKBX to recover it.

## Requirements

- A computer running Windows, macOS, or Linux
- A USB-C cable
- A LKBX
- PlatformIO installed on your computer
- Git installed on your computer
- A bit of technical knowledge
- A bit of patience

## Instructions

1. Clone this repository to your computer.
2. Plug your LKBX into your computer using a USB-C cable.
3. Open a terminal and navigate to the directory where you cloned this repository.
4. Run the following command to flash the firmware to your LKBX:

```bash
pio run
``` 

5. Wait for the firmware to flash. Once it's done, your LKBX should be recovered.

## Troubleshooting

### Error: `firmware.bin` not found

This error happens when you've already attempted to flash using the `pio run -t upload -t nobuild` command.
Simply, PlatformIO has deleted the `firmware.bin` file after flashing. But it's still in the git history.

To fix this, run the following command:

```bash
git checkout .
```

This will revert all your local changes and restore the `.pio/build/production/firmware.bin` file.

### Error:  The port doesn't exist

Make sure no other program is using the serial port. If you're on Windows, you can check this in the Device Manager.
If you're sure no other program is using the serial port, try unplugging and plugging the LKBX back in.
Or try using a different USB port.

If all else fails, restart your computer.

### Error: Upload Successful but LKBX still not working.

Did you erase the flash memory of your LKBX? If so, you need to flash the bootloader first.

Run the following command to install an empty project to your LKBX:

```bash
pio run -e bootloader -t upload -t monitor
```

If you see the message "LKBX Ready to upload firmware.", then you can proceed to flash the firmware.

stop the process with Ctrl+C and run the following command to flash the firmware:

```bash
pio run
```

### Error:  Serial port not found / No serial data

It is very likely that if you're in this situation, platformio cannot communicate with your LKBX.
This can usually be resolved by power cycling your LKBX.

However, this requires opening the back of your device and unplugging the battery. If you're not comfortable doing this,
please don't attempt it.
Contact R&D for further assistance.

Support@ResearchAndDesire.com