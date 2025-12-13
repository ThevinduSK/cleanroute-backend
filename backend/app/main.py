"""
CleanRoute Backend - Main FastAPI Application

This is the entry point for the backend service.
Run with: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import router
from . import mqtt_ingest
from . import mqtt_commands


# ─────────────────────────────────────────────────────────────────────────────
# Lifespan Management (startup/shutdown)
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan.
    Starts MQTT ingest and command publisher on startup, stops on shutdown.
    """
    # Startup
    print("Starting CleanRoute Backend...")
    mqtt_ingest.start_mqtt_ingest()
    mqtt_commands.init_command_client()
    
    yield  # Application runs here
    
    # Shutdown
    print("Shutting down CleanRoute Backend...")
    mqtt_ingest.stop_mqtt_ingest()
    mqtt_commands.stop_command_client()


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI Application
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="CleanRoute Backend",
    description="Smart waste bin monitoring and collection route optimization",
    version="0.1.0",
    lifespan=lifespan
)

# ─────────────────────────────────────────────────────────────────────────────
# CORS Middleware (for UI access)
# ─────────────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Include Routers
# ─────────────────────────────────────────────────────────────────────────────

app.include_router(router, prefix="/api")


# ─────────────────────────────────────────────────────────────────────────────
# Root Endpoint
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Root endpoint - API info."""
    return {
        "service": "CleanRoute Backend",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }
