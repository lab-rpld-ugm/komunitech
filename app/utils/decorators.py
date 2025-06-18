# app/utils/decorators.py - Complete Fixed Version
from functools import wraps
from flask import abort, flash, redirect, url_for, request, jsonify
from flask_login import current_user
import time


def admin_required(f):
    """Require admin role for access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Silakan login untuk mengakses halaman ini.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        
        if not current_user.is_admin:
            flash("Anda tidak memiliki izin untuk mengakses halaman ini.", "danger")
            abort(403)
        
        return f(*args, **kwargs)
    
    return decorated_function


def developer_required(f):
    """Require developer or admin role for access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Silakan login untuk mengakses halaman ini.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        
        if not (current_user.is_developer or current_user.is_admin):
            flash("Anda tidak memiliki izin untuk mengakses halaman ini.", "danger")
            abort(403)
        
        return f(*args, **kwargs)
    
    return decorated_function


def active_user_required(f):
    """Require active user account."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Silakan login untuk mengakses halaman ini.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        
        if not current_user.is_active:
            flash("Akun Anda telah dinonaktifkan. Hubungi admin untuk informasi lebih lanjut.", "danger")
            abort(403)
        
        return f(*args, **kwargs)
    
    return decorated_function


def verified_email_required(f):
    """Require verified email address."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Silakan login untuk mengakses halaman ini.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        
        if not current_user.email_verified:
            flash("Silakan verifikasi email Anda terlebih dahulu.", "warning")
            return redirect(url_for("user.verify_email"))
        
        return f(*args, **kwargs)
    
    return decorated_function


def rate_limit(max_calls=10, period=60):
    """Rate limiting decorator."""
    def decorator(f):
        calls = {}
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get user identifier
            if current_user.is_authenticated:
                key = f"user_{current_user.id}"
            else:
                key = f"ip_{request.remote_addr}"
            
            # Clean old entries
            now = time.time()
            calls[key] = [call for call in calls.get(key, []) if call > now - period]
            
            # Check rate limit
            if len(calls.get(key, [])) >= max_calls:
                if request.is_json:
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'message': f'Maximum {max_calls} requests per {period} seconds'
                    }), 429
                else:
                    flash(f"Terlalu banyak permintaan. Coba lagi dalam {period} detik.", "warning")
                    abort(429)
            
            # Record this call
            calls.setdefault(key, []).append(now)
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def async_task(f):
    """Run function asynchronously (requires Celery in production)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # In production, this would queue the task with Celery
        # For now, run synchronously
        return f(*args, **kwargs)
    
    return decorated_function


def cache_result(timeout=300):
    """Cache function result (requires Redis in production)."""
    def decorator(f):
        cache = {}
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Create cache key from function name and arguments
            key = f"{f.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check cache
            if key in cache:
                result, timestamp = cache[key]
                if time.time() - timestamp < timeout:
                    return result
            
            # Call function and cache result
            result = f(*args, **kwargs)
            cache[key] = (result, time.time())
            
            return result
        
        return decorated_function
    
    return decorator


def json_response(f):
    """Ensure function returns JSON response."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        result = f(*args, **kwargs)
        
        if isinstance(result, tuple):
            # Handle (data, status_code) format
            return jsonify(result[0]), result[1]
        else:
            return jsonify(result)
    
    return decorated_function


def audit_log(action_type):
    """Log admin/sensitive actions."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Execute function
            result = f(*args, **kwargs)
            
            # Log action
            if current_user.is_authenticated:
                from app.services.audit_service import log_admin_action
                log_admin_action(
                    user_id=current_user.id,
                    action=f"{action_type}_{f.__name__}",
                    entity_type=kwargs.get('entity_type'),
                    entity_id=kwargs.get('id') or kwargs.get('entity_id')
                )
            
            return result
        
        return decorated_function
    
    return decorator


def validate_ownership(model_class, id_param='id', allow_admin=True):
    """Validate that current user owns the resource."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Silakan login untuk mengakses halaman ini.", "warning")
                return redirect(url_for("auth.login", next=request.url))
            
            # Get resource ID
            resource_id = kwargs.get(id_param)
            if not resource_id:
                abort(400)
            
            # Get resource
            resource = model_class.query.get(resource_id)
            if not resource:
                abort(404)
            
            # Check ownership
            is_owner = False
            if hasattr(resource, 'pengguna_id'):
                is_owner = resource.pengguna_id == current_user.id
            elif hasattr(resource, 'user_id'):
                is_owner = resource.user_id == current_user.id
            
            # Allow admin override
            if not is_owner and not (allow_admin and current_user.is_admin):
                flash("Anda tidak memiliki izin untuk mengakses resource ini.", "danger")
                abort(403)
            
            # Add resource to kwargs for use in function
            kwargs['resource'] = resource
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def confirm_password_required(f):
    """Require password confirmation for sensitive actions."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'POST':
            password = request.form.get('confirm_password')
            if not password or not current_user.check_password(password):
                flash("Password konfirmasi tidak benar.", "danger")
                return redirect(request.url)
        
        return f(*args, **kwargs)
    
    return decorated_function