#!/usr/bin/env python3
"""
Server startup script for the AI-powered Help Desk System
"""

import sys
import os
import uvicorn

# Add src to Python path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))

def main():
    """Start the help desk server"""
    try:
        from helpdesk.api.api import app
        
        print("🚀 Starting AI-powered Help Desk System...")
        print("📚 Documentation available at: http://localhost:8000/docs")
        print("🔍 Health check at: http://localhost:8000/health")
        print("📝 Submit requests to: http://localhost:8000/submit")
        print()
        
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8000,
            reload=False,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
