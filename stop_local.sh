#!/usr/bin/env bash
# stop_local.sh — stop all local machines
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "▶ Stopping all machines..."
docker compose -f docker-compose.m4.yml down
docker compose -f docker-compose.m1.yml down
docker compose -f docker-compose.m2.yml down
docker compose -f docker-compose.m3.yml down
echo "✅ All machines stopped."
