# app/services/category_service.py
from typing import List, Optional, Dict, Any
from flask import current_app
from app.database.models import Kategori, Project, Kebutuhan
from app.database.base import db


def get_all_categories() -> List[Kategori]:
    """Get all categories ordered by name.

    Returns:
        List[Kategori]: List of all categories
    """
    return Kategori.query.order_by(Kategori.nama).all()


def get_category_by_id(category_id: int) -> Optional[Kategori]:
    """Get category by ID.

    Args:
        category_id: Category ID

    Returns:
        Kategori: Category object or None if not found
    """
    return Kategori.query.get(category_id)


def get_category_by_name(name: str) -> Optional[Kategori]:
    """Get category by name.

    Args:
        name: Category name

    Returns:
        Kategori: Category object or None if not found
    """
    return Kategori.query.filter_by(nama=name).first()


def create_category(nama: str, deskripsi: str) -> Kategori:
    """Create a new category.

    Args:
        nama: Category name
        deskripsi: Category description

    Returns:
        Kategori: Created category

    Raises:
        ValueError: If category with same name already exists
    """
    # Check if category already exists
    existing = Kategori.query.filter_by(nama=nama).first()
    if existing:
        raise ValueError(f"Kategori dengan nama '{nama}' sudah ada")

    category = Kategori(nama=nama, deskripsi=deskripsi)
    db.session.add(category)
    db.session.commit()

    current_app.logger.info(f"New category created: {nama}")
    return category


def update_category(
    category_id: int,
    nama: str = None,
    deskripsi: str = None
) -> Kategori:
    """Update an existing category.

    Args:
        category_id: Category ID to update
        nama: New name
        deskripsi: New description

    Returns:
        Kategori: Updated category

    Raises:
        ValueError: If category not found or name already exists
    """
    category = get_category_by_id(category_id)
    if not category:
        raise ValueError("Kategori tidak ditemukan")

    # Check if new name already exists (if changing name)
    if nama and nama != category.nama:
        existing = Kategori.query.filter_by(nama=nama).first()
        if existing:
            raise ValueError(f"Kategori dengan nama '{nama}' sudah ada")
        category.nama = nama

    if deskripsi is not None:
        category.deskripsi = deskripsi

    db.session.commit()

    current_app.logger.info(f"Category updated: {category.nama}")
    return category


def delete_category(category_id: int) -> bool:
    """Delete a category.

    Args:
        category_id: Category ID to delete

    Returns:
        bool: True if deleted successfully

    Raises:
        ValueError: If category not found or still in use
    """
    category = get_category_by_id(category_id)
    if not category:
        raise ValueError("Kategori tidak ditemukan")

    # Check if category is still in use
    if not category.can_delete():
        raise ValueError("Kategori tidak dapat dihapus karena sedang digunakan")

    db.session.delete(category)
    db.session.commit()

    current_app.logger.info(f"Category deleted: {category.nama}")
    return True


def get_category_stats(category_id: int = None) -> Dict[str, Any]:
    """Get category usage statistics.

    Args:
        category_id: Optional specific category ID

    Returns:
        Dict: Statistics data
    """
    if category_id:
        category = get_category_by_id(category_id)
        if not category:
            return {}

        return {
            'id': category.id,
            'nama': category.nama,
            'deskripsi': category.deskripsi,
            'project_count': category.projects.count(),
            'kebutuhan_count': category.kebutuhan.count(),
            'total_usage': category.usage_count,
            'can_delete': category.can_delete(),
            'created_at': category.created_at,
            'updated_at': category.updated_at
        }

    # Global stats for all categories
    categories = get_all_categories()
    stats = []

    for category in categories:
        project_count = category.projects.count()
        kebutuhan_count = category.kebutuhan.count()
        
        stats.append({
            'id': category.id,
            'nama': category.nama,
            'project_count': project_count,
            'kebutuhan_count': kebutuhan_count,
            'total_usage': project_count + kebutuhan_count
        })

    # Sort by usage
    stats.sort(key=lambda x: x['total_usage'], reverse=True)

    return {
        'total_categories': len(categories),
        'categories': stats,
        'most_used': stats[0] if stats else None,
        'least_used': stats[-1] if stats else None,
        'unused_categories': [cat for cat in stats if cat['total_usage'] == 0]
    }


def get_popular_categories(limit: int = 10) -> List[Dict[str, Any]]:
    """Get most popular categories by usage.

    Args:
        limit: Maximum number of categories to return

    Returns:
        List[Dict]: Popular categories with usage stats
    """
    categories = db.session.query(
        Kategori.id,
        Kategori.nama,
        (
            db.func.count(Project.id.distinct()) + 
            db.func.count(Kebutuhan.id.distinct())
        ).label('total_usage')
    ).outerjoin(
        Project, Kategori.id == Project.kategori_id
    ).outerjoin(
        Kebutuhan, Kategori.id == Kebutuhan.kategori_id
    ).group_by(
        Kategori.id, Kategori.nama
    ).order_by(
        db.text('total_usage DESC')
    ).limit(limit).all()

    return [
        {
            'id': cat[0],
            'nama': cat[1],
            'usage_count': cat[2]
        }
        for cat in categories
    ]


def search_categories(query: str) -> List[Kategori]:
    """Search categories by name or description.

    Args:
        query: Search query

    Returns:
        List[Kategori]: Matching categories
    """
    return Kategori.query.filter(
        db.or_(
            Kategori.nama.ilike(f'%{query}%'),
            Kategori.deskripsi.ilike(f'%{query}%')
        )
    ).order_by(Kategori.nama).all()


def create_default_categories() -> List[Kategori]:
    """Create default categories if they don't exist.

    Returns:
        List[Kategori]: List of created categories
    """
    default_categories = [
        ("Infrastruktur", "Kebutuhan terkait infrastruktur fisik seperti jalan, air, dan listrik"),
        ("Pendidikan", "Kebutuhan terkait pendidikan dan pelatihan"),
        ("Kesehatan", "Kebutuhan terkait layanan kesehatan"),
        ("Ekonomi", "Kebutuhan terkait pengembangan ekonomi dan bisnis"),
        ("Lingkungan", "Kebutuhan terkait pelestarian lingkungan"),
        ("Sosial", "Kebutuhan terkait masalah dan dukungan sosial"),
        ("Teknologi", "Kebutuhan terkait penerapan teknologi"),
        ("Lainnya", "Kebutuhan lain yang tidak termasuk dalam kategori di atas"),
    ]

    created_categories = []

    for nama, deskripsi in default_categories:
        if not get_category_by_name(nama):
            try:
                category = create_category(nama, deskripsi)
                created_categories.append(category)
                current_app.logger.info(f"Created default category: {nama}")
            except ValueError:
                # Category might have been created by another process
                pass

    return created_categories


def validate_category_data(nama: str, deskripsi: str) -> Dict[str, List[str]]:
    """Validate category data.

    Args:
        nama: Category name
        deskripsi: Category description

    Returns:
        Dict: Validation errors
    """
    errors = {}

    if not nama or len(nama.strip()) < 2:
        errors.setdefault('nama', []).append('Nama kategori minimal 2 karakter')
    elif len(nama) > 64:
        errors.setdefault('nama', []).append('Nama kategori maksimal 64 karakter')

    if not deskripsi or len(deskripsi.strip()) < 10:
        errors.setdefault('deskripsi', []).append('Deskripsi kategori minimal 10 karakter')
    elif len(deskripsi) > 200:
        errors.setdefault('deskripsi', []).append('Deskripsi kategori maksimal 200 karakter')

    return errors