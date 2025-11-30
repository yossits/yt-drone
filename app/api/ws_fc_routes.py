"""
WebSocket endpoints for Flight Controller data streaming
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import logging
import json

from app.fc.manager import fc_connection_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["flight-controller-websocket"])


async def _stream_fc_topic(websocket: WebSocket, topic: str):
    """
    Stream messages from a specific FC topic to WebSocket client
    Args:
        websocket: WebSocket connection
        topic: Topic name to subscribe to
    """
    await websocket.accept()
    logger.info(f"WebSocket connected for FC topic: {topic}")
    
    # Create queue for this subscriber
    queue = asyncio.Queue(maxsize=100)
    
    try:
        # Subscribe to topic
        fc_connection_manager.subscribe(topic, queue)
        
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "topic": topic,
            "status": "subscribed"
        })
        
        # Stream messages from queue
        while True:
            try:
                # Wait for message with timeout to allow cancellation
                message = await asyncio.wait_for(queue.get(), timeout=1.0)
                
                # Send message to client
                await websocket.send_json({
                    "type": "data",
                    "topic": topic,
                    "data": message
                })
                
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                await websocket.send_json({
                    "type": "heartbeat",
                    "topic": topic
                })
            except WebSocketDisconnect:
                raise
            except Exception as e:
                logger.error(f"Error streaming message for topic {topic}: {e}")
                await asyncio.sleep(0.1)
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for FC topic: {topic}")
    except Exception as e:
        logger.error(f"Error in WebSocket stream for topic {topic}: {e}")
    finally:
        # Unsubscribe from topic
        fc_connection_manager.unsubscribe(topic, queue)
        logger.debug(f"Unsubscribed from FC topic: {topic}")


@router.websocket("/fc-status")
async def websocket_fc_status(websocket: WebSocket):
    """
    WebSocket endpoint for Flight Controller status messages
    Streams: HEARTBEAT, SYS_STATUS
    """
    await _stream_fc_topic(websocket, "status")


@router.websocket("/fc-telemetry")
async def websocket_fc_telemetry(websocket: WebSocket):
    """
    WebSocket endpoint for Flight Controller telemetry messages
    Streams: ATTITUDE, GLOBAL_POSITION_INT, VFR_HUD, BATTERY_STATUS
    """
    await _stream_fc_topic(websocket, "telemetry")


@router.websocket("/fc-sensors")
async def websocket_fc_sensors(websocket: WebSocket):
    """
    WebSocket endpoint for Flight Controller sensor messages
    Streams: RAW_IMU, SCALED_PRESSURE, SCALED_IMU2, RAW_PRESSURE
    """
    await _stream_fc_topic(websocket, "sensors")


@router.websocket("/fc-map")
async def websocket_fc_map(websocket: WebSocket):
    """
    WebSocket endpoint for Flight Controller map/GPS messages
    Streams: GPS_RAW_INT, GLOBAL_POSITION_INT
    """
    await _stream_fc_topic(websocket, "map")

