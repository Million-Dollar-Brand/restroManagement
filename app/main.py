from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1.router import api_router

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description=settings.description,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads
from fastapi.staticfiles import StaticFiles
import os

uploads_dir = settings.upload_dir
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# Include routers
app.include_router(api_router)

@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "app": settings.app_name,
        "version": settings.version,
        "docs": "/docs",
        "api": "/api/v1"
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
