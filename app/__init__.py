# app/__init__.py - Fixed Complete Version
import logging
import os
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from app.config import config
from app.database.base import db, migrate, login_man


def create_app(config_name=None):
    """Create and configure the Flask application."""
    # Create Flask instance
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_man.init_app(app)
    
    # Configure login manager
    login_man.login_view = "auth.login"
    login_man.login_message = "Silakan login untuk mengakses halaman ini."
    login_man.login_message_category = "info"
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Register blueprints
    register_blueprints(app)
    
    # Register CLI commands
    register_commands(app)
    
    # Register template filters
    register_template_filters(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Configure logging
    configure_logging(app)
    
    # Register context processors
    register_context_processors(app)
    
    # Log startup
    app.logger.info(f"{app.config['APP_NAME']} startup complete")
    
    return app


def register_blueprints(app):
    """Register all application blueprints."""
    # Import blueprints here to avoid circular imports
    from app.routes.main_routes import main_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.project_routes import project_bp
    from app.routes.kebutuhan_routes import kebutuhan_bp
    from app.routes.comment_routes import comment_bp
    from app.routes.support_routes import support_bp
    from app.routes.user_routes import user_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.search_routes import search_bp
    from app.routes.health_routes import health_bp
    
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
    app.register_blueprint(health_bp)
    
    # Register API blueprint if enabled
    if app.config.get('ENABLE_API', False):
        from app.routes.api_routes import api_bp
        app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    # Register legacy route redirects
    register_legacy_routes(app)


def register_legacy_routes(app):
    """Register legacy route redirects for backward compatibility."""
    
    @app.route('/daftar')
    def daftar_redirect():
        from flask import redirect, url_for
        return redirect(url_for('auth.register'))
    
    @app.route('/login')
    def login_redirect():
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))
    
    @app.route('/logout')
    def logout_redirect():
        from flask import redirect, url_for
        return redirect(url_for('auth.logout'))
    
    @app.route('/daftar_project')
    def daftar_project():
        from flask import redirect, url_for
        return redirect(url_for('project.list_projects'))
    
    @app.route('/buat_project')
    def buat_project():
        from flask import redirect, url_for
        return redirect(url_for('project.create'))
    
    @app.route('/detail_project/<int:id>')
    def detail_project(id):
        from flask import redirect, url_for
        return redirect(url_for('project.detail', id=id))
    
    @app.route('/project/<int:project_id>/ajukan')
    def ajukan_kebutuhan(project_id):
        from flask import redirect, url_for
        return redirect(url_for('kebutuhan.create', project_id=project_id))
    
    @app.route('/project/<int:project_id>/kebutuhan/<int:id>/dukungan')
    def dukungan(project_id, id):
        from flask import redirect, url_for
        return redirect(url_for('support.toggle_support', kebutuhan_id=id))
    
    @app.route('/dukungan_saya')
    def dukungan_saya():
        from flask import redirect, url_for
        return redirect(url_for('user.supports'))
    
    @app.route('/kebutuhan_saya')
    def kebutuhan_saya():
        from flask import redirect, url_for
        return redirect(url_for('user.kebutuhans'))
    
    @app.route('/project_saya')
    def project_saya():
        from flask import redirect, url_for
        return redirect(url_for('user.projects'))


def register_commands(app):
    """Register CLI commands with the Flask app."""
    from app.database.commands import register_commands as register_db_commands
    register_db_commands(app)


