"""
Router למודול Camera
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.core.templates import templates
from app.modules.camera import services

router = APIRouter(prefix="/camera", tags=["camera"])

@router.get("/", response_class=HTMLResponse)
async def camera_page(request: Request):
    """דף Camera"""
    data = services.get_camera_data()
    return templates.TemplateResponse(
        "camera/templates/camera.html",
        {"request": request, **data}
    )

