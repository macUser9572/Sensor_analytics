import asyncio
import logging
from datetime import UTC, datetime

from config import settings
from simulator.models import SensorDefinition, SensorReading
from simulator.noise import anomaly_ramp, gaussian_noise, slow_drift
from simulator.registry import generate_sensor_registry


logger = logging.getLogger(__name__)


class SimulatorService:
    def __init__(self) -> None:
        self.sensors: list[SensorDefinition] = generate_sensor_registry()
        self._sensor_by_id: dict[str, SensorDefinition] = {sensor.id: sensor for sensor in self.sensors}
        self.current_state: dict[str, float] = {
            sensor.id: sensor.baseline_value for sensor in self.sensors
        }
        self.fault_mode: dict[str, bool] = {}
        self.fault_targets: dict[str, float] = {}
        self.killed_sensors: set[str] = set()
        self._fault_steps: dict[str, float] = {}
        self._task: asyncio.Task | None = None
        self._running = False
        self._lock = asyncio.Lock()
        self._last_timestamp = datetime.now(UTC)

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        logger.info("Simulator ready with %s sensors; OPC-UA server drives ticks", len(self.sensors))

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Simulator stopped. Active faults: %s", sorted(self.fault_targets))

    async def tick(self) -> list[SensorReading]:
        async with self._lock:
            timestamp = datetime.now(UTC)
            readings: list[SensorReading] = []

            for sensor in self.sensors:
                current = self.current_state[sensor.id]
                next_value = gaussian_noise(current, sensor.noise_amplitude)
                next_value = slow_drift(next_value, sensor.baseline_value, rate=0.02)

                if self.fault_mode.get(sensor.id):
                    target = self.fault_targets[sensor.id]
                    step = self._fault_steps[sensor.id]
                    next_value = anomaly_ramp(next_value, target, step)

                next_value = self._normalize_value(sensor, next_value)
                self.current_state[sensor.id] = next_value
                readings.append(self._reading_for(sensor, timestamp))

            self._last_timestamp = timestamp
            return readings

    def trigger_fault(self, sensor_id: str, target_multiplier: float = 1.2) -> None:
        sensor = self.get_sensor(sensor_id)
        if sensor is None:
            raise ValueError(f"Sensor {sensor_id} not found")

        tick_seconds = max(settings.simulator_tick_ms / 1000, 0.1)
        ramp_ticks = max(int(30 / tick_seconds), 1)
        target = sensor.max_threshold * target_multiplier
        current = self.current_state[sensor_id]

        self.fault_mode[sensor_id] = True
        self.fault_targets[sensor_id] = target
        self._fault_steps[sensor_id] = max(abs(target - current) / ramp_ticks, 0.01)
        logger.info("Fault triggered for %s toward %.3f", sensor_id, target)

    def resolve_fault(self, sensor_id: str) -> None:
        self.fault_mode.pop(sensor_id, None)
        self.fault_targets.pop(sensor_id, None)
        self._fault_steps.pop(sensor_id, None)
        logger.info("Fault resolved for %s", sensor_id)

    def resolve_all_faults(self) -> list[str]:
        sensor_ids = sorted(set(self.fault_targets) | self.killed_sensors)
        for sensor_id in sensor_ids:
            self.resolve_fault(sensor_id)
            self.revive_sensor(sensor_id)
        return sensor_ids

    def kill_sensor(self, sensor_id: str) -> None:
        if self.get_sensor(sensor_id) is None:
            raise ValueError(f"Sensor {sensor_id} not found")
        self.killed_sensors.add(sensor_id)
        logger.info("Sensor publishing killed for %s", sensor_id)

    def revive_sensor(self, sensor_id: str) -> None:
        self.killed_sensors.discard(sensor_id)
        logger.info("Sensor publishing revived for %s", sensor_id)

    def is_sensor_killed(self, sensor_id: str) -> bool:
        return sensor_id in self.killed_sensors

    def get_current_readings(self) -> list[SensorReading]:
        timestamp = self._last_timestamp
        return [self._reading_for(sensor, timestamp) for sensor in self.sensors]

    def get_sensor(self, sensor_id: str) -> SensorDefinition | None:
        return self._sensor_by_id.get(sensor_id)

    @property
    def registry(self) -> list[SensorDefinition]:
        return self.sensors

    def get_active_faults(self) -> list[dict[str, float | str]]:
        ramp_faults = [
            {
                "sensor_id": sensor_id,
                "kind": "threshold",
                "target": target,
                "current_value": self.current_state[sensor_id],
            }
            for sensor_id, target in sorted(self.fault_targets.items())
        ]
        stopped_faults = [
            {
                "sensor_id": sensor_id,
                "kind": "sensor_fault",
                "target": self.current_state[sensor_id],
                "current_value": self.current_state[sensor_id],
            }
            for sensor_id in sorted(self.killed_sensors)
            if sensor_id not in self.fault_targets
        ]
        return [*ramp_faults, *stopped_faults]

    def fault_snapshot(self, sensor_id: str, *, quality: str = "bad") -> dict:
        sensor = self.get_sensor(sensor_id)
        if sensor is None:
            raise ValueError(f"Sensor {sensor_id} not found")

        return {
            "id": sensor_id,
            "sensor_id": sensor_id,
            "name": sensor.name,
            "subsystem": sensor.subsystem,
            "value": self.current_state[sensor_id],
            "unit": sensor.unit,
            "status": "fault",
            "quality": quality,
            "max_threshold": sensor.max_threshold,
            "min_threshold": sensor.min_threshold,
            "baseline_value": sensor.baseline_value,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def _reading_for(self, sensor: SensorDefinition, timestamp: datetime) -> SensorReading:
        value = self.current_state[sensor.id]
        return SensorReading(
            sensor_id=sensor.id,
            name=sensor.name,
            subsystem=sensor.subsystem,
            value=value,
            unit=sensor.unit,
            status=self._status_for(sensor, value),
            timestamp=timestamp,
            max_threshold=sensor.max_threshold,
            min_threshold=sensor.min_threshold,
            baseline_value=sensor.baseline_value,
            quality="good",
        )

    def _status_for(self, sensor: SensorDefinition, value: float) -> str:
        if value <= sensor.min_threshold:
            return "critical"
        if value >= sensor.max_threshold:
            return "critical"

        threshold_span = sensor.max_threshold - sensor.baseline_value
        threshold_ratio = (value - sensor.baseline_value) / threshold_span if threshold_span else 0.0
        if threshold_ratio >= settings.warning_threshold_pct:
            return "warning"
        return "normal"

    def _normalize_value(self, sensor: SensorDefinition, value: float) -> float:
        if sensor.unit == "tap":
            return float(round(value))
        if sensor.unit in {"Hz", "mm", "mm/s"}:
            return round(value, 3)
        if sensor.unit in {"kV", "bar", "mbar"}:
            return round(value, 2)
        return round(value, 2)
