import random


def gaussian_noise(value: float, amplitude: float) -> float:
    return value + random.gauss(0.0, amplitude)


def slow_drift(current: float, baseline: float, rate: float = 0.005) -> float:
    return current + (baseline - current) * rate


def anomaly_ramp(current: float, target: float, step: float) -> float:
    if abs(target - current) <= step:
        return target
    if current < target:
        return current + step
    return current - step
