from dataclasses import dataclass
from datetime import datetime


@dataclass
class SensorDefinition:
    id: str
    name: str
    subsystem: str
    unit: str
    baseline_value: float
    noise_amplitude: float
    min_threshold: float
    max_threshold: float
    sampling_interval_ms: int


@dataclass
class SensorReading:
    sensor_id: str
    name: str
    subsystem: str
    value: float
    unit: str
    status: str
    timestamp: datetime
    max_threshold: float
    min_threshold: float
    quality: str
