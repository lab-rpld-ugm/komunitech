from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegisterForm, KebutuhanForm, KomentarForm
from app.models import Pengguna, Kategori, Kebutuhan, Komentar

@app.route('/')
@app.route('/beranda')
def beranda():
    return render_template('index.html', title='Beranda')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('beranda'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Pengguna.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Username atau password tidak valid')
            return redirect(url_for('login'))
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('beranda')
        return redirect(next_page)
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('beranda'))

@app.route('/daftar', methods=['GET', 'POST'])
def daftar():
    if current_user.is_authenticated:
        return redirect(url_for('beranda'))
    form = RegisterForm()
    if form.validate_on_submit():
        user = Pengguna(username=form.username.data, email=form.email.data, nama=form.nama.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Selamat! Anda telah berhasil mendaftar.')
        return redirect(url_for('login'))
    return render_template('daftar.html', title='Daftar', form=form)

@app.route('/ajukan', methods=['GET', 'POST'])
@login_required
def ajukan():
    form = KebutuhanForm()
    if form.validate_on_submit():
        kebutuhan = Kebutuhan(
            judul=form.judul.data,
            deskripsi=form.deskripsi.data,
            pengaju=current_user,
            kategori_id=form.kategori.data,
            prioritas=form.prioritas.data
        )
        db.session.add(kebutuhan)
        db.session.commit()
        flash('Kebutuhan Anda telah berhasil diajukan!')
        return redirect(url_for('daftar_kebutuhan'))
    return render_template('ajukan.html', title='Ajukan Kebutuhan', form=form)

@app.route('/daftar_kebutuhan')
def daftar_kebutuhan():
    halaman = request.args.get('halaman', 1, type=int)
    per_halaman = 10
    kebutuhan = Kebutuhan.query.order_by(Kebutuhan.timestamp.desc()).paginate(
        page=halaman, per_page=per_halaman, error_out=False)
    next_url = url_for('daftar_kebutuhan', halaman=kebutuhan.next_num) \
        if kebutuhan.has_next else None
    prev_url = url_for('daftar_kebutuhan', halaman=kebutuhan.prev_num) \
        if kebutuhan.has_prev else None
    return render_template('daftar_kebutuhan.html', title='Daftar Kebutuhan', 
                          kebutuhan=kebutuhan.items, next_url=next_url, prev_url=prev_url)

@app.route('/kebutuhan/<int:id>', methods=['GET', 'POST'])
def detail_kebutuhan(id):
    kebutuhan = Kebutuhan.query.get_or_404(id)
    form = KomentarForm()
    if form.validate_on_submit():
        if current_user.is_authenticated:
            komentar = Komentar(
                isi=form.isi.data,
                kebutuhan_terkait=kebutuhan,
                penulis=current_user
            )
            db.session.add(komentar)
            db.session.commit()
            flash('Komentar Anda telah ditambahkan!')
            return redirect(url_for('detail_kebutuhan', id=kebutuhan.id))
        else:
            flash('Anda harus login untuk berkomentar.')
            return redirect(url_for('login'))
    komentar = kebutuhan.komentar.order_by(Komentar.timestamp.asc()).all()
    return render_template('detail.html', title=kebutuhan.judul, 
                          kebutuhan=kebutuhan, komentar=komentar, form=form)

@app.route('/vote/<int:id>')
@login_required
def vote(id):
    kebutuhan = Kebutuhan.query.get_or_404(id)
    kebutuhan.jumlah_vote += 1
    db.session.commit()
    flash('Dukungan Anda telah diterima!')
    return redirect(url_for('detail_kebutuhan', id=id))

@app.route('/tentang')
def tentang():
    return render_template('tentang.html', title='Tentang KomuniTech')

# Admin route untuk menambahkan kategori (biasanya akan ada proteksi admin)
@app.route('/tambah_kategori', methods=['GET', 'POST'])
@login_required
def tambah_kategori():
    if request.method == 'POST':
        nama = request.form.get('nama')
        deskripsi = request.form.get('deskripsi')
        if nama:
            kategori = Kategori(nama=nama, deskripsi=deskripsi)
            db.session.add(kategori)
            db.session.commit()
            flash('Kategori baru telah ditambahkan!')
            return redirect(url_for('tambah_kategori'))
    kategori = Kategori.query.all()
    return render_template('tambah_kategori.html', title='Tambah Kategori', kategori=kategori)

# Inisialisasi kategori dasar ketika aplikasi pertama kali dijalankan
@app.before_first_request
def buat_kategori_dasar():
    kategori_default = [
        ('Infrastruktur', 'Kebutuhan terkait infrastruktur fisik seperti jalan, air, dan listrik'),
        ('Pendidikan', 'Kebutuhan terkait pendidikan dan pelatihan'),
        ('Kesehatan', 'Kebutuhan terkait layanan kesehatan'),
        ('Ekonomi', 'Kebutuhan terkait pengembangan ekonomi dan bisnis'),
        ('Lingkungan', 'Kebutuhan terkait pelestarian lingkungan'),
        ('Sosial', 'Kebutuhan terkait masalah dan dukungan sosial'),
        ('Teknologi', 'Kebutuhan terkait penerapan teknologi'),
        ('Lainnya', 'Kebutuhan lain yang tidak termasuk dalam kategori di atas')
    ]
    
    for nama, deskripsi in kategori_default:
        kategori = Kategori.query.filter_by(nama=nama).first()
        if not kategori:
            kategori = Kategori(nama=nama, deskripsi=deskripsi)
            db.session.add(kategori)
    
    db.session.commit()