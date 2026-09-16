from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import uuid
import hashlib
from datetime import datetime

from backend.database.session import get_db
from backend.database.models import (
    Project, ProjectEvent, ProjectDocument, ProjectEvidence,
    ProjectAnomaly, RiskScore
)
from backend.api.auth import get_current_user, require_role

router = APIRouter(prefix="/projects", tags=["Evidence & Reporting"])

@router.get("/{project_id}/timeline")
async def get_project_timeline(project_id: str, db: AsyncSession = Depends(get_db)):
    """Phase 4D: Project Timeline"""
    # Verify project
    query = select(Project).where(Project.project_id == project_id)
    project = (await db.execute(query)).scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    events_q = select(ProjectEvent).where(ProjectEvent.project_id == project_id).order_by(ProjectEvent.event_date.desc())
    events = (await db.execute(events_q)).scalars().all()
    
    anom_q = select(ProjectAnomaly).where(ProjectAnomaly.project_id == project_id).order_by(ProjectAnomaly.detected_at.desc())
    anomalies = (await db.execute(anom_q)).scalars().all()

    timeline = []
    for e in events:
        timeline.append({
            "date": str(e.event_date),
            "type": e.event_type,
            "description": e.description,
            "source": e.source
        })
    for a in anomalies:
        timeline.append({
            "date": str(a.detected_at.date()),
            "type": "ANOMALY_DETECTED",
            "description": f"Detected {a.anomaly_type} anomaly (Confidence: {a.confidence})",
            "source": "AI_ENGINE"
        })
    
    timeline.sort(key=lambda x: x["date"], reverse=True)
    if not timeline:
        return {"timeline": [], "message": "Historical evidence unavailable."}
        
    return {"timeline": timeline}


@router.post("/{project_id}/evidence")
async def upload_evidence(
    project_id: str, 
    file: UploadFile = File(...),
    source: str = Form("UPLOAD"),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role("OFFICER"))
):
    """Phase 4A: Evidence Ingestion"""
    if file.content_type not in ["image/jpeg", "image/png", "application/pdf"]:
        raise HTTPException(status_code=400, detail="Unsupported file format (JPEG, PNG, PDF only).")

    content = await file.read()
    file_hash = hashlib.sha256(content).hexdigest()

    if "image" in file.content_type:
        ev = ProjectEvidence(
            evidence_id=str(uuid.uuid4()),
            project_id=project_id,
            image_path=f"local_storage/{file.filename}",
            capture_timestamp=datetime.utcnow(),
            source=source,
            latitude=latitude,
            longitude=longitude,
            file_hash=file_hash,
            availability_status="PENDING"
        )
        db.add(ev)
    else:
        # PDF Document Phase 4B stub
        doc = ProjectDocument(
            doc_id=str(uuid.uuid4()),
            project_id=project_id,
            doc_type="UPLOADED_REPORT",
            file_path=f"local_storage/{file.filename}",
            upload_timestamp=datetime.utcnow(),
            uploaded_by=user.user_id,
            file_hash=file_hash,
            consistency_score=None
        )
        db.add(doc)

    await db.commit()
    return {"message": "Evidence uploaded securely", "hash": file_hash}


@router.get("/{project_id}/recommendations")
async def get_recommendations(project_id: str, db: AsyncSession = Depends(get_db)):
    """Phase 4E: Recommendation Engine"""
    risk_q = select(RiskScore).where(RiskScore.project_id == project_id).order_by(RiskScore.computed_at.desc())
    risk = (await db.execute(risk_q)).scalars().first()
    
    recs = []
    if not risk:
        recs.append("Insufficient signals for recommendations.")
    else:
        if risk.cost_anomaly_score and risk.cost_anomaly_score > 60:
            recs.append({"issue": "Financial/progress mismatch", "action": "Verify expenditure records and latest physical measurement."})
        if risk.delay_probability and risk.delay_probability > 0.6:
            recs.append({"issue": "Delay risk", "action": "Review implementation timeline."})
        if risk.reality_gap_score and risk.reality_gap_score > 50:
            recs.append({"issue": "High reality gap", "action": "Conduct additional field verification."})
        if risk.similarity_score and risk.similarity_score > 0.6:
            recs.append({"issue": "Project similarity detected", "action": "Review potentially similar projects."})

    return {"recommendations": recs}


@router.get("/{project_id}/report")
async def get_pdf_report_data(project_id: str, db: AsyncSession = Depends(get_db)):
    """Phase 4F: PDF Report Data Generator"""
    query = select(Project).where(Project.project_id == project_id)
    project = (await db.execute(query)).scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    risk_q = select(RiskScore).where(RiskScore.project_id == project_id).order_by(RiskScore.computed_at.desc())
    risk = (await db.execute(risk_q)).scalars().first()
    
    return {
        "PROJECT_INFORMATION": {
            "name": project.project_name,
            "district": project.district,
            "type": project.project_type,
            "status": project.status
        },
        "SOURCE_PROVENANCE": project.data_availability_status,
        "FINANCIAL_ANALYSIS": {
            "sanction_amount": float(project.sanction_amount) if project.sanction_amount else "NOT_AVAILABLE",
            "expenditure_amount": float(project.expenditure_amount) if project.expenditure_amount else "NOT_AVAILABLE"
        },
        "EXPECTED_REPORTED_OBSERVED": {
            "reported_progress": project.reported_progress,
            "expected_progress": "NOT_AVAILABLE",
            "observed_progress": "NOT_AVAILABLE"
        },
        "ML_SIGNALS": risk.components if risk else "NOT_AVAILABLE",
        "RISK_SCORE": risk.risk_score if risk else "NOT_AVAILABLE",
        "RISK_EXPLANATION": risk.explanation if risk else "NOT_AVAILABLE",
        "DOCUMENT_CONSISTENCY": "Verification Recommended",
        "TIMESTAMP": datetime.utcnow().isoformat(),
        "MODEL_VERSIONS": risk.model_version_ids if risk else "NOT_AVAILABLE"
    }
