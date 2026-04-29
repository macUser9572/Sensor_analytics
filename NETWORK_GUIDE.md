# NETWORK CONFIGURATION GUIDE

For the BHEL demo, guaranteeing a stable local network connection between the laptop (backend/dashboard) and the mobile device (Flutter app) is critical. Do NOT rely on the venue's corporate WiFi, as client isolation settings often block peer-to-peer traffic.

## 1. Creating a Dedicated Local Network (The Hotspot Method)

This is the most reliable method for a boardroom demo.

1. Turn OFF WiFi on the laptop.
2. On your smartphone, enable **Personal Hotspot** (Mobile Hotspot).
   *Pro-tip: If signal is weak, you can use USB Tethering. Plug the phone directly into the laptop via USB, and share the connection. This eliminates WiFi interference completely.*
3. Connect the laptop to the phone's Hotspot network.
4. (Optional but recommended) Turn off cellular data on the phone so no internet traffic interferes with the local routing. The router (phone) will still route local traffic perfectly.

## 2. Finding the Laptop's Local IP

Use the LAN address from `.env` on every client. Phone and tablet traffic must target `M2_IP`, not a device-private loopback address.

**On Mac:**
- Method A: Run `./start_demo.sh` (it will auto-detect and print it).
- Method B: Open Terminal, type `ipconfig getifaddr en0` (or `en1`).
- Method C: Hold the `Option` key and click the WiFi icon in the top menu bar. Look for "IP Address".

**On Windows:**
- Open Command Prompt or PowerShell.
- Type `ipconfig` and hit Enter.
- Look for the "IPv4 Address" under your active Wireless LAN adapter (usually starts with `192.168.x.x` or `172.x.x.x`).

## 3. Updating Flutter App Configuration

Before building the final artifact for the phone, pass the backend URL from `.env`.

1. Confirm `FLUTTER_API_BASE_URL` and `FLUTTER_WS_URL` point at `M2_IP`.
2. Build with Dart defines:

```bash
flutter build apk \
  --dart-define=FLUTTER_API_BASE_URL=http://${M2_IP}:8000 \
  --dart-define=FLUTTER_WS_URL=ws://${M2_IP}:8000
```

3. Rebuild the Flutter app and install it onto the physical device using `flutter build apk` (or `ios`) and deploying via USB. Do not hot-reload during the actual demo—run the compiled release app.
