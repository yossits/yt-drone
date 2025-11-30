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


class FCSettingsRequest(BaseModel):
    """Model for flight controller settings request"""
    connection_type: str
    device: str
    baud: int


@router.get("/", response_class=HTMLResponse)
async def flight_controller_page(request: Request):
    """Flight Controller page"""
    data = services.get_flight_controller_data()
    # Load settings to pass to template
    settings = services.load_fc_settings()
    data.update(settings)
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


@router.get("/settings")
async def get_fc_settings():
    """Get flight controller settings"""
    settings = services.load_fc_settings()
    return JSONResponse(settings)


@router.post("/settings")
async def save_fc_settings(request: FCSettingsRequest):
    """Save flight controller settings"""
    settings = {
        "connection_type": request.connection_type,
        "device": request.device,
        "baud": request.baud
    }
    success = services.save_fc_settings(settings)
    
    if success:
        return JSONResponse({"status": "success", "settings": settings})
    else:
        return JSONResponse({"status": "error", "message": "Failed to save settings"}, status_code=500)
