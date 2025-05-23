from typing import List, Optional
from flask import current_app
from app.database.models import Project
from app.database.base import db


def create_project(
    judul: str,
    deskripsi: str,
    pemilik_id: int,
    kategori_id: int,
    gambar_url: Optional[str] = None,
) -> Project:
    """Create a new project.

    Args:
        judul: Project title
        deskripsi: Project description
        pemilik_id: Owner user ID
        kategori_id: Category ID
        gambar_url: Optional image URL

    Returns:
        Project: Created project
    """
    project = Project(
        judul=judul,
        deskripsi=deskripsi,
        pengguna_id=pemilik_id,
        kategori_id=kategori_id,
        gambar_url=gambar_url,
    )

    db.session.add(project)
    db.session.commit()

    current_app.logger.info(f"New project created: {judul}")
    return project


def get_project_by_id(project_id: int) -> Project:
    """Get project by ID.

    Args:
        project_id: Project ID

    Returns:
        Project: Project object

    Raises:
        ValueError: If project not found
    """
    project = Project.query.get(project_id)
    if not project:
        raise ValueError("Project not found")
    return project


def update_project(
    project_id: int,
    judul: str,
    deskripsi: str,
    kategori_id: int,
    gambar_url: Optional[str] = None,
) -> Project:
    """Update an existing project.

    Args:
        project_id: Project ID to update
        judul: New title
        deskripsi: New description
        kategori_id: New category ID
        gambar_url: New image URL

    Returns:
        Project: Updated project
    """
    project = get_project_by_id(project_id)

    project.judul = judul
    project.deskripsi = deskripsi
    project.kategori_id = kategori_id
    if gambar_url:
        project.gambar_url = gambar_url

    db.session.commit()
    return project


def get_user_projects(user_id: int, page: int = 1, per_page: int = 10) -> List[Project]:
    """Get paginated projects for a user.

    Args:
        user_id: Owner user ID
        page: Page number
        per_page: Items per page

    Returns:
        List[Project]: List of projects
    """
    return (
        Project.query.filter_by(pengguna_id=user_id)
        .order_by(Project.timestamp.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )


def get_recent_projects(page: int = 1, per_page: int = 10) -> List[Project]:
    """Get recently created projects.

    Args:
        limit: Maximum number of projects

    Returns:
        List[Project]: List of recent projects
    """
    return Project.query.order_by(Project.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
