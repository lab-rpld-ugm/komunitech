# tests/conftest.py
import os
import tempfile
import pytest
from datetime import datetime
from flask import Flask
from flask_login import login_user, logout_user

from app import create_app
from app.config import TestConfig
from app.database.base import db as _db
from app.database.models import (
    Pengguna, Kategori, Project, Kebutuhan, 
    Komentar, Dukungan, Notification
)


@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    # Create a temporary file for the test database
    db_fd, db_path = tempfile.mkstemp()
    
    # Update test config with temp database
    TestConfig.SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    TestConfig.TESTING = True
    TestConfig.WTF_CSRF_ENABLED = False
    
    # Create app with test config
    app = create_app(TestConfig)
    
    # Create application context
    with app.app_context():
        yield app
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope='session')
def _db_setup(app):
    """Create database tables."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.drop_all()


@pytest.fixture(scope='function')
def db(_db_setup, app):
    """Provide clean database for each test."""
    with app.app_context():
        # Start a transaction
        connection = _db.engine.connect()
        transaction = connection.begin()
        
        # Configure session to use this connection
        options = dict(bind=connection, binds={})
        session = _db.create_scoped_session(options=options)
        
        # Make session available to app
        _db.session = session
        
        yield _db
        
        # Rollback transaction and cleanup
        transaction.rollback()
        connection.close()
        session.remove()


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def auth_client(client, user):
    """Create authenticated test client."""
    with client:
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
    return client


# User fixtures
@pytest.fixture
def user_data():
    """Basic user data."""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'nama': 'Test User',
        'password': 'Test123!'
    }


@pytest.fixture
def user(db, user_data):
    """Create a test user."""
    user = Pengguna(
        username=user_data['username'],
        email=user_data['email'],
        nama=user_data['nama']
    )
    user.set_password(user_data['password'])
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    admin = Pengguna(
        username='admin',
        email='admin@example.com',
        nama='Admin User',
        role='Admin'
    )
    admin.set_password('Admin123!')
    db.session.add(admin)
    db.session.commit()
    return admin


@pytest.fixture
def developer_user(db):
    """Create a developer user."""
    dev = Pengguna(
        username='developer',
        email='dev@example.com',
        nama='Developer User',
        role='Developer'
    )
    dev.set_password('Dev123!')
    db.session.add(dev)
    db.session.commit()
    return dev


# Category fixtures
@pytest.fixture
def categories(db):
    """Create test categories."""
    category_data = [
        ('Infrastruktur', 'Kebutuhan terkait infrastruktur fisik'),
        ('Pendidikan', 'Kebutuhan terkait pendidikan dan pelatihan'),
        ('Kesehatan', 'Kebutuhan terkait layanan kesehatan'),
        ('Teknologi', 'Kebutuhan terkait penerapan teknologi')
    ]
    
    categories = []
    for nama, deskripsi in category_data:
        cat = Kategori(nama=nama, deskripsi=deskripsi)
        db.session.add(cat)
        categories.append(cat)
    
    db.session.commit()
    return categories


# Project fixtures
@pytest.fixture
def project_data():
    """Basic project data."""
    return {
        'judul': 'Test Project',
        'deskripsi': 'This is a test project description',
        'kategori_id': 1
    }


@pytest.fixture
def project(db, user, categories, project_data):
    """Create a test project."""
    project = Project(
        judul=project_data['judul'],
        deskripsi=project_data['deskripsi'],
        pengguna_id=user.id,
        kategori_id=categories[0].id
    )
    db.session.add(project)
    db.session.commit()
    return project


# Kebutuhan fixtures
@pytest.fixture
def kebutuhan_data():
    """Basic kebutuhan data."""
    return {
        'judul': 'Test Kebutuhan',
        'deskripsi': 'This is a test kebutuhan description',
        'prioritas': 'Sedang'
    }


@pytest.fixture
def kebutuhan(db, user, project, categories, kebutuhan_data):
    """Create a test kebutuhan."""
    kebutuhan = Kebutuhan(
        judul=kebutuhan_data['judul'],
        deskripsi=kebutuhan_data['deskripsi'],
        pengguna_id=user.id,
        project_id=project.id,
        kategori_id=categories[0].id,
        prioritas=kebutuhan_data['prioritas']
    )
    db.session.add(kebutuhan)
    db.session.commit()
    return kebutuhan


# Comment fixtures
@pytest.fixture
def comment(db, user, kebutuhan):
    """Create a test comment."""
    comment = Komentar(
        isi='This is a test comment',
        pengguna_id=user.id,
        kebutuhan_id=kebutuhan.id
    )
    db.session.add(comment)
    db.session.commit()
    return comment


# Support fixtures
@pytest.fixture
def support(db, user, kebutuhan):
    """Create a test support."""
    # Create another user to support the kebutuhan
    supporter = Pengguna(
        username='supporter',
        email='supporter@example.com',
        nama='Supporter User'
    )
    supporter.set_password('Support123!')
    db.session.add(supporter)
    db.session.commit()
    
    support = Dukungan(
        pengguna_id=supporter.id,
        kebutuhan_id=kebutuhan.id
    )
    db.session.add(support)
    db.session.commit()
    return support


# File upload fixtures
@pytest.fixture
def image_file():
    """Create a test image file."""
    import io
    from werkzeug.datastructures import FileStorage
    
    data = io.BytesIO(b'fake image data')
    return FileStorage(
        stream=data,
        filename='test.jpg',
        content_type='image/jpeg'
    )


@pytest.fixture
def temp_upload_dir(app):
    """Create temporary upload directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        app.config['UPLOAD_FOLDER'] = tmpdir
        yield tmpdir


# Helper fixtures
@pytest.fixture
def auth_headers(user):
    """Create authentication headers for API requests."""
    # This would be used for API authentication
    # Implement based on your authentication method
    return {'Authorization': f'Bearer test-token-{user.id}'}


class AuthActions:
    """Helper class for authentication actions in tests."""
    
    def __init__(self, client):
        self._client = client
    
    def login(self, username='testuser', password='Test123!'):
        return self._client.post(
            '/auth/login',
            data={'username': username, 'password': password},
            follow_redirects=True
        )
    
    def logout(self):
        return self._client.get('/auth/logout', follow_redirects=True)


@pytest.fixture
def auth(client):
    """Authentication helper."""
    return AuthActions(client)