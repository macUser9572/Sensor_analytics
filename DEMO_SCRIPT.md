# BHEL TECHNICAL DEMO SCRIPT

**Total Duration:** ~10-15 Minutes
**Note for Demonstrator:** While this script is written chronologically, BHEL engineers may interrupt. *The structural order is flexible except for the fault demonstration, which must follow the setup.* If asked a question mid-demo, pause the script, answer the question using the dashboard as a visual aid, and resume from where you left off.

---

## The Fault Scenarios (Pre-configured)
*We have pre-configured three BHEL-specific scenarios into the UI buttons so they require only a **single click** to execute.*

### Scenario 1: Turbine Bearing Overheat (Demo Default)
- **Sensor:** `T001` (HP Turbine Bearing 1 Temp)
- **Physical Explanation:** The lubrication oil system for the high-pressure turbine bearing has reduced flow, causing friction and a rapid temperature spike.
- **Expected BHEL Question:** "How fast does your system process this compared to traditional DCS (Distributed Control Systems) polling?" -> *Answer: Our TimescaleDB/Websocket pipeline processes it in sub-50ms tick rates, drastically faster than traditional 1-second polling.*

### Scenario 2: Boiler Drum Pressure Spike
- **Sensor:** `B001` (Steam Pressure 1)
- **Physical Explanation:** A sudden blockage or main steam valve malfunction causing steam pressure to rapidly climb beyond safe structural limits.
- **Expected BHEL Question:** "Will temporary noise trigger a false alarm?" -> *Answer: We use continuous aggregates to smooth out temporary noise, ensuring alerts only trigger on sustained anomalies.*

### Scenario 3: Generator Frequency Deviation
- **Sensor:** `T041` (Turbine RPM 1 / Frequency)
- **Physical Explanation:** Grid load suddenly drops, causing the synchronous generator to spin faster (RPM increase), pushing frequency above 50Hz.
- **Expected BHEL Question:** "Can we correlate this with terminal voltage?" -> *Answer: Yes, the dashboard's synchronized timelines allow you to overlay RPM and Terminal Voltage to see the cascading effects.*

---

## Part 1: Opening & Overview (Minute 0-2)

**Action:** Open the dashboard on the laptop monitor. Ensure the phone/tablet with the Flutter app is placed on the table next to the laptop, screen awake.

**What to Say:** 
"Thank you for having us. Today, we're demonstrating our real-time sensor analytics platform, custom-built for high-frequency environments like your 500-megawatt thermal plants. What you are looking at is a live telemetry stream (continuous data feed) from 500 simulated sensors. All of this is running entirely locally on this machine—completely air-gapped (disconnected from the internet) to prove its security and resilience."

**What to Point At:** 
Gesture to the main **Sensor Heatmap**.
"Notice this heatmap grid. Every square represents a separate sensor across the Turbine, Boiler, Generator, and Cooling systems. Right now, they are all green, indicating that our 500 sensors are operating within their baseline parameters."

---

## Part 2: Normal Operation Walkthrough (Minute 2-5)

**Action:** Click through the left sidebar navigation to show different system views.

**What to Say:**
"Let's zoom into specific subsystems. Here in the Turbine view, we are plotting high-frequency data—like RPM (Rotations Per Minute) and bearing temperatures. Unlike legacy systems that poll data every few seconds, our backend utilizes an event-driven architecture (a design where data changes are pushed instantly rather than requested) ensuring sub-second latency."

**Action:** Pick up the mobile device running the Flutter app. Hand it to the lead BHEL engineer if comfortable, or place it where everyone can see.

**What to Say:**
"Equally important is putting this data in the hands of the floor operators. This mobile companion app is receiving the exact same live WebSocket (instant two-way connection) data stream as the dashboard. There is zero middle-man delay. If a value changes on the server, the web dashboard and the mobile app update at the exact same millisecond."

---

## Part 3: The Fault Demonstration (Minute 5-8) ***[CRITICAL PATH]***

**Action:** Ensure the laptop screen is showing the main Heatmap view and the phone is unlocked and visible. Hover your mouse over the "Simulate Overheat (T001)" button.

**What to Say:**
"In a perfectly running plant, data is quiet. The real test of an analytics platform is how it handles a sudden catastrophic deviation. I am going to simulate an HP Turbine Bearing Overheat condition (a severe friction event). Watch the heatmap, and keep an eye on the mobile app."

**Action:** **CLICK the "Simulate Overheat (T001)" button once.** Move your hand away from the mouse.

**What to Point At:**
1. Point at the specific cell for `T001` on the heatmap as it transitions from Green → Amber → Red.
2. Within 2 seconds, point to the top-right of the dashboard as the red Alert Toast appears.
3. Simultaneously point to the mobile phone as the Push Notification drops down.

**What to Say:**
"Within milliseconds, the incoming value breached the critical threshold of 120 degrees. The backend alert engine detected this, bypassed standard polling cycles, and pushed an asynchronous alert (an immediate, out-of-turn notification) to all connected clients. The operator on the floor gets the alert at the exact same time as the control room."

---

## Part 4: Recovery, Insights, and Closing (Minute 8-10)

**Action:** Click the "Resolve Fault" button. Navigate to the Historical/Charts view for the Turbine.

**What to Say:**
"Now we will resolve the fault. Notice the real-time cooldown curve as the bearing temperature returns to its baseline."

**Action:** Highlight the drop on the time-series line chart.

**What to Say:**
"Because we aggressively write this data to a time-series database (a database optimized specifically for time-stamped events), post-incident analysis is immediate. You don't have to wait for end-of-day batch processing to figure out what happened."

"To conclude, this architecture provides true real-time visibility, strict local security with no reliance on external clouds, and immediate alert delivery. We'd love to use our remaining time to dive deeper into any specific technical areas you'd like to explore."
