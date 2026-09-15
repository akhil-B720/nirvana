"""
NIRVANA Data Pipeline — Base Data Source

All data sources must implement this interface.
Enforces: fetch() → validate() → normalize() → load() → record_provenance()
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class IngestionRecord:
    """A single record flowing through the pipeline."""
    raw_data: dict
    normalized_data: dict = field(default_factory=dict)
    validation_errors: list[str] = field(default_factory=list)
    is_valid: bool = True
    source_name: str = ""
    source_url: str = ""
    availability_status: str = "PUBLIC_VERIFIED"


@dataclass
class PipelineResult:
    """Summary of a pipeline run."""
    source_name: str
    start_time: datetime
    end_time: datetime
    total_fetched: int
    total_valid: int
    total_invalid: int
    total_loaded: int
    errors: list[str]
    skipped_fields: list[str]  # Fields that were unavailable — NOT fabricated

    @property
    def success_rate(self) -> float:
        if self.total_fetched == 0:
            return 0.0
        return self.total_valid / self.total_fetched


class BaseDataSource(ABC):
    """
    Abstract base class for all NIRVANA data sources.
    
    Every source MUST:
    1. fetch() — Retrieve raw data
    2. validate() — Check quality, mark errors (never fabricate)
    3. normalize() — Standardize fields
    4. load() — Insert into DB with provenance
    5. record_provenance() — Log source metadata
    
    CRITICAL: If a field is unavailable, set to None and mark NOT_AVAILABLE.
    NEVER invent values.
    """

    def __init__(self, source_name: str, source_url: str, license: str = "UNKNOWN"):
        self.source_name = source_name
        self.source_url = source_url
        self.license = license
        self.logger = logging.getLogger(f"pipeline.{source_name}")

    @abstractmethod
    def fetch(self) -> list[dict]:
        """Retrieve raw records from source. Returns list of raw dicts."""
        pass

    @abstractmethod
    def validate(self, records: list[dict]) -> list[IngestionRecord]:
        """
        Validate each record.
        - Set is_valid=False for records that fail
        - Add to validation_errors
        - Never fabricate missing fields
        """
        pass

    @abstractmethod
    def normalize(self, records: list[IngestionRecord]) -> list[IngestionRecord]:
        """
        Normalize field values:
        - Standardize sector names
        - Normalize currency to INR
        - Standardize status codes
        - Set None for unavailable — NOT a fake value
        """
        pass

    @abstractmethod
    def load(self, records: list[IngestionRecord], db_session) -> int:
        """
        Load normalized records into database.
        Returns count of records loaded.
        """
        pass

    def record_provenance(self, db_session, record_count: int):
        """Register this data source in the data_sources table."""
        from backend.database.models import DataSource
        import uuid

        existing = db_session.query(DataSource).filter_by(source_url=self.source_url).first()
        if existing:
            existing.retrieval_timestamp = datetime.utcnow()
            existing.record_count = record_count
        else:
            src = DataSource(
                source_id=str(uuid.uuid4()),
                source_name=self.source_name,
                source_url=self.source_url,
                source_type="GOVERNMENT_OPEN",
                license=self.license,
                access_method="DIRECT_DOWNLOAD",
                verification_status="PUBLIC_VERIFIED",
                retrieval_timestamp=datetime.utcnow(),
                record_count=record_count,
            )
            db_session.add(src)
        db_session.commit()

    def run(self, db_session) -> PipelineResult:
        """Execute the full pipeline: fetch → validate → normalize → load → provenance."""
        start_time = datetime.utcnow()
        errors = []
        total_loaded = 0

        self.logger.info(f"Starting ingestion from: {self.source_name}")

        try:
            raw = self.fetch()
            self.logger.info(f"Fetched {len(raw)} raw records")
        except Exception as e:
            self.logger.error(f"Fetch failed: {e}")
            errors.append(f"Fetch error: {e}")
            raw = []

        try:
            validated = self.validate(raw)
            valid = [r for r in validated if r.is_valid]
            invalid = [r for r in validated if not r.is_valid]
            self.logger.info(f"Validated: {len(valid)} valid, {len(invalid)} invalid")
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            errors.append(f"Validation error: {e}")
            validated = []
            valid = []
            invalid = []

        try:
            normalized = self.normalize(valid)
        except Exception as e:
            self.logger.error(f"Normalization failed: {e}")
            errors.append(f"Normalization error: {e}")
            normalized = valid

        try:
            total_loaded = self.load(normalized, db_session)
            self.record_provenance(db_session, total_loaded)
            self.logger.info(f"Loaded {total_loaded} records to database.")
        except Exception as e:
            self.logger.error(f"Load failed: {e}")
            errors.append(f"Load error: {e}")

        end_time = datetime.utcnow()
        return PipelineResult(
            source_name=self.source_name,
            start_time=start_time,
            end_time=end_time,
            total_fetched=len(raw),
            total_valid=len(valid),
            total_invalid=len(invalid),
            total_loaded=total_loaded,
            errors=errors,
            skipped_fields=[],
        )
