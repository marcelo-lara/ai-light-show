"""
AI Light Show - Main FastAPI Application

A modular, Pythonic implementation of the AI Light Show system.
This file serves as the entry point and application configuration.
"""

import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Import routers
from backend.routers import songs, websocket

# Import DMX player service
from backend.services.dmx.dmx_player import dmx_player


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - handles startup and shutdown."""
    try:
        # Start the DMX player engine
        await dmx_player.start_playback_engine()
        print("🎬 DMX Player engine started")
        yield
    finally:
        # Stop the DMX player engine
        await dmx_player.stop_playback_engine()
        print("🎬 DMX Player engine stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="AI Light Show",
        description="An AI-driven lighting control system with real-time DMX control",
        version="2.0.0",
        lifespan=lifespan
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers first (before static files to ensure API routes take precedence)
    app.include_router(songs.router)
    app.include_router(websocket.router)

    # Static file serving - handle both Docker and local environments
    # In Docker: static files are in /app/static/ with songs mounted as volume
    # In local dev: frontend files are in frontend/ and songs in songs/
    
    # Mount songs directory
    songs_dir = "static/songs" if os.path.exists("static/songs") else "songs"
    if os.path.exists(songs_dir):
        app.mount("/songs", StaticFiles(directory=songs_dir), name="songs")
    
    # Mount main static files (frontend) - this should be last to catch all remaining routes
    static_dir = "static" if os.path.exists("static") else "frontend"
    if os.path.exists(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    return app


# Create the application instance
app = create_app()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ai-light-show"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
