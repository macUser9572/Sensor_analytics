import random

def gaussian_noise(value: float, amplitude: float) -> float:
    """Adds Gaussian noise to a base value"""
    return value + random.gauss(0, amplitude)

def slow_drift(current_value: float, baseline: float, drift_rate: float) -> float:
    """Slowly drifts value toward or away from baseline over time"""
    # Use a small random step bounded by drift_rate
    drift = random.uniform(-drift_rate, drift_rate)
    # Revert to baseline slowly
    reversion = (baseline - current_value) * 0.05
    return current_value + drift + reversion

def anomaly_ramp(current_value: float, target: float, step: float) -> float:
    """Moves value toward a fault target incrementally each second."""
    if current_value < target:
        return min(current_value + step, target)
    else:
        return max(current_value - step, target)
