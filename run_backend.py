"""
Run Script for Smart Goggle FastAPI Backend
Starts Uvicorn server on configured host and port (default 0.0.0.0:8000).
"""

import uvicorn
from backend.config import BACKEND_HOST, BACKEND_PORT

if __name__ == "__main__":
    print(f"Starting Smart Goggle FastAPI Backend on http://{BACKEND_HOST}:{BACKEND_PORT}")
    print("API Documentation available at: http://localhost:8000/docs")
    uvicorn.run("backend.main:app", host=BACKEND_HOST, port=BACKEND_PORT, reload=True)
