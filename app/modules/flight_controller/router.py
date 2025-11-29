"""
Router for Flight Controller module
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.core.templates import templates
from app.modules.flight_controller import services

router = APIRouter(prefix="/flight-controller", tags=["flight-controller"])


@router.get("/", response_class=HTMLResponse)
async def flight_controller_page(request: Request):
    """Flight Controller page"""
    data = services.get_flight_controller_data()
    return templates.TemplateResponse(
        "flight_controller/templates/flight_controller.html",
        {"request": request, **data},
    )
