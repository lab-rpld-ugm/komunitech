# tests/integration/test_project_routes.py
import pytest
from flask import url_for
from app.database.models import Project
import io


class TestProjectRoutes:
    """Test project-related routes."""
    
    def test_project_list_page(self, client):
        """Test project list page loads."""
        response = client.get('/project/')
        assert response.status_code == 200
        assert b'Daftar Project' in response.data
    
    def test_project_list_with_projects(self, client, project):
        """Test project list shows projects."""
        response = client.get('/project/')
        assert response.status_code == 200
        assert project.judul.encode() in response.data
        assert b'Dibuat oleh' in response.data
    
    def test_project_detail_page(self, client, project, kebutuhan):
        """Test project detail page."""
        response = client.get(f'/project/{project.id}')
        assert response.status_code == 200
        assert project.judul.encode() in response.data
        assert project.deskripsi.encode() in response.data
        assert kebutuhan.judul.encode() in response.data
    
    def test_project_detail_not_found(self, client):
        """Test project detail with non-existent ID."""
        response = client.get('/project/99999')
        assert response.status_code == 404
    
    def test_create_project_requires_login(self, client):
        """Test project creation requires authentication."""
        response = client.get('/project/create')
        assert response.status_code == 302
        assert '/auth/login' in response.location
    
    def test_create_project_page(self, auth_client):
        """Test project creation page loads for authenticated user."""
        response = auth_client.get('/project/create')
        assert response.status_code == 200
        assert b'Buat Project Baru' in response.data
        assert b'Judul Project' in response.data
        assert b'Deskripsi Project' in response.data
    
    def test_create_project_success(self, auth_client, categories):
        """Test successful project creation."""
        data = {
            'judul': 'New Test Project',
            'deskripsi': 'This is a detailed description of the test project that explains its purpose and goals.',
            'kategori': categories[0].id
        }
        
        response = auth_client.post('/project/create', data=data, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Project created successfully!' in response.data
        assert b'New Test Project' in response.data
        
        # Verify project was created
        project = Project.query.filter_by(judul='New Test Project').first()
        assert project is not None
        assert project.deskripsi == data['deskripsi']
        assert project.kategori_id == categories[0].id
    
    def test_create_project_with_image(self, auth_client, categories, image_file):
        """Test project creation with image upload."""
        data = {
            'judul': 'Project with Image',
            'deskripsi': 'This project has an image',
            'kategori': categories[0].id,
            'gambar': image_file
        }
        
        response = auth_client.post(
            '/project/create',
            data=data,
            content_type='multipart/form-data',
            follow_redirects=True
        )
        
        assert response.status_code == 200
        assert b'Project created successfully!' in response.data
        
        project = Project.query.filter_by(judul='Project with Image').first()
        assert project is not None
        assert project.gambar_url is not None
        assert project.gambar_url.startswith('/static/uploads/')
    
    def test_create_project_validation_errors(self, auth_client):
        """Test project creation with validation errors."""
        # Missing required fields
        response = auth_client.post('/project/create', data={})
        
        assert response.status_code == 200
        assert b'Judul project harus diisi' in response.data
        assert b'Deskripsi project harus diisi' in response.data
        assert b'Kategori harus dipilih' in response.data
    
    def test_edit_project_requires_owner(self, client, auth_client, project, user):
        """Test only project owner can edit."""
        # Create another user and login
        from app.database.models import Pengguna
        other_user = Pengguna(
            username='otheruser',
            email='other@example.com',
            nama='Other User'
        )
        other_user.set_password('password')
        client.application.db.session.add(other_user)
        client.application.db.session.commit()
        
        # Login as other user
        client.post('/auth/login', data={
            'username': 'otheruser',
            'password': 'password'
        })
        
        # Try to edit project
        response = client.get(f'/project/{project.id}/edit')
        assert response.status_code == 302  # Redirected
    
    def test_edit_project_page(self, auth_client, project):
        """Test project edit page loads for owner."""
        response = auth_client.get(f'/project/{project.id}/edit')
        assert response.status_code == 200
        assert b'Edit Project' in response.data
        assert project.judul.encode() in response.data
        assert project.deskripsi.encode() in response.data
    
    def test_edit_project_success(self, auth_client, project, categories):
        """Test successful project edit."""
        data = {
            'judul': 'Updated Project Title',
            'deskripsi': 'Updated project description with more details',
            'kategori': categories[1].id  # Change category
        }
        
        response = auth_client.post(
            f'/project/{project.id}/edit',
            data=data,
            follow_redirects=True
        )
        
        assert response.status_code == 200
        assert b'Project updated successfully!' in response.data
        
        # Verify changes
        updated = Project.query.get(project.id)
        assert updated.judul == 'Updated Project Title'
        assert updated.deskripsi == data['deskripsi']
        assert updated.kategori_id == categories[1].id
    
    def test_project_view_count_increment(self, client, project):
        """Test project view count increases."""
        initial_count = project.view_count
        
        response = client.get(f'/project/{project.id}')
        assert response.status_code == 200
        
        # Refresh from database
        project = Project.query.get(project.id)
        assert project.view_count == initial_count + 1
    
    def test_project_list_pagination(self, client, user, categories):
        """Test project list pagination."""
        # Create many projects
        for i in range(15):
            project = Project(
                judul=f'Project {i}',
                deskripsi='Test project',
                pengguna_id=user.id,
                kategori_id=categories[0].id
            )
            client.application.db.session.add(project)
        client.application.db.session.commit()
        
        # First page
        response = client.get('/project/')
        assert response.status_code == 200
        assert b'Project 14' in response.data  # Most recent first
        
        # Check pagination links exist
        assert b'next_url' in response.data or b'Selanjutnya' in response.data
    
    def test_project_status_display(self, client, project):
        """Test project status is displayed correctly."""
        # Active project
        response = client.get(f'/project/{project.id}')
        assert b'Aktif' in response.data
        
        # Change status
        project.status = 'Selesai'
        client.application.db.session.commit()
        
        response = client.get(f'/project/{project.id}')
        assert b'Selesai' in response.data