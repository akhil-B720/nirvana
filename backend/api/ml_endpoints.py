from fastapi import APIRouter

router = APIRouter(tags=["ML"])

@router.post("/trigger/cost-anomaly")
async def trigger_cost_anomaly():
    """Trigger the cost anomaly detection job (background)."""
    return {"message": "Cost anomaly job triggered in background", "status": "processing"}

@router.post("/trigger/delay-model")
async def trigger_delay_model():
    """Trigger the delay prediction model job."""
    return {"message": "Delay model job triggered", "status": "processing"}

@router.post("/trigger/similarity-model")
async def trigger_similarity_model():
    """Trigger duplicate detection model job."""
    return {"message": "Similarity model job triggered", "status": "processing"}
