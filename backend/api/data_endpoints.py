from fastapi import APIRouter

router = APIRouter(tags=["Data"])

@router.post("/sync/godl")
async def sync_godl_data():
    """Trigger data fetch from data.gov.in (GODL datasets)"""
    return {"message": "Data pipeline job triggered", "status": "processing"}

@router.get("/status")
async def data_status():
    """Get the status of datasets (Synthetic, Verified, etc.)"""
    return {"status": "ok", "last_sync": "2026-09-15T10:00:00Z"}
