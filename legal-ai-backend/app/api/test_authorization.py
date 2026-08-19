from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.dependencies.authorization import require_permission


class AuthorizationTestResponse(BaseModel):
    message: str
    user_id: int


router = APIRouter(
    prefix="/api/test",
    tags=["Authorization Test"],
)


@router.get("/document", response_model=AuthorizationTestResponse)
async def test_document_permission(
    user_id: int = Depends(
        require_permission("document.view")
    ),
):
    return {
        "message": "You have document.view permission",
        "user_id": user_id,
    }

 