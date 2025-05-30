from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField,
    TextAreaField,
    PasswordField,
    SelectField,
    SubmitField,
    BooleanField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.database.models import Pengguna, Kategori


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Masuk")


class RegisterForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=3, max=64)]
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    nama = StringField("Nama Lengkap", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    password2 = PasswordField(
        "Ulangi Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Daftar")

    def validate_username(self, username):
        user = Pengguna.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError(
                "Username ini sudah digunakan. Silakan gunakan username lain."
            )

    def validate_email(self, email):
        user = Pengguna.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(
                "Email ini sudah terdaftar. Silakan gunakan email lain."
            )


class ProjectForm(FlaskForm):
    judul = StringField(
        "Judul Project", validators=[DataRequired(), Length(min=5, max=140)]
    )
    kategori = SelectField("Kategori", coerce=int, validators=[DataRequired()])
    deskripsi = TextAreaField(
        "Deskripsi Project", validators=[DataRequired(), Length(min=10, max=5000)]
    )
    gambar = FileField(
        "Gambar Project (Opsional)",
        validators=[FileAllowed(["jpg", "png", "jpeg", "gif"])],
    )
    delete_gambar = BooleanField("Hapus Gambar")
    submit = SubmitField("Buat Project")
    edit = SubmitField("Ubah Project")

    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)
        self.kategori.choices = [
            (k.id, k.nama) for k in Kategori.query.order_by(Kategori.nama).all()
        ]


class KebutuhanForm(FlaskForm):
    judul = StringField(
        "Judul Kebutuhan", validators=[DataRequired(), Length(min=5, max=140)]
    )
    kategori = SelectField("Kategori", coerce=int, validators=[DataRequired()])
    deskripsi = TextAreaField(
        "Deskripsi Kebutuhan", validators=[DataRequired(), Length(min=10, max=5000)]
    )
    prioritas = SelectField(
        "Prioritas",
        choices=[("Rendah", "Rendah"), ("Sedang", "Sedang"), ("Tinggi", "Tinggi")],
        validators=[DataRequired()],
    )
    gambar = FileField(
        "Gambar Kebutuhan (Opsional)",
        validators=[FileAllowed(["jpg", "png", "jpeg", "gif"])],
    )
    submit = SubmitField("Ajukan Kebutuhan")

    def __init__(self, *args, **kwargs):
        super(KebutuhanForm, self).__init__(*args, **kwargs)
        self.kategori.choices = [
            (k.id, k.nama) for k in Kategori.query.order_by(Kategori.nama).all()
        ]


class KomentarForm(FlaskForm):
    isi = TextAreaField(
        "Komentar", validators=[DataRequired(), Length(min=2, max=1000)]
    )
    gambar = FileField(
        "Tambahkan Gambar (Opsional)",
        validators=[FileAllowed(["jpg", "png", "jpeg", "gif"])],
    )
    submit = SubmitField("Kirim Komentar")


class KategoriForm(FlaskForm):
    nama = TextAreaField("Nama", validators=[DataRequired(), Length(min=2, max=64)])
    deskripsi = TextAreaField(
        "Deskripsi", validators=[DataRequired(), Length(min=10, max=200)]
    )
    submit = SubmitField("Kirim Komentar")
