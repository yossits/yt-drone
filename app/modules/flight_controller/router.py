"""
Router for Flight Controller module.

Exposes both the HTML page and the API endpoints for managing the
connection to the flight controller.
"""

from __future__ import annotations

from typing import Any, Dict, Literal

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.core.templates import templates
from app.modules.flight_controller import services
from app.modules.flight_controller.connection_manager import FCConnectionManager

router = APIRouter(prefix="/flight-controller", tags=["flight-controller"])


@router.get("/", response_class=HTMLResponse)
async def flight_controller_page(request: Request):
    """Flight Controller page."""
    data = services.get_flight_controller_data()
    return templates.TemplateResponse(
        "flight_controller/templates/flight_controller.html",
        {"request": request, **data},
    )


class FCConnectRequest(BaseModel):
    """Request body for connecting to the flight controller."""

    connection_type: Literal["serial", "udp", "tcp"] = Field(
        ..., description="Connection type: serial / udp / tcp"
    )
    baudrate: int = Field(..., description="Baudrate for serial or ignored for UDP/TCP")
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Connection params: for serial: {device}, for UDP/TCP: {host, port}",
    )


def _get_fc_manager(request: Request) -> FCConnectionManager:
    manager = getattr(request.app.state, "fc_manager", None)
    if manager is None:
        raise HTTPException(status_code=500, detail="Flight Controller manager not initialized")
    return manager


@router.post("/api/flight-controller/connect")
async def connect_flight_controller(request: Request, body: FCConnectRequest):
    """
    Connect to the flight controller using the shared FCConnectionManager.
    """
    manager = _get_fc_manager(request)
    try:
        await manager.connect(
            connection_type=body.connection_type,
            params=body.params,
            baudrate=body.baudrate,
        )
    except (ValueError, FileNotFoundError, PermissionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect to flight controller: {exc}",
        ) from exc

    return manager.get_status()


@router.post("/api/flight-controller/disconnect")
async def disconnect_flight_controller(request: Request):
    """
    Disconnect from the flight controller.
    """
    manager = _get_fc_manager(request)
    await manager.disconnect(user_requested=True)
    return manager.get_status()


@router.get("/api/flight-controller/status")
async def flight_controller_status(request: Request):
    """
    Get current status of the flight controller connection.
    """
    manager = _get_fc_manager(request)
    return manager.get_status()

