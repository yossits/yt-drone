"""
Shared Jinja2 Templates management
"""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SHARED_TEMPLATES_DIR = BASE_DIR / "app" / "shared" / "templates"
MODULES_DIR = BASE_DIR / "app" / "modules"

# Create Jinja2 Environment with multiple directories
# Order is important - base.html needs to be accessible from the first directory
env = Environment(
    loader=FileSystemLoader(
        [
            str(
                SHARED_TEMPLATES_DIR
            ),  # shared templates (base.html) - accessible as "base.html"
            str(
                MODULES_DIR
            ),  # module templates - accessible as "dashboard/templates/dashboard.html"
        ]
    ),
    autoescape=select_autoescape(["html", "xml"]),
)

# Add helper function to Jinja2
def get_path(request):
    """Returns the request path without trailing slash"""
    path = str(request.url.path).rstrip('/')
    return path if path else '/'

env.globals['get_path'] = get_path

# Wrapper for Jinja2Templates that supports multiple directories
class CustomJinja2Templates:
    """Wrapper for Jinja2Templates that supports multiple directories"""

    def __init__(self, env: Environment):
        self.env = env

    def TemplateResponse(self, name: str, context: dict):
        """Returns TemplateResponse with template from the given name"""
        from fastapi.responses import HTMLResponse

        template = self.env.get_template(name)
        content = template.render(**context)
        return HTMLResponse(content=content)


# Create custom instance
templates = CustomJinja2Templates(env)
