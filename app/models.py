from datetime import datetime
from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Pengguna(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    nama = db.Column(db.String(120))
    password_hash = db.Column(db.String(128))
    kebutuhan = db.relationship('Kebutuhan', backref='pengaju', lazy='dynamic')
    komentar = db.relationship('Komentar', backref='penulis', lazy='dynamic')
    
    def __repr__(self):
        return f'<Pengguna {self.username}>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login.user_loader
def load_user(id):
    return Pengguna.query.get(int(id))

class Kategori(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(64), index=True, unique=True)
    deskripsi = db.Column(db.String(200))
    kebutuhan = db.relationship('Kebutuhan', backref='kategori_kebutuhan', lazy='dynamic')
    
    def __repr__(self):
        return f'<Kategori {self.nama}>'

class Kebutuhan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    judul = db.Column(db.String(140))
    deskripsi = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    pengguna_id = db.Column(db.Integer, db.ForeignKey('pengguna.id'))
    kategori_id = db.Column(db.Integer, db.ForeignKey('kategori.id'))
    status = db.Column(db.String(20), default='Diajukan') # Status: Diajukan, Diproses, Selesai
    prioritas = db.Column(db.String(20), default='Sedang') # Prioritas: Rendah, Sedang, Tinggi
    jumlah_vote = db.Column(db.Integer, default=0)
    komentar = db.relationship('Komentar', backref='kebutuhan_terkait', lazy='dynamic')
    
    def __repr__(self):
        return f'<Kebutuhan {self.judul}>'

class Komentar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    isi = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    pengguna_id = db.Column(db.Integer, db.ForeignKey('pengguna.id'))
    kebutuhan_id = db.Column(db.Integer, db.ForeignKey('kebutuhan.id'))
    
    def __repr__(self):
        return f'<Komentar {self.id}>'