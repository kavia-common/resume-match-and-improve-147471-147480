# PUBLIC_INTERFACE
from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/health",
    summary="Service health probe",
    description="Returns a simple status payload to indicate the API is responsive.",
)
def health():
    """Health check endpoint returning status ok."""
    return {"status": "ok"}
