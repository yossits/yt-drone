"""
Logic and demo data for Networks module
"""

def get_networks_data():
    """Returns demo data for Networks"""
    return {
        "networks": [
            {
                "name": "WiFi-5G",
                "type": "WiFi",
                "status": "Connected",
                "signal": 95,
                "ip": "192.168.1.10"
            },
            {
                "name": "LTE-Modem",
                "type": "LTE",
                "status": "Connected",
                "signal": 85,
                "ip": "10.0.0.15"
            },
            {
                "name": "Ethernet",
                "type": "Ethernet",
                "status": "Disconnected",
                "signal": 0,
                "ip": "-"
            }
        ]
    }

