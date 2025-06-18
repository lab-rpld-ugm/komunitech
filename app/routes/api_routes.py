# app/routes/api_routes.py - New File
from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from functools import wraps
from app.services.project_service import (
    get_recent_projects, get_project_by_id, create_project
)
from app.services.kebutuhan_service import (
    get_all_kebutuhan, get_kebutuhan_by_id, create_kebutuhan
)
from app.services.support_service import create_support, remove_support, has_supported
from app.services.user_service import get_user_by_username
from app.services.search_service import search_all
from app.database.base import db
import jwt
from datetime import datetime, timedelta

api_bp = Blueprint("api", __name__)


def require_api_key(f):
    """Decorator to require API key for endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # In production, validate against database
        # For now, just check if it exists
        if not api_key:
            return jsonify({'error': 'Invalid API key'}), 401
        
        return f(*args, **kwargs)
    return decorated_function


def generate_api_response(success=True, data=None, message=None, errors=None, pagination=None):
    """Generate standardized API response."""
    response = {
        'success': success,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if data is not None:
        response['data'] = data
    if message:
        response['message'] = message
    if errors:
        response['errors'] = errors
    if pagination:
        response['pagination'] = pagination
    
    return jsonify(response)


# Public endpoints
@api_bp.route("/projects", methods=["GET"])
def get_projects():
    """Get list of projects."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status', 'Aktif')
    category_id = request.args.get('category_id', type=int)
    
    projects = get_recent_projects(page=page, per_page=per_page)
    
    data = [{
        'id': p.id,
        'judul': p.judul,
        'deskripsi': p.deskripsi[:200] + '...' if len(p.deskripsi) > 200 else p.deskripsi,
        'status': p.status,
        'created_at': p.timestamp.isoformat(),
        'owner': {
            'id': p.pemilik.id,
            'nama': p.pemilik.nama,
            'username': p.pemilik.username
        },
        'category': {
            'id': p.kategori_project.id,
            'nama': p.kategori_project.nama
        },
        'stats': {
            'kebutuhan_count': p.kebutuhan.count(),
            'completion_percentage': p.completion_percentage,
            'view_count': p.view_count
        }
    } for p in projects.items]
    
    pagination = {
        'page': projects.page,
        'pages': projects.pages,
        'per_page': projects.per_page,
        'total': projects.total,
        'has_next': projects.has_next,
        'has_prev': projects.has_prev
    }
    
    return generate_api_response(data=data, pagination=pagination)


@api_bp.route("/projects/<int:id>", methods=["GET"])
def get_project(id):
    """Get single project details."""
    project = get_project_by_id(id)
    if not project:
        return generate_api_response(success=False, message="Project not found"), 404
    
    # Increment view count
    project.increment_views()
    
    data = {
        'id': project.id,
        'judul': project.judul,
        'deskripsi': project.deskripsi,
        'status': project.status,
        'gambar_url': project.gambar_url,
        'created_at': project.timestamp.isoformat(),
        'updated_at': project.updated_at.isoformat() if project.updated_at else None,
        'owner': {
            'id': project.pemilik.id,
            'nama': project.pemilik.nama,
            'username': project.pemilik.username,
            'avatar_url': project.pemilik.avatar_url
        },
        'category': {
            'id': project.kategori_project.id,
            'nama': project.kategori_project.nama
        },
        'stats': {
            'kebutuhan_count': project.kebutuhan.count(),
            'completion_percentage': project.completion_percentage,
            'total_support': project.total_support,
            'view_count': project.view_count
        },
        'kebutuhan': [{
            'id': k.id,
            'judul': k.judul,
            'status': k.status,
            'prioritas': k.prioritas,
            'support_count': k.jumlah_dukungan,
            'created_at': k.timestamp.isoformat()
        } for k in project.kebutuhan.limit(10).all()]
    }
    
    return generate_api_response(data=data)


