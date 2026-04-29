# DEMO PREPARATION CHECKLIST (AIR-GAP VERIFIED)

Run this checklist 2 hours before the demo, and again 30 minutes before the demo.

## 1. Network & Air-Gap Resilience (No Internet Required)
- [ ] **Plotly JS Local Bundle:** Verify that `frontend/package.json` contains `plotly.js` or `react-plotly.js` and there are NO `<script src="https://cdn.plot.ly/...">` tags in `public/index.html`. 
  *How to verify:* Disconnect from all WiFi, clear browser cache, load the dashboard. If graphs render, you are successfully bundled locally.
- [ ] **WebSocket Offline Connection:** While internet is still OFF, verify the dashboard connects to `REACT_WS_URL` and live data flows.
- [ ] **Flutter LAN IP Mapping:** Verify the laptop and phone/tablet are on the SAME local network and the Flutter build uses `FLUTTER_API_BASE_URL` / `FLUTTER_WS_URL` from `.env`.

## 2. Infrastructure & Environment
- [ ] **Docker Memory:** Open Docker Desktop settings. Ensure at least **4GB RAM** is allocated to handle Redis, TimescaleDB, and the Python FastAPI backend simultaneously.
- [ ] **Backend Startup:** Run `./start_demo.sh`. Verify it outputs "Ready for demo!" and all containers (`db`, `redis`, `api`) are healthy.
  *Expected Output:* `docker compose ps` shows all services "Up".
- [ ] **Hardware Check:** Laptop battery is at 100%. **Bring the charger.** Plug it in *before* starting the demo to prevent aggressive CPU throttling. Set screen sleep timeout to "Never".

## 3. Application Functionality tests
- [ ] **Fault Injection Triggers:** Use the dashboard UI to trigger the "Turbine Bearing Overheat" fault on sensor `T001`.
- [ ] **Alert Latency:** Verify visually that the dashboard UI displays the critical alert within **2 seconds** of the fault being triggered.
- [ ] **Mobile Push:** Verify that the Flutter app on the actual iPad/phone receives the alert notification while connected via local IP.
- [ ] **Recovery:** Resolve the fault and verify the dashboard returns to a normal (green) state within 5-10 seconds.

## Exit Criteria 
- [ ] Run the full `DEMO_SCRIPT.md` from start to finish **3 times** without stopping.
- [ ] On the last run, disable all internet access on the router/hotspot mid-demo to prove true local-only operation.
- [ ] Export the backup screen recording to a physical USB thumb drive.
