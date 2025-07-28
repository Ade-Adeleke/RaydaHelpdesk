import json
import re
from typing import List, Dict, Any

from ..models.models import RequestCategory, ClassificationResult, EscalationDecision
from ..utils.config import Config

class EscalationEngine:
    """Determines when help desk requests require human intervention"""
    
    def __init__(self):
        self.categories = self._load_categories()
        self.escalation_rules = self._load_escalation_rules()
    
    def _load_categories(self) -> Dict[str, Any]:
        """Load category definitions"""
        try:
            with open(Config.CATEGORIES_FILE, 'r') as f:
                data = json.load(f)
                return data['categories']
        except FileNotFoundError:
            return {}
    
    def _load_escalation_rules(self) -> Dict[str, List[str]]:
        """Extract escalation triggers from categories"""
        rules = {}
        for category, info in self.categories.items():
            rules[category] = info.get('escalation_triggers', [])
        return rules
    
    def should_escalate(self, request: str, category: RequestCategory, 
                       confidence: float) -> EscalationDecision:
        """Determine if a request should be escalated"""
        
        reasons = []
        urgency_level = "normal"
        
        # Check category-specific escalation triggers
        category_triggers = self.escalation_rules.get(category.value, [])
        for trigger in category_triggers:
            if self._matches_trigger(request, trigger):
                reasons.append(f"Category trigger: {trigger}")
                urgency_level = "high"
        
        # Check for urgent keywords
        urgent_keywords_found = self._check_urgent_keywords(request)
        if urgent_keywords_found:
            reasons.extend([f"Urgent keyword: {kw}" for kw in urgent_keywords_found])
            urgency_level = "critical"
        
        # Check classification confidence
        if confidence < Config.CLASSIFICATION_CONFIDENCE_THRESHOLD:
            reasons.append(f"Low classification confidence: {confidence:.2f}")
        
        # Check for specific high-priority categories
        high_priority_categories = [
            RequestCategory.SECURITY_INCIDENT,
            RequestCategory.HARDWARE_FAILURE
        ]
        
        if category in high_priority_categories:
            reasons.append(f"High-priority category: {category.value}")
            urgency_level = "critical"
        
        # Check for multiple issues in one request
        if self._contains_multiple_issues(request):
            reasons.append("Multiple issues detected in single request")
        
        # Check for business impact indicators
        business_impact_keywords = [
            "presentation", "meeting", "deadline", "client", "customer",
            "revenue", "business critical", "production", "server"
        ]
        
        for keyword in business_impact_keywords:
            if keyword.lower() in request.lower():
                reasons.append(f"Business impact indicator: {keyword}")
                if urgency_level == "normal":
                    urgency_level = "high"
                break
        
        should_escalate = len(reasons) > 0
        
        if should_escalate:
            reason = "; ".join(reasons)
        else:
            reason = "Request can be handled through automated response"
        
        return EscalationDecision(
            should_escalate=should_escalate,
            reason=reason,
            urgency_level=urgency_level
        )
    
    def _matches_trigger(self, request: str, trigger: str) -> bool:
        """Check if request matches an escalation trigger"""
        # Convert to lowercase for case-insensitive matching
        request_lower = request.lower()
        trigger_lower = trigger.lower()
        
        # Direct substring match
        if trigger_lower in request_lower:
            return True
        
        # Check for keyword variations
        trigger_words = trigger_lower.split()
        request_words = request_lower.split()
        
        # If all trigger words are found in request
        return all(any(tw in rw for rw in request_words) for tw in trigger_words)
    
    def _check_urgent_keywords(self, request: str) -> List[str]:
        """Check for urgent/emergency keywords in request"""
        found_keywords = []
        request_lower = request.lower()
        
        for keyword in Config.ESCALATION_KEYWORDS:
            if keyword.lower() in request_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def _contains_multiple_issues(self, request: str) -> bool:
        """Detect if request contains multiple separate issues"""
        # Look for connecting words that indicate multiple issues
        multiple_issue_indicators = [
            "and also", "in addition", "furthermore", "moreover",
            "another issue", "also", "plus", "as well as"
        ]
        
        request_lower = request.lower()
        return any(indicator in request_lower for indicator in multiple_issue_indicators)
