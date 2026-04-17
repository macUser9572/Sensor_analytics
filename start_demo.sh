#!/usr/bin/env bash
set -e

echo "============================================="
echo "🚀 STAGE 1/3: Starting Infrastructure..."
echo "============================================="
docker compose up -d

echo "============================================="
echo "⏳ STAGE 2/3: Waiting for Services..."
echo "============================================="

# Wait for the database
echo "Checking TimescaleDB readiness..."
until docker compose exec -T db pg_isready -U postgres > /dev/null 2>&1; do
    echo -n "."
    sleep 2
done
echo " DB is ready!"

# Wait for the API (sensors endpoint ensures it has booted and seeded)
echo "Checking FastAPI backend..."
until curl -s http://localhost:8000/simulator/sensors > /dev/null; do
    echo -n "."
    sleep 2
done
echo " API is ready!"

echo "============================================="
echo "📡 STAGE 3/3: Network Configuration..."
echo "============================================="

# Auto-detect Local IP for Mobile App connection
if command -v ipconfig >/dev/null 2>&1; then
    # MacOS
    IP=$(ipconfig getifaddr en0 || ipconfig getifaddr en1 || echo "127.0.0.1")
elif command -v hostname >/dev/null 2>&1; then
    # Linux / WSL
    IP=$(hostname -I | awk '{print $1}' || echo "127.0.0.1")
else
    IP="127.0.0.1"
fi

echo "=========================================================="
echo "✅ READY FOR DEMO"
echo "=========================================================="
echo "🌍 Laptop Browser:     http://localhost:3000"
echo "📲 Network Access:     http://$IP:3000"
echo "🔌 Backend API:        http://$IP:8000"
echo ""
echo "📱 FLUTTER COMPANION APP INSTRUCTIONS:"
echo "Update your Flutter networking code (e.g., api_service.dart) to:"
echo "   BASE_URL = 'http://$IP:8000'"
echo "   WS_URL   = 'ws://$IP:8000/ws'"
echo "=========================================================="
