"""
Router למודול Dynamic DNS
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.core.templates import templates
from app.modules.dynamic_dns import services

router = APIRouter(prefix="/dynamic-dns", tags=["dynamic-dns"])

@router.get("/", response_class=HTMLResponse)
async def dns_page(request: Request):
    """דף Dynamic DNS"""
    data = services.get_dns_data()
    return templates.TemplateResponse(
        "dynamic_dns/templates/dynamic_dns.html",
        {"request": request, **data}
    )

