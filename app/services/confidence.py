from config import settings

class ConfidenceService:
    """Evaluates resolution confidence and triggers escalation signals."""
    
    @staticmethod
    def should_escalate(score: float) -> bool:
        return score < settings.CONFIDENCE_THRESHOLD_ESCALATE

    @staticmethod
    def analyze_confidence(score: float, reasoning: str) -> dict:
        needs_escalation = score < settings.CONFIDENCE_THRESHOLD_ESCALATE
        return {
            "score": score,
            "is_confident": not needs_escalation,
            "action": "escalate" if needs_escalation else "proceed",
            "reasoning": reasoning
        }
