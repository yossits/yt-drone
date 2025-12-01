"""
Application entry point - FastAPI
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path

from app.config import settings
from app.core.static import STATIC_DIR

# Import routers from all modules
from app.modules.dashboard import router as dashboard_router
from app.modules.flight_controller import router as flight_controller_router
from app.modules.flight_map import router as flight_map_router
from app.modules.ground_control_station import router as gcs_router
from app.modules.modem import router as modem_router
from app.modules.vpn import router as vpn_router
from app.modules.dynamic_dns import router as dns_router
from app.modules.camera import router as camera_router
from app.modules.networks import router as networks_router
from app.modules.users import router as users_router
from app.modules.application import router as application_router

# Import WebSocket router
from app.core import websocket_router

# Import Monitor Manager
from app.core.monitor_manager import monitor_manager
from app.core.system import get_static_info, get_slow_dynamic_info, get_fast_dynamic_info

from app.modules.flight_controller.connection_manager import (
    FCConnectionManager,
    heartbeat_watcher,
    status_broadcast_loop,
)
from app.modules.flight_controller.connection_state import (
    load_connection_state,
    save_connection_state,
    ConnectionState,
)

import logging

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME, version=settings.APP_VERSION, debug=settings.DEBUG
)

# Attach Flight Controller connection manager to app state
app.state.fc_manager = FCConnectionManager()
app.state.fc_tasks = []

# Mount Static Files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Include routers from all modules
app.include_router(dashboard_router)
app.include_router(flight_controller_router)
app.include_router(flight_map_router)
app.include_router(gcs_router)
app.include_router(modem_router)
app.include_router(vpn_router)
app.include_router(dns_router)
app.include_router(camera_router)
app.include_router(networks_router)
app.include_router(users_router)
app.include_router(application_router)

# Include WebSocket router
app.include_router(websocket_router.router)


# Root redirect to dashboard
@app.get("/")
async def root():
    return RedirectResponse(url="/dashboard")


# Startup event - start all monitors and restore FC connection
@app.on_event("startup")
async def startup_event():
    """Start all monitors and restore Flight Controller connection when application starts."""

    # Register all monitors
    monitor_manager.register_monitor(
        topic="static_info",
        data_function=get_static_info,
        interval=None,  # one-time
    )

    monitor_manager.register_monitor(
        topic="slow_info",
        data_function=get_slow_dynamic_info,
        interval=60,  # every 60 seconds
    )

    monitor_manager.register_monitor(
        topic="fast_info",
        data_function=get_fast_dynamic_info,
        interval=5,  # every 5 seconds
    )

    # Start all monitors
    await monitor_manager.start_all()
    print("All monitors started")

    # Restore Flight Controller connection from persisted state if appropriate
    fc_manager: FCConnectionManager = app.state.fc_manager
    state: ConnectionState = load_connection_state()

    if state.is_connected and not state.user_disconnected:
        if state.connection_type and state.baudrate is not None:
            try:
                await fc_manager.connect(
                    connection_type=state.connection_type,
                    params=state.params,
                    baudrate=state.baudrate,
                )
                # Update last_success on successful restore
                state.is_connected = True
                state.user_disconnected = False
                save_connection_state(state)
                logger.info("Restored Flight Controller connection from previous state")
            except Exception as exc:  # pragma: no cover - defensive
                logger.error(
                    "Failed to restore Flight Controller connection on startup: %s", exc
                )
                state.is_connected = False
                save_connection_state(state)

    # Start heartbeat watcher and WebSocket status broadcast tasks
    import asyncio

    heartbeat_task = asyncio.create_task(heartbeat_watcher(fc_manager), name="fc_heartbeat_watcher")
    status_task = asyncio.create_task(
        status_broadcast_loop(fc_manager),
        name="fc_status_broadcast",
    )
    app.state.fc_tasks.extend([heartbeat_task, status_task])


# Shutdown event - stop all monitors
@app.on_event("shutdown")
async def shutdown_event():
    """Stop all monitors when application closes"""
    await monitor_manager.stop_all()
    print("All monitors stopped")

    # Cancel FC background tasks
    tasks = getattr(app.state, "fc_tasks", [])
    for task in tasks:
        task.cancel()
    for task in tasks:
        try:
            await task
        except asyncio.CancelledError:
            pass
