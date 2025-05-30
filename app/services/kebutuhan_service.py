from typing import List, Optional
from flask import current_app
from app.database.models import Kebutuhan, Project
from app.database.base import db


def create_kebutuhan(
    judul: str,
    deskripsi: str,
    pengaju_id: int,
    project_id: int,
    kategori_id: int,
    prioritas: str,
    gambar_url: Optional[str] = None,
) -> Kebutuhan:
    """Create a new kebutuhan.

    Args:
        judul: Kebutuhan title
        deskripsi: Kebutuhan description
        pengaju_id: Submitter user ID
        project_id: Related project ID
        kategori_id: Category ID
        prioritas: Priority level
        gambar_url: Optional image URL

    Returns:
        Kebutuhan: Created kebutuhan

    Raises:
        ValueError: If project doesn't exist
    """
    if not Project.query.get(project_id):
        raise ValueError("Project not found")

    kebutuhan = Kebutuhan(
        judul=judul,
        deskripsi=deskripsi,
        pengguna_id=pengaju_id,
        project_id=project_id,
        kategori_id=kategori_id,
        prioritas=prioritas,
        gambar_url=gambar_url,
    )

    db.session.add(kebutuhan)
    db.session.commit()

    current_app.logger.info(f"New kebutuhan created: {judul}")
    return kebutuhan


def get_kebutuhan_by_id(kebutuhan_id: int) -> Kebutuhan:
    """Get kebutuhan by ID.

    Args:
        kebutuhan_id: Kebutuhan ID

    Returns:
        Kebutuhan: Kebutuhan object

    Raises:
        ValueError: If kebutuhan not found
    """
    kebutuhan = Kebutuhan.query.get(kebutuhan_id)
    if not kebutuhan:
        raise ValueError("Kebutuhan not found")
    return kebutuhan


def get_project_kebutuhan(project_id: int) -> List[Kebutuhan]:
    """Get all kebutuhan for a project.

    Args:
        project_id: Project ID

    Returns:
        List[Kebutuhan]: List of kebutuhan
    """
    return (
        Kebutuhan.query.filter_by(project_id=project_id)
        .order_by(Kebutuhan.timestamp.desc())
        .all()
    )


def get_user_kebutuhan(
    user_id: int, page: int = 1, per_page: int = 10
) -> List[Kebutuhan]:
    """Get paginated kebutuhan submitted by a user.

    Args:
        user_id: Submitter user ID
        page: Page number
        per_page: Items per page

    Returns:
        List[Kebutuhan]: List of kebutuhan
    """
    return (
        Kebutuhan.query.filter_by(pengguna_id=user_id)
        .order_by(Kebutuhan.timestamp.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
