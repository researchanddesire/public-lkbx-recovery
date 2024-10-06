# LKBX Recovery

If you're reading this, then you need to flash your device with fresh firmware. Maybe your device is bricked, or you just want to start fresh.

Don't worry—it's not the end of the world. This guide will help you recover your LKBX.

In this repository, you'll find a functioning LKBX firmware that you can flash to your device to recover it.

# Requirements

- A computer running Windows, macOS, or Linux
- A USB-C cable
- An LKBX device
- PlatformIO installed on your computer
- Git installed on your computer
- A bit of technical knowledge
- A bit of patience

# Instructions

1. **Clone this repository** to your computer.
2. **Connect your LKBX** to your computer using a USB-C cable.
3. **Open a terminal** and navigate to the directory where you cloned this repository.
4. **Flash the firmware** to your LKBX by running:

   ```bash
   pio run
   ```

5. **Wait for the flashing process to complete**. Once it's done, your LKBX should be recovered.

# Troubleshooting

## Error: `firmware.bin` not found

This error occurs when you've already attempted to flash using the `pio run` command. PlatformIO may have deleted the `firmware.bin` file after flashing, but it's still in the Git history.

To fix this, run:

```bash
git checkout .
```

This will revert all your local changes and restore the `.pio/build/production/firmware.bin` file.

## Error: Not responding
This is a class of errors which may include messages like the following:
- `The port doesn't exist`
- `Device reports readiness to read but returned no data`
- `Serial data stream stopped: Possible serial noise or corruption.`
- `A fatal error occurred: The chip stopped responding.`

Typically this means some other process is using the serial port.

- **Ensure no other program** is using the serial port. Check all browers, IDE's and terminals.
- **Make sure no pio processes** are running that might be using the serial port.
- **Unplug and replug** the LKBX, or try a different USB port.
- **Restart your computer** if the issue persists.
- **If this fails**, Proceed to the next section.

## Error: Upload successful but LKBX still not working

If you erased the flash memory of your LKBX, you'll need to flash the bootloader first.

1. **Install an empty project** to your LKBX:

   ```bash
   pio run -e bootloader
   ```

2. If you see the message **"LKBX Ready to upload firmware."**, proceed to flash the firmware.
3. **Stop the process** with `Ctrl+C`.
4. **Flash the firmware** by running:

   ```bash
   pio run
   ```

## Error: Serial port not found / No serial data

If PlatformIO cannot communicate with your LKBX, and you've tried all the troubleshooting steps above, you may need power cycle your LKBX.

- **Power cycle your LKBX** by opening the back of your device and unplugging the battery.
    - *Note: Doing this may void your warranty. Contact R&D before proceeding*
    - *Note: If you're not comfortable doing this, please don't attempt it.*

If you are not comfortable power cycling your LKBX, please contact R&D for further assistance.

If you've disconnected the battery and reconnected it, then try following this guide form the top.
If that still doesn't work, please contact R&D for further assistance.

For support, email: [Support@ResearchAndDesire.com](mailto:Support@ResearchAndDesire.com)