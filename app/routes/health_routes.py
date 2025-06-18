# app/routes/health_routes.py
from flask import Blueprint, jsonify
from app.database.base import db
from datetime import datetime
import os

health_bp = Blueprint("health", __name__)


@health_bp.route("/health")
def health_check():
    """Basic health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "komunitech"
    })


@health_bp.route("/health/detailed")
def health_check_detailed():
    """Detailed health check with component status."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "komunitech",
        "version": os.environ.get("APP_VERSION", "1.0.0"),
        "components": {}
    }
    
    # Check database
    try:
        db.session.execute("SELECT 1")
        health_status["components"]["database"] = {
            "status": "healthy",
            "type": "postgresql" if "postgresql" in str(db.engine.url) else "sqlite"
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check Redis (if configured)
    redis_url = os.environ.get("REDIS_URL")
    if redis_url:
        try:
            import redis
            r = redis.from_url(redis_url)
            r.ping()
            health_status["components"]["redis"] = {"status": "healthy"}
        except Exception as e:
            health_status["components"]["redis"] = {
                "status": "unhealthy",
                "error": str(e)
            }
    
    # Check file storage
    upload_folder = os.path.join(os.path.dirname(__file__), "..", "static", "uploads")
    if os.path.exists(upload_folder) and os.access(upload_folder, os.W_OK):
        health_status["components"]["storage"] = {"status": "healthy"}
    else:
        health_status["status"] = "degraded"
        health_status["components"]["storage"] = {
            "status": "unhealthy",
            "error": "Upload directory not writable"
        }
    
    # Determine HTTP status code
    if health_status["status"] == "healthy":
        status_code = 200
    elif health_status["status"] == "degraded":
        status_code = 200  # Service is still operational
    else:
        status_code = 503  # Service unavailable
    
    return jsonify(health_status), status_code


@health_bp.route("/ready")
def readiness_check():
    """Kubernetes readiness probe endpoint."""
    try:
        # Check if database is accessible
        db.session.execute("SELECT 1")
        return jsonify({"ready": True}), 200
    except Exception:
        return jsonify({"ready": False}), 503


@health_bp.route("/live")
def liveness_check():
    """Kubernetes liveness probe endpoint."""
    return jsonify({"alive": True}), 200