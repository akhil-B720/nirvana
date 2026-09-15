"""
NIRVANA — Risk Fusion Engine

Combines multiple anomaly signals into a single risk score.
Weights are configurable via database settings.

Output:
  risk_score: 0-100 (higher = higher risk)
  risk_level: LOW / MEDIUM / HIGH / CRITICAL
  explanation: human-readable explanation
  contributing_factors: dict with individual signal contributions

⚠️  Risk score is a DECISION-SUPPORT signal.
    It does NOT constitute proof of fraud or wrongdoing.
"""
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

logger = logging.getLogger("engine.risk_fusion")


# Default weights (configurable by admin)
DEFAULT_WEIGHTS = {
    "cost_anomaly": 0.20,
    "payment_progress": 0.20,
    "delay": 0.15,
    "similarity": 0.10,
    "document": 0.10,
    "reality_gap": 0.25,
}

RISK_THRESHOLDS = {
    "LOW": (0, 30),
    "MEDIUM": (30, 55),
    "HIGH": (55, 75),
    "CRITICAL": (75, 100),
}


def get_risk_level(score: float) -> str:
    for level, (low, high) in RISK_THRESHOLDS.items():
        if low <= score < high:
            return level
    return "CRITICAL"


@dataclass
class RiskSignals:
    """Input signals to the risk fusion engine."""
    project_id: str
    cost_anomaly_score: Optional[float] = None    # 0-100, from Isolation Forest
    cost_anomaly_confidence: float = 0.5
    payment_progress_gap: Optional[float] = None  # 0-100
    delay_probability: Optional[float] = None     # 0-1
    similarity_score: Optional[float] = None      # 0-1
    document_score: Optional[float] = None        # 0-100 (higher = more inconsistent)
    reality_gap_score: Optional[float] = None     # 0-100
    
    # Availability flags
    cost_available: bool = True
    payment_available: bool = True
    delay_available: bool = True
    similarity_available: bool = True
    document_available: bool = False
    reality_gap_available: bool = True


