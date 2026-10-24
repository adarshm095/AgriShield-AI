import os
import sys
import uvicorn

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(SCRIPT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

if __name__ == "__main__":
    print("=" * 60)
    print("  AgriShield-AI: Intelligent Plant Pathology & Advisory System")
    print("=" * 60)
    print("  Starting unified backend & frontend server...")
    print("  Application URL: http://localhost:8000")
    print("  API Docs (Swagger): http://localhost:8000/docs")
    print("=" * 60)
    
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
