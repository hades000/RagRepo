"""
Main Flask application for RAG service with asyncpg
"""
from flask import Flask
from flask_cors import CORS
from config import Config
from utils.response import success_response, error_response
from core.db import init_db, close_db
import traceback

# Import blueprints
from api.sync import sync_bp, init_sync_services
from api.search import search_bp, init_search_services
from api.admin import admin_bp, init_admin_services
from api.documents import documents_bp
from api.settings import settings_bp


def create_app():
    """Create and configure Flask application"""
    
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Configure CORS
    CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)
    
    # Register blueprints
    app.register_blueprint(sync_bp, url_prefix='/api/rag')
    app.register_blueprint(search_bp, url_prefix='/api/rag')
    app.register_blueprint(admin_bp, url_prefix='/api/rag/admin')
    app.register_blueprint(documents_bp, url_prefix='/api/rag')
    app.register_blueprint(settings_bp, url_prefix='/api/rag/settings')
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return success_response(
            data={'status': 'healthy', 'version': '4.0.0-asyncpg'},
            message='RAG service is running'
        )
    
    # Root endpoint
    @app.route('/')
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
    
    # Global error handlers
    @app.errorhandler(404)
    def not_found(e):
        return error_response("Endpoint not found", 404)
    
    @app.errorhandler(500)
    def internal_error(e):
        return error_response("Internal server error", 500)
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        print(f"❌ Unhandled exception: {e}")
        traceback.print_exc()
        return error_response("Internal server error", 500)
    
    return app


def init_services():
    """Initialize all services (synchronous)"""
    try:
        print("🔧 Initializing services...")
        
        # Initialize database connection managers
        init_db()
        
        # Initialize service components
        init_sync_services()
        init_search_services()
        init_admin_services()
        
        print("✅ All services initialized successfully\n")
        
    except Exception as e:
        print(f"❌ Service initialization error: {e}")
        traceback.print_exc()
        raise


def cleanup_services():
    """Cleanup services on shutdown"""
    try:
        print("\n🛑 Shutting down services...")
        close_db()
        print("✅ Cleanup complete")
    except Exception as e:
        print(f"❌ Cleanup error: {e}")


# ============= Module-level app for gunicorn =============
# Gunicorn imports `app:app`, so the app must exist at module level.
# This also runs init_services() so DB and other services are ready.
app = create_app()
init_services()


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 CoreIQ RAG Service Starting (AsyncPG)...")
    print("="*60)
    
    print(f"📍 Running on: http://localhost:5000")
    print(f"🔍 Search: POST /api/rag/search")
    print(f"🔄 Sync: POST /api/rag/sync")
    print(f"👮 Admin: /api/rag/admin/*")
    print(f"🗄️  Database: AsyncPG per-request connections")
    print(f"💚 Health: GET /health")
    print("="*60 + "\n")
    
    # Run Flask dev server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=Config.DEBUG,
        use_reloader=False
    )