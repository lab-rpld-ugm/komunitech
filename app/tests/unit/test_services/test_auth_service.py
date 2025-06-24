# tests/unit/test_services/test_auth_service.py
import pytest
from app.services.auth_service import register_user, authenticate_user, get_user_by_id
from app.database.models import Pengguna


class TestAuthService:
    """Test authentication service functions."""
    
    def test_register_user_success(self, db):
        """Test successful user registration."""
        user = register_user(
            username='newuser',
            email='new@example.com',
            nama='New User',
            password='Password123!'
        )
        
        assert user is not None
        assert user.username == 'newuser'
        assert user.email == 'new@example.com'
        assert user.nama == 'New User'
        assert user.check_password('Password123!')
        
        # Verify user is in database
        db_user = Pengguna.query.filter_by(username='newuser').first()
        assert db_user is not None
        assert db_user.id == user.id
    
    def test_register_user_duplicate_username(self, db, user):
        """Test registration with existing username."""
        with pytest.raises(ValueError, match="Username already taken"):
            register_user(
                username=user.username,  # Existing username
                email='different@example.com',
                nama='Different Name',
                password='Password123!'
            )
    
    def test_register_user_duplicate_email(self, db, user):
        """Test registration with existing email."""
        with pytest.raises(ValueError, match="Email already registered"):
            register_user(
                username='differentuser',
                email=user.email,  # Existing email
                nama='Different Name',
                password='Password123!'
            )
    
    def test_authenticate_user_success(self, db, user, user_data):
        """Test successful authentication."""
        authenticated = authenticate_user(
            username=user_data['username'],
            password=user_data['password']
        )
        
        assert authenticated is not None
        assert authenticated.id == user.id
        assert authenticated.username == user.username
    
    def test_authenticate_user_wrong_password(self, db, user, user_data):
        """Test authentication with wrong password."""
        authenticated = authenticate_user(
            username=user_data['username'],
            password='WrongPassword123!'
        )
        
        assert authenticated is None
    
    def test_authenticate_user_nonexistent(self, db):
        """Test authentication with non-existent user."""
        authenticated = authenticate_user(
            username='nonexistent',
            password='Password123!'
        )
        
        assert authenticated is None
    
    def test_get_user_by_id_success(self, db, user):
        """Test getting user by ID."""
        found_user = get_user_by_id(user.id)
        
        assert found_user is not None
        assert found_user.id == user.id
        assert found_user.username == user.username
    
    def test_get_user_by_id_not_found(self, db):
        """Test getting non-existent user by ID."""
        with pytest.raises(ValueError, match="User not found"):
            get_user_by_id(99999)