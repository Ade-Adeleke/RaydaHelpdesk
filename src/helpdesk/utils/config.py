import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration settings for the Help Desk System"""
    
    # LLM Provider Configuration
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # "openai" or "groq"
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = "gpt-3.5-turbo"
    
    # Groq Configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = "llama-3.1-8b-instant"  # or "llama2-70b-4096"
    
    # Vector Search Configuration
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    SIMILARITY_THRESHOLD = 0.7
    MAX_RETRIEVED_DOCS = 3
    
    # Classification Configuration
    CLASSIFICATION_CONFIDENCE_THRESHOLD = 0.8
    
    # Escalation Configuration
    ESCALATION_KEYWORDS = [
        "urgent", "emergency", "critical", "asap", "immediately",
        "broken", "crashed", "not working", "down", "failed"
    ]
    
    # File Paths
    CATEGORIES_FILE = "categories.json"
    KNOWLEDGE_BASE_FILE = "knowledge_base.md"
    POLICIES_FILE = "company_it_policies.md"
    INSTALLATION_GUIDES_FILE = "installation_guides.json"
    TROUBLESHOOTING_FILE = "troubleshooting_database.json"
    TEST_REQUESTS_FILE = "test_requests.json"
