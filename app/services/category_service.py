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
