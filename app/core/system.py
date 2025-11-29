"""
Shared services for system data collection
Reusable across different modules
"""

import platform
import os
import psutil
from typing import Dict, Optional, Tuple


def get_os_info() -> str:
    """
    Returns operating system information
    Example: "Debian GNU/Linux 13 (bookworm)"
    """
    try:
        with open('/etc/os-release', 'r') as f:
            os_info = {}
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    os_info[key] = value.strip('"')
            
            # Example: "Debian GNU/Linux 13 (bookworm)"
            return os_info.get('PRETTY_NAME', f"{platform.system()} {platform.release()}")
    except Exception:
        # fallback to platform
        return f"{platform.system()} {platform.release()}"


def get_cpu_info() -> str:
    """
    Returns CPU information
    Example: "Sony UK BCM2837 (4 cores)"
    """
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpu_info = {}
            for line in f:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    if key not in cpu_info:
                        cpu_info[key] = value
            
            # Example: "Sony UK BCM2837"
            model = cpu_info.get('Model', cpu_info.get('Hardware', platform.processor()))
            cpu_count = os.cpu_count() or 1
            
            return f"{model} ({cpu_count} cores)"
    except Exception:
        return f"{platform.processor()} ({os.cpu_count() or 1} cores)"


def get_uptime() -> str:
    """
    Returns system uptime
    Example: "0 days 9 hours 12 minutes"
    """
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.read().split()[0])
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            
            return f"{days} days {hours} hours {minutes} minutes"
    except Exception:
        return "N/A"


def get_cpu_temperature() -> Optional[float]:
    """
    Returns CPU temperature in °C
    None if cannot be read
    """
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp = int(f.read().strip()) / 1000.0
            return round(temp, 1)
    except Exception:
        return None


def get_temperature_class(temperature: Optional[float]) -> str:
    """
    Returns CSS class based on temperature
    cold: < 40°C
    normal: 40-55°C
    warm: 55-70°C
    hot: > 70°C
    """
    if temperature is None:
        return "normal"
    
    if temperature < 40:
        return "cold"
    elif temperature < 55:
        return "normal"
    elif temperature < 70:
        return "warm"
    else:
        return "hot"


def get_cpu_usage() -> float:
    """
    Returns CPU usage percentage
    """
    try:
        return round(psutil.cpu_percent(interval=1), 1)
    except Exception:
        return 0.0


def get_ram_usage() -> Tuple[str, str, float]:
    """
    Returns RAM data: (used, total, percent)
    Example: ("1.2GB", "4.0GB", 30.0)
    """
    try:
        ram = psutil.virtual_memory()
        ram_total_gb = round(ram.total / (1024**3), 2)
        ram_used_gb = round(ram.used / (1024**3), 2)
        ram_percent = round(ram.percent, 1)
        
        return (f"{ram_used_gb}GB", f"{ram_total_gb}GB", ram_percent)
    except Exception:
        return ("0GB", "0GB", 0.0)


def get_static_info() -> Dict:
    """
    Static data that doesn't change
    For use in one-time updates
    """
    ram_used, ram_total, _ = get_ram_usage()
    
    return {
        "os_name": get_os_info(),
        "hardware": get_cpu_info(),
        "ram_total": ram_total,
    }


def get_storage_info() -> Dict:
    """
    Returns Storage data for Boot and Root partitions
    Returns:
        dict with boot and root storage info
    """
    try:
        boot_info = None
        root_info = None
        
        # Collect data on all partitions
        partitions = psutil.disk_partitions()
        
        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                
                # Boot partition - use MB instead of GB
                is_boot = partition.mountpoint == '/boot/firmware' or 'boot' in partition.mountpoint.lower()
                
                if is_boot:
                    total_mb = round(usage.total / (1024**2), 2)
                    used_mb = round(usage.used / (1024**2), 2)
                    free_mb = round(usage.free / (1024**2), 2)
                    percent = round(usage.percent, 2)
                    
                    partition_info = {
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "total": f"{total_mb} MB",
                        "used": f"{used_mb} MB",
                        "free": f"{free_mb} MB",
                        "percent": percent
                    }
                    boot_info = partition_info
                else:
                        # Root partition - use GB
                    total_gb = round(usage.total / (1024**3), 2)
                    used_gb = round(usage.used / (1024**3), 2)
                    free_gb = round(usage.free / (1024**3), 2)
                    percent = round(usage.percent, 2)
                
                partition_info = {
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "total": f"{total_gb} GB",
                    "used": f"{used_gb} GB",
                    "free": f"{free_gb} GB",
                    "percent": percent
                }
                
                # Root partition
                if partition.mountpoint == '/':
                    root_info = partition_info
                    
            except PermissionError:
                # Some partitions are not accessible
                continue
        
        return {
            "boot": boot_info or {
                "device": "N/A",
                "mountpoint": "/boot/firmware",
                "total": "0 MB",
                "used": "0 MB",
                "free": "0 MB",
                "percent": 0.0
            },
            "root": root_info or {
                "device": "N/A",
                "mountpoint": "/",
                "total": "0 GB",
                "used": "0 GB",
                "free": "0 GB",
                "percent": 0.0
            }
        }
    except Exception as e:
        return {
            "boot": {
                "device": "N/A",
                "mountpoint": "/boot/firmware",
                "total": "0 MB",
                "used": "0 MB",
                "free": "0 MB",
                "percent": 0.0
            },
            "root": {
                "device": "N/A",
                "mountpoint": "/",
                "total": "0 GB",
                "used": "0 GB",
                "free": "0 GB",
                "percent": 0.0
            }
        }


def get_slow_dynamic_info() -> Dict:
    """
    Dynamic data that changes slowly
    For use in updates every 60 seconds
    """
    storage_data = get_storage_info()
    
    return {
        "uptime": get_uptime(),
        "storage_boot": storage_data["boot"],
        "storage_root": storage_data["root"],
    }


def get_fast_dynamic_info() -> Dict:
    """
    Dynamic data that changes quickly
    For use in updates every 5 seconds
    """
    cpu_temp = get_cpu_temperature()
    cpu_temp_percent = min(100, int((cpu_temp / 85) * 100)) if cpu_temp else 0  # 85°C = 100%
    temp_class = get_temperature_class(cpu_temp)
    
    ram_used, _, ram_percent = get_ram_usage()
    
    return {
        "cpu_temp": cpu_temp or 0.0,
        "cpu_temp_percent": cpu_temp_percent,
        "temp_class": temp_class,
        "cpu_usage": get_cpu_usage(),
        "ram_used": ram_used,
        "ram_percent": ram_percent,
    }


def get_system_info() -> Dict:
    """
    Central function that returns dict with all system data
    For use in WebSocket and services
    Kept for backward compatibility
    """
    cpu_temp = get_cpu_temperature()
    cpu_temp_percent = min(100, int((cpu_temp / 85) * 100)) if cpu_temp else 0  # 85°C = 100%
    temp_class = get_temperature_class(cpu_temp)
    
    ram_used, ram_total, ram_percent = get_ram_usage()
    
    return {
        "os_name": get_os_info(),
        "hardware": get_cpu_info(),
        "uptime": get_uptime(),
        "cpu_temp": cpu_temp or 0.0,
        "cpu_temp_percent": cpu_temp_percent,
        "temp_class": temp_class,
        "cpu_usage": get_cpu_usage(),
        "ram_used": ram_used,
        "ram_total": ram_total,
        "ram_percent": ram_percent,
    }

