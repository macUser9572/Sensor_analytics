# Pre-Demo Checklist

□ Machine 1, 2, 3 all powered on and on same LAN
□ run `start_demo.sh` — all services green
□ run `start_machine1.sh` — OPC-UA running
□ Open React dashboard — heatmap shows 500 colored cells
□ Open Flutter app — 6 subsystem cards visible with live data
□ Set Flutter BASE_URL to `{M2_IP}:8000`
□ Test Flutter connection: Settings → Test Connection → OK
□ Verify Plotly works offline: turn off WiFi → React still renders charts
□ Test fault scenario 1: Turbine Bearing — alert appears < 2s
□ Verify alert appears in Flutter within 5s
□ Resolve fault — system returns to green
□ Test sensor kill: watchdog fires MISSING alert after ~50s
□ Test compare: select 3 sensors, click COMPARE, verify chart
□ Laptop charger plugged in
□ Docker memory allocation: minimum 4GB
□ Screen recording started (OBS or QuickTime) as backup
