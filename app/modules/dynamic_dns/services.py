"""
Logic and demo data for Dynamic DNS module
"""


def get_dns_data():
    """Returns demo data for Dynamic DNS"""
    return {
        "enabled": True,
        "provider": "DuckDNS",
        "domain": "my-drone.duckdns.org",
        "current_ip": "185.123.45.67",
        "last_update": "2024-01-15 10:30:00",
        "update_interval": "5 minutes",
    }
