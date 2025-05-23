from typing import List
from app.database.models import Kategori
from app.database.base import db


def get_all_categories() -> List[Kategori]:
    """Get all categories.

    Returns:
        List[Kategori]: List of all categories
    """
    return Kategori.query.all()


def create_category(nama: str, deskripsi: str = None) -> Kategori:
    """Create a new category.

    Args:
        nama: Category name
        deskripsi: Optional description

    Returns:
        Kategori: Created category

    Raises:
        ValueError: If category name exists
    """
    if Kategori.query.filter_by(nama=nama).first():
        raise ValueError("Category already exists")

    kategori = Kategori(nama=nama, deskripsi=deskripsi)
    db.session.add(kategori)
    db.session.commit()
    return kategori


def seed_default_categories():
    """Seed default categories if they don't exist."""
    defaults = [
        ("Infrastruktur", "Kebutuhan terkait infrastruktur fisik"),
        ("Pendidikan", "Kebutuhan terkait pendidikan dan pelatihan"),
        ("Kesehatan", "Kebutuhan terkait layanan kesehatan"),
        ("Ekonomi", "Kebutuhan terkait pengembangan ekonomi"),
        ("Lingkungan", "Kebutuhan terkait pelestarian lingkungan"),
        ("Sosial", "Kebutuhan terkait masalah sosial"),
        ("Teknologi", "Kebutuhan terkait penerapan teknologi"),
        ("Lainnya", "Kebutuhan lain yang tidak termasuk kategori lain"),
    ]

    for nama, deskripsi in defaults:
        if not Kategori.query.filter_by(nama=nama).first():
            create_category(nama, deskripsi)
