from flask import Flask
from .main_routes import main_bp
from .kebutuhan_routes import kebutuhan_bp
from .admin_routes import admin_bp
from .auth_routes import auth_bp
from .project_routes import project_bp
from .comment_routes import comment_bp
from .support_routes import support_bp
from .user_routes import user_bp


def register_blueprint(app: Flask):
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(project_bp)
    app.register_blueprint(kebutuhan_bp)
    app.register_blueprint(comment_bp)
    app.register_blueprint(support_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)
