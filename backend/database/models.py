"""
NIRVANA — SQLAlchemy ORM Models
All 15 database tables as defined in DATA_DICTIONARY.md
"""
import uuid
from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    Column, String, Float, Numeric, Boolean, Integer, Date, Text,
    DateTime, ForeignKey, JSON, Index, UniqueConstraint
)
from sqlalchemy.dialects.sqlite import TEXT as SQLiteText
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import func


def generate_uuid():
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class DataSource(Base):
    """Registry of all data sources with provenance."""
    __tablename__ = "data_sources"

    source_id = Column(String(36), primary_key=True, default=generate_uuid)
    source_name = Column(String(200), nullable=False)
    source_url = Column(Text)
    source_type = Column(String(50))  # GOVERNMENT_OPEN, AUTHORIZED_API, SYNTHETIC, CSV_UPLOAD
    retrieval_timestamp = Column(DateTime, default=datetime.utcnow)
    last_modified = Column(DateTime)
    license = Column(String(100))  # GODL, TOS, MIT, etc.
    access_method = Column(String(50))  # DIRECT_DOWNLOAD, API, UPLOAD
    verification_status = Column(String(20), default="PUBLIC_VERIFIED")  # PUBLIC_VERIFIED, AUTHORIZED, SYNTHETIC
    record_count = Column(Integer)

    projects = relationship("Project", back_populates="source")


