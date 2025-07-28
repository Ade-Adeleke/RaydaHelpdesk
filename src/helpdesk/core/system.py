import time
import uuid
from typing import Dict, Any

from ..models.models import HelpDeskRequest, HelpDeskResponse, ClassificationResult, RetrievalResult
from .classifier import LLMRequestClassifier
from .knowledge_retriever import LLMKnowledgeRetriever
from .escalation_logic import EscalationEngine
from .response_generator import ResponseGenerator

class HelpDeskSystem:
    """Main orchestrator for the intelligent help desk system"""
    
    def __init__(self):
        """Initialize all components of the help desk system"""
        print("Initializing Help Desk System...")
        
        try:
            self.classifier = LLMRequestClassifier()
            print("✓ Request classifier loaded")
            
            self.knowledge_retriever = LLMKnowledgeRetriever()
            print("✓ Knowledge retriever loaded")
            
            self.escalation_engine = EscalationEngine()
            print("✓ Escalation engine loaded")
            
            self.response_generator = ResponseGenerator()
            print("✓ Response generator loaded")
            
            print("Help Desk System initialized successfully!")
            
        except Exception as e:
            print(f"Error initializing Help Desk System: {e}")
            raise
    
    def process_request(self, request: HelpDeskRequest) -> HelpDeskResponse:
        """Process a complete help desk request through all components"""
        start_time = time.time()
        
        # Generate request ID if not provided
        if not request.id:
            request.id = str(uuid.uuid4())
        
        try:
            # Step 1: Classify the request
            classification = self.classifier.classify(request.request)
            
            # Step 2: Retrieve relevant knowledge
            retrieved_knowledge = self.knowledge_retriever.retrieve(
                request.request, 
                classification.category.value
            )
            
            # Step 3: Determine escalation
            escalation = self.escalation_engine.should_escalate(
                request.request,
                classification.category,
                classification.confidence
            )
            
            # Step 4: Generate response
            response_text = self.response_generator.generate_response(
                request.request,
                classification.category,
                retrieved_knowledge,
                escalation
            )
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            return HelpDeskResponse(
                request_id=request.id,
                classification=classification,
                retrieved_knowledge=retrieved_knowledge,
                response=response_text,
                escalation=escalation,
                processing_time=processing_time
            )
            
        except Exception as e:
            # Fallback response in case of errors
            processing_time = time.time() - start_time
            
            from models import ClassificationResult, RequestCategory, EscalationDecision
            
            return HelpDeskResponse(
                request_id=request.id,
                classification=ClassificationResult(
                    category=RequestCategory.POLICY_QUESTION,
                    confidence=0.0,
                    reasoning=f"Error in classification: {str(e)}"
                ),
                retrieved_knowledge=[],
                response=f"I apologize, but I encountered an error processing your request. Please contact IT support directly for assistance. Error: {str(e)}",
                escalation=EscalationDecision(
                    should_escalate=True,
                    reason=f"System error: {str(e)}",
                    urgency_level="high"
                ),
                processing_time=processing_time
            )
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get status information about the help desk system"""
        return {
            "status": "operational",
            "components": {
                "classifier": "loaded",
                "knowledge_retriever": f"{len(self.knowledge_retriever.knowledge_chunks)} chunks loaded",
                "escalation_engine": "loaded",
                "response_generator": "loaded"
            },
            "configuration": {
                "embedding_model": self.knowledge_retriever.model.get_sentence_embedding_dimension(),
                "similarity_threshold": self.knowledge_retriever.model.__class__.__name__
            }
        }
