import os
from flask import render_template, flash, redirect, url_for, request, abort
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from app import app, db
from app.forms import LoginForm, RegisterForm, ProjectForm, KebutuhanForm, KomentarForm
from app.database.models import (
    Pengguna,
    Kategori,
    Project,
    Kebutuhan,
    Komentar,
    Dukungan,
)


# Konfigurasi upload
UPLOAD_FOLDER = os.path.join(app.root_path, "static/uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

# Pastikan direktori upload ada
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# Fungsi untuk memeriksa file yang diizinkan
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# Fungsi untuk menyimpan file
def save_file(file, destination_type, id=None):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Buat nama file unik
        unique_filename = (
            f"{destination_type}_{id}_{filename}"
            if id
            else f"{destination_type}_{filename}"
        )
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(filepath)
        return f"/static/uploads/{unique_filename}"
    return None


@app.route("/")
@app.route("/beranda")
def beranda():
    # Ambil beberapa project terbaru untuk ditampilkan di homepage
    projects = Project.query.order_by(Project.timestamp.desc()).limit(6).all()
    return render_template("index.html", title="Beranda", projects=projects)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("beranda"))
    form = LoginForm()
    if form.validate_on_submit():
        user = Pengguna.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Username atau password tidak valid")
            return redirect(url_for("login"))
        login_user(user)
        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("beranda")
        return redirect(next_page)
    return render_template("login.html", title="Login", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("beranda"))


