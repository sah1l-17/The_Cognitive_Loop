"""
Startup script for Autonomous Tutor API Server
"""

import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("🚀 Starting Autonomous Tutor API Server")
    print("=" * 60)
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🏥 Health Check: http://localhost:8000/api/health")
    print("=" * 60)
    
    uvicorn.run(
        "main:app",  # Import string instead of app object
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )
