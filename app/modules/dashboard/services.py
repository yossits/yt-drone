"""
Logic and demo data for Dashboard module
"""

import subprocess
import logging
from datetime import datetime
from app.core.system import get_system_info, get_storage_info

logger = logging.getLogger(__name__)


def get_dashboard_data():
    """Returns demo data for Dashboard"""
    # Collect real system data
    system_data = get_system_info()
    storage_data = get_storage_info()
    
    return {
        # Real system data
        "os_name": system_data["os_name"],
        "hardware": system_data["hardware"],
        "uptime": system_data["uptime"],
        "cpu_temp": system_data["cpu_temp"],
        "cpu_temp_percent": system_data["cpu_temp_percent"],
        "temp_class": system_data["temp_class"],
        "cpu_usage": system_data["cpu_usage"],
        "ram_used": system_data["ram_used"],
        "ram_total": system_data["ram_total"],
        "ram_percent": system_data["ram_percent"],
        # Storage data
        "storage_boot": storage_data["boot"],
        "storage_root": storage_data["root"],
        # Demo data (for future)
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


def check_autostart_status() -> bool:
    """
    Check if the systemd service is enabled for autostart
    Returns:
        True if service is enabled, False otherwise
    """
    service_name = "yt-drone.service"
    try:
        # Check if service is enabled using systemctl
        result = subprocess.run(
            ["systemctl", "is-enabled", service_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # systemctl is-enabled returns "enabled" if enabled, other statuses if not
        is_enabled = result.returncode == 0 and result.stdout.strip() == "enabled"
        
        logger.debug(f"Autostart status check: service={service_name}, enabled={is_enabled}")
        return is_enabled
        
    except subprocess.TimeoutExpired:
        logger.warning(f"Timeout checking autostart status for {service_name}")
        return False
    except FileNotFoundError:
        logger.warning("systemctl command not found, cannot check autostart status")
        return False
    except Exception as e:
        logger.error(f"Error checking autostart status: {e}", exc_info=True)
        return False
