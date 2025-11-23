"""
Router למודול Networks
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.core.templates import templates
from app.modules.networks import services

router = APIRouter(prefix="/networks", tags=["networks"])

@router.get("/", response_class=HTMLResponse)
async def networks_page(request: Request):
    """דף Networks"""
    data = services.get_networks_data()
    return templates.TemplateResponse(
        "networks/templates/networks.html",
        {"request": request, **data}
    )

