"""
Router למודול VPN
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.core.templates import templates
from app.modules.vpn import services

router = APIRouter(prefix="/vpn", tags=["vpn"])

@router.get("/", response_class=HTMLResponse)
async def vpn_page(request: Request):
    """דף VPN"""
    data = services.get_vpn_data()
    return templates.TemplateResponse(
        "vpn/templates/vpn.html",
        {"request": request, **data}
    )

