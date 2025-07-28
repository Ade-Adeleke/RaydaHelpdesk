#!/usr/bin/env python3
"""
Demo script to showcase the Help Desk System capabilities
"""

import os
import json
from help_desk_system import HelpDeskSystem
from models import HelpDeskRequest

def demo_vector_search():
    """Demonstrate how vector search works"""
    print("🔍 VECTOR SEARCH DEMO")
    print("=" * 50)
    
    # Initialize just the knowledge retriever
    from llm_knowledge_retriever import LLMKnowledgeRetriever
    retriever = LLMKnowledgeRetriever()
    
    print(f"📚 Loaded {len(retriever.knowledge_chunks)} knowledge chunks")
    print(f"🧠 Using LLM-based semantic search")
    
    # Test queries
    test_queries = [
        "password reset help",
        "software installation error",
        "network connection problems",
        "email configuration issues"
    ]
    
    for query in test_queries:
        print(f"\n🔎 Query: '{query}'")
        results = retriever.retrieve(query)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"  {i}. Score: {result.relevance_score:.3f}")
                print(f"     Source: {result.source}")
                print(f"     Content: {result.content[:100]}...")
        else:
            print("  No relevant results found")

def demo_classification():
    """Demonstrate request classification"""
    print("\n🏷️  CLASSIFICATION DEMO")
    print("=" * 50)
    
    from llm_classifier import LLMRequestClassifier
    classifier = LLMRequestClassifier()
    
    test_requests = [
        "I forgot my password and can't log in",
        "My laptop screen is completely black",
        "I can't connect to WiFi",
        "How do I install new software?",
        "I think my computer has a virus"
    ]
    
    for request in test_requests:
        result = classifier.classify(request)
        print(f"\n📝 Request: '{request}'")
        print(f"   Category: {result.category}")
        print(f"   Confidence: {result.confidence:.3f}")
        print(f"   Reasoning: {result.reasoning}")

def demo_full_system():
    """Demonstrate the complete system"""
    print("\n🚀 FULL SYSTEM DEMO")
    print("=" * 50)
    
    # Check if we have API keys
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_groq = bool(os.getenv("GROQ_API_KEY"))
    
    if not (has_openai or has_groq):
        print("⚠️  No LLM API keys found. Set OPENAI_API_KEY or GROQ_API_KEY to test response generation.")
        print("   Continuing with classification and retrieval only...")
        return
    
    try:
        help_desk = HelpDeskSystem()
        
        test_request = HelpDeskRequest(
            request="I forgot my password and have an important meeting in 10 minutes. Please help urgently!"
        )
        
        print(f"📨 Processing request: '{test_request.request}'")
        response = help_desk.process_request(test_request)
        
        print(f"\n📊 Results:")
        print(f"   Category: {response.classification.category}")
        print(f"   Confidence: {response.classification.confidence:.3f}")
        print(f"   Escalate: {response.escalation.should_escalate}")
        print(f"   Urgency: {response.escalation.urgency_level}")
        print(f"   Processing Time: {response.processing_time:.3f}s")
        
        print(f"\n📚 Retrieved Knowledge ({len(response.retrieved_knowledge)} items):")
        for i, knowledge in enumerate(response.retrieved_knowledge, 1):
            print(f"   {i}. {knowledge.source} (score: {knowledge.relevance_score:.3f})")
        
        print(f"\n🤖 Generated Response:")
        print(f"   {response.response}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def show_system_info():
    """Show system configuration and capabilities"""
    print("ℹ️  SYSTEM INFORMATION")
    print("=" * 50)
    
    from config import Config
    
    print(f"LLM Provider: {Config.LLM_PROVIDER}")
    print(f"Search Method: LLM-based semantic search")
    print(f"Classification: LLM-based")
    print(f"Classification Threshold: {Config.CLASSIFICATION_CONFIDENCE_THRESHOLD}")
    
    # Check available categories
    try:
        with open(Config.CATEGORIES_FILE, 'r') as f:
            categories = json.load(f)['categories']
        print(f"\nAvailable Categories ({len(categories)}):")
        for cat, info in categories.items():
            print(f"  • {cat}: {info['description']}")
    except FileNotFoundError:
        print("Categories file not found")

def main():
    """Run all demos"""
    print("🎯 INTELLIGENT HELP DESK SYSTEM DEMO")
    print("=" * 60)
    
    show_system_info()
    demo_vector_search()
    demo_classification()
    demo_full_system()
    
    print("\n✅ Demo completed!")

if __name__ == "__main__":
    main()
