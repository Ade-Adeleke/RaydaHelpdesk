from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import Dict, Any

from ..core.system import HelpDeskSystem
from ..models.models import HelpDeskRequest, HelpDeskResponse

# Initialize FastAPI app
app = FastAPI(
    title="Intelligent Help Desk System",
    description="AI-powered help desk system with request classification, knowledge retrieval, and escalation logic",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize help desk system
try:
    help_desk = HelpDeskSystem()
except Exception as e:
    print(f"Failed to initialize help desk system: {e}")
    help_desk = None

class SimpleRequest(BaseModel):
    """Simplified request model for API"""
    request: str
    user_id: str = "anonymous"

@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "message": "Intelligent Help Desk System API",
        "version": "1.0.0",
        "status": "operational" if help_desk else "error",
        "endpoints": {
            "submit_request": "/submit",
            "system_status": "/status",
            "health_check": "/health"
        }
    }

@app.post("/submit", response_model=HelpDeskResponse)
async def submit_request(request: SimpleRequest) -> HelpDeskResponse:
    """Submit a help desk request for processing"""
    if not help_desk:
        raise HTTPException(status_code=500, detail="Help desk system not initialized")
    
    try:
        # Convert to internal request model
        help_desk_request = HelpDeskRequest(
            request=request.request,
            user_id=request.user_id
        )
        
        # Process the request
        response = help_desk.process_request(help_desk_request)
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/status")
async def get_status() -> Dict[str, Any]:
    """Get system status and configuration"""
    if not help_desk:
        return {"status": "error", "message": "Help desk system not initialized"}
    
    try:
        return help_desk.get_system_status()
    except Exception as e:
        return {"status": "error", "message": f"Error getting status: {str(e)}"}

@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy" if help_desk else "unhealthy",
        "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp in production
    }

@app.post("/classify")
async def classify_request(request: SimpleRequest):
    """Classify a request without full processing (for testing)"""
    if not help_desk:
        raise HTTPException(status_code=500, detail="Help desk system not initialized")
    
    try:
        classification = help_desk.classifier.classify(request.request)
        return {
            "request": request.request,
            "classification": classification.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error classifying request: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
