from fastapi import FastAPI

from app.api.v1.api import api_router

app = FastAPI(
    title="Mentee-Mentor Recommendation API",
    description="API для тестирования рекомендательной системы ментор-менти",
    version="0.1.0",
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    return {"status": "ok"}