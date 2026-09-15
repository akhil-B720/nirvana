from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from backend.database.session import get_db
from backend.database.models import Project

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.get("/")
async def list_projects(
    state: Optional[str] = None,
    sector: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List all projects with optional filtering."""
    query = select(Project)
    
    if state:
        query = query.where(Project.state == state)
    if sector:
        query = query.where(Project.sector == sector)
    if status:
        query = query.where(Project.status == status)
        
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    projects = result.scalars().all()
    
    return [
        {
            "id": p.project_id,
            "name": p.project_name,
            "external_id": p.external_id,
            "sector": p.sector,
            "state": p.state,
            "district": p.district,
            "sanction_amount": float(p.sanction_amount) if p.sanction_amount else None,
            "status": p.status,
            "data_availability_status": p.data_availability_status,
        }
        for p in projects
    ]


@router.get("/{project_id}")
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get full details for a specific project."""
    query = select(Project).where(Project.project_id == project_id)
    result = await db.execute(query)
    project = result.scalars().first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    return {
        "id": project.project_id,
        "name": project.project_name,
        "external_id": project.external_id,
        "sector": project.sector,
        "type": project.project_type,
        "state": project.state,
        "district": project.district,
        "constituency": project.constituency,
        "latitude": project.latitude,
        "longitude": project.longitude,
        "geo_precision": project.geo_precision,
        "sanction_amount": float(project.sanction_amount) if project.sanction_amount else None,
        "released_amount": float(project.released_amount) if project.released_amount else None,
        "expenditure_amount": float(project.expenditure_amount) if project.expenditure_amount else None,
        "start_date": str(project.start_date) if project.start_date else None,
        "expected_completion_date": str(project.expected_completion_date) if project.expected_completion_date else None,
        "actual_completion_date": str(project.actual_completion_date) if project.actual_completion_date else None,
        "reported_progress": project.reported_progress,
        "status": project.status,
        "agency": project.agency,
        "mp_name": project.mp_name,
        "house": project.house,
        "data_availability_status": project.data_availability_status,
    }
