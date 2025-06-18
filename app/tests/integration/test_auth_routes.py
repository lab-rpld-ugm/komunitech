# tests/integration/test_auth_routes.py
import pytest
from flask import session, url_for


class TestAuthRoutes:
    """Test authentication routes."""
    
    def test_login_page(self, client):
        """Test login page loads."""
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'Masuk ke KomuniTech' in response.data
        assert b'Username' in response.data
        assert b'Password' in response.data
    
    def test_login_success(self, client, user, user_data):
        """Test successful login."""
        response = client.post('/auth/login', data={
            'username': user_data['username'],
            'password': user_data['password']
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Beranda' in response.data  # Redirected to home
        
        # Check user is logged in
        with client.session_transaction() as sess:
            assert '_user_id' in sess
    
    def test_login_invalid_credentials(self, client, user):
        """Test login with invalid credentials."""
        response = client.post('/auth/login', data={
            'username': 'wronguser',
            'password': 'wrongpass'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Invalid username or password' in response.data
    
    def test_login_redirect_authenticated(self, client, auth_client, user):
        """Test login page redirects if already authenticated."""
        response = auth_client.get('/auth/login', follow_redirects=True)
        assert response.status_code == 200
        assert b'Beranda' in response.data
    
    def test_register_page(self, client):
        """Test register page loads."""
        response = client.get('/auth/register')
        assert response.status_code == 200
        assert b'Daftar Akun Baru' in response.data
        assert b'Username' in response.data
        assert b'Email' in response.data
        assert b'Nama Lengkap' in response.data
    
    def test_register_success(self, client, db):
        """Test successful registration."""
        response = client.post('/auth/register', data={
            'username': 'newuser',
            'email': 'new@example.com',
            'nama': 'New User',
            'password': 'Password123!',
            'password2': 'Password123!'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Registration successful' in response.data
        assert b'Masuk ke KomuniTech' in response.data  # Redirected to login
        
        # Verify user created
        from app.database.models import Pengguna
        user = Pengguna.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.email == 'new@example.com'
    
    def test_register_validation_errors(self, client, db):
        """Test registration with validation errors."""
        # Missing fields
        response = client.post('/auth/register', data={
            'username': '',
            'email': '',
            'nama': '',
            'password': '',
            'password2': ''
        })
        
        assert response.status_code == 200
        assert b'Username harus diisi' in response.data
        assert b'Email harus diisi' in response.data
        assert b'Nama lengkap harus diisi' in response.data
    
    def test_register_password_mismatch(self, client, db):
        """Test registration with password mismatch."""
        response = client.post('/auth/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'nama': 'Test User',
            'password': 'Password123!',
            'password2': 'Different123!'
        })
        
        assert response.status_code == 200
        assert b'Password tidak cocok' in response.data
    
    def test_register_duplicate_username(self, client, user):
        """Test registration with existing username."""
        response = client.post('/auth/register', data={
            'username': user.username,
            'email': 'different@example.com',
            'nama': 'Different User',
            'password': 'Password123!',
            'password2': 'Password123!'
        })
        
        assert response.status_code == 200
        assert b'Username ini sudah digunakan' in response.data
    
    def test_logout(self, client, auth, user):
        """Test logout functionality."""
        # Login first
        auth.login()
        
        # Then logout
        response = client.get('/auth/logout', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Beranda' in response.data
        
        # Check user is logged out
        with client.session_transaction() as sess:
            assert '_user_id' not in sess
    
    def test_login_next_parameter(self, client, user, user_data):
        """Test login redirects to 'next' parameter."""
        # Try to access protected page
        response = client.get('/project/create')
        assert response.status_code == 302  # Redirect to login
        
        # Login with next parameter
        response = client.post(
            '/auth/login?next=/project/create',
            data={
                'username': user_data['username'],
                'password': user_data['password']
            },
            follow_redirects=True
        )
        
        assert response.status_code == 200
        assert b'Buat Project Baru' in response.data  # Redirected to create project
    
    def test_login_invalid_next_parameter(self, client, user, user_data):
        """Test login ignores invalid 'next' parameter."""
        response = client.post(
            '/auth/login?next=http://evil.com',
            data={
                'username': user_data['username'],
                'password': user_data['password']
            },
            follow_redirects=True
        )
        
        assert response.status_code == 200
        assert b'Beranda' in response.data  # Redirected to home, not evil.com