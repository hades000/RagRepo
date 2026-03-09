"""
Main FastAPI application for RAG service with asyncpg
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from config import Config
from core.db import init_db, close_db
from utils.response import success_response, error_response
import traceback


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    try:
        print("Initializing services...")

        # Initialize database connection managers
        init_db()

        # Initialize service components
        from api.sync import init_sync_services
        from api.search import init_search_services
        from api.admin import init_admin_services

        init_sync_services()
        init_search_services()
        init_admin_services()

        print("All services initialized successfully\n")

    except Exception as e:
        print(f"Service initialization error: {e}")
        traceback.print_exc()
        raise

    yield

    # Shutdown
    try:
        print("\nShutting down services...")
        close_db()
        print("Cleanup complete")
    except Exception as e:
        print(f"Cleanup error: {e}")


# Import routers
from api.sync import router as sync_router
from api.search import router as search_router
from api.admin import router as admin_router
from api.documents import router as documents_router
from api.settings import router as settings_router


app = FastAPI(
    title="CoreIQ RAG Service",
    version="4.0.0-asyncpg",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(sync_router, prefix="/api/rag", tags=["sync"])
app.include_router(search_router, prefix="/api/rag", tags=["search"])
app.include_router(admin_router, prefix="/api/rag/admin", tags=["admin"])
app.include_router(documents_router, prefix="/api/rag", tags=["documents"])
app.include_router(settings_router, prefix="/api/rag/settings", tags=["settings"])


# Health check endpoint
@app.get("/health")
def health_check():
    return success_response(
        data={'status': 'healthy', 'version': '4.0.0-asyncpg'},
        message='RAG service is running'
    )


# Root endpoint
@app.get("/")
def index():
    return success_response(
        data={
            'service': 'CoreIQ RAG Service',
            'version': '4.0.0-asyncpg',
            'database': 'asyncpg',
            'endpoints': {
                'health': '/health',
                'search': '/api/rag/search',
                'search_similar': '/api/rag/search/similar',
                'sync_trigger': '/api/rag/sync',
                'sync_status': '/api/rag/sync/status',
                'sync_rebuild': '/api/rag/sync/rebuild',
                'admin_stats': '/api/rag/admin/stats',
                'admin_health': '/api/rag/admin/health',
                'settings_models': '/api/rag/settings/models/available'
            }
        },
        message='Welcome to CoreIQ RAG Service (AsyncPG)'
    )


# Global exception handlers
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """Wrap HTTPException in standard error envelope."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.detail}
    )


@app.exception_handler(404)
async def not_found(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"success": False, "error": "Endpoint not found"}
    )


@app.exception_handler(Exception)
async def handle_exception(request: Request, exc: Exception):
    print(f"Unhandled exception: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error"}
    )


if __name__ == '__main__':
    import uvicorn

    print("\n" + "=" * 60)
    print("CoreIQ RAG Service Starting (AsyncPG)...")
    print("=" * 60)

    print(f"Running on: http://localhost:5000")
    print(f"Search: POST /api/rag/search")
    print(f"Sync: POST /api/rag/sync")
    print(f"Admin: /api/rag/admin/*")
    print(f"Database: AsyncPG per-request connections")
    print(f"Health: GET /health")
    print("=" * 60 + "\n")

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5000,
        reload=Config.DEBUG,
    )
