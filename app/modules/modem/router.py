"""
Router למודול Modem
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.core.templates import templates
from app.modules.modem import services

router = APIRouter(prefix="/modem", tags=["modem"])

@router.get("/", response_class=HTMLResponse)
async def modem_page(request: Request):
    """דף Modem"""
    data = services.get_modem_data()
    return templates.TemplateResponse(
        "modem/templates/modem.html",
        {"request": request, **data}
    )

