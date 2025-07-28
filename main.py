#!/usr/bin/env python3
"""
Main entry point for the AI-powered Help Desk System
"""

import sys
import os

# Add src to Python path
project_root = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(project_root, 'src'))

def main():
    """Main entry point"""
    try:
        from helpdesk.api.api import app
        import uvicorn
        
        print("🚀 Starting AI-powered Help Desk System...")
        print("📚 Documentation: http://localhost:8000/docs")
        print("🔍 Health check: http://localhost:8000/health")
        print("📝 Submit endpoint: http://localhost:8000/submit")
        print()
        
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8000,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
