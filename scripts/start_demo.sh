#!/bin/bash

# Prints colored header: "BHEL DEMO STARTUP"
echo -e "\e[1;36m========================================\e[0m"
echo -e "\e[1;36m          BHEL DEMO STARTUP             \e[0m"
echo -e "\e[1;36m========================================\e[0m"

START_TIME=$(date +%s)

# Checks .env exists and has M1_IP, M2_IP, M3_IP set
if [ ! -f .env ]; then
    echo -e "\e[1;31mERROR: .env file not found!\e[0m"
    exit 1
fi

source .env

if [ -z "$M1_IP" ] || [ -z "$M2_IP" ] || [ -z "$M3_IP" ]; then
    echo -e "\e[1;31mERROR: M1_IP, M2_IP, or M3_IP is missing in .env!\e[0m"
    exit 1
fi

echo -e "\e[1;34mStarting Machine 3 (Database) services...\e[0m"
docker compose -f docker-compose.m3.yml up -d

echo -e "\e[1;34mStarting Machine 2 (Hub) services...\e[0m"
docker compose -f docker-compose.m2.yml up -d

echo -e "\e[1;34mWaiting for services to be healthy...\e[0m"
# Wait loop: polls GET /health every 2 seconds until all services return "ok"
while true; do
    # Assuming health endpoint is available at M2_IP:8000
    STATUS=$(curl -s http://${M2_IP}:8000/health | grep -o '"status":"ok"')
    if [ "$STATUS" == '"status":"ok"' ]; then
        echo -e "\e[1;32mAll services are healthy!\e[0m"
        break
    fi
    echo "Waiting for services..."
    sleep 2
done

echo -e "\e[1;34mRunning environment check...\e[0m"
python3 env_check.py

M4_IP_DISPLAY=${M4_IP:-"localhost"}

echo -e "\e[1;32m✓ READY — Dashboard: http://${M2_IP}:8000/docs  React: http://${M4_IP_DISPLAY}:5173\e[0m"
echo -e "\e[1;32mFlutter BASE URL: http://${M2_IP}:8000\e[0m"

END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))
echo -e "\e[1;36mTotal startup time: ${TOTAL_TIME} seconds\e[0m"
exit 0
