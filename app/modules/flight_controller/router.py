"""
Router for Flight Controller module
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from app.core.templates import templates
from app.modules.flight_controller import services

router = APIRouter(prefix="/flight-controller", tags=["flight-controller"])


class FCStatusRequest(BaseModel):
    """Model for flight controller status request"""
    connected: bool


@router.get("/", response_class=HTMLResponse)
async def flight_controller_page(request: Request):
    """Flight Controller page"""
    data = services.get_flight_controller_data()
    return templates.TemplateResponse(
        "flight_controller/templates/flight_controller.html",
        {"request": request, **data},
    )


@router.get("/status")
async def get_fc_status():
    """Get flight controller connection status"""
    status = services.load_fc_status()
    return JSONResponse(status)


@router.post("/status")
async def update_fc_status(request: FCStatusRequest):
    """Update flight controller connection status"""
    success = services.save_fc_status(request.connected)
    
    if success:
        return JSONResponse({"status": "success", "connected": request.connected})
    else:
        return JSONResponse({"status": "error", "message": "Failed to save status"}, status_code=500)
