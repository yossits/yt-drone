"""
Global application settings
"""

from typing import Optional


class Settings:
    """Application settings"""

    APP_NAME: str = "YT-Drone"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Paths
    TEMPLATES_DIR: str = "templates"
    STATIC_DIR: str = "static"


settings = Settings()
