"""
לוגיקה ונתוני דמו למודול Ground Control Station
"""
from datetime import datetime

def get_gcs_data():
    """מחזיר נתוני דמו ל-Ground Control Station"""
    return {
        "logs": [
            {"time": "10:15:32", "level": "INFO", "message": "System initialized"},
            {"time": "10:15:35", "level": "INFO", "message": "Flight controller connected"},
            {"time": "10:15:40", "level": "WARNING", "message": "GPS signal weak"},
            {"time": "10:15:45", "level": "INFO", "message": "GPS signal restored"},
            {"time": "10:16:00", "level": "INFO", "message": "Ready for takeoff"},
        ],
        "commands": [
            "ARM",
            "DISARM",
            "TAKEOFF",
            "LAND",
            "RTL",
            "GUIDED",
            "AUTO"
        ]
    }

