"""
Logic and demo data for Users module
"""

def get_users_data():
    """Returns demo data for Users"""
    return {
        "users": [
            {
                "id": 1,
                "username": "admin",
                "email": "admin@example.com",
                "role": "Administrator",
                "status": "Active",
                "last_login": "2024-01-15 10:30:00"
            },
            {
                "id": 2,
                "username": "pilot1",
                "email": "pilot1@example.com",
                "role": "Pilot",
                "status": "Active",
                "last_login": "2024-01-15 09:15:00"
            },
            {
                "id": 3,
                "username": "viewer1",
                "email": "viewer1@example.com",
                "role": "Viewer",
                "status": "Inactive",
                "last_login": "2024-01-14 15:20:00"
            }
        ]
    }

