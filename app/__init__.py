from flask import Flask
from app.config import Config
from app.database.base import init_db
from app.routes import register_blueprint


def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)

    init_db(app)
    register_blueprint(app)

    return app
