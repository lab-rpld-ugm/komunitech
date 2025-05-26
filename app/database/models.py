from sqlalchemy import func
from .base import db, login_man
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class Pengguna(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    nama = db.Column(db.String(120))
    password_hash = db.Column(db.String(128))
    # Role: Regular, Admin, Developer
    role = db.Column(db.Boolean, default="Regular", nullable=False)
    projects = db.relationship("Project", backref="pemilik", lazy="dynamic")
    kebutuhan = db.relationship("Kebutuhan", backref="pengaju", lazy="dynamic")
    komentar = db.relationship("Komentar", backref="penulis", lazy="dynamic")
    dukungan = db.relationship("Dukungan", backref="pendukung", lazy="dynamic")

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


@login_man.user_loader
def load_user(id):
    return Pengguna.query.get(int(id))


class Kategori(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(64), index=True, unique=True)
    deskripsi = db.Column(db.String(200))
    kebutuhan = db.relationship(
        "Kebutuhan", backref="kategori_kebutuhan", lazy="dynamic"
    )
    projects = db.relationship("Project", backref="kategori_project", lazy="dynamic")

    def __repr__(self):
        return f"<Kategori {self.nama}>"


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    judul = db.Column(db.String(140))
    deskripsi = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=func.now())
    pengguna_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    kategori_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    # Status: Aktif, Selesai, Ditutup
    status = db.Column(db.String(20), default="Aktif")
    gambar_url = db.Column(db.String(200))
    kebutuhan = db.relationship(
        "Kebutuhan", backref="project", lazy="dynamic", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Project {self.judul}>"


class Kebutuhan(db.Model):
    __tablename__ = "requirements"

    id = db.Column(db.Integer, primary_key=True)
    judul = db.Column(db.String(140))
    deskripsi = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=func.now())
    pengguna_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    kategori_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    # Status: Diajukan, Diproses, Selesai
    status = db.Column(db.String(20), default="Diajukan")
    # Prioritas: Rendah, Sedang, Tinggi
    prioritas = db.Column(db.String(20), default="Sedang")
    gambar_url = db.Column(db.String(200))
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


class Komentar(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    isi = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=func.now())
    pengguna_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    kebutuhan_id = db.Column(db.Integer, db.ForeignKey("requirements.id"))
    gambar_url = db.Column(db.String(200))

    def __repr__(self):
        return f"<Komentar {self.id}>"


class Dukungan(db.Model):
    __tablename__ = "supports"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=func.now())
    pengguna_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    kebutuhan_id = db.Column(db.Integer, db.ForeignKey("requirements.id"))

    def __repr__(self):
        return f"<Dukungan {self.id}>"


class Media(db.Model):
    __tablename__ = "medias"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200))
    filepath = db.Column(db.String(255))
    filetype = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, index=True, default=func.now())
    pengguna_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=True)
    kebutuhan_id = db.Column(
        db.Integer, db.ForeignKey("requirements.id"), nullable=True
    )

    def __repr__(self):
        return f"<Media {self.filename}>"
