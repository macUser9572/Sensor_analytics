#!/usr/bin/env bash
# start_local.sh — run all 4 machines on a single Mac and open log terminals
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── 1. Ensure .env uses container names for single-machine ──────────────────
echo "▶ Applying single-machine .env settings..."
sed -i '' \
  -e 's/^M1_IP=.*/M1_IP=bhel_opcua_server/' \
  -e 's/^M2_IP=.*/M2_IP=bhel_redis/' \
  -e 's/^M3_IP=.*/M3_IP=bhel_timescaledb/' \
  -e 's/^M4_IP=.*/M4_IP=localhost/' \
  -e 's|^REACT_API_BASE_URL=.*|REACT_API_BASE_URL=http://localhost:8000|' \
  -e 's|^REACT_WS_URL=.*|REACT_WS_URL=ws://localhost:8000|' \
  -e 's|^FLUTTER_API_BASE_URL=.*|FLUTTER_API_BASE_URL=http://localhost:8000|' \
  -e 's|^FLUTTER_WS_URL=.*|FLUTTER_WS_URL=ws://localhost:8000|' \
  .env

# ── 2. Start M3 (TimescaleDB + MinIO) ───────────────────────────────────────
echo "▶ Starting M3 (TimescaleDB + MinIO)..."
docker compose -f docker-compose.m3.yml up -d

echo "   Waiting for TimescaleDB to be healthy..."
until [ "$(docker inspect --format='{{.State.Health.Status}}' bhel_timescaledb 2>/dev/null)" = "healthy" ]; do
  sleep 3
done
echo "   ✓ TimescaleDB ready"

# ── 3. Start M2 (Redis + FastAPI) ───────────────────────────────────────────
echo "▶ Starting M2 (Redis + FastAPI)..."
docker compose -f docker-compose.m2.yml up -d

echo "   Waiting for Redis to be healthy..."
until [ "$(docker inspect --format='{{.State.Health.Status}}' bhel_redis 2>/dev/null)" = "healthy" ]; do
  sleep 3
done
echo "   ✓ Redis ready"

# ── 4. Start M1 (OPC-UA server) ─────────────────────────────────────────────
echo "▶ Starting M1 (OPC-UA server)..."
docker compose -f docker-compose.m1.yml up -d
echo "   ✓ OPC-UA server starting"

# ── 5. Start M4 (React frontend) ────────────────────────────────────────────
echo "▶ Starting M4 (React frontend)..."
docker compose -f docker-compose.m4.yml up -d
echo "   ✓ React dashboard starting (npm install may take a minute)"

# ── 6. Open 5 Terminal windows with logs ────────────────────────────────────
echo "▶ Opening log terminals..."

# Helper: open a new Terminal window — title set via ANSI escape in the command
open_terminal() {
  local title="$1"
  local cmd="$2"
  osascript -e "tell application \"Terminal\" to do script \"printf '\\\\033]0;${title}\\\\007'; ${cmd}\"" || true
  sleep 0.5
}

open_terminal \
  "M1 - OPC-UA Server" \
  "cd '${SCRIPT_DIR}' && docker logs -f bhel_opcua_server 2>&1"

open_terminal \
  "M2 - FastAPI + Redis" \
  "cd '${SCRIPT_DIR}' && docker logs -f --since=0s bhel_fastapi 2>&1 & docker logs -f --since=0s bhel_redis 2>&1 | sed 's/^/[redis] /' & wait"

open_terminal \
  "M3 - TimescaleDB + MinIO" \
  "cd '${SCRIPT_DIR}' && docker logs -f --since=0s bhel_timescaledb 2>&1 | grep -Ev 'LOG|DETAIL|NOTICE|pg_wal|checkpoint' & docker logs -f --since=0s bhel_minio 2>&1 | sed 's/^/[minio] /' & wait"

open_terminal \
  "M4 - React Frontend" \
  "cd '${SCRIPT_DIR}' && docker logs -f bhel_react_dashboard 2>&1"

open_terminal \
  "All Machines - Health" \
  "while true; do clear; docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'; sleep 5; done"

echo ""
echo "✅ All machines started. Log terminals are opening."
echo ""
echo "   M1 OPC-UA      → opc.tcp://localhost:4840"
echo "   M2 FastAPI      → http://localhost:8000/health"
echo "   M3 TimescaleDB  → localhost:5432"
echo "   M3 MinIO        → http://localhost:9001  (console)"
echo "   M4 Frontend     → http://localhost:3000"
echo ""
echo "To stop everything:  ./stop_local.sh"
