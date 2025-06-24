# app/database/models.py - Complete Fixed Version
from datetime import datetime
from sqlalchemy import func
from .base import db, login_man
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class Pengguna(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    nama = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(200))
    # Role: Regular, Admin, Developer
    role = db.Column(db.String(20), default="Regular", nullable=False)
    # Profile fields
    bio = db.Column(db.Text)
    avatar_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=func.now())
    last_seen = db.Column(db.DateTime, default=func.now())
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    
    # Relationships
    projects = db.relationship("Project", backref="pemilik", lazy="dynamic", cascade="all, delete-orphan")
    kebutuhan = db.relationship("Kebutuhan", backref="pengaju", lazy="dynamic", cascade="all, delete-orphan")
    komentar = db.relationship("Komentar", backref="penulis", lazy="dynamic", cascade="all, delete-orphan")
    dukungan = db.relationship("Dukungan", backref="pendukung", lazy="dynamic", cascade="all, delete-orphan")
    notifications = db.relationship("Notification", backref="user", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Pengguna {self.username}>"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_supported(self, kebutuhan_id):
        return (
            Dukungan.query.filter_by(
                pengguna_id=self.id, kebutuhan_id=kebutuhan_id
            ).first()
            is not None
        )
    
    @property
    def is_admin(self):
        return self.role == "Admin"
    
    @property
    def is_developer(self):
        return self.role == "Developer"
    
    def update_last_seen(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()
    
    def get_notifications(self, unread_only=False):
        query = self.notifications
        if unread_only:
            query = query.filter_by(is_read=False)
        return query.order_by(Notification.created_at.desc())
    
    def mark_notifications_read(self):
        self.notifications.filter_by(is_read=False).update({'is_read': True})
        db.session.commit()


@login_man.user_loader
def load_user(id):
    return Pengguna.query.get(int(id))


class Kategori(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(64), index=True, unique=True, nullable=False)
    deskripsi = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    kebutuhan = db.relationship("Kebutuhan", backref="kategori_kebutuhan", lazy="dynamic")
    projects = db.relationship("Project", backref="kategori_project", lazy="dynamic")

    def __repr__(self):
        return f"<Kategori {self.nama}>"
    
    @property
    def usage_count(self):
        return self.projects.count() + self.kebutuhan.count()
    
    def can_delete(self):
        return self.usage_count == 0


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    judul = db.Column(db.String(140), nullable=False)
    deskripsi = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    pengguna_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    kategori_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    # Status: Aktif, Selesai, Ditutup
    status = db.Column(db.String(20), default="Aktif")
    gambar_url = db.Column(db.String(200))
    view_count = db.Column(db.Integer, default=0)
    
    # Relationships
    kebutuhan = db.relationship(
        "Kebutuhan", backref="project", lazy="dynamic", cascade="all, delete-orphan"
    )
    collaborators = db.relationship(
        "ProjectCollaborator", backref="project", lazy="dynamic", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Project {self.judul}>"
    
    @property
    def total_support(self):
        return db.session.query(func.sum(Kebutuhan.jumlah_dukungan)).filter(
            Kebutuhan.project_id == self.id
        ).scalar() or 0
    
    @property
    def completion_percentage(self):
        total = self.kebutuhan.count()
        if total == 0:
            return 0
        completed = self.kebutuhan.filter_by(status="Selesai").count()
        return int((completed / total) * 100)
    
    def increment_views(self):
        self.view_count += 1
        db.session.add(self)
        db.session.commit()
    
    def is_collaborator(self, user_id):
        return self.collaborators.filter_by(user_id=user_id).first() is not None
    
    def can_edit(self, user):
        return user.id == self.pengguna_id or user.is_admin or self.is_collaborator(user.id)


class Kebutuhan(db.Model):
    __tablename__ = "requirements"

    id = db.Column(db.Integer, primary_key=True)
    judul = db.Column(db.String(140), nullable=False)
    deskripsi = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    pengguna_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    kategori_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    # Status: Diajukan, Diproses, Selesai, Ditolak
    status = db.Column(db.String(20), default="Diajukan")
    # Prioritas: Rendah, Sedang, Tinggi
    prioritas = db.Column(db.String(20), default="Sedang")
    gambar_url = db.Column(db.String(200))
    view_count = db.Column(db.Integer, default=0)
    # Tracking fields
    processed_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    processed_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    
    # Relationships
    komentar = db.relationship(
        "Komentar",
        backref="kebutuhan_terkait",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    dukungan = db.relationship(
        "Dukungan",
        backref="kebutuhan_didukung",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Kebutuhan {self.judul}>"

    @property
    def jumlah_dukungan(self):
        return self.dukungan.count()
    
    @property
    def jumlah_komentar(self):
        return self.komentar.count()
    
    def increment_views(self):
        self.view_count += 1
        db.session.add(self)
        db.session.commit()
    
    def update_status(self, new_status, user_id=None):
        old_status = self.status
        self.status = new_status
        
        if new_status == "Diproses" and old_status == "Diajukan":
            self.processed_at = datetime.utcnow()
            self.processed_by = user_id
        elif new_status == "Selesai":
            self.completed_at = datetime.utcnow()
        
        db.session.add(self)
        db.session.commit()
    
    def can_edit(self, user):
        return user.id == self.pengguna_id or user.is_admin


class Komentar(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    isi = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    pengguna_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    kebutuhan_id = db.Column(db.Integer, db.ForeignKey("requirements.id"), nullable=False)
    gambar_url = db.Column(db.String(200))
    is_edited = db.Column(db.Boolean, default=False)
    
    # For threaded comments
    parent_id = db.Column(db.Integer, db.ForeignKey("comments.id"))
    replies = db.relationship(
        "Komentar", backref=db.backref("parent", remote_side=[id]),
        lazy="dynamic", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Komentar {self.id}>"
    
    def can_edit(self, user):
        # Allow edit within 15 minutes of posting
        time_limit = datetime.utcnow() - self.timestamp
        return user.id == self.pengguna_id and time_limit.total_seconds() < 900
    
    def can_delete(self, user):
        return user.id == self.pengguna_id or user.is_admin


class Dukungan(db.Model):
    __tablename__ = "supports"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=func.now())
    pengguna_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    kebutuhan_id = db.Column(db.Integer, db.ForeignKey("requirements.id"), nullable=False)
    
    # Unique constraint to prevent duplicate supports
    __table_args__ = (
        db.UniqueConstraint('pengguna_id', 'kebutuhan_id', name='unique_user_requirement_support'),
    )

    def __repr__(self):
        return f"<Dukungan {self.id}>"


class Media(db.Model):
    __tablename__ = "medias"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    filetype = db.Column(db.String(50), nullable=False)
    filesize = db.Column(db.Integer)  # in bytes
    timestamp = db.Column(db.DateTime, index=True, default=func.now())
    pengguna_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=True)
    kebutuhan_id = db.Column(db.Integer, db.ForeignKey("requirements.id"), nullable=True)
    komentar_id = db.Column(db.Integer, db.ForeignKey("comments.id"), nullable=True)

    def __repr__(self):
        return f"<Media {self.filename}>"


class Notification(db.Model):
    __tablename__ = "notifications"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # comment, support, status_change, etc.
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text)
    link = db.Column(db.String(200))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=func.now())
    
    def __repr__(self):
        return f"<Notification {self.type} for {self.user_id}>"


class ProjectCollaborator(db.Model):
    __tablename__ = "project_collaborators"
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    role = db.Column(db.String(50), default="Contributor")  # Contributor, Moderator
    added_at = db.Column(db.DateTime, default=func.now())
    added_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('project_id', 'user_id', name='unique_project_collaborator'),
    )
    
    def __repr__(self):
        return f"<ProjectCollaborator {self.user_id} on {self.project_id}>"


class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50))  # project, kebutuhan, user, etc.
    entity_id = db.Column(db.Integer)
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=func.now())
    
    def __repr__(self):
        return f"<AuditLog {self.action} by {self.user_id}>"