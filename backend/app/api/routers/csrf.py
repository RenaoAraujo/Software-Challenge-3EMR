from fastapi import APIRouter

from app.security.csrf import create_csrf_token

router = APIRouter()


@router.get("/csrf-token")
def get_csrf_token() -> dict[str, str]:
    return {"csrf_token": create_csrf_token()}
