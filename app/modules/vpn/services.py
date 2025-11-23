"""
לוגיקה ונתוני דמו למודול VPN
"""

def get_vpn_data():
    """מחזיר נתוני דמו ל-VPN"""
    return {
        "enabled": True,
        "server": "vpn.example.com",
        "protocol": "OpenVPN",
        "status": "Connected",
        "ip_address": "192.168.1.100",
        "uptime": "2d 5h 32m"
    }

