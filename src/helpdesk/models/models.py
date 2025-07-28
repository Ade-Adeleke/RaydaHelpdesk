from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum

class RequestCategory(str, Enum):
    """Enumeration of help desk request categories"""
    PASSWORD_RESET = "password_reset"
    SOFTWARE_INSTALLATION = "software_installation"
    HARDWARE_FAILURE = "hardware_failure"
    NETWORK_CONNECTIVITY = "network_connectivity"
    EMAIL_CONFIGURATION = "email_configuration"
    SECURITY_INCIDENT = "security_incident"
    POLICY_QUESTION = "policy_question"

class HelpDeskRequest(BaseModel):
    """Model for incoming help desk requests"""
    id: Optional[str] = None
    request: str
    user_id: Optional[str] = None
    priority: Optional[str] = "normal"
    timestamp: Optional[str] = None

class ClassificationResult(BaseModel):
    """Model for classification results"""
    category: RequestCategory
    confidence: float
    reasoning: str

class RetrievalResult(BaseModel):
    """Model for knowledge retrieval results"""
    content: str
    source: str
    relevance_score: float

class EscalationDecision(BaseModel):
    """Model for escalation decisions"""
    should_escalate: bool
    reason: str
    urgency_level: str

class HelpDeskResponse(BaseModel):
    """Model for complete help desk response"""
    request_id: str
    classification: ClassificationResult
    retrieved_knowledge: List[RetrievalResult]
    response: str
    escalation: EscalationDecision
    processing_time: float

class TestRequest(BaseModel):
    """Model for test requests with expected results"""
    id: str
    request: str
    expected_classification: str
    expected_elements: List[str]
    escalate: bool
