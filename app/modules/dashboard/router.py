"""
Router למודול Dashboard
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.core.templates import templates
from app.modules.dashboard import services

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """דף Dashboard הראשי"""
    data = services.get_dashboard_data()
    return templates.TemplateResponse(
        "dashboard/templates/dashboard.html", {"request": request, **data}
    )
