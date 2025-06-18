# tests/unit/test_services/test_project_service.py
import pytest
from app.services.project_service import (
    create_project, get_project_by_id, update_project,
    get_user_projects, get_recent_projects, get_project_stats,
    add_collaborator
)
from app.database.models import Project, ProjectCollaborator


class TestProjectService:
    """Test project service functions."""
    
    def test_create_project_success(self, db, user, categories):
        """Test successful project creation."""
        project = create_project(
            judul='New Test Project',
            deskripsi='This is a test project',
            pemilik_id=user.id,
            kategori_id=categories[0].id,
            gambar_url='/static/uploads/test.jpg'
        )
        
        assert project is not None
        assert project.judul == 'New Test Project'
        assert project.deskripsi == 'This is a test project'
        assert project.pengguna_id == user.id
        assert project.kategori_id == categories[0].id
        assert project.gambar_url == '/static/uploads/test.jpg'
        assert project.status == 'Aktif'
    
    def test_create_project_invalid_category(self, db, user):
        """Test project creation with invalid category."""
        with pytest.raises(ValueError, match="Kategori tidak valid"):
            create_project(
                judul='Test Project',
                deskripsi='Description',
                pemilik_id=user.id,
                kategori_id=99999  # Non-existent category
            )
    
    def test_get_project_by_id(self, db, project):
        """Test getting project by ID."""
        found = get_project_by_id(project.id)
        
        assert found is not None
        assert found.id == project.id
        assert found.judul == project.judul
    
    def test_update_project_success(self, db, project, categories):
        """Test successful project update."""
        updated = update_project(
            project_id=project.id,
            judul='Updated Title',
            deskripsi='Updated description',
            kategori_id=categories[1].id,
            status='Selesai'
        )
        
        assert updated.judul == 'Updated Title'
        assert updated.deskripsi == 'Updated description'
        assert updated.kategori_id == categories[1].id
        assert updated.status == 'Selesai'
    
    def test_update_project_invalid_status(self, db, project):
        """Test project update with invalid status."""
        with pytest.raises(ValueError, match="Status tidak valid"):
            update_project(
                project_id=project.id,
                status='InvalidStatus'
            )
    
    def test_get_user_projects(self, db, user, categories):
        """Test getting user's projects."""
        # Create multiple projects
        for i in range(3):
            project = Project(
                judul=f'Project {i}',
                deskripsi='Test',
                pengguna_id=user.id,
                kategori_id=categories[0].id
            )
            db.session.add(project)
        db.session.commit()
        
        # Get user projects
        paginated = get_user_projects(user.id, page=1, per_page=10)
        
        assert paginated.total == 3
        assert len(paginated.items) == 3
        assert all(p.pengguna_id == user.id for p in paginated.items)
    
    def test_get_recent_projects(self, db, user, categories):
        """Test getting recent active projects."""
        # Create projects with different statuses
        statuses = ['Aktif', 'Aktif', 'Selesai', 'Ditutup']
        for i, status in enumerate(statuses):
            project = Project(
                judul=f'Project {i}',
                deskripsi='Test',
                pengguna_id=user.id,
                kategori_id=categories[0].id,
                status=status
            )
            db.session.add(project)
        db.session.commit()
        
        # Get recent projects (only active ones)
        paginated = get_recent_projects(page=1, per_page=10)
        
        assert paginated.total == 2  # Only active projects
        assert all(p.status == 'Aktif' for p in paginated.items)
    
    def test_get_project_stats_single(self, db, project, kebutuhan):
        """Test getting stats for a single project."""
        stats = get_project_stats(project.id)
        
        assert stats['total_kebutuhan'] == 1
        assert stats['view_count'] == 0
        assert stats['completion_percentage'] == 0
        assert stats['total_support'] == 0
        assert 'by_status' in stats
    
    def test_get_project_stats_global(self, db, user, categories):
        """Test getting global project stats."""
        # Create projects
        for status in ['Aktif', 'Aktif', 'Selesai']:
            project = Project(
                judul='Test',
                deskripsi='Test',
                pengguna_id=user.id,
                kategori_id=categories[0].id,
                status=status
            )
            db.session.add(project)
        db.session.commit()
        
        stats = get_project_stats()
        
        assert stats['total'] == 3
        assert stats['active'] == 2
        assert stats['completed'] == 1
        assert 'by_status' in stats
    
    def test_add_collaborator_success(self, db, project, user):
        """Test adding a collaborator to project."""
        # Create another user
        collaborator = Pengguna(
            username='collab',
            email='collab@test.com',
            nama='Collaborator'
        )
        collaborator.set_password('password')
        db.session.add(collaborator)
        db.session.commit()
        
        # Add as collaborator
        collab_record = add_collaborator(
            project_id=project.id,
            user_id=collaborator.id,
            role='Contributor',
            added_by=user.id
        )
        
        assert collab_record is not None
        assert collab_record.project_id == project.id
        assert collab_record.user_id == collaborator.id
        assert collab_record.role == 'Contributor'
        assert collab_record.added_by == user.id
    
    def test_add_collaborator_duplicate(self, db, project, user):
        """Test adding duplicate collaborator."""
        # Add collaborator
        collab = ProjectCollaborator(
            project_id=project.id,
            user_id=user.id,
            role='Contributor'
        )
        db.session.add(collab)
        db.session.commit()
        
        # Try to add again
        with pytest.raises(ValueError, match="User sudah menjadi kolaborator"):
            add_collaborator(
                project_id=project.id,
                user_id=user.id,
                role='Contributor'
            )