@app.route("/daftar", methods=["GET", "POST"])
def daftar():
    if current_user.is_authenticated:
        return redirect(url_for("beranda"))
    form = RegisterForm()
    if form.validate_on_submit():
        user = Pengguna(
            username=form.username.data, email=form.email.data, nama=form.nama.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Selamat! Anda telah berhasil mendaftar.")
        return redirect(url_for("login"))
    return render_template("daftar.html", title="Daftar", form=form)


# Routes untuk Project
@app.route("/project")
def daftar_project():
    halaman = request.args.get("halaman", 1, type=int)
    per_halaman = 12
    projects = Project.query.order_by(Project.timestamp.desc()).paginate(
        page=halaman, per_page=per_halaman, error_out=False
    )
    next_url = (
        url_for("daftar_project", halaman=projects.next_num)
        if projects.has_next
        else None
    )
    prev_url = (
        url_for("daftar_project", halaman=projects.prev_num)
        if projects.has_prev
        else None
    )
    return render_template(
        "daftar_project.html",
        title="Daftar Project",
        projects=projects.items,
        next_url=next_url,
        prev_url=prev_url,
    )


@app.route("/project/buat", methods=["GET", "POST"])
@login_required
def buat_project():
    form = ProjectForm()
    if form.validate_on_submit():
        project = Project(
            judul=form.judul.data,
            deskripsi=form.deskripsi.data,
            pemilik=current_user,
            kategori_id=form.kategori.data,
        )

        # Proses upload gambar
        if form.gambar.data:
            gambar_url = save_file(form.gambar.data, "project")
            if gambar_url:
                project.gambar_url = gambar_url

        db.session.add(project)
        db.session.commit()

        flash("Project Anda telah berhasil dibuat!")
        return redirect(url_for("detail_project", id=project.id))
    return render_template("buat_project.html", title="Buat Project Baru", form=form)


@app.route("/project/<int:id>")
def detail_project(id):
    project = Project.query.get_or_404(id)
    kebutuhan = (
        Kebutuhan.query.filter_by(project_id=project.id)
        .order_by(Kebutuhan.timestamp.desc())
        .all()
    )
    return render_template(
        "detail_project.html", title=project.judul, project=project, kebutuhan=kebutuhan
    )


@app.route("/project/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_project(id):
    project = Project.query.get_or_404(id)
    if project.pengguna_id != current_user.id:
        abort(403)
    form = ProjectForm()
    if form.validate_on_submit():
        project.judul = form.judul.data
        project.deskripsi = form.deskripsi.data
        project.kategori_id = form.kategori.data

        # Proses upload gambar
        if form.gambar.data:
            gambar_url = save_file(form.gambar.data, "project", project.id)
            if gambar_url:
                project.gambar_url = gambar_url

        db.session.commit()
        flash("Project Anda telah berhasil diperbarui!")
        return redirect(url_for("detail_project", id=project.id))
    elif request.method == "GET":
        form.judul.data = project.judul
        form.deskripsi.data = project.deskripsi
        form.kategori.data = project.kategori_id
    return render_template(
        "edit_project.html", title="Edit Project", form=form, project=project
    )


# Routes untuk Kebutuhan
@app.route("/project/<int:project_id>/ajukan", methods=["GET", "POST"])
@login_required
def ajukan(project_id):
    project = Project.query.get_or_404(project_id)
    form = KebutuhanForm()

    if form.validate_on_submit():
        kebutuhan = Kebutuhan(
            judul=form.judul.data,
            deskripsi=form.deskripsi.data,
            pengaju=current_user,
            kategori_id=form.kategori.data,
            project_id=project_id,
            prioritas=form.prioritas.data,
        )

        # Proses upload gambar
        if form.gambar.data:
            gambar_url = save_file(form.gambar.data, "kebutuhan")
            if gambar_url:
                kebutuhan.gambar_url = gambar_url

        db.session.add(kebutuhan)
        db.session.commit()
        flash("Kebutuhan Anda telah berhasil diajukan!")
        return redirect(url_for("detail_project", id=project_id))

    return render_template(
        "ajukan.html", title="Ajukan Kebutuhan", form=form, project=project
    )


@app.route("/project/<int:project_id>/kebutuhan/<int:id>", methods=["GET", "POST"])
def detail_kebutuhan(project_id, id):
    project = Project.query.get_or_404(project_id)
    kebutuhan = Kebutuhan.query.get_or_404(id)

    # Pastikan kebutuhan memang milik project ini
    if kebutuhan.project_id != project.id:
        abort(404)

    form = KomentarForm()
    if form.validate_on_submit():
        if current_user.is_authenticated:
            komentar = Komentar(
                isi=form.isi.data, kebutuhan_terkait=kebutuhan, penulis=current_user
            )

            # Proses upload gambar untuk komentar
            if form.gambar.data:
                gambar_url = save_file(form.gambar.data, "komentar")
                if gambar_url:
                    komentar.gambar_url = gambar_url

            db.session.add(komentar)
            db.session.commit()
            flash("Komentar Anda telah ditambahkan!")
            return redirect(url_for("detail_kebutuhan", project_id=project_id, id=id))
        else:
            flash("Anda harus login untuk berkomentar.")
            return redirect(url_for("login"))

    komentar = kebutuhan.komentar.order_by(Komentar.timestamp.asc()).all()

    # Cek apakah user sudah memberikan dukungan
    user_supported = False
    if current_user.is_authenticated:
        user_supported = current_user.has_supported(kebutuhan.id)

    return render_template(
        "detail.html",
        title=kebutuhan.judul,
        project=project,
        kebutuhan=kebutuhan,
        komentar=komentar,
        form=form,
        user_supported=user_supported,
    )


@app.route("/project/<int:project_id>/kebutuhan/<int:id>/dukungan")
@login_required
def dukungan(project_id, id):
    kebutuhan = Kebutuhan.query.get_or_404(id)

    # Pastikan kebutuhan memang milik project ini
    if kebutuhan.project_id != project_id:
        abort(404)

    # Cek apakah user adalah pembuat kebutuhan
    if kebutuhan.pengguna_id == current_user.id:
        flash("Anda tidak dapat mendukung kebutuhan yang Anda ajukan sendiri.")
        return redirect(url_for("detail_kebutuhan", project_id=project_id, id=id))

    # Cek apakah user sudah mendukung kebutuhan ini
    if current_user.has_supported(id):
        flash("Anda sudah memberikan dukungan untuk kebutuhan ini.")
        return redirect(url_for("detail_kebutuhan", project_id=project_id, id=id))

    # Tambahkan dukungan
    dukungan = Dukungan(pendukung=current_user, kebutuhan_didukung=kebutuhan)
    db.session.add(dukungan)
    db.session.commit()
    flash("Dukungan Anda telah diterima!")
    return redirect(url_for("detail_kebutuhan", project_id=project_id, id=id))


@app.route("/dukungan_saya")
@login_required
def dukungan_saya():
    halaman = request.args.get("halaman", 1, type=int)
    per_halaman = 10

    # Query kebutuhan yang didukung oleh user
    dukungan_query = Dukungan.query.filter_by(pengguna_id=current_user.id)
    dukungan_paginate = dukungan_query.paginate(
        page=halaman, per_page=per_halaman, error_out=False
    )

    next_url = (
        url_for("dukungan_saya", halaman=dukungan_paginate.next_num)
        if dukungan_paginate.has_next
        else None
    )
    prev_url = (
        url_for("dukungan_saya", halaman=dukungan_paginate.prev_num)
        if dukungan_paginate.has_prev
        else None
    )

    return render_template(
        "dukungan_saya.html",
        title="Dukungan Saya",
        dukungan=dukungan_paginate.items,
        next_url=next_url,
        prev_url=prev_url,
    )


@app.route("/kebutuhan_saya")
@login_required
def kebutuhan_saya():
    halaman = request.args.get("halaman", 1, type=int)
    per_halaman = 10

    # Query kebutuhan yang diajukan oleh user
    kebutuhan = (
        Kebutuhan.query.filter_by(pengguna_id=current_user.id)
        .order_by(Kebutuhan.timestamp.desc())
        .paginate(page=halaman, per_page=per_halaman, error_out=False)
    )

    next_url = (
        url_for("kebutuhan_saya", halaman=kebutuhan.next_num)
        if kebutuhan.has_next
        else None
    )
    prev_url = (
        url_for("kebutuhan_saya", halaman=kebutuhan.prev_num)
        if kebutuhan.has_prev
        else None
    )

    return render_template(
        "kebutuhan_saya.html",
        title="Kebutuhan Saya",
        kebutuhan=kebutuhan.items,
        next_url=next_url,
        prev_url=prev_url,
    )


@app.route("/project_saya")
@login_required
def project_saya():
    halaman = request.args.get("halaman", 1, type=int)
    per_halaman = 10

    # Query project yang diajukan oleh user
    projects = (
        Project.query.filter_by(pengguna_id=current_user.id)
        .order_by(Project.timestamp.desc())
        .paginate(page=halaman, per_page=per_halaman, error_out=False)
    )

    next_url = (
        url_for("project_saya", halaman=projects.next_num)
        if projects.has_next
        else None
    )
    prev_url = (
        url_for("project_saya", halaman=projects.prev_num)
        if projects.has_prev
        else None
    )

    return render_template(
        "project_saya.html",
        title="Project Saya",
        projects=projects.items,
        next_url=next_url,
        prev_url=prev_url,
    )


@app.route("/tentang")
def tentang():
    return render_template("tentang.html", title="Tentang KomuniTech")


# Admin route untuk menambahkan kategori (biasanya akan ada proteksi admin)
@app.route("/tambah_kategori", methods=["GET", "POST"])
@login_required
def tambah_kategori():
    if request.method == "POST":
        nama = request.form.get("nama")
        deskripsi = request.form.get("deskripsi")
        if nama:
            kategori = Kategori(nama=nama, deskripsi=deskripsi)
            db.session.add(kategori)
            db.session.commit()
            flash("Kategori baru telah ditambahkan!")
            return redirect(url_for("tambah_kategori"))
    kategori = Kategori.query.all()
    return render_template(
        "tambah_kategori.html", title="Tambah Kategori", kategori=kategori
    )


def buat_kategori_dasar():
    kategori_default = [
        (
            "Infrastruktur",
            "Kebutuhan terkait infrastruktur fisik seperti jalan, air, dan listrik",
        ),
        ("Pendidikan", "Kebutuhan terkait pendidikan dan pelatihan"),
        ("Kesehatan", "Kebutuhan terkait layanan kesehatan"),
        ("Ekonomi", "Kebutuhan terkait pengembangan ekonomi dan bisnis"),
        ("Lingkungan", "Kebutuhan terkait pelestarian lingkungan"),
        ("Sosial", "Kebutuhan terkait masalah dan dukungan sosial"),
        ("Teknologi", "Kebutuhan terkait penerapan teknologi"),
        ("Lainnya", "Kebutuhan lain yang tidak termasuk dalam kategori di atas"),
    ]

    for nama, deskripsi in kategori_default:
        kategori = Kategori.query.filter_by(nama=nama).first()
        if not kategori:
            kategori = Kategori(nama=nama, deskripsi=deskripsi)
            db.session.add(kategori)

    db.session.commit()


with app.app_context():
    buat_kategori_dasar()
