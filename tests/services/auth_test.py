import pytest
from app import create_app
from unittest.mock import patch, MagicMock
from werkzeug.security import generate_password_hash
from app.config import TestConfig
from app.database.models import Pengguna
from app.database.base import db
from app.services.auth_service import register_user
from sqlalchemy.exc import SQLAlchemyError


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app(TestConfig)

    # Set up database (mock or real)
    with app.app_context():
        # db.create_all()
        yield app


@pytest.fixture
def mock_db(app):
    """Mock database session within app context"""
    with app.app_context():
        with patch("app.services.auth_service.db") as mock_db:
            yield mock_db


@pytest.fixture
def sample_user_data():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "nama": "Test User",
        "password": "securepassword123",
    }


def test_register_user_success(app, mock_db, sample_user_data):
    """Test successful user registration"""
    with app.app_context():
        # Mock database queries
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = (
            None
        )

        # Mock current_app logger
        with patch("app.services.auth_service.current_app") as mock_app:
            mock_app.logger = MagicMock()

            # Call the function
            result = register_user(**sample_user_data)

            # Assertions
            assert isinstance(result, Pengguna)
            assert result.username == sample_user_data["username"]
            mock_db.session.add.assert_called_once()
            mock_db.session.commit.assert_called_once()
            mock_app.logger.info.assert_called_once()


def test_register_user_username_taken(app, mock_db, sample_user_data):
    """Test username already exists"""
    with app.app_context():
        # Mock existing user
        mock_user = MagicMock()
        mock_db.session.query.return_value.filter_by.return_value.first.side_effect = [
            mock_user,  # Username exists
            None,  # Email doesn't exist
        ]

        with pytest.raises(ValueError, match="Username already taken"):
            register_user(**sample_user_data)


def test_register_user_database_error(app, mock_db, sample_user_data):
    """Test database commit failure"""
    with app.app_context():
        # Setup successful query but fail on commit
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = (
            None
        )
        mock_db.session.commit.side_effect = SQLAlchemyError("DB error")

        with pytest.raises(SQLAlchemyError):
            register_user(**sample_user_data)
        mock_db.session.rollback.assert_called_once()
