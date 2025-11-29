"""
Router for Dynamic DNS module
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.core.templates import templates
from app.modules.dynamic_dns import services

router = APIRouter(prefix="/dynamic-dns", tags=["dynamic-dns"])

@router.get("/", response_class=HTMLResponse)
async def dns_page(request: Request):
    """Dynamic DNS page"""
    data = services.get_dns_data()
    return templates.TemplateResponse(
        "dynamic_dns/templates/dynamic_dns.html",
        {"request": request, **data}
    )

