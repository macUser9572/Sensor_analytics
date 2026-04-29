from simulator.models import SensorDefinition, SensorReading
from simulator.registry import generate_sensor_registry

__all__ = [
    "SensorDefinition",
    "SensorReading",
    "SimulatorService",
    "generate_sensor_registry",
]


def __getattr__(name: str):
    if name == "SimulatorService":
        from simulator.service import SimulatorService

        return SimulatorService
    raise AttributeError(name)
