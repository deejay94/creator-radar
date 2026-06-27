"""AI opportunity scoring."""

from radar.scoring.config import is_ai_scoring_enabled
from radar.scoring.scorer import ScoreResult, apply_score, score_opportunity

__all__ = [
    "ScoreResult",
    "apply_score",
    "is_ai_scoring_enabled",
    "score_opportunity",
]
