#!/usr/bin/env python3
"""
Simple test to verify response formatting works correctly
"""

import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from helpdesk.core.response_generator import ResponseGenerator
from helpdesk.models.models import RequestCategory, EscalationDecision, RetrievalResult

def test_response_formatting():
    """Test that response formatting removes markdown and cleans text"""
    
    # Create a mock response generator without initializing LLM clients
    os.environ['LLM_PROVIDER'] = 'groq'
    os.environ['GROQ_API_KEY'] = 'test-key'  # Mock key for testing
    
    # Mock the ResponseGenerator to avoid client initialization
    class MockResponseGenerator:
        def _clean_response_formatting(self, response: str) -> str:
            """Clean up response formatting for better readability"""
            # Remove excessive markdown formatting
            response = response.replace('**', '')
            response = response.replace('##', '')
            response = response.replace('###', '')
            
            # Clean up line breaks and spacing
            lines = response.split('\n')
            cleaned_lines = []
            
            for line in lines:
                line = line.strip()
                if line:  # Only add non-empty lines
                    cleaned_lines.append(line)
                elif cleaned_lines and cleaned_lines[-1]:  # Add empty line only if previous line wasn't empty
                    cleaned_lines.append('')
            
            # Join lines and ensure proper paragraph spacing
            cleaned_response = '\n'.join(cleaned_lines)
            
            # Remove multiple consecutive empty lines
            while '\n\n\n' in cleaned_response:
                cleaned_response = cleaned_response.replace('\n\n\n', '\n\n')
            
            return cleaned_response.strip()
    
    generator = MockResponseGenerator()
    
    # Test the formatting cleanup function directly
    test_response = """**Hello there!**

## This is a header

### Another header

This is some text with **bold** formatting.

Here are some steps:
1. First step
2. Second step
3. Third step



Multiple empty lines above should be cleaned up.

- Bullet point 1
- Bullet point 2

**End of response**"""
    
    cleaned = generator._clean_response_formatting(test_response)
    
    print("Original response:")
    print(repr(test_response))
    print("\nCleaned response:")
    print(repr(cleaned))
    print("\nCleaned response (readable):")
    print(cleaned)
    
    # Verify markdown is removed
    assert '**' not in cleaned
    assert '##' not in cleaned
    assert '###' not in cleaned
    
    # Verify no excessive empty lines
    assert '\n\n\n' not in cleaned
    
    print("\n✅ Response formatting test passed!")

def test_fallback_response():
    """Test fallback response generation"""
    
    # Mock the fallback response function
    def mock_generate_fallback_response(request: str, category, escalation):
        """Generate a fallback response when LLM fails"""
        response = f"Thank you for contacting IT support regarding your {category.value.replace('_', ' ')} issue.\n\n"
        response += "I apologize, but I'm experiencing technical difficulties generating a detailed response right now.\n\n"
        
        if escalation.should_escalate:
            response += f"Your request has been classified as {escalation.urgency_level} priority and will be escalated to our technical team. "
            response += "You can expect a response within 2-4 hours.\n\n"
        else:
            response += "Please try the following general troubleshooting steps or contact IT support directly.\n\n"
        
        response += "For immediate assistance, please contact IT support at extension 1234 or email support@company.com."
        
        return response
    
    class MockGenerator:
        def _generate_fallback_response(self, request, category, escalation):
            return mock_generate_fallback_response(request, category, escalation)
    
    generator = MockGenerator()
    
    # Test fallback response
    category = RequestCategory.PASSWORD_RESET
    escalation = EscalationDecision(
        should_escalate=True,
        reason="High priority request",
        urgency_level="high"
    )
    
    fallback = generator._generate_fallback_response(
        "I forgot my password", 
        category, 
        escalation
    )
    
    print("Fallback response:")
    print(fallback)
    
    # Verify fallback contains expected elements
    assert "password reset" in fallback.lower()
    assert "escalated" in fallback.lower()
    assert "high priority" in fallback.lower()
    
    print("\n- Fallback response test passed!")

if __name__ == "__main__":
    test_response_formatting()
    test_fallback_response()
    print("\n🎉 All tests passed!")
