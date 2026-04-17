import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List

import redis.asyncio as aioredis
from app.config import settings
from app.simulator.sensor_registry import generate_sensors, SensorDefinition
from app.simulator.noise import gaussian_noise, slow_drift, anomaly_ramp

class SimulatorService:
    def __init__(self):
        self.sensors: List[SensorDefinition] = generate_sensors()
        self.current_state: Dict[str, float] = {s.id: s.baseline_value for s in self.sensors}
        self.active_faults: Dict[str, float] = {}
        
        self.is_running = False
        self._task = None
        self.redis = None

    async def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        self._task = asyncio.create_task(self._loop())

    async def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self.redis:
            await self.redis.close()

    async def _loop(self):
        while self.is_running:
            await self.tick()
            await asyncio.sleep(1)

    async def tick(self):
        now_str = datetime.now(timezone.utc).isoformat()
        now_ts = time.time()
        
        grouped_readings: Dict[str, List[Dict]] = {}
        
        for sensor in self.sensors:
            current = self.current_state[sensor.id]
            
            if sensor.id in self.active_faults:
                target = self.active_faults[sensor.id]
                step = max(abs(target - sensor.baseline_value) / 30.0, 0.01)
                new_value = anomaly_ramp(current, target, step)
            else:
                new_value = slow_drift(current, sensor.baseline_value, sensor.noise_amplitude * 0.1)
                
            new_value = gaussian_noise(new_value, sensor.noise_amplitude)
            self.current_state[sensor.id] = round(new_value, 2)
            
            val = self.current_state[sensor.id]
            
            if val >= sensor.max_threshold:
                status = "critical"
            elif val >= 0.8 * sensor.max_threshold:
                status = "warning"
            else:
                status = "normal"
            
            reading_doc = {
                "id": sensor.id,
                "name": sensor.name,
                "value": val,
                "unit": sensor.unit,
                "status": status,
                "min_threshold": sensor.min_threshold,
                "max_threshold": sensor.max_threshold
            }
            
            sub = sensor.subsystem
            if sub not in grouped_readings:
                grouped_readings[sub] = []
            grouped_readings[sub].append(reading_doc)

        if not self.redis:
            return

        pipeline = self.redis.pipeline()
        for sub, readings in grouped_readings.items():
            payload = {
                "subsystem": sub,
                "timestamp": now_str,
                "readings": readings
            }
            payload_json = json.dumps(payload)
            pipeline.publish(f"subsystem:{sub}", payload_json)
            key = f"buffer:subsystem:{sub}"
            pipeline.zadd(key, {payload_json: now_ts})
            pipeline.zremrangebyscore(key, "-inf", now_ts - 60)
            
        await pipeline.execute()

    def trigger_fault(self, sensor_id: str, target_multiplier: float = 1.2):
        for s in self.sensors:
            if s.id == sensor_id:
                self.active_faults[sensor_id] = s.max_threshold * target_multiplier
                return
        raise ValueError(f"Sensor {sensor_id} not found")

    def resolve_fault(self, sensor_id: str):
        if sensor_id in self.active_faults:
            del self.active_faults[sensor_id]

    def get_current_readings(self) -> Dict[str, Any]:
        result = []
        for s in self.sensors:
            result.append({
                "id": s.id,
                "name": s.name,
                "subsystem": s.subsystem,
                "unit": s.unit,
                "value": self.current_state[s.id],
                "baseline": s.baseline_value
            })
        return {"readings": result}
        
    def get_sensors_metadata(self) -> Dict[str, Any]:
        return {"sensors": [s.__dict__ for s in self.sensors]}
