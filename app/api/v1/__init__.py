from fastapi import APIRouter
from .github import router as github_router
from .announcement import router as announcement_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(github_router, prefix="/github", tags=["GitHub"])
api_router.include_router(announcement_router, prefix="/announcement", tags=["Announcement"])

__all__ = ["api_router"]
