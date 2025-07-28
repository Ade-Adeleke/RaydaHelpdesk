# AI-Powered Help Desk System

An intelligent help desk system using Large Language Models (LLMs) for automated request classification, knowledge retrieval, and response generation with clean, professional formatting.

## 🚀 Quick Start

```bash
# Build and run (with vector search)
docker build -t ai-helpdesk-system .
docker run -d --name helpdesk -p 8000:8000 --env-file .env ai-helpdesk-system

# Check status
curl http://localhost:8000/health
```

## 📋 Setup

### 1. Environment Configuration
Create a `.env` file:
```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
EMBEDDING_MODEL=groq-embed-english-v1  # Embedding model used for vector search
```

### 2. API Key
- **Groq**: Get your API key from [Groq Console](https://console.groq.com/)

## 🏗️ Architecture

```
src/helpdesk/
├── api/                    # REST API layer
│   └── api.py             # FastAPI application
├── core/                   # Business logic
│   ├── classifier.py      # LLM-based request classification
│   ├── knowledge_retriever.py  # Knowledge base search
│   ├── response_generator.py   # LLM response generation
│   ├── escalation_logic.py     # Escalation rules engine
│   └── system.py          # Main system orchestrator
├── models/                 # Data models
│   └── models.py          # Pydantic schemas
└── utils/                  # Utilities
    └── config.py          # Configuration management
```

## 🔧 API Endpoints

### Submit Request
```bash
POST /submit
```

**Request:**
```json
{
  "request_text": "I forgot my password and can't log in",
  "user_id": "user123",
  "priority": "medium"
}
```

**Response:**
```json
{
  "request_id": "uuid",
  "classification": {
    "category": "password_reset",
    "confidence": 0.95,
    "reasoning": "Request mentions password and login issues"
  },
  "retrieved_knowledge": [...],
  "response": "I understand you're having trouble with your password. Here's how to reset it:\n\n1. Go to the login page\n2. Click 'Forgot Password'\n3. Enter your email address\n4. Check your email for reset instructions\n\nIf you don't receive the email within 5 minutes, please check your spam folder.",
  "escalation": {
    "should_escalate": false,
    "reason": "Standard request with high confidence",
    "urgency_level": "medium"
  },
  "processing_time": 2.34
}
```

### Health Check
```bash
GET /health
```

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Testing

### Run Tests
```bash
python -m pytest tests/
```

### Test Specific Features
```bash
# Response formatting
python tests/test_formatting.py

# Newline handling
python tests/test_newline_fix.py

# System integration
python tests/test_system.py
```

### Test API Manually
```bash
# Health check
curl http://localhost:8000/health

# Submit request
curl -X POST "http://localhost:8000/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "request_text": "My computer won'\''t start",
    "user_id": "test123",
    "priority": "high"
  }'
```

## 🎯 Key Features

### ✅ Clean Response Formatting
- Removes markdown artifacts (`**bold**`, `##headers##`)
- Converts literal `\n` strings to actual newlines
- Professional paragraph spacing
- Consistent plain text output

### ✅ Groq LLM Integration
- Groq (Mixtral, Llama models)
- Fast inference and reliable performance
- Configurable model selection

### ✅ Intelligent Classification
- 5 predefined categories: password_reset, software_installation, hardware_failure, network_connectivity, email_configuration
- Confidence scoring and reasoning
- Fallback keyword-based classification

### ✅ Smart Escalation
- Automatic detection of requests requiring human intervention
- Priority-based escalation (low, medium, high, critical)
- Confidence threshold analysis

### ✅ Knowledge Retrieval (Vector Search)
- Groq embeddings + FAISS vector index for fast semantic search
- Fallback to LLM or keyword search if embeddings unavailable
- Semantic search through knowledge base
- Multiple document types (Markdown, JSON)
- Relevance scoring and context building

## 🐳 Docker Deployment

### Build Image
```bash
docker build -t ai-helpdesk-system .
```

### Run Container
```bash
docker run -d \
  --name helpdesk \
  -p 8000:8000 \
  --env-file .env \
  ai-helpdesk-system
```

##  Development



### Adding New Features
1. Add business logic to `src/helpdesk/core/`
2. Update models in `src/helpdesk/models/`
3. Add API endpoints in `src/helpdesk/api/`
4. Write tests in `tests/`
5. Update documentation

### Knowledge Base
Add new knowledge files to `data/` directory:
- `knowledge_base.md` - General IT knowledge
- `company_it_policies.md` - Company policies
- `installation_guides.json` - Software guides
- `troubleshooting_database.json` - Common issues

