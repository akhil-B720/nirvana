from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database.session import get_db
from backend.database.models import Project
from backend.engines.reality_gap import RealityGapEngine

router = APIRouter(prefix="/projects/{project_id}/reality-gap", tags=["Reality Gap"])
gap_engine = RealityGapEngine()

@router.get("/")
async def get_reality_gap(project_id: str, db: AsyncSession = Depends(get_db)):
    """Compute and retrieve the Reality Gap score for a project."""
    query = select(Project).where(Project.project_id == project_id)
    result = await db.execute(query)
    project = result.scalars().first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Create dictionary from ORM object for engine
    project_dict = {
        "project_id": project.project_id,
        "sector": project.sector,
        "project_type": project.project_type,
        "start_date": project.start_date,
        "expected_completion_date": project.expected_completion_date,
        "reported_progress": project.reported_progress,
        "observed_progress": None, # Should be fetched from latest ProjectProgress but public usually missing
        "sanction_amount": float(project.sanction_amount) if project.sanction_amount else 0,
        "expenditure_amount": float(project.expenditure_amount) if project.expenditure_amount else 0,
        "released_amount": float(project.released_amount) if project.released_amount else 0,
        "status": project.status,
    }
    
    return gap_engine.compute(project_dict)