@api_bp.route("/kebutuhan", methods=["GET"])
def get_kebutuhan_list():
    """Get list of kebutuhan."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')
    priority = request.args.get('priority')
    project_id = request.args.get('project_id', type=int)
    
    kebutuhan = get_all_kebutuhan(
        page=page,
        per_page=per_page,
        status=status,
        prioritas=priority
    )
    
    data = [{
        'id': k.id,
        'judul': k.judul,
        'deskripsi': k.deskripsi[:200] + '...' if len(k.deskripsi) > 200 else k.deskripsi,
        'status': k.status,
        'prioritas': k.prioritas,
        'created_at': k.timestamp.isoformat(),
        'project': {
            'id': k.project.id,
            'judul': k.project.judul
        },
        'pengaju': {
            'id': k.pengaju.id,
            'nama': k.pengaju.nama,
            'username': k.pengaju.username
        },
        'category': {
            'id': k.kategori_kebutuhan.id,
            'nama': k.kategori_kebutuhan.nama
        },
        'stats': {
            'support_count': k.jumlah_dukungan,
            'comment_count': k.jumlah_komentar,
            'view_count': k.view_count
        }
    } for k in kebutuhan.items]
    
    pagination = {
        'page': kebutuhan.page,
        'pages': kebutuhan.pages,
        'per_page': kebutuhan.per_page,
        'total': kebutuhan.total,
        'has_next': kebutuhan.has_next,
        'has_prev': kebutuhan.has_prev
    }
    
    return generate_api_response(data=data, pagination=pagination)


@api_bp.route("/search", methods=["GET"])
def search():
    """Search API endpoint."""
    query = request.args.get('q', '')
    category_id = request.args.get('category_id', 0, type=int)
    page = request.args.get('page', 1, type=int)
    
    if len(query) < 2:
        return generate_api_response(
            success=False,
            message="Query must be at least 2 characters"
        ), 400
    
    results = search_all(query, category_id, page)
    
    data = {
        'query': query,
        'total_results': results['total'],
        'projects': [{
            'id': p.id,
            'judul': p.judul,
            'deskripsi': p.deskripsi[:100] + '...',
            'url': f"/project/{p.id}"
        } for p in (results['projects'].items if results['projects'] else [])],
        'kebutuhan': [{
            'id': k.id,
            'judul': k.judul,
            'deskripsi': k.deskripsi[:100] + '...',
            'url': f"/kebutuhan/project/{k.project_id}/kebutuhan/{k.id}"
        } for k in (results['kebutuhan'].items if results['kebutuhan'] else [])]
    }
    
    return generate_api_response(data=data)


@api_bp.route("/users/<username>", methods=["GET"])
def get_user(username):
    """Get public user profile."""
    user = get_user_by_username(username)
    if not user:
        return generate_api_response(success=False, message="User not found"), 404
    
    data = {
        'id': user.id,
        'username': user.username,
        'nama': user.nama,
        'bio': user.bio,
        'avatar_url': user.avatar_url,
        'created_at': user.created_at.isoformat(),
        'stats': {
            'projects': user.projects.count(),
            'kebutuhan': user.kebutuhan.count(),
            'supports': user.dukungan.count()
        }
    }
    
    return generate_api_response(data=data)


# Authenticated endpoints
@api_bp.route("/auth/token", methods=["POST"])
def get_auth_token():
    """Get authentication token."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return generate_api_response(
            success=False,
            message="Username and password required"
        ), 400
    
    from app.services.auth_service import authenticate_user
    user = authenticate_user(username, password)
    
    if not user:
        return generate_api_response(
            success=False,
            message="Invalid credentials"
        ), 401
    
    # Generate JWT token
    payload = {
        'user_id': user.id,
        'username': user.username,
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    
    token = jwt.encode(
        payload,
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )
    
    return generate_api_response(data={
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'nama': user.nama,
            'role': user.role
        }
    })


@api_bp.route("/projects", methods=["POST"])
@require_api_key
def create_project_api():
    """Create new project via API."""
    data = request.get_json()
    
    required_fields = ['judul', 'deskripsi', 'kategori_id']
    for field in required_fields:
        if field not in data:
            return generate_api_response(
                success=False,
                message=f"Field '{field}' is required"
            ), 400
    
    try:
        # In production, get user from token
        # For now, use current_user if authenticated
        user_id = current_user.id if current_user.is_authenticated else 1
        
        project = create_project(
            judul=data['judul'],
            deskripsi=data['deskripsi'],
            pemilik_id=user_id,
            kategori_id=data['kategori_id']
        )
        
        return generate_api_response(
            data={'id': project.id, 'judul': project.judul},
            message="Project created successfully"
        ), 201
        
    except Exception as e:
        db.session.rollback()
        return generate_api_response(
            success=False,
            message=str(e)
        ), 400


@api_bp.route("/kebutuhan/<int:id>/support", methods=["POST", "DELETE"])
@require_api_key
def toggle_support_api(id):
    """Toggle support for kebutuhan via API."""
    try:
        # In production, get user from token
        user_id = current_user.id if current_user.is_authenticated else 1
        
        if request.method == "POST":
            if has_supported(user_id, id):
                return generate_api_response(
                    success=False,
                    message="Already supported"
                ), 400
            
            support = create_support(id, user_id)
            return generate_api_response(
                message="Support added successfully"
            )
        
        else:  # DELETE
            if not has_supported(user_id, id):
                return generate_api_response(
                    success=False,
                    message="Not supported"
                ), 400
            
            remove_support(user_id, id)
            return generate_api_response(
                message="Support removed successfully"
            )
            
    except Exception as e:
        db.session.rollback()
        return generate_api_response(
            success=False,
            message=str(e)
        ), 400


# Error handlers for API
@api_bp.errorhandler(404)
def api_not_found(error):
    return generate_api_response(
        success=False,
        message="Endpoint not found"
    ), 404


@api_bp.errorhandler(500)
def api_internal_error(error):
    db.session.rollback()
    return generate_api_response(
        success=False,
        message="Internal server error"
    ), 500