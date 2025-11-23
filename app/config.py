"""
הגדרות גלובליות לאפליקציה
"""

from typing import Optional


class Settings:
    """הגדרות האפליקציה"""

    APP_NAME: str = "Drone Control Center"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # נתיבים
    TEMPLATES_DIR: str = "templates"
    STATIC_DIR: str = "static"


settings = Settings()
