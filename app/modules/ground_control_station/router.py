"""
Router למודול Ground Control Station
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.core.templates import templates
from app.modules.ground_control_station import services

router = APIRouter(prefix="/ground-control-station", tags=["ground-control-station"])

@router.get("/", response_class=HTMLResponse)
async def gcs_page(request: Request):
    """דף Ground Control Station"""
    data = services.get_gcs_data()
    return templates.TemplateResponse(
        "ground_control_station/templates/ground_control_station.html",
        {"request": request, **data}
    )

