
from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.test_authorization import router as test_authorization_router


app = FastAPI(
    title="Legal Document Intelligence API",
)

app.include_router(auth_router)
app.include_router(test_authorization_router)