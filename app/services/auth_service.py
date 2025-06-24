from flask import current_app
from app.database.models import Pengguna
from app.database.base import db


def register_user(username: str, email: str, nama: str, password: str) -> Pengguna:
    """Register a new user.

    Args:
        username: Unique username
        email: User email
        nama: Full name
        password: Plain text password

    Returns:
        Pengguna: The created user object

    Raises:
        ValueError: If username or email already exists
    """
    if Pengguna.query.filter_by(username=username).first():
        raise ValueError("Username already taken")
    if Pengguna.query.filter_by(email=email).first():
        raise ValueError("Email already registered")

    user = Pengguna(username=username, email=email, nama=nama)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    current_app.logger.info(f"New user registered: {username}")
    return user


def authenticate_user(username: str, password: str) -> Pengguna:
    """Authenticate a user.

    Args:
        username: User's username
        password: Plain text password

    Returns:
        Pengguna: User object if authenticated, None otherwise
    """
    user = Pengguna.query.filter_by(username=username).first()
    if user and user.check_password(password):
        current_app.logger.info(f"User authenticated: {username}")
        return user
    return None


def get_user_by_id(user_id: int) -> Pengguna:
    """Get user by ID.

    Args:
        user_id: User ID

    Returns:
        Pengguna: User object

    Raises:
        ValueError: If user not found
    """
    user = Pengguna.query.get(user_id)
    if not user:
        raise ValueError("User not found")
    return user
