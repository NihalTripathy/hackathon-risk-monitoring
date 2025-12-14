"""
Explanation Service - Priority 2: Plain-Language Forecast Explanations
SOLID compliant service for generating human-readable explanations
"""

from typing import Dict, Any, Optional
from datetime import datetime
from abc import ABC, abstractmethod


class ExplanationProvider(ABC):
    """Abstract base class for explanation providers (SOLID: Dependency Inversion)"""
    
    @abstractmethod
    def explain_forecast(self, forecast: Dict[str, Any], baseline_days: Optional[int] = None) -> str:
        """Generate plain-language forecast explanation"""
        pass
    
    @abstractmethod
    def explain_risk_score(self, risk_score: float, risk_level: str) -> str:
        """Generate plain-language risk score explanation"""
        pass


class PlainLanguageExplanationProvider(ExplanationProvider):
    """Plain-language explanation provider implementation"""
    
    def explain_forecast(self, forecast: Dict[str, Any], baseline_days: Optional[int] = None) -> str:
        """Generate plain-language forecast explanation"""
        p50 = forecast.get("p50", 0)
        p80 = forecast.get("p80", 0)
        current = forecast.get("current", 0)
        
        explanation = f"Your project will most likely finish in {p50} days (50% confidence). "
        explanation += f"This means there's a 50% chance you'll complete the project on or before day {p50}. "
        
        if p80 > p50:
            diff = p80 - p50
            explanation += f"In the worst-case scenario (80% confidence), it could take up to {p80} days, "
            explanation += f"which is {diff} days longer than the most likely scenario. "
        
        if baseline_days:
            if p50 > baseline_days:
                delay = p50 - baseline_days
                explanation += f"This is {delay} day{'s' if delay != 1 else ''} later than your baseline of {baseline_days} days. "
            elif p50 < baseline_days:
                ahead = baseline_days - p50
                explanation += f"This is {ahead} day{'s' if ahead != 1 else ''} ahead of your baseline of {baseline_days} days. "
            else:
                explanation += f"This matches your baseline of {baseline_days} days. "
        
        if current > 0:
            explanation += f"Current progress: {current:.1f}% complete. "
        
        # Add context about uncertainty
        if p80 - p50 > 5:
            explanation += "The significant difference between most likely and worst-case suggests high uncertainty in the project schedule. "
            explanation += "Consider reviewing high-risk activities to reduce this uncertainty."
        elif p80 - p50 <= 2:
            explanation += "The small difference between scenarios indicates relatively low schedule uncertainty."
        
        return explanation.strip()
    
    def explain_risk_score(self, risk_score: float, risk_level: str) -> str:
        """Generate plain-language risk score explanation"""
        if risk_level.lower() == "high":
            explanation = f"This activity has a high risk score of {risk_score:.1f}/100. "
            explanation += "This means it has a significant chance of causing project delays. "
            explanation += "Immediate attention and mitigation actions are recommended."
        elif risk_level.lower() == "medium":
            explanation = f"This activity has a medium risk score of {risk_score:.1f}/100. "
            explanation += "While not critical, it should be monitored closely. "
            explanation += "Consider preventive actions to avoid escalation."
        else:
            explanation = f"This activity has a low risk score of {risk_score:.1f}/100. "
            explanation += "It's currently on track, but continue monitoring as project conditions change."
        
        return explanation


class ExplanationService:
    """Main explanation service (SOLID: Single Responsibility)"""
    
    def __init__(self, provider: Optional[ExplanationProvider] = None):
        """Initialize with explanation provider"""
        self.provider = provider or PlainLanguageExplanationProvider()
    
    def register_provider(self, provider: ExplanationProvider):
        """Register a new explanation provider (SOLID: Open/Closed)"""
        self.provider = provider
    
    def explain_forecast(
        self,
        forecast: Dict[str, Any],
        baseline_days: Optional[int] = None,
        project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive forecast explanation"""
        plain_language = self.provider.explain_forecast(forecast, baseline_days)
        
        explanation = {
            "plain_language": plain_language,
            "p50": forecast.get("p50"),
            "p80": forecast.get("p80"),
            "p90": forecast.get("p90"),
            "p95": forecast.get("p95"),
            "current_progress": forecast.get("current", 0),
            "baseline_days": baseline_days,
            "confidence_intervals": self._calculate_confidence_intervals(forecast),
            "key_insights": self._generate_key_insights(forecast, baseline_days, project_context)
        }
        
        return explanation
    
    def explain_risk_score(self, risk_score: float, risk_level: str) -> str:
        """Generate plain-language risk score explanation"""
        return self.provider.explain_risk_score(risk_score, risk_level)
    
    def _calculate_confidence_intervals(self, forecast: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate confidence intervals for forecasts"""
        p50 = forecast.get("p50", 0)
        p80 = forecast.get("p80", 0)
        mean = forecast.get("mean", p50)
        std = forecast.get("std", 0)
        
        # Calculate 95% confidence interval around P50
        if std > 0:
            ci_lower = max(0, int(mean - 1.96 * std))
            ci_upper = int(mean + 1.96 * std)
        else:
            ci_lower = p50 - 2
            ci_upper = p50 + 2
        
        return {
            "p50_ci_95": {
                "lower": ci_lower,
                "upper": ci_upper,
                "interpretation": f"95% confident that actual completion will be between {ci_lower} and {ci_upper} days"
            },
            "uncertainty_range": p80 - p50,
            "uncertainty_level": "high" if (p80 - p50) > 5 else "medium" if (p80 - p50) > 2 else "low"
        }
    
    def _generate_key_insights(
        self,
        forecast: Dict[str, Any],
        baseline_days: Optional[int],
        project_context: Optional[Dict[str, Any]]
    ) -> list:
        """Generate key insights from forecast"""
        insights = []
        
        p50 = forecast.get("p50", 0)
        p80 = forecast.get("p80", 0)
        
        # Baseline comparison
        if baseline_days:
            if p50 > baseline_days:
                delay = p50 - baseline_days
                insights.append(f"Project is {delay} day{'s' if delay != 1 else ''} behind baseline schedule")
            elif p50 < baseline_days:
                ahead = baseline_days - p50
                insights.append(f"Project is {ahead} day{'s' if ahead != 1 else ''} ahead of baseline schedule")
        
        # Uncertainty analysis
        uncertainty = p80 - p50
        if uncertainty > 10:
            insights.append("High schedule uncertainty - consider risk mitigation strategies")
        elif uncertainty > 5:
            insights.append("Moderate schedule uncertainty - monitor high-risk activities")
        
        # Critical path insights
        if project_context:
            high_risk_count = project_context.get("high_risk_activities", 0)
            if high_risk_count > 0:
                insights.append(f"{high_risk_count} high-risk activities detected - review mitigation options")
        
        return insights


# Global explanation service instance
_explanation_service: Optional[ExplanationService] = None


def get_explanation_service() -> ExplanationService:
    """Get global explanation service instance"""
    global _explanation_service
    if _explanation_service is None:
        _explanation_service = ExplanationService()
    return _explanation_service

