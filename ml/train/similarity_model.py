"""
NIRVANA ML — Duplicate/Similarity Detection

Detects potentially similar projects using:
1. TF-IDF cosine similarity on project names + descriptions
2. Geographic distance (Haversine)
3. Sector + amount comparison

Output: text_similarity (0-1), geo_similarity (0-1), combined_similarity (0-1)
        potentially_similar (bool) — NOT confirmed_duplicate

⚠️ Output is labeled 'potentially_similar' — never 'duplicate' or 'fraud'
"""
import os
import sys
import uuid
import logging
import warnings
import numpy as np
import pandas as pd
import joblib
from datetime import datetime
from pathlib import Path
from math import radians, cos, sin, asin, sqrt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
warnings.filterwarnings("ignore")

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("ml.similarity")

MODEL_DIR = Path("models/similarity_model")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

TEXT_SIM_THRESHOLD = 0.75  # Cosine similarity threshold for text
GEO_DIST_THRESHOLD_KM = 2.0  # Within 2km = potentially same location
COMBINED_THRESHOLD = 0.60  # Combined score to flag as potentially similar


def haversine_km(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km."""
    if any(v is None for v in [lat1, lon1, lat2, lon2]):
        return float("inf")
    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 2 * R * asin(sqrt(a))


def load_project_data() -> pd.DataFrame:
    """Load projects for similarity analysis."""
    from backend.database.session import SyncSessionLocal
    from backend.database.models import Project

    db = SyncSessionLocal()
    try:
        projects = db.query(Project).all()
        rows = [{
            "project_id": p.project_id,
            "project_name": p.project_name or "",
            "sector": p.sector or "",
            "project_type": p.project_type or "",
            "state": p.state or "",
            "district": p.district or "",
            "constituency": p.constituency or "",
            "latitude": p.latitude,
            "longitude": p.longitude,
            "sanction_amount": float(p.sanction_amount or 0),
        } for p in projects]
        df = pd.DataFrame(rows)
        logger.info(f"Loaded {len(df)} projects for similarity analysis")
        return df
    finally:
        db.close()


def build_text_corpus(df: pd.DataFrame) -> list[str]:
    """Build text corpus for TF-IDF."""
    corpus = []
    for _, row in df.iterrows():
        # Combine project name, sector, type, constituency for richer text
        text = f"{row['project_name']} {row['sector']} {row['project_type']} {row['district']} {row['constituency']}"
        corpus.append(text.lower().strip())
    return corpus


def compute_similarity_pairs(df: pd.DataFrame, vectorizer, tfidf_matrix, top_k: int = 5):
    """
    For each project, find top-K most similar others.
    Returns list of similarity pairs.
    """
    pairs = []
    n = len(df)

    for i in range(n):
        # Text similarity — cosine of TF-IDF vectors
        try:
            sim_scores = cosine_similarity(tfidf_matrix[i:i+1], tfidf_matrix).flatten()
        except Exception:
            continue
        
        # Get top-K (excluding self)
        sim_indices = np.argsort(sim_scores)[::-1][1:top_k+1]

        for j in sim_indices:
            text_sim = float(sim_scores[j])
            if text_sim < 0.3:  # Skip low similarity pairs
                continue

            # Geographic similarity
            geo_dist = haversine_km(
                df.iloc[i]["latitude"], df.iloc[i]["longitude"],
                df.iloc[j]["latitude"], df.iloc[j]["longitude"],
            )
            # Convert distance to similarity score (0 km = 1.0, >50 km = 0.0)
            geo_sim = max(0.0, 1.0 - geo_dist / 50.0) if geo_dist != float("inf") else 0.0

            # Amount similarity
            amt_i = df.iloc[i]["sanction_amount"]
            amt_j = df.iloc[j]["sanction_amount"]
            max_amt = max(amt_i, amt_j, 1)
            amt_sim = 1.0 - abs(amt_i - amt_j) / max_amt if max_amt > 0 else 0.0

            # Combined score (weighted)
            combined = 0.5 * text_sim + 0.35 * geo_sim + 0.15 * amt_sim

            if combined >= 0.40:  # Store pairs above minimum threshold
                pairs.append({
                    "project_id_a": df.iloc[i]["project_id"],
                    "project_id_b": df.iloc[j]["project_id"],
                    "text_similarity": round(text_sim, 4),
                    "geo_similarity": round(geo_sim, 4),
                    "geo_distance_km": round(geo_dist, 2) if geo_dist != float("inf") else None,
                    "amount_similarity": round(amt_sim, 4),
                    "combined_similarity": round(combined, 4),
                    "potentially_similar": combined >= COMBINED_THRESHOLD,
                    "computed_at": datetime.utcnow().isoformat(),
                })

    # Deduplicate (A-B and B-A are the same pair)
    seen = set()
    unique_pairs = []
    for p in pairs:
        key = tuple(sorted([p["project_id_a"], p["project_id_b"]]))
        if key not in seen:
            seen.add(key)
            unique_pairs.append(p)

    return unique_pairs


def train():
    """Train TF-IDF vectorizer and compute similarity pairs."""
    logger.info("=== NIRVANA Similarity Model Training ===")
    logger.info("Method: TF-IDF + Cosine Similarity + Haversine Distance")

    df = load_project_data()

    if len(df) < 2:
        logger.error("Need at least 2 projects for similarity analysis.")
        return

    corpus = build_text_corpus(df)
    logger.info(f"Built corpus of {len(corpus)} documents")

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=5000,
        stop_words=["the", "of", "and", "in", "at", "on", "for", "to"],
        min_df=1,
    )
    tfidf_matrix = vectorizer.fit_transform(corpus)
    logger.info(f"TF-IDF matrix shape: {tfidf_matrix.shape}")

    # Compute pairs
    all_pairs = compute_similarity_pairs(df, vectorizer, tfidf_matrix)
    flagged = [p for p in all_pairs if p["potentially_similar"]]

    logger.info(f"Found {len(all_pairs)} pairs above 0.40 combined similarity")
    logger.info(f"Flagged {len(flagged)} as potentially_similar (threshold={COMBINED_THRESHOLD})")
    logger.info("⚠️  'potentially_similar' does NOT mean confirmed duplicate or fraud")

    # Save model
    version = datetime.now().strftime("%Y%m%d_%H%M%S")
    artifacts = {
        "vectorizer": vectorizer,
        "feature_names": vectorizer.get_feature_names_out().tolist()[:100],
        "text_threshold": TEXT_SIM_THRESHOLD,
        "geo_threshold_km": GEO_DIST_THRESHOLD_KM,
        "combined_threshold": COMBINED_THRESHOLD,
        "training_metadata": {
            "version": version,
            "n_projects": len(df),
            "n_pairs_found": len(all_pairs),
            "n_potentially_similar": len(flagged),
            "trained_at": datetime.utcnow().isoformat(),
        }
    }

    model_path = MODEL_DIR / f"similarity_model_{version}.joblib"
    latest_path = MODEL_DIR / "similarity_model_latest.joblib"
    joblib.dump(artifacts, model_path)
    joblib.dump(artifacts, latest_path)

    # Save pairs CSV for inspection
    if all_pairs:
        pairs_df = pd.DataFrame(all_pairs)
        pairs_df.to_csv(MODEL_DIR / "similarity_pairs_latest.csv", index=False)
        logger.info(f"Pairs saved to: {MODEL_DIR}/similarity_pairs_latest.csv")

    # Store anomalies in DB
    store_similarity_anomalies(flagged)

    register_model(artifacts, str(latest_path), version)
    logger.info("✅ Similarity model training complete.")


def store_similarity_anomalies(similar_pairs: list[dict]):
    """Store potentially similar flags as anomalies in the database."""
    try:
        from backend.database.session import SyncSessionLocal
        from backend.database.models import ProjectAnomaly

        db = SyncSessionLocal()
        stored = 0
        for pair in similar_pairs:
            for proj_id in [pair["project_id_a"], pair["project_id_b"]]:
                existing = db.query(ProjectAnomaly).filter_by(
                    project_id=proj_id,
                    anomaly_type="DUPLICATE",
                ).first()
                if not existing:
                    anomaly = ProjectAnomaly(
                        anomaly_id=str(uuid.uuid4()),
                        project_id=proj_id,
                        anomaly_type="DUPLICATE",
                        signal_value=pair["combined_similarity"],
                        normalized_score=pair["combined_similarity"] * 100,
                        confidence=0.6,
                        contributing_features={
                            "text_similarity": pair["text_similarity"],
                            "geo_similarity": pair["geo_similarity"],
                            "geo_distance_km": pair.get("geo_distance_km"),
                            "similar_to": pair["project_id_b"] if proj_id == pair["project_id_a"] else pair["project_id_a"],
                            "note": "potentially_similar — not confirmed duplicate",
                        },
                        status="OPEN",
                    )
                    db.add(anomaly)
                    stored += 1

        db.commit()
        db.close()
        logger.info(f"Stored {stored} potential-similarity anomaly flags in DB")
    except Exception as e:
        logger.warning(f"Could not store anomalies: {e}")


def register_model(artifacts, model_path, version):
    try:
        from backend.database.session import SyncSessionLocal
        from backend.database.models import ModelVersion
        
        db = SyncSessionLocal()
        meta = artifacts["training_metadata"]

        db.query(ModelVersion).filter_by(
            model_name="similarity_tfidf_cosine",
            status="ACTIVE"
        ).update({"status": "RETIRED"})

        mv = ModelVersion(
            model_id=str(uuid.uuid4()),
            model_name="similarity_tfidf_cosine",
            version=version,
            algorithm="TF-IDF + Cosine Similarity + Haversine",
            training_data_version=f"n={meta['n_projects']}",
            training_timestamp=datetime.utcnow(),
            features={"method": "TF-IDF (n-gram 1-2), max_features=5000"},
            hyperparameters={
                "text_threshold": TEXT_SIM_THRESHOLD,
                "geo_threshold_km": GEO_DIST_THRESHOLD_KM,
                "combined_threshold": COMBINED_THRESHOLD,
            },
            metrics={
                "n_pairs_found": meta["n_pairs_found"],
                "n_potentially_similar": meta["n_potentially_similar"],
                "note": "Unsupervised — no precision/recall without confirmed labels",
            },
            status="ACTIVE",
            model_path=model_path,
            card_path="MODEL_CARD_SIMILARITY.md",
        )
        db.add(mv)
        db.commit()
        db.close()
    except Exception as e:
        logger.warning(f"Could not register model: {e}")


if __name__ == "__main__":
    train()
