"""
ניהול Jinja2 Templates משותף
"""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

# נתיבים
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SHARED_TEMPLATES_DIR = BASE_DIR / "app" / "shared" / "templates"
MODULES_DIR = BASE_DIR / "app" / "modules"

# יצירת Jinja2 Environment עם מספר directories
# הסדר חשוב - base.html צריך להיות נגיש מהתיקייה הראשונה
env = Environment(
    loader=FileSystemLoader(
        [
            str(
                SHARED_TEMPLATES_DIR
            ),  # templates משותפים (base.html) - נגיש כ-"base.html"
            str(
                MODULES_DIR
            ),  # templates של מודולים - נגישים כ-"dashboard/templates/dashboard.html"
        ]
    ),
    autoescape=select_autoescape(["html", "xml"]),
)


# Wrapper ל-Jinja2Templates שתומך במספר directories
class CustomJinja2Templates:
    """Wrapper ל-Jinja2Templates שתומך במספר directories"""

    def __init__(self, env: Environment):
        self.env = env

    def TemplateResponse(self, name: str, context: dict):
        """מחזיר TemplateResponse עם template מהשם הנתון"""
        from fastapi.responses import HTMLResponse

        template = self.env.get_template(name)
        content = template.render(**context)
        return HTMLResponse(content=content)


# יצירת instance מותאם אישית
templates = CustomJinja2Templates(env)
