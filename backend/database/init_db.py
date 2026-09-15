"""
NIRVANA — Database Initialization
Creates all tables and seeds initial data:
- Admin user
- Data sources registry
- Synthetic project data (clearly labeled)
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy import text
from backend.database.session import async_engine, sync_engine
from backend.database.models import Base, User, DataSource
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_tables():
    """Create all tables synchronously."""
    Base.metadata.create_all(bind=sync_engine)
    print("✅ All database tables created.")


def seed_data_sources(db):
    """Register all known data sources."""
    from backend.database.models import DataSource
    import uuid
    from datetime import datetime

    sources = [
        {
            "source_id": str(uuid.uuid4()),
            "source_name": "MPLADS Works List — 17th Lok Sabha",
            "source_url": "https://data.gov.in/resource/mplads-works-list-17th-lok-sabha",
            "source_type": "GOVERNMENT_OPEN",
            "license": "GODL",
            "access_method": "DIRECT_DOWNLOAD",
            "verification_status": "PUBLIC_VERIFIED",
        },
        {
            "source_id": str(uuid.uuid4()),
            "source_name": "Year-wise MPLADS Fund Position 2014-2018",
            "source_url": "https://data.gov.in/resource/year-wise-position-members-parliament-local-area-development-scheme-mplads-2014-15-2017-18",
            "source_type": "GOVERNMENT_OPEN",
            "license": "GODL",
            "access_method": "DIRECT_DOWNLOAD",
            "verification_status": "PUBLIC_VERIFIED",
        },
        {
            "source_id": str(uuid.uuid4()),
            "source_name": "State-wise MPLADS Financial Performance 2016-2020",
            "source_url": "https://data.gov.in/resource/state-wise-details-worksprojects-under-members-parliament-local-area-development-scheme",
            "source_type": "GOVERNMENT_OPEN",
            "license": "GODL",
            "access_method": "DIRECT_DOWNLOAD",
            "verification_status": "PUBLIC_VERIFIED",
        },
        {
            "source_id": str(uuid.uuid4()),
            "source_name": "Sector-wise Cumulative Cost 2015",
            "source_url": "https://data.gov.in/resource/sector-wise-cumulative-cost-sanctioned-works-under-members-parliament-local-area",
            "source_type": "GOVERNMENT_OPEN",
            "license": "GODL",
            "access_method": "DIRECT_DOWNLOAD",
            "verification_status": "PUBLIC_VERIFIED",
        },
        {
            "source_id": str(uuid.uuid4()),
            "source_name": "Synthetic Development Data (NIRVANA)",
            "source_url": "INTERNAL",
            "source_type": "SYNTHETIC",
            "license": "INTERNAL",
            "access_method": "GENERATED",
            "verification_status": "SYNTHETIC",
        },
    ]

    added = 0
    for src_data in sources:
        existing = db.query(DataSource).filter_by(source_url=src_data["source_url"]).first()
        if not existing:
            src = DataSource(**src_data)
            db.add(src)
            added += 1

    db.commit()
    print(f"✅ Seeded {added} data sources.")
    return {s["source_name"]: s["source_id"] for s in sources}


def seed_admin_user(db):
    """Create default admin user if not exists."""
    username = os.getenv("INITIAL_ADMIN_USERNAME", "admin")
    existing = db.query(User).filter_by(username=username).first()
    if existing:
        print(f"ℹ️  Admin user '{username}' already exists.")
        return

    import uuid
    admin = User(
        user_id=str(uuid.uuid4()),
        username=username,
        email=os.getenv("INITIAL_ADMIN_EMAIL", "admin@nirvana.gov.in"),
        hashed_password=pwd_context.hash(os.getenv("INITIAL_ADMIN_PASSWORD", "ChangeMe@2024!")),
        role="ADMIN",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    print(f"✅ Created admin user: {username}")


def main():
    from backend.database.session import SyncSessionLocal

    print("🚀 Initializing NIRVANA database...")
    create_tables()

    db = SyncSessionLocal()
    try:
        seed_data_sources(db)
        seed_admin_user(db)
        print("\n✅ Database initialized successfully.")
        print("   Run: python -m data_pipeline.run  (to ingest real data)")
        print("   Run: python -m ml.train.cost_anomaly  (to train ML models)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
