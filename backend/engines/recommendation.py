import json
import logging
from fastapi import Request

logger = logging.getLogger("engine.reality_gap")

# Simple mock recommendation engine
class VerificationRecommendationEngine:
    def get_recommendations(self, risk_score_dict: dict) -> list[str]:
        recs = []
        comp = risk_score_dict.get("components", {})
        
        if comp.get("cost_anomaly", {}).get("raw_score", 0) > 50:
            recs.append("Verify actual expenditure against sanction amounts.")
            
        if comp.get("payment_progress", {}).get("raw_score", 0) > 30:
            recs.append("Large gap between expenditure and reported progress. Request latest physical measurement.")
            
        if comp.get("delay", {}).get("delay_probability", 0) > 0.7:
            recs.append("Project highly likely to be delayed. Request timeline update.")
            
        if comp.get("similarity", {}).get("similarity_score", 0) > 0.6:
            recs.append("Potential duplicate project detected. Check coordinates against similar projects.")
            
        if comp.get("reality_gap", {}).get("raw_score", 0) > 60:
            recs.append("High overall reality gap. Field inspection recommended.")
            
        if not recs:
            recs.append("No specific high-priority verification recommended at this time.")
            
        return recs
