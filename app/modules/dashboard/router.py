"""
Router for Dashboard module
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from app.core.templates import templates
from app.modules.dashboard import services

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Main Dashboard page"""
    data = services.get_dashboard_data()
    return templates.TemplateResponse(
        "dashboard/templates/dashboard.html", {"request": request, **data}
    )


@router.get("/autostart-status")
async def get_autostart_status():
    """Get autostart status (systemd service enabled/disabled)"""
    try:
        is_enabled = services.check_autostart_status()
        return JSONResponse({"enabled": is_enabled})
    except Exception as e:
        return JSONResponse({"enabled": False, "error": str(e)}, status_code=500)
