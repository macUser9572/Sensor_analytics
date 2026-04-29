from simulator.models import SensorDefinition


GENERATOR_INTERVAL_MS = 2000
BOILER_INTERVAL_MS = 5000
TURBINE_INTERVAL_MS = 10000
SLOW_INTERVAL_MS = 15000


def _variation(index: int, step: float, spread: int = 5) -> float:
    return ((index - 1) % spread - spread // 2) * step


def _sensor(
    sensor_id: str,
    name: str,
    subsystem: str,
    unit: str,
    baseline: float,
    noise: float,
    min_threshold: float,
    max_threshold: float,
    sampling_interval_ms: int,
) -> SensorDefinition:
    return SensorDefinition(
        id=sensor_id,
        name=name,
        subsystem=subsystem,
        unit=unit,
        baseline_value=round(baseline, 3),
        noise_amplitude=noise,
        min_threshold=round(min_threshold, 3),
        max_threshold=round(max_threshold, 3),
        sampling_interval_ms=sampling_interval_ms,
    )


def _generate_turbine() -> list[SensorDefinition]:
    sensors: list[SensorDefinition] = []

    for i in range(1, 33):
        prefix = "HP" if i <= 16 else "LP"
        bearing_no = i if i <= 16 else i - 16
        sensors.append(
            _sensor(
                f"T{i:03d}",
                f"{prefix} Turbine Bearing {bearing_no:02d} Temperature",
                "turbine",
                "°C",
                85.0,
                0.5,
                45.0,
                120.0,
                TURBINE_INTERVAL_MS,
            )
        )

    for i in range(33, 49):
        section_no = i - 32
        sensors.append(
            _sensor(
                f"T{i:03d}",
                f"Turbine Shaft Section {section_no:02d} Speed",
                "turbine",
                "RPM",
                3000.0,
                2.0,
                2850.0,
                3150.0,
                TURBINE_INTERVAL_MS,
            )
        )

    for i in range(49, 81):
        bearing_no = i - 48
        baseline = 2.8 + _variation(i, 0.04)
        sensors.append(
            _sensor(
                f"T{i:03d}",
                f"Turbine Bearing {bearing_no:02d} Radial Vibration",
                "turbine",
                "mm/s",
                baseline,
                0.05,
                0.0,
                7.1,
                TURBINE_INTERVAL_MS,
            )
        )

    for i in range(81, 105):
        stage_no = i - 80
        baseline = 535.0 + _variation(i, 2.0)
        sensors.append(
            _sensor(
                f"T{i:03d}",
                f"Main Steam Line {stage_no:02d} Temperature",
                "turbine",
                "°C",
                baseline,
                1.0,
                480.0,
                565.0,
                TURBINE_INTERVAL_MS,
            )
        )

    for i in range(105, 121):
        probe_no = i - 104
        baseline = 0.08 + _variation(i, 0.003)
        sensors.append(
            _sensor(
                f"T{i:03d}",
                f"Turbine Shaft Eccentricity Probe {probe_no:02d}",
                "turbine",
                "mm",
                baseline,
                0.004,
                0.0,
                0.25,
                TURBINE_INTERVAL_MS,
            )
        )

    return sensors


def _generate_boiler() -> list[SensorDefinition]:
    sensors: list[SensorDefinition] = []

    categories = [
        ("Drum Pressure Transmitter", "bar", 150.0, 0.2, 125.0, 180.0),
        ("Drum Water Level Gauge", "mm", 0.0, 4.0, -250.0, 250.0),
        ("Economizer Outlet Flue Gas Temperature", "°C", 365.0, 1.5, 280.0, 430.0),
        ("Feed Water Flow Element", "t/h", 1550.0, 6.0, 900.0, 1900.0),
        ("Final Superheater Outlet Temperature", "°C", 540.0, 1.2, 500.0, 570.0),
    ]

    sensor_no = 1
    for title, unit, baseline, noise, min_threshold, max_threshold in categories:
        for i in range(1, 21):
            sensors.append(
                _sensor(
                    f"B{sensor_no:03d}",
                    f"Boiler {title} {i:02d}",
                    "boiler",
                    unit,
                    baseline + _variation(i, noise * 0.4),
                    noise,
                    min_threshold,
                    max_threshold,
                    BOILER_INTERVAL_MS,
                )
            )
            sensor_no += 1

    return sensors


def _generate_generator() -> list[SensorDefinition]:
    sensors: list[SensorDefinition] = []

    categories = [
        ("Generator Terminal Voltage Phase", "kV", 11.0, 0.05, 10.5, 11.5),
        ("Generator Stator Current Phase", "A", 15500.0, 45.0, 9000.0, 18000.0),
        ("Generator Grid Frequency Channel", "Hz", 50.0, 0.02, 48.5, 51.5),
        ("Generator Stator Winding Temperature", "°C", 92.0, 0.4, 45.0, 125.0),
        ("Generator Active Power Export", "MW", 500.0, 1.5, 250.0, 540.0),
    ]

    sensor_no = 1
    for title, unit, baseline, noise, min_threshold, max_threshold in categories:
        for i in range(1, 17):
            sensors.append(
                _sensor(
                    f"G{sensor_no:03d}",
                    f"{title} {i:02d}",
                    "generator",
                    unit,
                    baseline + _variation(i, noise * 0.5),
                    noise,
                    min_threshold,
                    max_threshold,
                    GENERATOR_INTERVAL_MS,
                )
            )
            sensor_no += 1

    return sensors


def _generate_cooling() -> list[SensorDefinition]:
    sensors: list[SensorDefinition] = []

    categories = [
        ("Cooling Water Circulation Pump Flow", 20, "m³/h", 42000.0, 120.0, 30000.0, 52000.0),
        ("Cooling Water Condenser Inlet Temperature", 15, "°C", 31.0, 0.2, 20.0, 40.0),
        ("Cooling Water Condenser Outlet Temperature", 15, "°C", 41.0, 0.25, 28.0, 52.0),
        ("Condenser Back Pressure", 15, "mbar", 85.0, 0.8, 45.0, 140.0),
        ("Condenser Vacuum", 15, "%", 92.0, 0.15, 80.0, 100.0),
    ]

    sensor_no = 1
    for title, count, unit, baseline, noise, min_threshold, max_threshold in categories:
        for i in range(1, count + 1):
            sensors.append(
                _sensor(
                    f"C{sensor_no:03d}",
                    f"{title} {i:02d}",
                    "cooling",
                    unit,
                    baseline + _variation(i, noise * 0.4),
                    noise,
                    min_threshold,
                    max_threshold,
                    SLOW_INTERVAL_MS,
                )
            )
            sensor_no += 1

    return sensors


def _generate_transformer() -> list[SensorDefinition]:
    sensors: list[SensorDefinition] = []

    categories = [
        ("Generator Transformer Oil Temperature", "°C", 68.0, 0.3, 35.0, 95.0),
        ("Generator Transformer Load Current", "A", 820.0, 5.0, 300.0, 1100.0),
        ("Generator Transformer On-load Tap Position", "tap", 9.0, 0.0, 1.0, 17.0),
        ("Generator Transformer Winding Temperature", "°C", 78.0, 0.4, 40.0, 110.0),
    ]

    sensor_no = 1
    for title, unit, baseline, noise, min_threshold, max_threshold in categories:
        for i in range(1, 16):
            sensors.append(
                _sensor(
                    f"TR{sensor_no:03d}",
                    f"{title} {i:02d}",
                    "transformer",
                    unit,
                    baseline + _variation(i, max(noise, 0.2) * 0.4),
                    noise,
                    min_threshold,
                    max_threshold,
                    SLOW_INTERVAL_MS,
                )
            )
            sensor_no += 1

    return sensors


def _generate_auxiliary() -> list[SensorDefinition]:
    sensors: list[SensorDefinition] = []

    categories = [
        ("Induced Draft Fan Motor Current", "A", 310.0, 2.5, 120.0, 430.0),
        ("Boiler Feed Pump Discharge Pressure", "bar", 175.0, 0.4, 120.0, 220.0),
        ("Fuel Oil Header Pressure", "bar", 12.5, 0.08, 8.0, 18.0),
        ("Main Steam Bypass Valve Position", "%", 42.0, 0.4, 0.0, 100.0),
    ]

    sensor_no = 1
    for title, unit, baseline, noise, min_threshold, max_threshold in categories:
        for i in range(1, 16):
            sensor_title = title
            if title == "Induced Draft Fan Motor Current" and i > 8:
                sensor_title = "Forced Draft Fan Motor Current"
            sensors.append(
                _sensor(
                    f"A{sensor_no:03d}",
                    f"{sensor_title} {i:02d}",
                    "auxiliary",
                    unit,
                    baseline + _variation(i, noise * 0.5),
                    noise,
                    min_threshold,
                    max_threshold,
                    SLOW_INTERVAL_MS,
                )
            )
            sensor_no += 1

    return sensors


def generate_sensor_registry() -> list[SensorDefinition]:
    sensors = [
        *_generate_turbine(),
        *_generate_boiler(),
        *_generate_generator(),
        *_generate_cooling(),
        *_generate_transformer(),
        *_generate_auxiliary(),
    ]

    if len(sensors) != 500:
        raise RuntimeError(f"Expected 500 sensors, generated {len(sensors)}")
    return sensors
