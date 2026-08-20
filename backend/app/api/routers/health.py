from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Health check",
    description="Return backend readiness status.",
)
async def health():
    return {"ok": True, "data": {"status": "ready"}}