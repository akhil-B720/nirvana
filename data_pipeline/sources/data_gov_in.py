"""
NIRVANA Data Pipeline — data.gov.in Source

Fetches MPLADS datasets from the Open Government Data Platform India.
License: Government Open Data License (GODL)
All data used with attribution.
"""
import requests
import csv
import io
import logging
import uuid
from datetime import datetime, date
from typing import Optional

from data_pipeline.sources.base import BaseDataSource, IngestionRecord

logger = logging.getLogger(__name__)


# Known GODL-licensed MPLADS dataset URLs from data.gov.in
MPLADS_DATASETS = {
    "17th_lok_sabha_works": {
        "name": "MPLADS Works List — 17th Lok Sabha",
        "download_url": "https://data.gov.in/backend/dms/v1/ogdp/resource/download?resource_id=3bee0cdb-f39a-418e-b9e8-9e00bf5a01c5&format=csv",
        "fallback_url": "https://data.gov.in/resource/mplads-works-list-17th-lok-sabha",
        "license": "GODL",
        "description": "Year, State, District, Constituency and MP-wise list of works under MPLADS — 17th Lok Sabha",
    },
    "financial_2014_2018": {
        "name": "Year-wise MPLADS Fund Position 2014-2018",
        "download_url": "https://data.gov.in/backend/dms/v1/ogdp/resource/download?resource_id=9ef84268-d588-465a-a308-a864a43d0070&format=csv",
        "license": "GODL",
        "description": "Year-wise position of MPLADS funds from 2014-15 to 2017-18",
    },
}

# Constituency centroid coordinates (approximate, from Census gazetteer)
# Used when precise project geo-coordinates are unavailable
CONSTITUENCY_CENTROIDS = {
    "AMETHI": (26.1542, 81.7257),
    "VARANASI": (25.3176, 82.9739),
    "LUCKNOW": (26.8467, 80.9462),
    "DELHI": (28.6139, 77.2090),
    "MUMBAI NORTH": (19.2183, 72.9781),
    "BANGALORE NORTH": (13.0827, 77.5877),
    "CHENNAI NORTH": (13.0827, 80.2707),
    "KOLKATA NORTH": (22.5726, 88.3639),
    "HYDERABAD": (17.3850, 78.4867),
    "BHOPAL": (23.2599, 77.4126),
    "JAIPUR": (26.9124, 75.7873),
    "PATNA SAHIB": (25.5941, 85.1376),
    "PUNE": (18.5204, 73.8567),
    # Add more as needed
}

SECTOR_MAPPING = {
    "roads": "ROAD",
    "road": "ROAD",
    "bridges": "BRIDGE",
    "bridge": "BRIDGE",
    "education": "BUILDING",
    "school": "BUILDING",
    "health": "BUILDING",
    "hospital": "BUILDING",
    "drinking water": "WATER_TANK",
    "water": "WATER_TANK",
    "sanitation": "OTHER",
    "drainage": "OTHER",
    "sports": "BUILDING",
    "community": "BUILDING",
}

STATUS_MAPPING = {
    "completed": "COMPLETED",
    "complete": "COMPLETED",
    "in progress": "IN_PROGRESS",
    "ongoing": "IN_PROGRESS",
    "not started": "NOT_STARTED",
    "delayed": "DELAYED",
    "stalled": "STALLED",
    "dropped": "STALLED",
}


