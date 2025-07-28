"""
LLM-based Request Classifier
Uses LLM for classification instead of embeddings
"""

import json
import os
from typing import Dict, Any
from ..models.models import RequestCategory, ClassificationResult
from ..utils.config import Config
from .response_generator import ResponseGenerator


class LLMRequestClassifier:
    """Request classifier using LLM instead of embeddings"""
    
    def __init__(self, categories_file: str = None):
        if categories_file is None:
            # Default to data directory relative to project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            categories_file = os.path.join(project_root, "data", "categories.json")
        self.categories = {}
        self.response_generator = ResponseGenerator()
        self._load_categories(categories_file)
    
    def _load_categories(self, categories_file: str):
        """Load request categories from JSON file"""
        try:
            with open(categories_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Map JSON keys to enum values and create descriptions
            for category_key, category_data in data['categories'].items():
                # Find matching enum value
                enum_value = None
                for enum_item in RequestCategory:
                    if enum_item.value == category_key:
                        enum_value = enum_item
                        break
                
                if enum_value:
                    readable_name = category_key.replace('_', ' ').title()
                    self.categories[readable_name] = {
                        'enum': enum_value,
                        'description': category_data['description'],
                        'typical_resolution_time': category_data['typical_resolution_time'],
                        'escalation_triggers': category_data['escalation_triggers']
                    }
                
        except Exception as e:
            print(f"Error loading categories: {e}")
            # Fallback categories
            self.categories = {
                "Password Reset": {
                    'enum': RequestCategory.PASSWORD_RESET,
                    'description': "User needs to reset or recover their password",
                    'typical_resolution_time': "5 minutes",
                    'escalation_triggers': ["Multiple failed attempts"]
                },
                "Software Installation": {
                    'enum': RequestCategory.SOFTWARE_INSTALLATION,
                    'description': "User needs help installing or updating software",
                    'typical_resolution_time': "15 minutes",
                    'escalation_triggers': ["Admin rights required"]
                }
            }
    
    def classify(self, request_text: str) -> ClassificationResult:
        """Classify a request using LLM"""
        
        # Create category descriptions for the prompt
        category_descriptions = []
        for name, category_info in self.categories.items():
            desc = f"- {name}: {category_info['description']}"
            category_descriptions.append(desc)
        
        categories_text = "\n".join(category_descriptions)
        
        # Create classification prompt
        prompt = f"""Classify this help desk request into one of the following categories:

{categories_text}

Request: "{request_text}"

Respond with ONLY the exact category name from the list above. If none fit well, choose the closest match."""

        try:
            # Get classification from LLM
            response = self.response_generator._generate_response(prompt, max_tokens=20)
            predicted_category = response.strip()
            
            # Validate the prediction
            if predicted_category not in self.categories:
                # Try to find a close match
                for category_name in self.categories.keys():
                    if category_name.lower() in predicted_category.lower() or predicted_category.lower() in category_name.lower():
                        predicted_category = category_name
                        break
                else:
                    # Default to first category if no match
                    predicted_category = list(self.categories.keys())[0]
            
            # Generate confidence and reasoning
            confidence_prompt = f"""Rate your confidence (0.0 to 1.0) in classifying this request as "{predicted_category}":

Request: "{request_text}"
Classification: {predicted_category}

Respond with just a number between 0.0 and 1.0:"""
            
            confidence_response = self.response_generator._generate_response(confidence_prompt, max_tokens=10)
            
            try:
                confidence = float(confidence_response.strip())
                confidence = max(0.0, min(1.0, confidence))  # Clamp to [0,1]
            except:
                confidence = 0.8  # Default confidence
            
            # Generate reasoning
            reasoning_prompt = f"""Briefly explain (1-2 sentences) why this request was classified as "{predicted_category}":

Request: "{request_text}"
Classification: {predicted_category}

Explanation:"""
            
            reasoning = self.response_generator._generate_response(reasoning_prompt, max_tokens=100)
            
            # Get the enum value for the predicted category
            category_enum = self.categories[predicted_category]['enum']
            
            return ClassificationResult(
                category=category_enum,
                confidence=confidence,
                reasoning=reasoning.strip()
            )
            
        except Exception as e:
            print(f"Error in LLM classification: {e}")
            # Fallback to keyword-based classification
            return self._fallback_keyword_classification(request_text)
    
    def _fallback_keyword_classification(self, request_text: str) -> ClassificationResult:
        """Fallback keyword-based classification if LLM fails"""
        request_lower = request_text.lower()
        
        # Simple keyword matching
        keyword_mapping = {
            "Password Reset": ["password", "login", "forgot", "reset", "access", "account"],
            "Software Installation": ["install", "software", "program", "application", "app", "update"],
            "Network Issues": ["internet", "wifi", "network", "connection", "slow"],
            "Hardware Support": ["computer", "laptop", "mouse", "keyboard", "screen", "hardware"],
            "Email Configuration": ["email", "outlook", "mail", "smtp", "imap"]
        }
        
        best_category = "General Inquiry"
        best_score = 0
        
        for category, keywords in keyword_mapping.items():
            if category in self.categories:
                score = sum(1 for keyword in keywords if keyword in request_lower)
                if score > best_score:
                    best_score = score
                    best_category = category
        
        confidence = min(0.9, best_score * 0.2) if best_score > 0 else 0.3
        
        # Get enum value for best category, fallback to first available
        if best_category in self.categories:
            category_enum = self.categories[best_category]['enum']
        else:
            # Fallback to first available category
            category_enum = list(self.categories.values())[0]['enum']
        
        return ClassificationResult(
            category=category_enum,
            confidence=confidence,
            reasoning=f"Classified based on keyword matching (score: {best_score})"
        )
    
    def get_categories(self) -> Dict[str, RequestCategory]:
        """Get all available categories"""
        return self.categories.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get classifier statistics"""
        return {
            "total_categories": len(self.categories),
            "category_names": list(self.categories.keys()),
            "classifier_type": "LLM-based"
        }
