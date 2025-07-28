import openai
from typing import List
import json

from ..models.models import RequestCategory, RetrievalResult, EscalationDecision
from ..utils.config import Config

class ResponseGenerator:
    """Generates contextual responses using LLM and retrieved knowledge"""
    
    def __init__(self):
        self.provider = Config.LLM_PROVIDER.lower()
        
        if self.provider == "openai":
            if not Config.OPENAI_API_KEY:
                raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
            try:
                self.openai_client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
            except Exception as e:
                print(f"Warning: OpenAI client initialization failed: {e}")
                # Try with minimal parameters
                import os
                os.environ['OPENAI_API_KEY'] = Config.OPENAI_API_KEY
                self.openai_client = openai.OpenAI()
            
        elif self.provider == "groq":
            if not Config.GROQ_API_KEY:
                raise ValueError("Groq API key not found. Please set GROQ_API_KEY environment variable.")
            try:
                from groq import Groq
                # Initialize Groq client with minimal parameters to avoid conflicts
                self.groq_client = Groq(api_key=Config.GROQ_API_KEY)
            except ImportError:
                raise ImportError("Groq package not installed. Run: pip install groq")
            except Exception as e:
                print(f"Warning: Groq client initialization failed: {e}")
                # Try with environment variable approach
                import os
                os.environ['GROQ_API_KEY'] = Config.GROQ_API_KEY
                try:
                    self.groq_client = Groq()
                except Exception as e2:
                    raise Exception(f"Failed to initialize Groq client: {e2}")
                
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}. Use 'openai' or 'groq'")
    
    def generate_response(self, 
                         request: str,
                         category: RequestCategory,
                         retrieved_knowledge: List[RetrievalResult],
                         escalation: EscalationDecision) -> str:
        """Generate a helpful response based on the request and context"""
        
        # Build context from retrieved knowledge
        context = self._build_context(retrieved_knowledge)
        
        # Create system prompt
        system_prompt = self._create_system_prompt()
        
        # Create user prompt
        user_prompt = self._create_user_prompt(request, category, context, escalation)
        
        try:
            if self.provider == "openai":
                response = self.openai_client.chat.completions.create(
                    model=Config.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                return self._clean_response_formatting(response.choices[0].message.content.strip())
                
            elif self.provider == "groq":
                response = self.groq_client.chat.completions.create(
                    model=Config.GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                return self._clean_response_formatting(response.choices[0].message.content.strip())
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return self._generate_fallback_response(request, category, escalation)
    
    def _generate_response(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate a simple response using the LLM"""
        try:
            if self.provider == "openai":
                response = self.openai_client.chat.completions.create(
                    model=Config.OPENAI_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=max_tokens
                )
                return self._clean_response_formatting(response.choices[0].message.content.strip())
                
            elif self.provider == "groq":
                response = self.groq_client.chat.completions.create(
                    model=Config.GROQ_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=max_tokens
                )
                return self._clean_response_formatting(response.choices[0].message.content.strip())
            
        except Exception as e:
            raise Exception(f"LLM generation failed: {str(e)}")
    
    def _clean_response_formatting(self, response: str) -> str:
        """Clean up response formatting for better readability"""
        if not response:
            return ""
            
        # Handle literal \n strings that might appear in the response
        response = response.replace('\\n', '\n')
        
        # Remove excessive markdown formatting
        response = response.replace('**', '')
        response = response.replace('##', '')
        response = response.replace('###', '')
        response = response.replace('*', '')  # Remove single asterisks too
        
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
        
        # Handle any remaining literal newline strings
        cleaned_response = cleaned_response.replace('\\n', '\n')
        
        return cleaned_response.strip()
    
    def _generate_fallback_response(self, request: str, category: RequestCategory, escalation: EscalationDecision) -> str:
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
    
    def _build_context(self, retrieved_knowledge: List[RetrievalResult]) -> str:
        """Build context string from retrieved knowledge"""
        if not retrieved_knowledge:
            return "No specific knowledge found for this request."
        
        context_parts = []
        for i, result in enumerate(retrieved_knowledge, 1):
            context_parts.append(f"Knowledge {i} (from {result.source}):\n{result.content}")
        
        return "\n\n".join(context_parts)
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the LLM"""
        return """You are an AI assistant for an IT help desk system. Your role is to provide helpful, accurate, and professional responses to IT support requests.

IMPORTANT FORMATTING RULES:
- Write in plain text format, NOT markdown
- Use actual line breaks for paragraphs, NOT literal \n strings
- Use numbered lists (1., 2., 3.) for steps
- Use bullet points (-) for simple lists
- NEVER use **bold**, ##headers##, or any markdown formatting
- NEVER include literal \n strings in your response
- Keep responses clean and readable in plain text
- Use proper paragraph spacing with blank lines between sections

Guidelines:
1. Be concise but thorough in your responses
2. Use the provided knowledge base information when relevant
3. Provide step-by-step instructions when appropriate
4. Be empathetic and professional in tone
5. If escalation is required, clearly explain why and what the user should expect
6. Always prioritize security and company policies
7. If you're unsure about something, recommend contacting human IT support

Response Structure:
1. Brief acknowledgment of the issue
2. Clear, actionable steps or information
3. Next steps or escalation information if needed
4. Professional closing"""
    
    def _create_user_prompt(self, 
                           request: str, 
                           category: RequestCategory, 
                           context: str, 
                           escalation: EscalationDecision) -> str:
        """Create the user prompt with all context"""
        
        prompt = f"""Please help with this IT support request:

USER REQUEST: {request}

CLASSIFIED CATEGORY: {category.value}

RELEVANT KNOWLEDGE:
{context}

ESCALATION STATUS: {"ESCALATION REQUIRED" if escalation.should_escalate else "NO ESCALATION NEEDED"}
ESCALATION REASON: {escalation.reason}
URGENCY LEVEL: {escalation.urgency_level}

Please provide a helpful response that:
1. Addresses the user's specific request
2. Uses the relevant knowledge provided
3. Includes appropriate escalation information if needed
4. Maintains a professional and helpful tone"""

        return prompt
