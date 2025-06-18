# tests/unit/test_models.py
import pytest
from datetime import datetime, timedelta
from app.database.models import (
    Pengguna, Kategori, Project, Kebutuhan, 
    Komentar, Dukungan, Notification
)


class TestPenggunaModel:
    """Test Pengguna (User) model."""
    
    def test_create_user(self, db):
        """Test user creation."""
        user = Pengguna(
            username='newuser',
            email='new@example.com',
            nama='New User'
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        assert user.id is not None
        assert user.username == 'newuser'
        assert user.email == 'new@example.com'
        assert user.nama == 'New User'
        assert user.role == 'Regular'  # Default role
        assert user.is_active is True
        assert user.email_verified is False
    
    def test_password_hashing(self, db):
        """Test password is hashed properly."""
        user = Pengguna(username='testpwd', email='pwd@test.com', nama='Test')
        user.set_password('mypassword')
        
        assert user.password_hash is not None
        assert user.password_hash != 'mypassword'
        assert user.check_password('mypassword') is True
        assert user.check_password('wrongpassword') is False
    
    def test_user_roles(self, db):
        """Test user role properties."""
        regular_user = Pengguna(username='regular', email='regular@test.com', nama='Regular')
        admin_user = Pengguna(username='admin', email='admin@test.com', nama='Admin', role='Admin')
        dev_user = Pengguna(username='dev', email='dev@test.com', nama='Dev', role='Developer')
        
        assert regular_user.is_admin is False
        assert regular_user.is_developer is False
        
        assert admin_user.is_admin is True
        assert admin_user.is_developer is False
        
        assert dev_user.is_admin is False
        assert dev_user.is_developer is True
    
    def test_has_supported(self, db, user, kebutuhan):
        """Test has_supported method."""
        # User hasn't supported yet
        assert user.has_supported(kebutuhan.id) is False
        
        # Add support
        support = Dukungan(pengguna_id=user.id, kebutuhan_id=kebutuhan.id)
        db.session.add(support)
        db.session.commit()
        
        # Now user has supported
        assert user.has_supported(kebutuhan.id) is True
    
    def test_user_relationships(self, db, user):
        """Test user relationship properties."""
        # Create related objects
        project = Project(
            judul='User Project',
            deskripsi='Test',
            pengguna_id=user.id,
            kategori_id=1
        )
        db.session.add(project)
        db.session.commit()
        
        assert user.projects.count() == 1
        assert user.projects.first() == project


class TestKategoriModel:
    """Test Kategori (Category) model."""
    
    def test_create_category(self, db):
        """Test category creation."""
        category = Kategori(
            nama='Test Category',
            deskripsi='Test description'
        )
        db.session.add(category)
        db.session.commit()
        
        assert category.id is not None
        assert category.nama == 'Test Category'
        assert category.deskripsi == 'Test description'
    
    def test_usage_count(self, db, categories, user):
        """Test category usage count."""
        category = categories[0]
        
        # Initially no usage
        assert category.usage_count == 0
        
        # Add a project
        project = Project(
            judul='Test',
            deskripsi='Test',
            pengguna_id=user.id,
            kategori_id=category.id
        )
        db.session.add(project)
        db.session.commit()
        
        assert category.usage_count == 1
    
    def test_can_delete(self, db, categories):
        """Test can_delete method."""
        category = categories[0]
        
        # Can delete when not in use
        assert category.can_delete() is True
        
        # Cannot delete when in use
        project = Project(
            judul='Test',
            deskripsi='Test',
            pengguna_id=1,
            kategori_id=category.id
        )
        db.session.add(project)
        db.session.commit()
        
        assert category.can_delete() is False


class TestProjectModel:
    """Test Project model."""
    
    def test_create_project(self, db, user, categories):
        """Test project creation."""
        project = Project(
            judul='New Project',
            deskripsi='Project description',
            pengguna_id=user.id,
            kategori_id=categories[0].id
        )
        db.session.add(project)
        db.session.commit()
        
        assert project.id is not None
        assert project.judul == 'New Project'
        assert project.status == 'Aktif'  # Default status
        assert project.view_count == 0
    
    def test_total_support(self, db, project, kebutuhan):
        """Test total support calculation."""
        # Initially no support
        assert project.total_support == 0
        
        # Add supports to kebutuhan
        for i in range(3):
            user = Pengguna(
                username=f'user{i}',
                email=f'user{i}@test.com',
                nama=f'User {i}'
            )
            db.session.add(user)
            db.session.commit()
            
            support = Dukungan(
                pengguna_id=user.id,
                kebutuhan_id=kebutuhan.id
            )
            db.session.add(support)
        
        db.session.commit()
        
        # Should have 3 supports total
        assert project.total_support == 3
    
    def test_completion_percentage(self, db, project, user, categories):
        """Test project completion percentage."""
        # No kebutuhan = 0%
        assert project.completion_percentage == 0
        
        # Add kebutuhan
        for i, status in enumerate(['Diajukan', 'Diproses', 'Selesai']):
            k = Kebutuhan(
                judul=f'Kebutuhan {i}',
                deskripsi='Test',
                pengguna_id=user.id,
                project_id=project.id,
                kategori_id=categories[0].id,
                status=status
            )
            db.session.add(k)
        
        db.session.commit()
        
        # 1 completed out of 3 = 33%
        assert project.completion_percentage == 33
    
    def test_increment_views(self, db, project):
        """Test view count increment."""
        initial_views = project.view_count
        project.increment_views()
        
        assert project.view_count == initial_views + 1
    
    def test_can_edit(self, db, project, user, admin_user):
        """Test can_edit permission."""
        # Owner can edit
        assert project.can_edit(user) is True
        
        # Admin can edit
        assert project.can_edit(admin_user) is True
        
        # Other user cannot edit
        other_user = Pengguna(
            username='other',
            email='other@test.com',
            nama='Other'
        )
        db.session.add(other_user)
        db.session.commit()
        
        assert project.can_edit(other_user) is False


class TestKebutuhanModel:
    """Test Kebutuhan model."""
    
    def test_create_kebutuhan(self, db, user, project, categories):
        """Test kebutuhan creation."""
        kebutuhan = Kebutuhan(
            judul='New Kebutuhan',
            deskripsi='Description',
            pengguna_id=user.id,
            project_id=project.id,
            kategori_id=categories[0].id,
            prioritas='Tinggi'
        )
        db.session.add(kebutuhan)
        db.session.commit()
        
        assert kebutuhan.id is not None
        assert kebutuhan.status == 'Diajukan'  # Default
        assert kebutuhan.prioritas == 'Tinggi'
        assert kebutuhan.view_count == 0
    
    def test_jumlah_dukungan(self, db, kebutuhan):
        """Test support count property."""
        assert kebutuhan.jumlah_dukungan == 0
        
        # Add support
        user = Pengguna(username='sup1', email='sup1@test.com', nama='Sup1')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()
        
        support = Dukungan(pengguna_id=user.id, kebutuhan_id=kebutuhan.id)
        db.session.add(support)
        db.session.commit()
        
        assert kebutuhan.jumlah_dukungan == 1
    
    def test_jumlah_komentar(self, db, kebutuhan, user):
        """Test comment count property."""
        assert kebutuhan.jumlah_komentar == 0
        
        # Add comments
        for i in range(3):
            comment = Komentar(
                isi=f'Comment {i}',
                pengguna_id=user.id,
                kebutuhan_id=kebutuhan.id
            )
            db.session.add(comment)
        
        db.session.commit()
        assert kebutuhan.jumlah_komentar == 3
    
    def test_update_status(self, db, kebutuhan, user):
        """Test status update with tracking."""
        # Update to Diproses
        kebutuhan.update_status('Diproses', user.id)
        
        assert kebutuhan.status == 'Diproses'
        assert kebutuhan.processed_at is not None
        assert kebutuhan.processed_by == user.id
        
        # Update to Selesai
        kebutuhan.update_status('Selesai')
        
        assert kebutuhan.status == 'Selesai'
        assert kebutuhan.completed_at is not None


class TestKomentarModel:
    """Test Komentar (Comment) model."""
    
    def test_create_comment(self, db, user, kebutuhan):
        """Test comment creation."""
        comment = Komentar(
            isi='Test comment',
            pengguna_id=user.id,
            kebutuhan_id=kebutuhan.id
        )
        db.session.add(comment)
        db.session.commit()
        
        assert comment.id is not None
        assert comment.isi == 'Test comment'
        assert comment.is_edited is False
    
    def test_threaded_comments(self, db, user, kebutuhan):
        """Test comment threading."""
        # Create parent comment
        parent = Komentar(
            isi='Parent comment',
            pengguna_id=user.id,
            kebutuhan_id=kebutuhan.id
        )
        db.session.add(parent)
        db.session.commit()
        
        # Create child comment
        child = Komentar(
            isi='Child comment',
            pengguna_id=user.id,
            kebutuhan_id=kebutuhan.id,
            parent_id=parent.id
        )
        db.session.add(child)
        db.session.commit()
        
        assert child.parent == parent
        assert parent.replies.first() == child
    
    def test_can_edit(self, db, user, kebutuhan):
        """Test comment edit permissions."""
        comment = Komentar(
            isi='Test',
            pengguna_id=user.id,
            kebutuhan_id=kebutuhan.id
        )
        db.session.add(comment)
        db.session.commit()
        
        # Owner can edit within time limit
        assert comment.can_edit(user) is True
        
        # Simulate time passing (more than 15 minutes)
        comment.timestamp = datetime.utcnow() - timedelta(minutes=16)
        db.session.commit()
        
        # Cannot edit after time limit
        assert comment.can_edit(user) is False
        
        # Other user cannot edit
        other = Pengguna(username='other', email='other@test.com', nama='Other')
        db.session.add(other)
        db.session.commit()
        
        assert comment.can_edit(other) is False


class TestDukunganModel:
    """Test Dukungan (Support) model."""
    
    def test_create_support(self, db, user, kebutuhan):
        """Test support creation."""
        support = Dukungan(
            pengguna_id=user.id,
            kebutuhan_id=kebutuhan.id
        )
        db.session.add(support)
        db.session.commit()
        
        assert support.id is not None
        assert support.pengguna_id == user.id
        assert support.kebutuhan_id == kebutuhan.id
    
    def test_unique_constraint(self, db, user, kebutuhan):
        """Test unique constraint on user-kebutuhan pair."""
        # Create first support
        support1 = Dukungan(
            pengguna_id=user.id,
            kebutuhan_id=kebutuhan.id
        )
        db.session.add(support1)
        db.session.commit()
        
        # Try to create duplicate
        support2 = Dukungan(
            pengguna_id=user.id,
            kebutuhan_id=kebutuhan.id
        )
        db.session.add(support2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            db.session.commit()


class TestNotificationModel:
    """Test Notification model."""
    
    def test_create_notification(self, db, user):
        """Test notification creation."""
        notification = Notification(
            user_id=user.id,
            type='comment',
            title='New Comment',
            message='Someone commented on your kebutuhan',
            link='/kebutuhan/1'
        )
        db.session.add(notification)
        db.session.commit()
        
        assert notification.id is not None
        assert notification.is_read is False
        assert notification.type == 'comment'