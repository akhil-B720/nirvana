"""
Mock Expected Progress Model
"""
from backend.engines.reality_gap import SECTOR_PROGRESS_CURVES, interpolate_progress

class ExpectedProgressModel:
    def compute(self, elapsed_ratio: float, sector: str = "DEFAULT") -> float:
        curve = SECTOR_PROGRESS_CURVES.get(sector) or SECTOR_PROGRESS_CURVES.get("DEFAULT")
        return interpolate_progress(curve, elapsed_ratio)
