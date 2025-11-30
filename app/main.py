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

# Import FC API routers
from app.api import fc_routes, ws_fc_routes

# Import Monitor Manager
from app.core.monitor_manager import monitor_manager
from app.core.system import get_static_info, get_slow_dynamic_info, get_fast_dynamic_info

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME, version=settings.APP_VERSION, debug=settings.DEBUG
)

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

# Include FC API routers
app.include_router(fc_routes.router)
app.include_router(ws_fc_routes.router)


# Root redirect to dashboard
@app.get("/")
async def root():
    return RedirectResponse(url="/dashboard")


# Startup event - start all monitors
@app.on_event("startup")
async def startup_event():
    """Start all monitors when application starts"""
    
    # Register all monitors
    monitor_manager.register_monitor(
        topic="static_info",
        data_function=get_static_info,
        interval=None  # one-time
    )
    
    monitor_manager.register_monitor(
        topic="slow_info",
        data_function=get_slow_dynamic_info,
        interval=60  # every 60 seconds
    )
    
    monitor_manager.register_monitor(
        topic="fast_info",
        data_function=get_fast_dynamic_info,
        interval=5  # every 5 seconds
    )
    
    # Start all monitors
    await monitor_manager.start_all()
    print("All monitors started")


# Shutdown event - stop all monitors
@app.on_event("shutdown")
async def shutdown_event():
    """Stop all monitors when application closes"""
    await monitor_manager.stop_all()
    print("All monitors stopped")
