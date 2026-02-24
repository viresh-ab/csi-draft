from fastapi import FastAPI
from app.routes.query import router as query_router
from app.routes.health import router as health_router

app = FastAPI(
    title="CSI Engine",
    description="Case Study Intelligence Engine — Retrieve & Generate content from case studies.",
    version="1.0.0"
)

app.include_router(query_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")
