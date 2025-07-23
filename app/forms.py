# app/forms.py - Complete Fixed Version
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import (
    StringField,
    TextAreaField,
    PasswordField,
    SelectField,
    SubmitField,
    BooleanField,
    HiddenField,
    IntegerField,
    EmailField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional, Regexp, URL
from app.database.models import Pengguna, Kategori
import re


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(message="Username harus diisi"), Length(min=3, max=64)])
    password = PasswordField("Password", validators=[DataRequired(message="Password harus diisi")])
    remember_me = BooleanField("Ingat Saya")
    submit = SubmitField("Masuk")


class RegisterForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            DataRequired(message="Username harus diisi"),
            Length(min=3, max=64),
            Regexp("^[A-Za-z0-9_]+$", message="Username hanya boleh mengandung huruf, angka, dan underscore"),
        ],
    )
    email = EmailField(
        "Email", validators=[DataRequired(message="Email harus diisi"), Email(message="Format email tidak valid")]
    )
    nama = StringField(
        "Nama Lengkap", validators=[DataRequired(message="Nama lengkap harus diisi"), Length(min=3, max=120)]
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(message="Password harus diisi"), Length(min=6, message="Password minimal 6 karakter")],
    )
    password2 = PasswordField(
        "Ulangi Password",
        validators=[
            DataRequired(message="Konfirmasi password harus diisi"),
            EqualTo("password", message="Password tidak cocok"),
        ],
    )
    submit = SubmitField("Daftar")

    def validate_username(self, username):
        user = Pengguna.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError("Username ini sudah digunakan. Silakan gunakan username lain.")

    def validate_email(self, email):
        user = Pengguna.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError("Email ini sudah terdaftar. Silakan gunakan email lain.")

    def validate_password(self, password):
        # Additional password strength validation
        if not re.search(r"[A-Za-z]", password.data):
            raise ValidationError("Password harus mengandung minimal satu huruf.")
        if not re.search(r"[0-9]", password.data):
            raise ValidationError("Password harus mengandung minimal satu angka.")


class ProjectForm(FlaskForm):
    judul = StringField(
        "Judul Project", validators=[DataRequired(message="Judul project harus diisi"), Length(min=5, max=140)]
    )
    kategori = SelectField("Kategori", coerce=int, validators=[DataRequired(message="Kategori harus dipilih")])
    deskripsi = TextAreaField(
        "Deskripsi Project",
        validators=[DataRequired(message="Deskripsi project harus diisi"), Length(min=10, max=5000)],
    )
    gambar = FileField(
        "Gambar Project (Opsional)",
        validators=[FileAllowed(["jpg", "png", "jpeg", "gif"], "Hanya file gambar yang diperbolehkan")],
    )
    delete_gambar = BooleanField("Hapus Gambar")
    submit = SubmitField("Simpan Project")
    edit = SubmitField("Simpan Project")

    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)
        self.kategori.choices = [(0, "-- Pilih Kategori --")] + [
            (k.id, k.nama) for k in Kategori.query.order_by(Kategori.nama).all()
        ]

    def validate_kategori(self, kategori):
        if kategori.data == 0:
            raise ValidationError("Silakan pilih kategori yang valid.")


class KebutuhanForm(FlaskForm):
    judul = StringField(
        "Judul Kebutuhan", validators=[DataRequired(message="Judul kebutuhan harus diisi"), Length(min=5, max=140)]
    )
    kategori = SelectField("Kategori", coerce=int, validators=[DataRequired(message="Kategori harus dipilih")])
    deskripsi = TextAreaField(
        "Deskripsi Kebutuhan",
        validators=[DataRequired(message="Deskripsi kebutuhan harus diisi"), Length(min=10, max=5000)],
    )
    prioritas = SelectField(
        "Prioritas",
        choices=[("Rendah", "Rendah"), ("Sedang", "Sedang"), ("Tinggi", "Tinggi")],
        validators=[DataRequired()],
    )
    gambar = FileField(
        "Gambar Kebutuhan (Opsional)",
        validators=[FileAllowed(["jpg", "png", "jpeg", "gif"], "Hanya file gambar yang diperbolehkan")],
    )
    delete_gambar = BooleanField("Hapus Gambar")
    submit = SubmitField("Simpan Kebutuhan")
    edit = SubmitField("Simpan Kebutuhan")

    def __init__(self, *args, **kwargs):
        super(KebutuhanForm, self).__init__(*args, **kwargs)
        self.kategori.choices = [(0, "-- Pilih Kategori --")] + [
            (k.id, k.nama) for k in Kategori.query.order_by(Kategori.nama).all()
        ]

    def validate_kategori(self, kategori):
        if kategori.data == 0:
            raise ValidationError("Silakan pilih kategori yang valid.")


class KomentarForm(FlaskForm):
    isi = TextAreaField(
        "Komentar", validators=[DataRequired(message="Komentar tidak boleh kosong"), Length(min=2, max=1000)]
    )
    gambar = FileField(
        "Tambahkan Gambar (Opsional)",
        validators=[FileAllowed(["jpg", "png", "jpeg", "gif"], "Hanya file gambar yang diperbolehkan")],
    )
    parent_id = HiddenField()  # For threaded comments
    submit = SubmitField("Kirim Komentar")


