"""
NIRVANA — Reality Gap Engine

Computes the gap between Expected, Reported, and Observed reality.

⚠️  PROTOTYPE ANALYTICAL SCORE — not an official government metric.
    Gaps in observed data are shown as NOT_AVAILABLE, not fabricated.

Five gap dimensions:
1. Financial Gap: utilization vs. reported progress
2. Reported-Observed Gap: reported vs. AI-observed (if available)
3. Expected-Reported Gap: expected progress vs. reported
4. Time-Progress Gap: deviation from expected timeline
5. Document Consistency Gap: extracted values vs. reported
"""
import logging
from datetime import date, datetime
from typing import Optional

logger = logging.getLogger("engine.reality_gap")


REALITY_GAP_LEVELS = {
    "NORMAL": (0, 30),
    "WATCH": (30, 60),
    "HIGH": (60, 80),
    "CRITICAL": (80, 100),
}

# Sector-wise typical completion curves (% progress at elapsed_ratio)
# Derived from historical MPLADS data patterns
SECTOR_PROGRESS_CURVES = {
    "Road": {0.0: 0, 0.25: 20, 0.5: 45, 0.75: 70, 1.0: 95},
    "ROAD": {0.0: 0, 0.25: 20, 0.5: 45, 0.75: 70, 1.0: 95},
    "Building": {0.0: 0, 0.25: 15, 0.5: 40, 0.75: 65, 1.0: 95},
    "BUILDING": {0.0: 0, 0.25: 15, 0.5: 40, 0.75: 65, 1.0: 95},
    "Bridge": {0.0: 0, 0.25: 12, 0.5: 35, 0.75: 60, 1.0: 90},
    "BRIDGE": {0.0: 0, 0.25: 12, 0.5: 35, 0.75: 60, 1.0: 90},
    "Water Tank": {0.0: 0, 0.25: 18, 0.5: 42, 0.75: 68, 1.0: 95},
    "WATER_TANK": {0.0: 0, 0.25: 18, 0.5: 42, 0.75: 68, 1.0: 95},
    "DEFAULT": {0.0: 0, 0.25: 15, 0.5: 40, 0.75: 65, 1.0: 90},
}


def interpolate_progress(curve: dict, elapsed_ratio: float) -> float:
    """Linearly interpolate progress from curve."""
    elapsed_ratio = min(1.0, max(0.0, elapsed_ratio))
    keys = sorted(curve.keys())
    
    for i in range(len(keys) - 1):
        k1, k2 = keys[i], keys[i+1]
        if k1 <= elapsed_ratio <= k2:
            t = (elapsed_ratio - k1) / (k2 - k1)
            return curve[k1] + t * (curve[k2] - curve[k1])
    
    return curve[keys[-1]]


