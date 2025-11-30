"""
Logic and demo data for Flight Controller module
"""
import json
from pathlib import Path

# Path to data file
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
STATUS_FILE = DATA_DIR / "flight_controller_status.json"
SETTINGS_FILE = DATA_DIR / "flight_controller_settings.json"


def ensure_data_dir():
    """Creates the data directory if it doesn't exist"""
    DATA_DIR.mkdir(exist_ok=True)


def load_fc_status():
    """Loads flight controller status from JSON file"""
    ensure_data_dir()
    
    if not STATUS_FILE.exists():
        # Create default file if it doesn't exist
        default_status = {"connected": False, "device": None, "baud": None}
        save_fc_status(False, None, None)
        return default_status
    
    try:
        with open(STATUS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {
                "connected": data.get('connected', False),
                "device": data.get('device', None),
                "baud": data.get('baud', None)
            }
    except (json.JSONDecodeError, IOError):
        return {"connected": False, "device": None, "baud": None}


def save_fc_status(connected: bool, device: str = None, baud: int = None):
    """Saves flight controller status to JSON file"""
    ensure_data_dir()
    
    data = {
        "connected": connected,
        "device": device,
        "baud": baud
    }
    
    try:
        with open(STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except IOError:
        return False


def load_fc_settings():
    """Loads flight controller settings from JSON file"""
    ensure_data_dir()
    
    if not SETTINGS_FILE.exists():
        # Create default file if it doesn't exist
        default_settings = {
            "connection_type": "serial",
            "device": "/dev/serial0",
            "baud": 57600
        }
        save_fc_settings(default_settings)
        return default_settings
    
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {
                "connection_type": data.get('connection_type', 'serial'),
                "device": data.get('device', '/dev/serial0'),
                "baud": data.get('baud', 57600)
            }
    except (json.JSONDecodeError, IOError):
        return {
            "connection_type": "serial",
            "device": "/dev/serial0",
            "baud": 57600
        }


def save_fc_settings(settings: dict):
    """Saves flight controller settings to JSON file"""
    ensure_data_dir()
    
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        return True
    except IOError:
        return False


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
