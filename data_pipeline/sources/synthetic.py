"""
NIRVANA Data Pipeline — Synthetic Data Generator

Generates clearly-labeled SYNTHETIC data for development and testing.
Statistical distributions derived from real MPLADS GODL data.

⚠️  ALL SYNTHETIC RECORDS ARE MARKED data_availability_status='SYNTHETIC'
⚠️  NEVER used as real government data
"""
import uuid
import random
import math
from datetime import date, timedelta, datetime
from typing import Optional

from data_pipeline.sources.base import BaseDataSource, IngestionRecord


STATES_DISTRICTS = {
    "Uttar Pradesh": ["Lucknow", "Varanasi", "Agra", "Allahabad", "Kanpur", "Meerut", "Gorakhpur"],
    "Maharashtra": ["Pune", "Nashik", "Nagpur", "Aurangabad", "Thane"],
    "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Kota", "Bikaner"],
    "Bihar": ["Patna", "Gaya", "Muzaffarpur", "Bhagalpur", "Darbhanga"],
    "Madhya Pradesh": ["Bhopal", "Indore", "Gwalior", "Jabalpur", "Rewa"],
    "Karnataka": ["Bangalore", "Mysore", "Hubli", "Belgaum", "Mangalore"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Salem", "Trichy"],
    "West Bengal": ["Kolkata", "Howrah", "Asansol", "Siliguri", "Durgapur"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Bhavnagar"],
    "Andhra Pradesh": ["Visakhapatnam", "Vijayawada", "Guntur", "Nellore", "Kurnool"],
}

SECTORS = ["Road", "Education", "Health", "Drinking Water", "Sanitation", "Sports", "Community Hall", "Bridge", "Drainage", "Cultural"]
PROJECT_TYPES_FOR_SECTORS = {
    "Road": "ROAD", "Education": "BUILDING", "Health": "BUILDING",
    "Drinking Water": "WATER_TANK", "Sanitation": "OTHER",
    "Sports": "BUILDING", "Community Hall": "BUILDING",
    "Bridge": "BRIDGE", "Drainage": "OTHER", "Cultural": "BUILDING",
}

# Cost distribution per sector (in INR Lakhs) — derived from public MPLADS statistics
SECTOR_COST_PARAMS = {
    "Road": (25.0, 15.0),
    "Education": (20.0, 10.0),
    "Health": (22.0, 12.0),
    "Drinking Water": (18.0, 9.0),
    "Sanitation": (12.0, 6.0),
    "Sports": (30.0, 15.0),
    "Community Hall": (28.0, 14.0),
    "Bridge": (45.0, 20.0),
    "Drainage": (15.0, 8.0),
    "Cultural": (25.0, 12.0),
}

# State-level geo centroids (approximate)
STATE_CENTROIDS = {
    "Uttar Pradesh": (26.8467, 80.9462),
    "Maharashtra": (19.7515, 75.7139),
    "Rajasthan": (27.0238, 74.2179),
    "Bihar": (25.0961, 85.3131),
    "Madhya Pradesh": (22.9734, 78.6569),
    "Karnataka": (15.3173, 75.7139),
    "Tamil Nadu": (11.1271, 78.6569),
    "West Bengal": (22.9868, 87.8550),
    "Gujarat": (22.2587, 71.1924),
    "Andhra Pradesh": (15.9129, 79.7400),
}

def _add_geo_noise(lat, lon, radius_km=50):
    """Add random offset within ~radius_km."""
    dlat = random.uniform(-radius_km/111, radius_km/111)
    dlon = random.uniform(-radius_km/111, radius_km/111)
    return lat + dlat, lon + dlon


class SyntheticDataSource(BaseDataSource):
    """
    Generates SYNTHETIC MPLADS-like data for development and testing.
    Statistical properties reflect real MPLADS distributions.
    
    ⚠️ SYNTHETIC — NOT real government data.
    """

    def __init__(self, n_projects: int = 500, seed: int = 42, include_anomalies: bool = True):
        super().__init__(
            source_name="Synthetic MPLADS Data (NIRVANA Dev)",
            source_url="INTERNAL",
            license="SYNTHETIC",
        )
        self.n_projects = n_projects
        self.seed = seed
        self.include_anomalies = include_anomalies
        random.seed(seed)

    def fetch(self) -> list[dict]:
        """Generate synthetic records."""
        records = []
        for i in range(self.n_projects):
            state = random.choice(list(STATES_DISTRICTS.keys()))
            district = random.choice(STATES_DISTRICTS[state])
            sector = random.choice(SECTORS)
            project_type = PROJECT_TYPES_FOR_SECTORS[sector]

            mean_cost, std_cost = SECTOR_COST_PARAMS[sector]
            sanction_lakhs = max(5.0, random.gauss(mean_cost, std_cost))
            sanction_inr = sanction_lakhs * 100_000

            # Timeline
            start_days_ago = random.randint(180, 1800)
            start_date = date.today() - timedelta(days=start_days_ago)
            duration_days = random.randint(180, 730)
            expected_completion = start_date + timedelta(days=duration_days)
            elapsed_ratio = min(1.0, start_days_ago / duration_days)

            # Status logic
            if elapsed_ratio >= 1.0:
                # Past due
                rand = random.random()
                if rand < 0.6:
                    status = "COMPLETED"
                    actual_completion = start_date + timedelta(days=int(duration_days * random.uniform(0.9, 1.3)))
                elif rand < 0.8:
                    status = "DELAYED"
                    actual_completion = None
                else:
                    status = "STALLED"
                    actual_completion = None
            elif elapsed_ratio > 0.5:
                status = random.choice(["IN_PROGRESS", "IN_PROGRESS", "DELAYED"])
                actual_completion = None
            else:
                status = "IN_PROGRESS"
                actual_completion = None

            # Normal progress
            if status == "COMPLETED":
                reported_progress = 100.0
            elif status == "STALLED":
                reported_progress = random.uniform(10, 50)
            else:
                reported_progress = min(95, elapsed_ratio * 100 * random.uniform(0.6, 1.1))

            # Expenditure (normal case)
            utilization = min(1.0, random.uniform(0.3, 1.05))
            expenditure = sanction_inr * utilization
            released = sanction_inr * min(1.0, utilization + random.uniform(0, 0.1))

            # Introduce synthetic anomalies for ~15% of projects
            is_anomalous = self.include_anomalies and (i % 7 == 0)
            anomaly_type = None
            if is_anomalous:
                anomaly_type = random.choice([
                    "COST_SPIKE",         # Unusually high cost
                    "PAYMENT_PROGRESS",   # High spend, low progress
                    "STALL_WITH_EXPENSE", # Stalled but expenditure continues
                ])
                if anomaly_type == "COST_SPIKE":
                    sanction_inr *= random.uniform(3.0, 8.0)
                    expenditure = sanction_inr * utilization
                elif anomaly_type == "PAYMENT_PROGRESS":
                    expenditure = sanction_inr * 0.9  # 90% spent
                    reported_progress = random.uniform(10, 30)  # Only 10-30% done
                elif anomaly_type == "STALL_WITH_EXPENSE":
                    status = "STALLED"
                    reported_progress = random.uniform(15, 35)
                    expenditure = sanction_inr * random.uniform(0.5, 0.8)

            # Geo
            centroid = STATE_CENTROIDS.get(state, (20.5937, 78.9629))
            lat, lon = _add_geo_noise(*centroid, radius_km=100)

            records.append({
                "_synthetic": True,
                "_anomaly_type": anomaly_type,
                "project_name": f"{sector} Work - {district} [{i+1:04d}]",
                "sector": sector,
                "project_type": project_type,
                "state": state,
                "district": district,
                "constituency": f"{district} Constituency",
                "latitude": round(lat, 6),
                "longitude": round(lon, 6),
                "sanction_amount": round(sanction_inr, 2),
                "released_amount": round(released, 2),
                "expenditure_amount": round(expenditure, 2),
                "start_date": start_date.isoformat(),
                "expected_completion_date": expected_completion.isoformat(),
                "actual_completion_date": actual_completion.isoformat() if actual_completion else None,
                "reported_progress": round(reported_progress, 1),
                "status": status,
                "mp_name": f"MP-{district[:3].upper()}-{random.randint(100, 999)}",
                "house": random.choice(["LOK_SABHA", "LOK_SABHA", "RAJYA_SABHA"]),
                "lok_sabha_term": random.choice(["17th", "18th"]),
                "agency": f"{district} Municipal Corporation",
            })

        self.logger.info(f"Generated {len(records)} synthetic records "
                        f"({sum(1 for r in records if r.get('_anomaly_type'))} with anomaly markers)")
        return records

    def validate(self, records: list[dict]) -> list[IngestionRecord]:
        """Basic validation of synthetic records."""
        validated = []
        for raw in records:
            errors = []
            ir = IngestionRecord(
                raw_data=raw,
                source_name=self.source_name,
                source_url=self.source_url,
                availability_status="SYNTHETIC",
            )

            if not raw.get("project_name"):
                errors.append("Missing project_name")
                ir.is_valid = False
            if raw.get("sanction_amount", 0) < 0:
                errors.append(f"Negative sanction_amount")
                ir.is_valid = False
            if raw.get("reported_progress", 0) > 100:
                errors.append(f"Progress > 100")
                ir.is_valid = False

            ir.validation_errors = errors
            validated.append(ir)
        return validated

    def normalize(self, records: list[IngestionRecord]) -> list[IngestionRecord]:
        """Normalized data is already structured in fetch()."""
        for ir in records:
            ir.normalized_data = {
                k: v for k, v in ir.raw_data.items()
                if not k.startswith("_")
            }
            # Convert date strings
            for date_field in ["start_date", "expected_completion_date", "actual_completion_date"]:
                val = ir.normalized_data.get(date_field)
                if val:
                    from datetime import date as date_cls
                    try:
                        ir.normalized_data[date_field] = date_cls.fromisoformat(val)
                    except ValueError:
                        ir.normalized_data[date_field] = None
        return records

    def load(self, records: list[IngestionRecord], db_session) -> int:
        """Insert synthetic records into DB."""
        from backend.database.models import Project, DataSource, ProjectProgress
        
        source = db_session.query(DataSource).filter_by(source_url="INTERNAL").first()
        source_id = source.source_id if source else None

        loaded = 0
        for ir in records:
            nd = ir.normalized_data
            if not nd:
                continue

            project_id = str(uuid.uuid4())
            project = Project(
                project_id=project_id,
                source_id=source_id,
                data_availability_status="SYNTHETIC",
                geo_precision="EXACT",  # Synthetic data has precise coords
                **{k: v for k, v in nd.items() if v is not None and hasattr(Project, k)},
            )
            db_session.add(project)

            # Add initial progress snapshot
            if nd.get("start_date"):
                snap = ProjectProgress(
                    progress_id=str(uuid.uuid4()),
                    project_id=project_id,
                    snapshot_date=date.today(),
                    reported_progress=nd.get("reported_progress"),
                    observed_progress=None,  # CV model not available
                    observation_source="NOT_AVAILABLE",
                    expected_progress=None,  # Computed by engine at query time
                )
                db_session.add(snap)

            loaded += 1

        try:
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            self.logger.error(f"Load failed: {e}")
            raise

        return loaded
