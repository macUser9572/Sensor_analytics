#!/bin/bash

echo -e "\e[1;34mStarting Machine 1 (Simulator & OPC-UA)...\e[0m"

if [ ! -f .env ]; then
    echo -e "\e[1;31mERROR: .env file not found!\e[0m"
    exit 1
fi

source .env

echo -e "\e[1;34mStarting OPC-UA Bridge service...\e[0m"
# In a real setup this might be a systemd service or docker container.
# For demo, assuming it's part of docker-compose.m1.yml
docker compose -f docker-compose.m1.yml up -d opcua_bridge

echo -e "\e[1;34mWaiting for FastAPI (Hub) to be healthy...\e[0m"
while true; do
    STATUS=$(curl -s http://${M2_IP}:8000/health | grep -o '"status":"ok"')
    if [ "$STATUS" == '"status":"ok"' ]; then
        echo -e "\e[1;32mFastAPI is ready!\e[0m"
        break
    fi
    echo "Waiting for FastAPI on ${M2_IP}:8000..."
    sleep 2
done

echo -e "\e[1;34mStarting simulator and OPC-UA server...\e[0m"
docker compose -f docker-compose.m1.yml up -d simulator

echo -e "\e[1;32mMachine 1 ready — OPC-UA: opc.tcp://${M1_IP}:4840\e[0m"
exit 0