class KategoriForm(FlaskForm):
    nama = StringField("Nama", validators=[DataRequired(message="Nama kategori harus diisi"), Length(min=2, max=64)])
    deskripsi = TextAreaField(
        "Deskripsi", validators=[DataRequired(message="Deskripsi kategori harus diisi"), Length(min=10, max=200)]
    )
    submit = SubmitField("Tambah Kategori")

    def validate_nama(self, nama):
        # Check for duplicate category names
        existing = Kategori.query.filter_by(nama=nama.data).first()
        if existing:
            raise ValidationError("Kategori dengan nama ini sudah ada.")


class UserProfileForm(FlaskForm):
    nama = StringField(
        "Nama Lengkap", validators=[DataRequired(message="Nama lengkap harus diisi"), Length(min=3, max=120)]
    )
    bio = TextAreaField("Bio", validators=[Optional(), Length(max=500, message="Bio maksimal 500 karakter")])
    avatar = FileField(
        "Foto Profil", validators=[FileAllowed(["jpg", "png", "jpeg", "gif"], "Hanya file gambar yang diperbolehkan")]
    )
    delete_avatar = BooleanField("Hapus Foto Profil")
    submit = SubmitField("Simpan Profil")


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField("Password Lama", validators=[DataRequired(message="Password lama harus diisi")])
    new_password = PasswordField(
        "Password Baru",
        validators=[
            DataRequired(message="Password baru harus diisi"),
            Length(min=6, message="Password minimal 6 karakter"),
        ],
    )
    new_password2 = PasswordField(
        "Konfirmasi Password Baru",
        validators=[
            DataRequired(message="Konfirmasi password harus diisi"),
            EqualTo("new_password", message="Password tidak cocok"),
        ],
    )
    submit = SubmitField("Ubah Password")


class PasswordResetRequestForm(FlaskForm):
    email = EmailField(
        "Email", validators=[DataRequired(message="Email harus diisi"), Email(message="Format email tidak valid")]
    )
    submit = SubmitField("Reset Password")


class PasswordResetForm(FlaskForm):
    password = PasswordField(
        "Password Baru",
        validators=[DataRequired(message="Password harus diisi"), Length(min=6, message="Password minimal 6 karakter")],
    )
    password2 = PasswordField(
        "Konfirmasi Password",
        validators=[
            DataRequired(message="Konfirmasi password harus diisi"),
            EqualTo("password", message="Password tidak cocok"),
        ],
    )
    submit = SubmitField("Reset Password")


class SearchForm(FlaskForm):
    query = StringField(
        "Cari",
        validators=[
            DataRequired(message="Kata kunci pencarian harus diisi"),
            Length(min=2, message="Kata kunci minimal 2 karakter"),
        ],
    )
    category = SelectField("Kategori", coerce=int)
    search_type = SelectField("Tipe", choices=[("all", "Semua"), ("projects", "Project"), ("kebutuhan", "Kebutuhan")])
    submit = SubmitField("Cari")

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.category.choices = [(0, "Semua Kategori")] + [
            (k.id, k.nama) for k in Kategori.query.order_by(Kategori.nama).all()
        ]


class StatusUpdateForm(FlaskForm):
    status = SelectField("Status", validators=[DataRequired()])
    reason = TextAreaField("Alasan (Opsional)", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Update Status")

    def __init__(self, entity_type="project", *args, **kwargs):
        super(StatusUpdateForm, self).__init__(*args, **kwargs)
        if entity_type == "project":
            self.status.choices = [("Aktif", "Aktif"), ("Selesai", "Selesai"), ("Ditutup", "Ditutup")]
        else:  # kebutuhan
            self.status.choices = [
                ("Diajukan", "Diajukan"),
                ("Diproses", "Diproses"),
                ("Selesai", "Selesai"),
                ("Ditolak", "Ditolak"),
            ]


class CollaboratorForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(message="Username harus diisi")])
    role = SelectField("Role", choices=[("Contributor", "Contributor"), ("Moderator", "Moderator")])
    submit = SubmitField("Tambah Kolaborator")

    def validate_username(self, username):
        user = Pengguna.query.filter_by(username=username.data).first()
        if not user:
            raise ValidationError("Username tidak ditemukan.")


class BulkActionForm(FlaskForm):
    action = SelectField(
        "Aksi",
        choices=[
            ("", "-- Pilih Aksi --"),
            ("delete", "Hapus"),
            ("approve", "Setujui"),
            ("reject", "Tolak"),
            ("archive", "Arsipkan"),
        ],
    )
    items = HiddenField()  # JSON array of IDs
    confirm = BooleanField("Saya yakin dengan tindakan ini")
    submit = SubmitField("Lakukan Aksi")

    def validate_action(self, action):
        if not action.data:
            raise ValidationError("Pilih aksi yang akan dilakukan.")

    def validate_confirm(self, confirm):
        if not confirm.data:
            raise ValidationError("Anda harus mencentang konfirmasi.")


class AdminUserForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(message="Username harus diisi"), Length(min=3, max=64)])
    email = EmailField(
        "Email", validators=[DataRequired(message="Email harus diisi"), Email(message="Format email tidak valid")]
    )
    nama = StringField(
        "Nama Lengkap", validators=[DataRequired(message="Nama lengkap harus diisi"), Length(min=3, max=120)]
    )
    role = SelectField("Role", choices=[("Regular", "Regular"), ("Developer", "Developer"), ("Admin", "Admin")])
    is_active = BooleanField("Aktif")
    email_verified = BooleanField("Email Terverifikasi")
    new_password = PasswordField(
        "Password Baru (kosongkan jika tidak diubah)",
        validators=[Optional(), Length(min=6, message="Password minimal 6 karakter")],
    )
    submit = SubmitField("Simpan")
