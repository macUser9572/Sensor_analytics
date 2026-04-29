#!/usr/bin/env bash
set -e

echo "============================================="
echo "🚀 STAGE 1/3: Starting Infrastructure..."
echo "============================================="
docker compose up -d

set -a
source .env
set +a

echo "============================================="
echo "⏳ STAGE 2/3: Waiting for Services..."
echo "============================================="

# Wait for the database
echo "Checking TimescaleDB readiness..."
until python3 env_check.py --service timescaledb > /dev/null 2>&1; do
    echo -n "."
    sleep 2
done
echo " DB is ready!"

# Wait for the API (sensors endpoint ensures it has booted and seeded)
echo "Checking FastAPI backend..."
until curl -s "${REACT_API_BASE_URL}/simulator/sensors" > /dev/null; do
    echo -n "."
    sleep 2
done
echo " API is ready!"

echo "============================================="
echo "📡 STAGE 3/3: Network Configuration..."
echo "============================================="

echo "=========================================================="
echo "✅ READY FOR DEMO"
echo "=========================================================="
echo "🌍 Dashboard:          http://${M4_IP}:3000"
echo "🔌 Backend API:        ${REACT_API_BASE_URL}"
echo ""
echo "📱 FLUTTER COMPANION APP INSTRUCTIONS:"
echo "Build or run with:"
echo "   --dart-define=FLUTTER_API_BASE_URL=${FLUTTER_API_BASE_URL}"
echo "   --dart-define=FLUTTER_WS_URL=${FLUTTER_WS_URL}"
echo "=========================================================="
