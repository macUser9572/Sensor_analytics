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

You cannot use `localhost` or `127.0.0.1` on the phone, because `localhost` refers to the phone itself. You need the laptop's network IP address.

**On Mac:**
- Method A: Run `./start_demo.sh` (it will auto-detect and print it).
- Method B: Open Terminal, type `ipconfig getifaddr en0` (or `en1`).
- Method C: Hold the `Option` key and click the WiFi icon in the top menu bar. Look for "IP Address".

**On Windows:**
- Open Command Prompt or PowerShell.
- Type `ipconfig` and hit Enter.
- Look for the "IPv4 Address" under your active Wireless LAN adapter (usually starts with `192.168.x.x` or `172.x.x.x`).

## 3. Updating Flutter App Configuration

Before building the final artifact for the phone, you must hardcode the laptop's IP address.

1. Open `companion_app/lib/config.dart` (or wherever your API service variables are stored, such as `companion_app/lib/services/api_service.dart`).
2. Replace any instance of `localhost` or `10.0.2.2` (Android emulator loopback) with the IP address.

```dart
// Change THIS:
// final String BASE_URL = "http://localhost:8000";
// final String WS_URL = "ws://localhost:8000/ws";

// To THIS (example IP):
final String BASE_URL = "http://192.168.1.45:8000";
final String WS_URL = "ws://192.168.1.45:8000/ws";
```

3. Rebuild the Flutter app and install it onto the physical device using `flutter build apk` (or `ios`) and deploying via USB. Do not hot-reload during the actual demo—run the compiled release app.
