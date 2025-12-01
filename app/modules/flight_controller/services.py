"""
Logic and demo data for Flight Controller module
"""


def get_flight_controller_data():
    """Returns demo data for Flight Controller"""
    return {
        "flight_mode": "GUIDED",
        "arm_status": "ARMED",
        "failsafe": "Disabled",
        "throttle": 45,
        "roll": 0.2,
        "pitch": -0.1,
        "yaw": 12.5,
        "battery_voltage": 12.6,
        "battery_current": 15.3,
        "cpu_load": 25,
        "memory_usage": 45,
    }