class Project(Base):
    """Core project table — never overwrite original government values."""
    __tablename__ = "projects"

    project_id = Column(String(36), primary_key=True, default=generate_uuid)
    external_id = Column(String(100))  # ID from source system
    project_name = Column(Text, nullable=False)
    project_type = Column(String(50))  # BUILDING, ROAD, BRIDGE, WATER_TANK, OTHER
    sector = Column(String(100))  # Roads, Education, Health, Drinking Water, etc.
    state = Column(String(100))
    district = Column(String(100))
    constituency = Column(String(100))
    block = Column(String(100))
    village = Column(String(100))
    latitude = Column(Float)  # Constituency centroid if precise not available
    longitude = Column(Float)
    geo_precision = Column(String(30), default="CONSTITUENCY_CENTROID")  # EXACT, NEIGHBOURHOOD, DISTRICT_CENTROID

    # Financial
    sanction_amount = Column(Numeric(15, 2))
    released_amount = Column(Numeric(15, 2))
    expenditure_amount = Column(Numeric(15, 2))

    # Timeline
    start_date = Column(Date)
    expected_completion_date = Column(Date)
    actual_completion_date = Column(Date)

    # Progress & status
    reported_progress = Column(Float)  # 0-100, as reported
    status = Column(String(30))  # COMPLETED, IN_PROGRESS, NOT_STARTED, DELAYED, STALLED

    # Classification
    mp_name = Column(String(200))
    agency = Column(String(200))
    house = Column(String(20))  # LOK_SABHA, RAJYA_SABHA
    lok_sabha_term = Column(String(10))  # 17th, 18th, etc.

    # Data quality
    data_availability_status = Column(String(20), default="PUBLIC_VERIFIED")
    # PUBLIC_VERIFIED, AUTHORIZED, SYNTHETIC, MISSING

    # Provenance
    source_id = Column(String(36), ForeignKey("data_sources.source_id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    source = relationship("DataSource", back_populates="projects")
    financials = relationship("ProjectFinancial", back_populates="project", cascade="all, delete-orphan")
    progress_snapshots = relationship("ProjectProgress", back_populates="project", cascade="all, delete-orphan")
    events = relationship("ProjectEvent", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("ProjectDocument", back_populates="project", cascade="all, delete-orphan")
    evidence = relationship("ProjectEvidence", back_populates="project", cascade="all, delete-orphan")
    locations = relationship("ProjectLocation", back_populates="project", cascade="all, delete-orphan")
    anomalies = relationship("ProjectAnomaly", back_populates="project", cascade="all, delete-orphan")
    risk_scores = relationship("RiskScore", back_populates="project", cascade="all, delete-orphan")
    predictions = relationship("ModelPrediction", back_populates="project", cascade="all, delete-orphan")
    officer_feedback = relationship("OfficerFeedback", back_populates="project", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="project")

    __table_args__ = (
        Index("idx_projects_state", "state"),
        Index("idx_projects_sector", "sector"),
        Index("idx_projects_status", "status"),
        Index("idx_projects_constituency", "constituency"),
    )


class ProjectFinancial(Base):
    """Financial time-series per project."""
    __tablename__ = "project_financials"

    financial_id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.project_id"), nullable=False)
    record_date = Column(Date, nullable=False)
    cumulative_expenditure = Column(Numeric(15, 2))
    installment_released = Column(Numeric(15, 2))
    utilization_rate = Column(Float)  # expenditure / released_amount
    financial_source = Column(String(50))

    project = relationship("Project", back_populates="financials")

    __table_args__ = (Index("idx_financials_project", "project_id"),)


class ProjectProgress(Base):
    """Progress snapshots over time."""
    __tablename__ = "project_progress"

    progress_id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.project_id"), nullable=False)
    snapshot_date = Column(Date, nullable=False)
    reported_progress = Column(Float)
    observed_progress = Column(Float)  # null if not available
    observed_confidence = Column(Float)
    observation_source = Column(String(50), default="NOT_AVAILABLE")
    # IMAGE_AI, FIELD_INSPECTION, SATELLITE, NOT_AVAILABLE
    expected_progress = Column(Float)
    expected_confidence = Column(Float)
    expected_range_low = Column(Float)
    expected_range_high = Column(Float)

    project = relationship("Project", back_populates="progress_snapshots")

    __table_args__ = (Index("idx_progress_project", "project_id"),)


class ProjectEvent(Base):
    """Timeline of significant project events."""
    __tablename__ = "project_events"

    event_id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.project_id"), nullable=False)
    event_date = Column(Date)
    event_type = Column(String(50))
    # RECOMMENDATION, SANCTION, PAYMENT, COMPLETION, DELAY, STALL, INSPECTION
    description = Column(Text)
    source = Column(String(100))

    project = relationship("Project", back_populates="events")


class ProjectDocument(Base):
    """Document inventory for a project."""
    __tablename__ = "project_documents"

    doc_id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.project_id"), nullable=False)
    doc_type = Column(String(50))  # SANCTION_ORDER, COMPLETION_CERT, PHOTO, etc.
    file_path = Column(Text)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(String(36), ForeignKey("users.user_id"))
    file_hash = Column(String(64))
    extracted_amount = Column(Numeric(15, 2))
    extracted_date = Column(Date)
    consistency_score = Column(Float)  # 0–1

    project = relationship("Project", back_populates="documents")
    uploader = relationship("User")


class ProjectEvidence(Base):
    """Physical evidence (images) per project."""
    __tablename__ = "project_evidence"

    evidence_id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.project_id"), nullable=False)
    image_path = Column(Text)
    capture_timestamp = Column(DateTime)
    latitude = Column(Float)
    longitude = Column(Float)
    source = Column(String(50))  # DRONE, SATELLITE, FIELD_PHONE, UPLOAD
    file_hash = Column(String(64))
    estimated_progress = Column(Float)  # null if model not available
    cv_confidence = Column(Float)
    detected_components = Column(JSON)  # list of detected components
    availability_status = Column(String(20), default="NOT_AVAILABLE")
    # NOT_AVAILABLE, PENDING, PROCESSED

    project = relationship("Project", back_populates="evidence")


class ProjectLocation(Base):
    """Geographic data for projects."""
    __tablename__ = "project_locations"

    location_id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.project_id"), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    precision_level = Column(String(30))  # EXACT, NEIGHBOURHOOD, CONSTITUENCY_CENTROID
    source = Column(String(100))
    verified = Column(Boolean, default=False)

    project = relationship("Project", back_populates="locations")


class ProjectAnomaly(Base):
    """Individual anomaly signals detected."""
    __tablename__ = "project_anomalies"

    anomaly_id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.project_id"), nullable=False)
    anomaly_type = Column(String(50))
    # COST, PAYMENT_PROGRESS, DELAY, DUPLICATE, LOCATION, DOCUMENT, REALITY_GAP
    signal_value = Column(Float)
    normalized_score = Column(Float)  # 0–100
    confidence = Column(Float)  # 0–1
    contributing_features = Column(JSON)
    model_id = Column(String(36), ForeignKey("model_versions.model_id"))
    detected_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="OPEN")  # OPEN, VERIFIED, DISMISSED

    project = relationship("Project", back_populates="anomalies")
    model = relationship("ModelVersion")

    __table_args__ = (Index("idx_anomalies_project", "project_id"),)


class RiskScore(Base):
    """Fused risk score for a project."""
    __tablename__ = "risk_scores"

    risk_id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.project_id"), nullable=False)
    risk_score = Column(Float)  # 0–100
    risk_level = Column(String(20))  # LOW, MEDIUM, HIGH, CRITICAL
    reality_gap_score = Column(Float)
    cost_anomaly_score = Column(Float)
    delay_probability = Column(Float)
    similarity_score = Column(Float)
    document_score = Column(Float)
    weights_used = Column(JSON)
    explanation = Column(Text)
    shap_values = Column(JSON)
    confidence = Column(Float)
    computed_at = Column(DateTime, default=datetime.utcnow)
    model_version_ids = Column(JSON)

    project = relationship("Project", back_populates="risk_scores")

    __table_args__ = (
        Index("idx_risk_project", "project_id"),
        Index("idx_risk_level", "risk_level"),
    )


class ModelVersion(Base):
    """Model registry."""
    __tablename__ = "model_versions"

    model_id = Column(String(36), primary_key=True, default=generate_uuid)
    model_name = Column(String(100), nullable=False)
    version = Column(String(20), nullable=False)
    algorithm = Column(String(100))
    training_data_version = Column(String(50))
    training_timestamp = Column(DateTime)
    features = Column(JSON)
    hyperparameters = Column(JSON)
    metrics = Column(JSON)
    status = Column(String(20), default="ACTIVE")  # ACTIVE, RETIRED, EXPERIMENTAL
    model_path = Column(Text)
    card_path = Column(Text)

    __table_args__ = (UniqueConstraint("model_name", "version", name="uq_model_version"),)


class ModelPrediction(Base):
    """Individual model output records."""
    __tablename__ = "model_predictions"

    prediction_id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.project_id"), nullable=False)
    model_id = Column(String(36), ForeignKey("model_versions.model_id"))
    prediction_type = Column(String(50))
    input_features = Column(JSON)
    raw_output = Column(JSON)
    prediction_value = Column(Float)
    confidence = Column(Float)
    predicted_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="predictions")
    model = relationship("ModelVersion")


class OfficerFeedback(Base):
    """Human feedback loop records."""
    __tablename__ = "officer_feedback"

    feedback_id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.project_id"), nullable=False)
    officer_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    feedback_type = Column(String(50))
    # VERIFIED_NORMAL, CONFIRMED_ANOMALY, DISMISSED, ESCALATED
    risk_score_at_feedback = Column(Float)
    notes = Column(Text)
    field_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="officer_feedback")
    officer = relationship("User")


class User(Base):
    """User accounts with roles."""
    __tablename__ = "users"

    user_id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    role = Column(String(20), default="VIEWER")  # ADMIN, OFFICER, ANALYST, VIEWER
    state = Column(String(100))  # null = national access
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    audit_logs = relationship("AuditLog", back_populates="user")


class AuditLog(Base):
    """Complete audit trail — every important action."""
    __tablename__ = "audit_logs"

    log_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.user_id"))
    project_id = Column(String(36), ForeignKey("projects.project_id"))
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(String(36))
    previous_value = Column(JSON)
    new_value = Column(JSON)
    model_version = Column(String(50))
    ip_address = Column(String(45))
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")
    project = relationship("Project", back_populates="audit_logs")

    __table_args__ = (
        Index("idx_audit_timestamp", "timestamp"),
        Index("idx_audit_project", "project_id"),
        Index("idx_audit_user", "user_id"),
    )
