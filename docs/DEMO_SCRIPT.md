# BHEL Demo Script

> **Note for Presenter:** This script is designed to be FLEXIBLE. If the client asks to see things out of order, you can jump between sections. The only FIXED part is the fault demonstration timing.

## MINUTE 0-2: OPENING (FLEXIBLE)
**SAY:** "What you're looking at is 500 sensors from a simulated 500MW thermal unit — same architecture as your actual plant. Everything runs within your network. Let me show you the overview."

**DO:** Point at the heatmap. Let it sit for 10 seconds. Let them see the scale.

## MINUTE 2-4: NORMAL OPERATION (FLEXIBLE)
**DO:** Click Turbine in sidebar — show line charts and RPM gauge

**SAY:** "Each sensor updates at its own frequency — generator frequency every 2 seconds, bearing temperatures every 10. No fixed polling — the system receives data only when values change."

**DO:** Show Flutter phone alongside laptop — "Same live data, mobile access over your plant LAN."

## MINUTE 4-7: FAULT DEMONSTRATION (FIXED — The Key Moment)
**SAY:** "Let me show you what happens when something goes wrong."

**DO:** Click "Turbine Bearing Overheat" demo button. Say NOTHING for 15 seconds.

**POINT:** at heatmap cell slowly turning amber, then red

**SAY:** "That alert fired under 2 seconds from the threshold being crossed. One alert — not one per second. The system deduplicates automatically."

**SHOW:** Flutter phone — push notification has appeared

**SAY:** "Your field engineer gets the same notification on their phone over plant WiFi."

## MINUTE 7-9: SENSOR FAILURE DEMO (FIXED)
**SAY:** "Now let me show you how we handle sensor hardware failure — not a value anomaly, but the sensor going completely silent."

**DO:** Trigger "Sensor Kill" for T010 (use curl or admin button)

**SAY:** "We've killed that sensor. Watch what happens in about 45 seconds..."

**DO:** Wait 50 seconds — point at cell turning grey

**SAY:** "Our watchdog detected 45 seconds of silence and fired a Sensor Missing alert. This is different from a threshold alert — it means the sensor itself needs attention (e.g. cable cut or power loss)."

## MINUTE 9-11: HISTORICAL ANALYSIS + COMPARE (FLEXIBLE)
**DO:** Click the faulted sensor cell — show modal with 60-minute history chart

**SAY:** "Every reading is stored in time-series format. Historical trend is available instantly — the query returns in under 50 milliseconds."

**DO:** Navigate to Sensor List → select T001, T003, B012 → click COMPARE

**SAY:** "We can overlay any combination of sensors — across subsystems — in a single chart. Your engineers can correlate bearing temperature against boiler pressure in real time."

## MINUTE 11-12: CLOSING (FLEXIBLE)
**DO:** Resolve all faults — system returns to green

**SAY:** "When BHEL is ready to connect this to your actual DCS (Distributed Control System), the change is one configuration line — the server URL. Your OPC-UA endpoint replaces our simulator. The entire pipeline downstream is unchanged."
