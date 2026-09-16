from fastapi import APIRouter, BackgroundTasks
from ml.inference.engine import run_project_inference, load_models

router = APIRouter(tags=["ML"])

@router.on_event("startup")
def startup_event():
    load_models()

@router.post("/trigger/infrastructure/{project_id}")
async def trigger_inference(project_id: str, background_tasks: BackgroundTasks):
    """Trigger inference for all models on a specific project."""
    background_tasks.add_task(run_project_inference, project_id)
    return {"message": "Inference triggered", "status": "processing", "project_id": project_id}

@router.post("/trigger/cost-anomaly")
async def trigger_cost_anomaly():
    """Trigger the cost anomaly detection job (background batch)."""
    return {"message": "Batch cost anomaly job triggered", "status": "processing"}

@router.post("/trigger/delay-model")
async def trigger_delay_model():
    """Trigger the delay prediction model job."""
    return {"message": "Batch delay model job triggered", "status": "processing"}

@router.post("/trigger/similarity-model")
async def trigger_similarity_model():
    """Trigger duplicate detection model job."""
    from ml.train.similarity_model import train as train_similarity
    import threading
    threading.Thread(target=train_similarity).start()
    return {"message": "Similarity model job triggered", "status": "processing"}

