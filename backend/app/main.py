"""FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(
    title="Werewolf AI Agents",
    description="AI-to-AI persuasion research using Werewolf social deduction",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from app.api.games import router as games_router  # noqa: E402
from app.api.export import router as export_router  # noqa: E402
from app.api.batch import router as batch_router  # noqa: E402
from app.api.analytics import router as analytics_router  # noqa: E402

app.include_router(games_router)
app.include_router(export_router)
app.include_router(batch_router)
app.include_router(analytics_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
