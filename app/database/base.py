from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


# class Base(DeclarativeBase):
#     pass


# db = SQLAlchemy(model_class=Base)
db = SQLAlchemy()
migrate = Migrate()
login_man = LoginManager()


def init_db(app: Flask):
    db.init_app(app)
    migrate.init_app(app, db)
    login_man.init_app(app)
    login_man.login_view = "auth.login"
    login_man.login_message = "Silakan login untuk mengakses halaman ini."

    with app.app_context():
        db.create_all()
