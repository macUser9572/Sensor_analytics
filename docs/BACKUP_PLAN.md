# Backup Plan & Contingencies

If things go wrong during the demo, follow these steps calmly:

- **If Docker fails entirely:** Run the core services directly on bare metal using `python main.py` in the respective directories.
- **If WebSocket keeps dropping:** Check the CORS settings in the FastAPI backend. Verify that `M2_IP` is correctly set in the React `.env` file and that the laptop is on the same Wi-Fi network as the server.
- **If Flutter won't connect:** Use the Settings screen in the Flutter app to manually update the IP to match the Hub (Machine 2). Use "Test Connection" to verify.
- **If a scenario crashes or hangs:** Use the "Resolve All Faults" button in the Demo Control Panel to reset the state, apologize briefly ("Let's reset the scenario state"), and move to the next scenario.
- **Ultimate Backup:** A screen recording of the full demo (created during the checklist step) MUST be available locally on the laptop before you leave for the meeting. Play the video if the live system completely fails.