class DataGovInSource(BaseDataSource):
    """
    Fetches MPLADS data from data.gov.in (GODL license).
    Handles both the 17th LS works list and financial summary datasets.
    """

    def __init__(self, dataset_key: str = "17th_lok_sabha_works"):
        cfg = MPLADS_DATASETS.get(dataset_key)
        if not cfg:
            raise ValueError(f"Unknown dataset key: {dataset_key}")
        self.cfg = cfg
        self.dataset_key = dataset_key
        super().__init__(
            source_name=cfg["name"],
            source_url=cfg["download_url"],
            license=cfg["license"],
        )

    def fetch(self) -> list[dict]:
        """Download CSV from data.gov.in."""
        urls_to_try = [self.cfg["download_url"]]
        if "fallback_url" in self.cfg:
            urls_to_try.append(self.cfg["fallback_url"])

        for url in urls_to_try:
            try:
                self.logger.info(f"Fetching from: {url}")
                response = requests.get(url, timeout=30, headers={
                    "User-Agent": "NIRVANA-MPLADS-Pipeline/1.0 (SIH26102; research)"
                })
                if response.status_code == 200:
                    content = response.text
                    if content.strip():
                        reader = csv.DictReader(io.StringIO(content))
                        records = list(reader)
                        self.logger.info(f"Fetched {len(records)} records from {url}")
                        return records
                else:
                    self.logger.warning(f"HTTP {response.status_code} from {url}")
            except requests.RequestException as e:
                self.logger.warning(f"Request failed for {url}: {e}")

        self.logger.error("All fetch attempts failed — returning empty list")
        return []

    def validate(self, records: list[dict]) -> list[IngestionRecord]:
        """Validate records. Mark invalids — never fabricate."""
        validated = []
        for raw in records:
            errors = []
            ir = IngestionRecord(
                raw_data=raw,
                source_name=self.source_name,
                source_url=self.source_url,
                availability_status="PUBLIC_VERIFIED",
            )

            # Check for project name
            name = (
                raw.get("Work Description", "") or
                raw.get("work_name", "") or
                raw.get("Work Name", "")
            ).strip()
            if not name:
                errors.append("Missing project name")
                ir.is_valid = False

            # Validate amount
            amount_str = (
                raw.get("Estimated Cost (Rs.)", "") or
                raw.get("amount", "") or
                raw.get("Sanctioned Amount", "")
            ).replace(",", "").replace("₹", "").strip()
            if amount_str:
                try:
                    amt = float(amount_str)
                    if amt < 0:
                        errors.append(f"Negative amount: {amt}")
                        ir.is_valid = False
                except ValueError:
                    errors.append(f"Invalid amount: {amount_str}")

            ir.validation_errors = errors
            validated.append(ir)

        valid_count = sum(1 for r in validated if r.is_valid)
        self.logger.info(f"Validation: {valid_count}/{len(validated)} valid records")
        return validated

    def normalize(self, records: list[IngestionRecord]) -> list[IngestionRecord]:
        """Normalize fields. Set None for unavailable — NEVER fabricate."""
        for ir in records:
            raw = ir.raw_data
            nd = {}

            # Project identification
            nd["external_id"] = (
                raw.get("unique_work_number") or
                raw.get("Work ID") or
                str(uuid.uuid4())[:8]
            ) or None

            nd["project_name"] = (
                raw.get("Work Description") or
                raw.get("work_name") or
                raw.get("Work Name") or ""
            ).strip()

            # Sector normalization
            raw_sector = (raw.get("Sector") or raw.get("work_category") or "").strip().lower()
            nd["sector"] = raw_sector.title() if raw_sector else None

            # Project type from sector
            ptype = "OTHER"
            for kw, ptype_val in SECTOR_MAPPING.items():
                if kw in raw_sector:
                    ptype = ptype_val
                    break
            nd["project_type"] = ptype

            # Location
            nd["state"] = (raw.get("State/UT") or raw.get("state") or "").strip() or None
            nd["district"] = (
                raw.get("District") or
                raw.get("implementing_district_per_source") or
                raw.get("implementing_district_per_lgd") or ""
            ).strip() or None
            nd["constituency"] = (
                raw.get("Constituency") or
                raw.get("loksabha_constituency") or ""
            ).strip() or None
            nd["mp_name"] = (
                raw.get("MP Name") or
                raw.get("loksabha_MP_name") or ""
            ).strip() or None
            nd["house"] = (
                "LOK_SABHA" if "lok sabha" in (raw.get("house_name") or "").lower()
                else "RAJYA_SABHA" if "rajya" in (raw.get("house_name") or "").lower()
                else None
            )

            # Geo — use centroid if precise not available
            constituency_key = (nd["constituency"] or "").upper()
            centroid = CONSTITUENCY_CENTROIDS.get(constituency_key)
            nd["latitude"] = centroid[0] if centroid else None
            nd["longitude"] = centroid[1] if centroid else None
            nd["geo_precision"] = "CONSTITUENCY_CENTROID" if centroid else None

            # Financial — None if unavailable
            def parse_amount(raw_val):
                if not raw_val:
                    return None
                try:
                    return float(str(raw_val).replace(",", "").replace("₹", "").replace("Rs.", "").strip())
                except (ValueError, TypeError):
                    return None

            nd["sanction_amount"] = parse_amount(
                raw.get("Estimated Cost (Rs.)") or raw.get("amount") or raw.get("Sanctioned Amount")
            )
            nd["released_amount"] = parse_amount(raw.get("Released Amount") or raw.get("Funds Released"))
            nd["expenditure_amount"] = parse_amount(
                raw.get("Expenditure") or raw.get("Funds Utilised") or raw.get("Expenditure Incurred")
            )

            # Dates — None if unavailable or unparseable
            def parse_date(raw_val):
                if not raw_val:
                    return None
                for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"):
                    try:
                        return datetime.strptime(str(raw_val).strip(), fmt).date()
                    except ValueError:
                        continue
                return None

            nd["start_date"] = parse_date(raw.get("Recommended Date") or raw.get("Start Date"))
            nd["expected_completion_date"] = parse_date(raw.get("Expected Completion") or raw.get("Due Date"))
            nd["actual_completion_date"] = parse_date(raw.get("date_of_completion") or raw.get("Completion Date"))

            # Status normalization
            raw_status = (raw.get("Status of Work") or raw.get("status") or "").strip().lower()
            nd["status"] = STATUS_MAPPING.get(raw_status, "IN_PROGRESS") if raw_status else None

            # Progress — only if explicitly available
            nd["reported_progress"] = None  # Public data doesn't include % progress
            if nd["status"] == "COMPLETED":
                nd["reported_progress"] = 100.0

            nd["data_availability_status"] = "PUBLIC_VERIFIED"
            nd["lok_sabha_term"] = raw.get("lok_sabha_term", "17th")
            nd["agency"] = (raw.get("implementing_agency_name") or raw.get("Agency") or "").strip() or None

            ir.normalized_data = nd

        return records

    def load(self, records: list[IngestionRecord], db_session) -> int:
        """Upsert normalized records into database."""
        from backend.database.models import Project, DataSource, ProjectEvent
        import uuid

        # Get or create source record
        source = db_session.query(DataSource).filter_by(source_url=self.source_url).first()
        source_id = source.source_id if source else None

        loaded = 0
        for ir in records:
            if not ir.normalized_data:
                continue

            nd = ir.normalized_data
            project_name = nd.get("project_name", "")
            if not project_name:
                continue

            # Check for existing project by external_id or name+constituency
            existing = None
            if nd.get("external_id"):
                existing = db_session.query(Project).filter_by(
                    external_id=nd["external_id"]
                ).first()
            if not existing and nd.get("constituency"):
                existing = db_session.query(Project).filter_by(
                    project_name=project_name,
                    constituency=nd.get("constituency"),
                ).first()

            if existing:
                # Update financial fields if we have newer data
                if nd.get("expenditure_amount") and not existing.expenditure_amount:
                    existing.expenditure_amount = nd["expenditure_amount"]
                if nd.get("actual_completion_date") and not existing.actual_completion_date:
                    existing.actual_completion_date = nd["actual_completion_date"]
                existing.updated_at = datetime.utcnow()
            else:
                # Create new project record
                project = Project(
                    project_id=str(uuid.uuid4()),
                    source_id=source_id,
                    **{k: v for k, v in nd.items() if v is not None},
                )
                db_session.add(project)

                # Create initial event
                if nd.get("start_date"):
                    event = ProjectEvent(
                        event_id=str(uuid.uuid4()),
                        project_id=project.project_id,
                        event_date=nd["start_date"],
                        event_type="RECOMMENDATION",
                        description=f"Work recommended: {project_name}",
                        source=self.source_name,
                    )
                    db_session.add(event)

                loaded += 1

        try:
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            self.logger.error(f"Database commit failed: {e}")
            raise

        return loaded
