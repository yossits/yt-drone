"""
Router למודול Flight Map
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.core.templates import templates
from app.modules.flight_map import services

router = APIRouter(prefix="/flight-map", tags=["flight-map"])


@router.get("/", response_class=HTMLResponse)
async def flight_map_page(request: Request):
    """דף Flight Map"""
    data = services.get_flight_map_data()
    return templates.TemplateResponse(
        "flight_map/templates/flight_map.html", {"request": request, **data}
    )
