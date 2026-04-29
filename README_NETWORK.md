# BHEL LAN Deployment

This project is configured for four machines on the same LAN. Do not use loopback addresses in `.env`; every machine must point at the actual LAN IPs.

## 1. Create the shared `.env`

On your workstation:

```bash
cp .env.example .env
```

Edit these values first:

```dotenv
M1_IP=<machine-1-lan-ip>
M2_IP=<machine-2-lan-ip>
M3_IP=<machine-3-lan-ip>
M4_IP=<machine-4-lan-ip>
```

Keep service hosts derived from those IPs:

```dotenv
REDIS_HOST=${M2_IP}
DB_HOST=${M3_IP}
MINIO_HOST=${M3_IP}
REACT_API_BASE_URL=http://${M2_IP}:8000
REACT_WS_URL=ws://${M2_IP}:8000
FLUTTER_API_BASE_URL=http://${M2_IP}:8000
FLUTTER_WS_URL=ws://${M2_IP}:8000
```

Use real secrets for `JWT_SECRET`, `DB_PASSWORD`, and `MINIO_SECRET_KEY` before production use.

## 2. Copy `.env` to every machine

Copy the same `.env` file to the project root on M1, M2, M3, and M4:

```bash
scp .env user@<m1-ip>:/path/to/Sensor_analytics/.env
scp .env user@<m2-ip>:/path/to/Sensor_analytics/.env
scp .env user@<m3-ip>:/path/to/Sensor_analytics/.env
scp .env user@<m4-ip>:/path/to/Sensor_analytics/.env
```

The file should be identical on all machines unless the LAN IPs change.

## 3. Verify connectivity

Install Python dependencies on each machine, then run:

```bash
pip install -r requirements.txt
python env_check.py
```

Expected output:

```text
service     | IP           | port | status
------------+--------------+------+-------
redis       | <m2-ip>      | 6379 | OK
timescaledb | <m3-ip>      | 5432 | OK
minio       | <m3-ip>      | 9000 | OK
```

Run a single check when debugging:

```bash
python env_check.py --service redis
python env_check.py --service timescaledb
python env_check.py --service minio
```

## 4. Start services by machine

Machine 3:

```bash
docker compose -f docker-compose.m3.yml up -d
```

Machine 2:

```bash
docker compose -f docker-compose.m2.yml up -d
```

Machine 1:

```bash
docker compose -f docker-compose.m1.yml up -d
```

Machine 4:

```bash
docker compose -f docker-compose.m4.yml up -d
```

## 5. Demo IP changes

When the demo network changes, update only the machine IP block in `.env`. If M2 receives a new address, set:

```dotenv
M2_IP=<new-machine-2-lan-ip>
```

Because `REACT_API_BASE_URL`, `REACT_WS_URL`, `FLUTTER_API_BASE_URL`, and `FLUTTER_WS_URL` derive from `${M2_IP}`, restarting M1 and M4 is enough for clients and publishers to target the new backend.

Flutter builds must receive the current API values:

```bash
flutter run \
  --dart-define=FLUTTER_API_BASE_URL=http://${M2_IP}:8000 \
  --dart-define=FLUTTER_WS_URL=ws://${M2_IP}:8000
```
