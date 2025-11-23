"""
לוגיקה ונתוני דמו למודול Dashboard
"""

from datetime import datetime


def get_dashboard_data():
    """מחזיר נתוני דמו ל-Dashboard"""
    return {
        "system_status": "Online",
        "battery_level": 85,
        "connection_status": "Connected",
        "flight_time": "00:15:32",
        "altitude": 45.2,
        "speed": 12.5,
        "gps_satellites": 12,
        "signal_strength": 95,
        "last_update": datetime.now().strftime("%H:%M:%S"),
    }
