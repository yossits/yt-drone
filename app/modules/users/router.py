"""
Router למודול Users
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.core.templates import templates
from app.modules.users import services

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_class=HTMLResponse)
async def users_page(request: Request):
    """דף Users"""
    data = services.get_users_data()
    return templates.TemplateResponse(
        "users/templates/users.html",
        {"request": request, **data}
    )

