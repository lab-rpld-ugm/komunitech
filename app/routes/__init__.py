# app/routes/__init__.py - Complete Fixed Version
from flask import Flask, redirect, url_for, render_template
from .main_routes import main_bp
from .kebutuhan_routes import kebutuhan_bp
from .admin_routes import admin_bp
from .auth_routes import auth_bp
from .project_routes import project_bp
from .comment_routes import comment_bp
from .support_routes import support_bp
from .user_routes import user_bp
from .search_routes import search_bp
from .api_routes import api_bp


def register_blueprint(app: Flask):
    """Register all blueprints with the application."""
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(project_bp)
    app.register_blueprint(kebutuhan_bp)
    app.register_blueprint(comment_bp)
    app.register_blueprint(support_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(search_bp)
    
    # Register API blueprint if enabled
    if app.config.get('ENABLE_API', False):
        app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    # Register legacy route redirects for backward compatibility
    register_legacy_routes(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register context processors
    register_context_processors(app)


def register_legacy_routes(app: Flask):
    """Register legacy route redirects for backward compatibility."""
    
    @app.route('/daftar_project')
    def daftar_project():
        return redirect(url_for('project.list_projects'))
    
    @app.route('/detail_project/<int:id>')
    def detail_project(id):
        return redirect(url_for('project.detail', id=id))
    
    @app.route('/detail_kebutuhan/<int:project_id>/<int:id>')
    def detail_kebutuhan(project_id, id):
        return redirect(url_for('kebutuhan.detail', project_id=project_id, id=id))
    
    @app.route('/dukungan/<int:project_id>/<int:id>')
    def dukungan(project_id, id):
        return redirect(url_for('support.support', kebutuhan_id=id))
    
    @app.route('/dukungan_saya')
    def dukungan_saya():
        return redirect(url_for('user.supports'))
    
    @app.route('/kebutuhan_saya')
    def kebutuhan_saya():
        return redirect(url_for('user.kebutuhans'))
    
    @app.route('/project_saya')
    def project_saya():
        return redirect(url_for('user.projects'))
    
    @app.route('/tambah_kategori')
    def tambah_kategori():
        return redirect(url_for('admin.categories'))


def register_error_handlers(app: Flask):
    """Register error handlers for common HTTP errors."""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        from app.database.base import db
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(413)
    def file_too_large(error):
        return render_template('errors/413.html'), 413


def register_context_processors(app: Flask):
    """Register context processors to inject common variables."""
    
    @app.context_processor
    def inject_config():
        """Inject app configuration into templates."""
        return dict(
            APP_NAME=app.config.get('APP_NAME', 'KomuniTech'),
            APP_VERSION=app.config.get('APP_VERSION', '1.0.0'),
            ENABLE_API=app.config.get('ENABLE_API', False),
            ENABLE_NOTIFICATIONS=app.config.get('ENABLE_NOTIFICATIONS', True)
        )
    
    @app.context_processor
    def inject_forms():
        """Inject commonly used forms into templates."""
        from app.forms import SearchForm
        return dict(
            search_form=SearchForm()
        )
    
    @app.context_processor
    def inject_user_stats():
        """Inject user statistics if logged in."""
        from flask_login import current_user
        if current_user.is_authenticated:
            return dict(
                unread_notifications=current_user.notifications.filter_by(is_read=False).count(),
                user_projects_count=current_user.projects.count(),
                user_kebutuhan_count=current_user.kebutuhan.count(),
                user_supports_count=current_user.dukungan.count()
            )
        return dict()