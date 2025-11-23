"""
לוגיקה ונתוני דמו למודול Flight Controller
"""


def get_flight_controller_data():
    """מחזיר נתוני דמו ל-Flight Controller"""
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
