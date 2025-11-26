"""
לוגיקה ונתוני דמו למודול Application
"""

def get_application_data():
    """מחזיר נתוני דמו ל-Application"""
    return {
        "app_name": "YT-Drone",
        "version": "1.0.0",
        "build_date": "2024-01-15",
        "python_version": "3.11.0",
        "fastapi_version": "0.104.1",
        "auto_start": True,
        "log_level": "INFO",
        "max_log_size": "100 MB"
    }

