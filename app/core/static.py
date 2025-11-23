"""
הגדרת Static Files
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = BASE_DIR / "app" / "static"