class RealityGapEngine:
    """
    Computes how different the reported/observed state is from what's expected.
    
    All gaps are 0-100 (higher = larger gap).
    Output includes data availability status for each dimension.
    """

    def compute(self, project_data: dict) -> dict:
        """
        Args:
            project_data: dict with project fields
        
        Returns:
            dict with gap scores, availability status, and explanation
        """
        today = date.today()
        
        # Extract project fields
        project_id = project_data.get("project_id")
        sector = project_data.get("sector", "DEFAULT")
        project_type = project_data.get("project_type", "OTHER")
        start_date = project_data.get("start_date")
        expected_completion_date = project_data.get("expected_completion_date")
        reported_progress = project_data.get("reported_progress")  # May be None
        observed_progress = project_data.get("observed_progress")  # Very likely None
        sanction_amount = project_data.get("sanction_amount", 0) or 0
        expenditure_amount = project_data.get("expenditure_amount", 0) or 0
        released_amount = project_data.get("released_amount", 0) or 0
        status = project_data.get("status")
        doc_consistency_score = project_data.get("doc_consistency_score")  # Usually None

        gaps = {}
        contributing_factors = []

        # --- 1. Financial Gap ---
        if sanction_amount > 0 and expenditure_amount > 0 and reported_progress is not None:
            utilization_rate = expenditure_amount / sanction_amount
            financial_gap_raw = abs(utilization_rate - reported_progress / 100.0)
            financial_gap = min(100, financial_gap_raw * 200)  # Scale to 0-100
            gaps["financial_gap"] = {
                "score": round(financial_gap, 2),
                "utilization_rate": round(utilization_rate, 3),
                "reported_progress_pct": reported_progress,
                "status": "AVAILABLE",
            }
            if financial_gap > 30:
                contributing_factors.append(
                    f"Financial-progress mismatch: {utilization_rate:.0%} spent vs. {reported_progress:.0f}% reported"
                )
        else:
            gaps["financial_gap"] = {"status": "NOT_AVAILABLE", "score": None}

        # --- 2. Time-Progress Gap ---
        if start_date and expected_completion_date and reported_progress is not None:
            try:
                if isinstance(start_date, str):
                    start_date = date.fromisoformat(start_date)
                if isinstance(expected_completion_date, str):
                    expected_completion_date = date.fromisoformat(expected_completion_date)
                    
                planned_duration = (expected_completion_date - start_date).days
                elapsed = (today - start_date).days
                elapsed_ratio = min(2.0, elapsed / max(planned_duration, 1))

                # Expected progress from historical curve
                curve = SECTOR_PROGRESS_CURVES.get(sector) or \
                        SECTOR_PROGRESS_CURVES.get(project_type) or \
                        SECTOR_PROGRESS_CURVES["DEFAULT"]
                expected_progress = interpolate_progress(curve, elapsed_ratio)
                expected_range_low = expected_progress * 0.85
                expected_range_high = min(100, expected_progress * 1.15)

                time_gap_raw = abs(expected_progress - reported_progress)
                time_gap = min(100, time_gap_raw * 1.5)

                gaps["time_progress_gap"] = {
                    "score": round(time_gap, 2),
                    "expected_progress": round(expected_progress, 1),
                    "expected_range": [round(expected_range_low, 1), round(expected_range_high, 1)],
                    "reported_progress": reported_progress,
                    "elapsed_ratio": round(elapsed_ratio, 3),
                    "elapsed_days": elapsed,
                    "planned_duration_days": planned_duration,
                    "status": "AVAILABLE",
                }
                if time_gap > 25:
                    contributing_factors.append(
                        f"Expected {expected_progress:.0f}% progress, reported {reported_progress:.0f}%"
                    )
            except Exception as e:
                gaps["time_progress_gap"] = {"status": "ERROR", "error": str(e), "score": None}
        else:
            expected_progress = None
            gaps["time_progress_gap"] = {"status": "NOT_AVAILABLE", "score": None}

        # --- 3. Reported-Observed Gap ---
        # Critical: only compute if actual observed data exists
        if observed_progress is not None and reported_progress is not None:
            reported_observed_gap = abs(reported_progress - observed_progress)
            gaps["reported_observed_gap"] = {
                "score": min(100, reported_observed_gap * 1.5),
                "reported_progress": reported_progress,
                "observed_progress": observed_progress,
                "status": "AVAILABLE",
            }
            contributing_factors.append(
                f"Reported {reported_progress:.0f}% vs. observed {observed_progress:.0f}%"
            )
        else:
            gaps["reported_observed_gap"] = {
                "status": "NOT_AVAILABLE",
                "score": None,
                "note": "Physical evidence unavailable — image-based estimation not yet active",
            }

        # --- 4. Document Consistency Gap ---
        if doc_consistency_score is not None:
            gaps["document_gap"] = {
                "score": round((1.0 - doc_consistency_score) * 100, 2),
                "consistency_score": doc_consistency_score,
                "status": "AVAILABLE",
            }
        else:
            gaps["document_gap"] = {
                "status": "NOT_AVAILABLE",
                "score": None,
                "note": "No documents uploaded for this project",
            }

        # --- Compute combined reality gap score ---
        available_gaps = [
            g["score"] for g in gaps.values()
            if g.get("status") == "AVAILABLE" and g.get("score") is not None
        ]

        if available_gaps:
            # Weighted average if available, else mean
            reality_gap_score = sum(available_gaps) / len(available_gaps)
            gap_level = self._get_gap_level(reality_gap_score)
        else:
            reality_gap_score = None
            gap_level = "UNKNOWN"

        # Confidence (based on available signals)
        available_count = sum(1 for g in gaps.values() if g.get("status") == "AVAILABLE")
        total_count = len(gaps)
        confidence = available_count / total_count

        return {
            "project_id": project_id,
            "reality_gap_score": round(reality_gap_score, 2) if reality_gap_score else None,
            "gap_level": gap_level,
            "confidence": round(confidence, 2),
            "expected_progress": round(expected_progress, 1) if expected_progress is not None else None,
            "reported_progress": reported_progress,
            "observed_progress": observed_progress,  # null if not available
            "observed_progress_status": "NOT_AVAILABLE" if observed_progress is None else "AVAILABLE",
            "gaps": gaps,
            "contributing_factors": contributing_factors,
            "disclaimer": (
                "Reality Gap Score is a prototype analytical score. "
                "It is not an official government metric. "
                "Values represent AI-estimated deviations requiring human verification."
            ),
            "computed_at": datetime.utcnow().isoformat(),
        }

    def _get_gap_level(self, score: float) -> str:
        for level, (low, high) in REALITY_GAP_LEVELS.items():
            if low <= score < high:
                return level
        return "CRITICAL"
