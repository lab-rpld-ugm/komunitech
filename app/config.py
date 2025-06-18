# app/config.py - Complete Fixed Version
import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config:
    """Base configuration."""
    
    # Basic Flask config
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or "sqlite:///" + os.path.join(basedir, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    # File uploads
    UPLOAD_FOLDER = os.path.join(basedir, "static/uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB for individual files
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx'}
    
    # Pagination
    ITEMS_PER_PAGE = 12
    ITEMS_PER_PAGE_ADMIN = 20
    MAX_SEARCH_RESULTS = 100
    
    # Session config
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@komunitech.id'
    
    # Application settings
    APP_NAME = "KomuniTech"
    APP_DESCRIPTION = "Platform untuk komunitas menyuarakan kebutuhan mereka"
    APP_VERSION = "1.0.0"
    
    # Security
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # CSRF tokens don't expire
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL') or 'memory://'
    RATELIMIT_DEFAULT = "200 per day, 50 per hour"
    
    # Logging
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    
    # Feature flags
    ENABLE_EMAIL_VERIFICATION = os.environ.get('ENABLE_EMAIL_VERIFICATION', 'false').lower() in ['true', 'on', '1']
    ENABLE_NOTIFICATIONS = os.environ.get('ENABLE_NOTIFICATIONS', 'true').lower() in ['true', 'on', '1']
    ENABLE_API = os.environ.get('ENABLE_API', 'false').lower() in ['true', 'on', '1']
    ENABLE_AUDIT_LOG = os.environ.get('ENABLE_AUDIT_LOG', 'true').lower() in ['true', 'on', '1']
    
    # Cache settings
    CACHE_TYPE = os.environ.get('CACHE_TYPE') or 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Search settings
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    SEARCH_MIN_LENGTH = 2
    
    # Admin settings
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@komunitech.id'
    AUTO_APPROVE_VERIFIED_USERS = False
    
    # Comment settings
    COMMENT_EDIT_WINDOW = 900  # 15 minutes in seconds
    MAX_COMMENT_DEPTH = 3  # Maximum nesting level for replies
    
    # Support settings
    ALLOW_SELF_SUPPORT = False
    SUPPORT_NOTIFICATION_THRESHOLD = 10  # Notify project owner after X supports
    
    # Project settings
    PROJECT_COMPLETION_THRESHOLD = 0.8  # 80% of requirements completed
    AUTO_ARCHIVE_DAYS = 365  # Archive projects after 1 year of inactivity
    
    # Media settings
    IMAGE_QUALITY = 85  # JPEG quality for resized images
    THUMBNAIL_SIZE = (300, 300)
    MEDIUM_SIZE = (800, 800)
    
    # API settings (if enabled)
    API_VERSION = 'v1'
    API_RATE_LIMIT = "100 per hour"
    
    @staticmethod
    def init_app(app):
        """Initialize application with config."""
        # Create upload directory if it doesn't exist
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Create subdirectories for different upload types
        for subdir in ['projects', 'kebutuhan', 'comments', 'avatars', 'temp']:
            os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], subdir), exist_ok=True)


class DevConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    
    # Development database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DEV_DATABASE_URL"
    ) or "sqlite:///" + os.path.join(basedir, "app-dev.db")
    
    # Disable CSRF for easier testing (remove in production)
    WTF_CSRF_ENABLED = True
    
    # More verbose logging
    SQLALCHEMY_ECHO = False  # Set to True to see SQL queries
    
    # Development email - print to console
    MAIL_SUPPRESS_SEND = True
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log to console in development
        import logging
        from logging import StreamHandler
        
        if not app.logger.handlers:
            handler = StreamHandler()
            handler.setLevel(logging.DEBUG)
            app.logger.addHandler(handler)
            app.logger.setLevel(logging.DEBUG)


class TestConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = False
    
    # Test database - in memory
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    # Disable rate limiting for tests
    RATELIMIT_ENABLED = False
    
    # Use simple cache for testing
    CACHE_TYPE = 'simple'
    
    # Disable email sending
    MAIL_SUPPRESS_SEND = True
    
    # Faster password hashing for tests
    BCRYPT_LOG_ROUNDS = 4


class ProdConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    
    # Production database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or "postgresql://komunitech_user:password@localhost/komunitech_db"
    
    # Security settings for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Use Redis for caching in production
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Email verification required in production
    ENABLE_EMAIL_VERIFICATION = True
    
    # Stricter rate limiting in production
    RATELIMIT_DEFAULT = "100 per day, 20 per hour"
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log to syslog in production
        import logging
        from logging.handlers import SysLogHandler
        
        if not app.logger.handlers:
            syslog_handler = SysLogHandler()
            syslog_handler.setLevel(logging.WARNING)
            app.logger.addHandler(syslog_handler)
        
        # Email errors to admins
        if app.config['MAIL_SERVER']:
            from logging.handlers import SMTPHandler
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr=app.config['MAIL_DEFAULT_SENDER'],
                toaddrs=[app.config['ADMIN_EMAIL']],
                subject=f"{app.config['APP_NAME']} Application Error",
                credentials=(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD']),
                secure=() if app.config['MAIL_USE_TLS'] else None
            )
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)


# Configuration dictionary
config = {
    'development': DevConfig,
    'testing': TestConfig,
    'production': ProdConfig,
    'default': DevConfig
}