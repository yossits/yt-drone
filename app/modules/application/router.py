"""
Router for Application module
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.core.templates import templates
from app.modules.application import services

router = APIRouter(prefix="/application", tags=["application"])

@router.get("/", response_class=HTMLResponse)
async def application_page(request: Request):
    """Application page"""
    data = services.get_application_data()
    return templates.TemplateResponse(
        "application/templates/application.html",
        {"request": request, **data}
    )

