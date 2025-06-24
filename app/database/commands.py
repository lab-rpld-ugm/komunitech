# /your_project_directory/your_app_module/commands.py

import click
from flask.cli import with_appcontext
from .base import db  # Assuming db is in base.py
from .models import Pengguna, Kategori  # Assuming models are in models.py


@click.command(name="seed-db")
@with_appcontext
def seed_db_command():
    """Seeds the database with initial data."""

    # Seed Kategori
    kategori_defaults = [
        ("Infrastruktur", "Kebutuhan terkait infrastruktur fisik"),
        ("Pendidikan", "Kebutuhan terkait pendidikan dan pelatihan"),
        ("Kesehatan", "Kebutuhan terkait layanan kesehatan"),
        ("Ekonomi", "Kebutuhan terkait pengembangan ekonomi"),
        ("Lingkungan", "Kebutuhan terkait pelestarian lingkungan"),
        ("Sosial", "Kebutuhan terkait masalah sosial"),
        ("Teknologi", "Kebutuhan terkait penerapan teknologi"),
        ("Lainnya", "Kebutuhan lain yang tidak termasuk kategori lain"),
    ]

    click.echo("Seeding Kategori...")
    for nama_kategori, deskripsi_kategori in kategori_defaults:
        if not Kategori.query.filter_by(nama=nama_kategori).first():
            kategori = Kategori(nama=nama_kategori, deskripsi=deskripsi_kategori)
            db.session.add(kategori)
            click.echo(f"Added category: {nama_kategori}")
        else:
            click.echo(f"Category '{nama_kategori}' already exists.")

    db.session.commit()
    click.echo("Kategori seeding complete.")
    click.echo("-" * 20)

    # Seed Pengguna (admin)
    click.echo("Seeding Pengguna (admin)...")
    admin_username = "admin"
    if not Pengguna.query.filter_by(username=admin_username).first():
        admin_user = Pengguna(
            username=admin_username,
            email="admin@ugm.com",
            nama="admin",
            role="Admin",  # Assigning the string role
        )
        admin_user.set_password("admin123")
        db.session.add(admin_user)
        db.session.commit()  # Commit after adding user
        click.echo(f"Added user: {admin_username} with role 'Admin'")
    else:
        click.echo(f"User '{admin_username}' already exists.")

    click.echo("Pengguna seeding complete.")
    click.echo("-" * 20)
    click.echo("Database seeded successfully!")


def register_commands(app):
    """Registers CLI commands with the Flask app."""
    app.cli.add_command(seed_db_command)
