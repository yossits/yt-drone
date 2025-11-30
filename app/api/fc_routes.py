"""
REST API endpoints for Flight Controller connection management
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
import serial

from app.fc.manager import fc_connection_manager
from app.modules.flight_controller import services

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/fc", tags=["flight-controller-api"])


class ConnectRequest(BaseModel):
    """Request model for FC connection"""
    device: str
    baud: int


class ConnectResponse(BaseModel):
    """Response model for FC connection"""
    status: str
    connected: bool
    device: Optional[str] = None
    baud: Optional[int] = None
    message: Optional[str] = None


class DisconnectResponse(BaseModel):
    """Response model for FC disconnection"""
    status: str
    connected: bool
    message: Optional[str] = None


class StatusResponse(BaseModel):
    """Response model for FC status"""
    connected: bool
    device: Optional[str] = None
    baud: Optional[int] = None
    heartbeat_active: Optional[bool] = None


@router.post("/connect", response_model=ConnectResponse)
async def connect_fc(request: ConnectRequest):
    """
    Connect to Flight Controller
    Args:
        request: Connection request with device and baud rate
    Returns:
        Connection status and details
    """
    logger.info(f"FC connect request received: device={request.device}, baud={request.baud}")
    try:
        # Validate baud rate
        if request.baud <= 0:
            raise HTTPException(
                status_code=400,
                detail="Baud rate must be positive"
            )
        
        # Attempt connection
        try:
            success = await fc_connection_manager.connect(request.device, request.baud)
        except ValueError as e:
            # Already connected
            logger.warning(f"FC connection failed: {str(e)}")
            return ConnectResponse(
                status="error",
                connected=False,
                message=str(e)
            )
        except (serial.SerialException, FileNotFoundError, PermissionError) as e:
            # Specific connection errors
            logger.warning(f"FC connection failed: {request.device} @ {request.baud} - {str(e)}")
            return ConnectResponse(
                status="error",
                connected=False,
                message=str(e)
            )
        except Exception as e:
            # Other connection errors
            logger.warning(f"FC connection failed: {request.device} @ {request.baud} - {str(e)}")
            return ConnectResponse(
                status="error",
                connected=False,
                message=f"Connection failed: {str(e)}"
            )
        
        if success:
            status = fc_connection_manager.get_status()
            logger.info(f"FC connection established: {request.device} @ {request.baud}")
            # Save connection state to disk for persistence
            services.save_fc_status(True, status["device"], status["baud"])
            return ConnectResponse(
                status="success",
                connected=True,
                device=status["device"],
                baud=status["baud"],
                message="Connected successfully"
            )
        else:
            logger.warning(f"FC connection failed: {request.device} @ {request.baud}")
            return ConnectResponse(
                status="error",
                connected=False,
                message="Failed to connect. Check device path and permissions."
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connecting to FC: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Connection error: {str(e)}"
        )


@router.post("/disconnect", response_model=DisconnectResponse)
async def disconnect_fc():
    """
    Disconnect from Flight Controller
    Returns:
        Disconnection status
    """
    try:
        await fc_connection_manager.disconnect()
        logger.info("FC disconnected")
        # Save disconnected state to disk for persistence
        services.save_fc_status(False, None, None)
        return DisconnectResponse(
            status="success",
            connected=False,
            message="Disconnected successfully"
        )
    except Exception as e:
        logger.error(f"Error disconnecting from FC: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Disconnection error: {str(e)}"
        )


@router.get("/status", response_model=StatusResponse)
async def get_fc_status():
    """
    Get Flight Controller connection status
    Returns:
        Current connection status, device, and baud rate
    """
    try:
        status = fc_connection_manager.get_status()
        return StatusResponse(
            connected=status["connected"],
            device=status["device"],
            baud=status["baud"],
            heartbeat_active=status.get("heartbeat_active", False)
        )
    except Exception as e:
        logger.error(f"Error getting FC status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Status error: {str(e)}"
        )