def register_template_filters(app):
    """Register custom Jinja2 template filters."""
    from datetime import datetime
    
    @app.template_filter('datetime')
    def datetime_filter(value, format='%d/%m/%Y %H:%M'):
        """Format datetime for display."""
        if value is None:
            return ""
        return value.strftime(format)
    
    @app.template_filter('date')
    def date_filter(value, format='%d/%m/%Y'):
        """Format date for display."""
        if value is None:
            return ""
        return value.strftime(format)
    
    @app.template_filter('nl2br')
    def nl2br_filter(value):
        """Convert newlines to HTML line breaks."""
        if not value:
            return ""
        # Import Markup here to avoid circular imports
        from markupsafe import Markup
        return Markup(value.replace('\n', '<br>\n'))
    
    @app.template_filter('truncate_words')
    def truncate_words_filter(value, num_words=50):
        """Truncate text to specified number of words."""
        if not value:
            return ""
        words = value.split()
        if len(words) <= num_words:
            return value
        return ' '.join(words[:num_words]) + '...'
    
    @app.template_filter('filesize')
    def filesize_filter(value):
        """Format file size for display."""
        if value is None:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if value < 1024.0:
                return f"{value:.1f} {unit}"
            value /= 1024.0
        return f"{value:.1f} TB"
    
    @app.template_filter('timesince')
    def timesince_filter(dt, default="just now"):
        """Returns string representing 'time since' e.g. 3 days ago."""
        if dt is None:
            return default
        
        now = datetime.utcnow()
        diff = now - dt
        
        periods = (
            (diff.days / 365, "year", "years"),
            (diff.days / 30, "month", "months"),
            (diff.days / 7, "week", "weeks"),
            (diff.days, "day", "days"),
            (diff.seconds / 3600, "hour", "hours"),
            (diff.seconds / 60, "minute", "minutes"),
            (diff.seconds, "second", "seconds"),
        )
        
        for period, singular, plural in periods:
            if period >= 1:
                return "%d %s ago" % (period, singular if period == 1 else plural)
        
        return default


def register_error_handlers(app):
    """Register error handlers."""
    
    @app.errorhandler(404)
    def not_found_error(error):
        if hasattr(error, 'description'):
            app.logger.warning(f"404 error: {error.description}")
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        if hasattr(error, 'description'):
            app.logger.warning(f"403 error: {error.description}")
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f"500 error: {error}")
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(413)
    def file_too_large(error):
        return render_template('errors/413.html'), 413
    
    @app.errorhandler(429)
    def ratelimit_handler(error):
        return render_template('errors/429.html'), 429


def configure_logging(app):
    """Configure application logging."""
    if not app.debug and not app.testing:
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Set up file handler with rotation
        file_handler = RotatingFileHandler(
            'logs/komunitech.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        
        # Set formatting
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        
        # Set log level
        log_level = app.config.get('LOG_LEVEL', 'INFO')
        file_handler.setLevel(getattr(logging, log_level.upper()))
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(getattr(logging, log_level.upper()))
        app.logger.info('KomuniTech startup')


# Context processors to inject common variables
def register_context_processors(app):
    """Register context processors."""
    
    @app.context_processor
    def inject_config():
        """Inject app configuration into templates."""
        return dict(
            APP_NAME=app.config.get('APP_NAME', 'KomuniTech'),
            APP_VERSION=app.config.get('APP_VERSION', '1.0.0'),
            APP_DESCRIPTION=app.config.get('APP_DESCRIPTION', ''),
            ENABLE_API=app.config.get('ENABLE_API', False),
            ENABLE_NOTIFICATIONS=app.config.get('ENABLE_NOTIFICATIONS', True)
        )
    
    @app.context_processor
    def inject_forms():
        """Inject commonly used forms into templates."""
        # Import here to avoid circular imports
        from app.forms import SearchForm
        return dict(
            search_form=SearchForm()
        )
    
    @app.context_processor
    def inject_user_stats():
        """Inject user statistics if logged in."""
        from flask_login import current_user
        if current_user.is_authenticated:
            # Avoid circular imports by using current_user methods directly
            return dict(
                unread_notifications=current_user.notifications.filter_by(is_read=False).count() if hasattr(current_user, 'notifications') else 0,
                user_projects_count=current_user.projects.count() if hasattr(current_user, 'projects') else 0,
                user_kebutuhan_count=current_user.kebutuhan.count() if hasattr(current_user, 'kebutuhan') else 0,
                user_supports_count=current_user.dukungan.count() if hasattr(current_user, 'dukungan') else 0
            )
        return dict(
            unread_notifications=0,
            user_projects_count=0,
            user_kebutuhan_count=0,
            user_supports_count=0
        )
    
    @app.context_processor
    def utility_processor():
        """Inject utility functions."""
        def get_categories():
            # Import here to avoid circular imports
            from app.database.models import Kategori
            return Kategori.query.order_by(Kategori.nama).all()
        
        return dict(get_categories=get_categories)