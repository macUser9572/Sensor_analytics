from simulator.models import SensorDefinition
from simulator.registry import generate_sensor_registry


def generate_sensors() -> list[SensorDefinition]:
    return generate_sensor_registry()
