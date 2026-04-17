from dataclasses import dataclass
from typing import List

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

def generate_sensors() -> List[SensorDefinition]:
    sensors = []
    
    # Turbine (120 sensors)
    for i in range(1, 121):
        if i <= 40:
            sensors.append(SensorDefinition(f"T{i:03d}", f"HP Turbine Bearing {i} Temp", "turbine", "°C", 85.0, 0.5, 40.0, 120.0))
        elif i <= 80:
            sensors.append(SensorDefinition(f"T{i:03d}", f"Turbine RPM {i-40}", "turbine", "RPM", 3000.0, 10.0, 2800.0, 3200.0))
        else:
            sensors.append(SensorDefinition(f"T{i:03d}", f"Turbine Vibration {i-80}", "turbine", "mm/s", 2.5, 0.1, 0.0, 7.0))

    # Boiler (100 sensors)
    for i in range(1, 101):
        if i <= 50:
            sensors.append(SensorDefinition(f"B{i:03d}", f"Steam Pressure {i}", "boiler", "bar", 170.0, 1.5, 150.0, 190.0))
        else:
            sensors.append(SensorDefinition(f"B{i:03d}", f"Flue Gas Temp {i-50}", "boiler", "°C", 140.0, 1.0, 110.0, 160.0))

    # Generator (80 sensors)
    for i in range(1, 81):
        if i <= 40:
            sensors.append(SensorDefinition(f"G{i:03d}", f"Terminal Voltage {i}", "generator", "kV", 21.0, 0.1, 19.5, 22.5))
        else:
            sensors.append(SensorDefinition(f"G{i:03d}", f"Stator Current {i-40}", "generator", "A", 15000.0, 100.0, 13000.0, 17000.0))

    # Cooling System (80 sensors)
    for i in range(1, 81):
        if i <= 40:
            sensors.append(SensorDefinition(f"C{i:03d}", f"Cooling Water Flow {i}", "cooling", "m³/h", 45000.0, 200.0, 40000.0, 50000.0))
        else:
            sensors.append(SensorDefinition(f"C{i:03d}", f"Condenser Vacuum {i-40}", "cooling", "kPa", 9.0, 0.2, 5.0, 15.0))

    # Transformer (60 sensors)
    for i in range(1, 61):
        if i <= 30:
            sensors.append(SensorDefinition(f"TR{i:03d}", f"Transformer Oil Temp {i}", "transformer", "°C", 65.0, 0.2, 40.0, 90.0))
        else:
            sensors.append(SensorDefinition(f"TR{i:03d}", f"Load Current {i-30}", "transformer", "A", 800.0, 10.0, 500.0, 1000.0))
            
    # Auxiliary (60 sensors)
    for i in range(1, 61):
        if i <= 30:
            sensors.append(SensorDefinition(f"A{i:03d}", f"Pump Discharge Press {i}", "auxiliary", "bar", 12.0, 0.2, 8.0, 16.0))
        else:
            sensors.append(SensorDefinition(f"A{i:03d}", f"Control Valve Pos {i-30}", "auxiliary", "%", 50.0, 0.5, 10.0, 90.0))

    return sensors
