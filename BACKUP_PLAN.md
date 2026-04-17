# DEMO FAILSAFE & BACKUP PLAN

Even with rigorous air-gap preparation, live demos have variables. This document outlines exact steps to mitigate catastrophic failures.

## 1. What to do if Docker fails to start
**Symptom:** `./start_demo.sh` hangs, or `docker compose ps` shows services continuously restarting.
**Immediate Response:**
1. Do not troubleshoot live in front of the client. Stall by introducing the architecture slide.
2. Run a full teardown: `docker compose down -v` (This wipes volumes, which is fine since the DB auto-seeds on boot).
3. If the daemon is completely frozen, restart Docker Desktop entirely.
4. Run `./start_demo.sh` again. This entire process takes under 45 seconds.

## 2. What to do if WebSocket keeps disconnecting
**Symptom:** The dashboard sensor values pause, or the browser developer console shows recurrent `1006` WebSocket close events.
**Immediate Response:**
1. This is almost always caused by background OS energy saving pausing the browser tab, or network interference.
2. Hard refresh the browser using `Cmd + Shift + R` (Mac) or `Ctrl + F5` (Windows) to aggressively clear the socket pool and force a reconnection.
3. If using venue WiFi, the corporate firewall is likely severing long-lived TCP streams. Immediately switch to offline hotspot mode (see NETWORK_GUIDE.md).

## 3. What to do if the Phone won't connect
**Symptom:** UI spinner is stuck on the mobile app, no live data.
**Immediate Response:**
1. Verify the phone is on the *exact* same WiFi network/hotspot as the laptop.
2. The laptop's IP address may have changed due to DHCP lease expiration.
3. If rebuilding the app isn't feasible live, rely entirely on the web dashboard. *Say: "To respect your time, let's look at the web control room first while the mobile client syncs."*
4. **Best Prevention:** Plug the phone into the laptop via a physical USB cable and use **USB Tethering**. This forces a direct network link that cannot be affected by WiFi congestion.

## 4. The Ultimate Fallback: The Pre-Recorded Video
If a hardware failure occurs (e.g., laptop overheating, complete crash), you MUST have a high-fidelity video of a perfect demo run.

**How to Record Before Leaving:**
1. Set up your screen exactly as it will look during the demo.
2. Open **QuickTime Player** (Mac).
3. Go to **File -> New Screen Recording** (or use the exact shortcut `Cmd + Shift + 5`).
4. Select "Record Entire Screen".
5. In the "Options" menu, ensure **Microphone** is checked (so you can record your voice explaining as a reference).
6. Click **Record** and perform the entire 10-minute demo flawlessly.
7. Save the file as `BHEL_Demo_Backup_Full.mov`.

*(If using OBS Studio: Launch OBS, set Source to Display Capture, add Audio Input Capture, and click "Start Recording").*

**Crucial Storage Step:**
Save this file onto a **physical USB thumb drive**. If your main laptop's motherboard dies, you can plug the USB into a BHEL engineer's laptop and still play the video.