class RiskFusionEngine:
    """
    Fuses multiple anomaly signals into a single configurable risk score.
    
    Key design principles:
    1. Weights are configurable by authorities
    2. Missing signals reduce confidence, not substitute with 0
    3. Every output has a confidence score
    4. All computations are logged for auditability
    5. Output is ALWAYS labeled as a decision-support signal
    """

    def __init__(self, weights: dict = None):
        self.weights = weights or DEFAULT_WEIGHTS
        self._validate_weights()

    def _validate_weights(self):
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.01:
            logger.warning(f"Risk weights sum to {total:.3f}, not 1.0 — normalizing")
            self.weights = {k: v / total for k, v in self.weights.items()}

    def compute(self, signals: RiskSignals) -> dict:
        """
        Compute fused risk score.
        
        Returns:
          risk_score: 0-100
          risk_level: LOW/MEDIUM/HIGH/CRITICAL
          confidence: 0-1 (lower if many signals are None)
          explanation: human-readable
          contributing_factors: dict
          disclaimer: ethical statement
        """
        components = {}
        available_signals = 0
        total_signals = 0

        # --- Cost anomaly ---
        total_signals += 1
        if signals.cost_anomaly_score is not None:
            components["cost_anomaly"] = {
                "raw_score": signals.cost_anomaly_score,
                "weighted": signals.cost_anomaly_score * self.weights["cost_anomaly"],
                "weight": self.weights["cost_anomaly"],
                "available": True,
                "confidence": signals.cost_anomaly_confidence,
            }
            available_signals += 1
        else:
            components["cost_anomaly"] = {"available": False, "note": "NOT_AVAILABLE"}

        # --- Payment-progress gap ---
        total_signals += 1
        if signals.payment_progress_gap is not None:
            components["payment_progress"] = {
                "raw_score": signals.payment_progress_gap,
                "weighted": signals.payment_progress_gap * self.weights["payment_progress"],
                "weight": self.weights["payment_progress"],
                "available": True,
                "confidence": 0.7,
            }
            available_signals += 1
        else:
            components["payment_progress"] = {"available": False, "note": "NOT_AVAILABLE"}

        # --- Delay probability ---
        total_signals += 1
        if signals.delay_probability is not None:
            delay_score = signals.delay_probability * 100
            components["delay"] = {
                "raw_score": delay_score,
                "delay_probability": signals.delay_probability,
                "weighted": delay_score * self.weights["delay"],
                "weight": self.weights["delay"],
                "available": True,
                "confidence": 0.65,
            }
            available_signals += 1
        else:
            components["delay"] = {"available": False, "note": "NOT_AVAILABLE"}

        # --- Similarity (duplicate detection) ---
        total_signals += 1
        if signals.similarity_score is not None:
            sim_score = signals.similarity_score * 100
            components["similarity"] = {
                "raw_score": sim_score,
                "similarity_score": signals.similarity_score,
                "weighted": sim_score * self.weights["similarity"],
                "weight": self.weights["similarity"],
                "available": True,
                "confidence": 0.6,
                "note": "potentially_similar — not confirmed duplicate",
            }
            available_signals += 1
        else:
            components["similarity"] = {"available": False, "note": "NOT_AVAILABLE"}

        # --- Document consistency ---
        total_signals += 1
        if signals.document_score is not None:
            components["document"] = {
                "raw_score": signals.document_score,
                "weighted": signals.document_score * self.weights["document"],
                "weight": self.weights["document"],
                "available": True,
                "confidence": 0.5,
            }
            available_signals += 1
        else:
            components["document"] = {"available": False, "note": "NOT_AVAILABLE"}

        # --- Reality gap ---
        total_signals += 1
        if signals.reality_gap_score is not None:
            components["reality_gap"] = {
                "raw_score": signals.reality_gap_score,
                "weighted": signals.reality_gap_score * self.weights["reality_gap"],
                "weight": self.weights["reality_gap"],
                "available": True,
                "confidence": 0.7,
            }
            available_signals += 1
        else:
            components["reality_gap"] = {"available": False, "note": "NOT_AVAILABLE"}

        # Sum weighted scores (renormalize for available signals)
        weighted_sum = sum(
            c["weighted"] for c in components.values()
            if c.get("available") and "weighted" in c
        )

        # Effective weight of available signals
        available_weight = sum(
            self.weights.get(key, 0)
            for key, c in components.items()
            if c.get("available")
        )

        # Normalize to available weight
        if available_weight > 0:
            risk_score = weighted_sum / available_weight * 100
        else:
            risk_score = 0.0

        risk_score = min(100.0, max(0.0, risk_score))
        risk_level = get_risk_level(risk_score)

        # Overall confidence (decreases with missing signals)
        base_confidence = available_signals / max(total_signals, 1)
        avg_component_confidence = sum(
            c.get("confidence", 0.5) for c in components.values() if c.get("available")
        ) / max(available_signals, 1)
        confidence = base_confidence * avg_component_confidence

        # Generate explanation
        explanation = self._generate_explanation(components, risk_score, risk_level)

        return {
            "project_id": signals.project_id,
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "confidence": round(confidence, 3),
            "components": components,
            "weights_used": self.weights,
            "available_signals": available_signals,
            "total_signals": total_signals,
            "explanation": explanation,
            "disclaimer": (
                "AI-generated risk indicators are decision-support signals. "
                "They do not constitute proof of fraud, corruption, or wrongdoing. "
                "Final determinations must be made by authorized government officers."
            ),
            "computed_at": datetime.utcnow().isoformat(),
        }

    def _generate_explanation(self, components: dict, risk_score: float, risk_level: str) -> str:
        """Generate human-readable explanation from contributing factors."""
        # Find top contributing signals
        top_signals = []
        signal_labels = {
            "cost_anomaly": "cost anomaly",
            "payment_progress": "payment-progress mismatch",
            "delay": "delay probability",
            "similarity": "project similarity flag",
            "document": "document inconsistency",
            "reality_gap": "reality gap",
        }

        for key, comp in components.items():
            if comp.get("available") and "weighted" in comp:
                contribution = comp["weighted"]
                if contribution > 5:
                    top_signals.append((key, contribution))

        top_signals.sort(key=lambda x: -x[1])

        if not top_signals:
            return f"Risk level {risk_level} (score: {risk_score:.0f}/100). Insufficient signals for detailed explanation."

        signal_str = ", ".join(f"{signal_labels.get(k, k)} ({v:.0f})" for k, v in top_signals[:3])
        return (
            f"Risk level: {risk_level} (score: {risk_score:.0f}/100). "
            f"Primary contributing factors: {signal_str}. "
            f"Verification recommended for flagged signals."
        )

    def save_to_db(self, result: dict, db_session):
        """Persist the computed risk score to database."""
        from backend.database.models import RiskScore

        # Get latest model version IDs
        model_version_ids = []

        risk = RiskScore(
            risk_id=str(uuid.uuid4()),
            project_id=result["project_id"],
            risk_score=result["risk_score"],
            risk_level=result["risk_level"],
            reality_gap_score=result["components"].get("reality_gap", {}).get("raw_score"),
            cost_anomaly_score=result["components"].get("cost_anomaly", {}).get("raw_score"),
            delay_probability=result["components"].get("delay", {}).get("delay_probability"),
            similarity_score=result["components"].get("similarity", {}).get("similarity_score"),
            document_score=result["components"].get("document", {}).get("raw_score"),
            weights_used=result["weights_used"],
            explanation=result["explanation"],
            confidence=result["confidence"],
            computed_at=datetime.utcnow(),
            model_version_ids=model_version_ids,
        )
        db_session.add(risk)
        db_session.commit()
        return risk
