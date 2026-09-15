"""
Digital Twin API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database.session import get_db
from backend.database.models import Project

router = APIRouter(prefix="/projects/{project_id}/digital-twin", tags=["Digital Twin"])

@router.get("/")
async def get_digital_twin_state(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get the 3D digital twin state for a project."""
    query = select(Project).where(Project.project_id == project_id)
    result = await db.execute(query)
    project = result.scalars().first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "project_id": project.project_id,
        "project_type": project.project_type,
        "reported_progress": project.reported_progress,
        "component_states": {
            "foundation": {"start_progress": 0, "end_progress": 15},
            "columns": {"start_progress": 10, "end_progress": 35},
            "beams": {"start_progress": 25, "end_progress": 45},
            "walls": {"start_progress": 40, "end_progress": 70},
            "roof": {"start_progress": 65, "end_progress": 80},
            "services": {"start_progress": 75, "end_progress": 92},
            "finishing": {"start_progress": 90, "end_progress": 100},
        }
    }
