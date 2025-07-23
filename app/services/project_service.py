from typing import List, Optional, Dict, Any
from flask import current_app
from app.database.models import Project, Kategori, ProjectCollaborator, Pengguna
from app.database.base import db
from datetime import datetime


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

    Raises:
        ValueError: If category doesn't exist
    """
    # Validate category exists
    if not Kategori.query.get(kategori_id):
        raise ValueError("Kategori tidak valid")

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


def get_project_by_id(project_id: int) -> Optional[Project]:
    """Get project by ID.

    Args:
        project_id: Project ID

    Returns:
        Project: Project object or None if not found
    """
    project = Project.query.get(project_id)
    # print(f"KEBUTUHAN: {len(project.kebutuhan.all())}")
    return project


def update_project(
    project_id: int,
    judul: str = None,
    deskripsi: str = None,
    kategori_id: int = None,
    gambar_url: str = None,
    status: str = None,
) -> Project:
    """Update an existing project.

    Args:
        project_id: Project ID to update
        judul: New title
        deskripsi: New description
        kategori_id: New category ID
        gambar_url: New image URL
        status: New status

    Returns:
        Project: Updated project

    Raises:
        ValueError: If project not found or invalid status
    """
    project = get_project_by_id(project_id)
    if not project:
        raise ValueError("Project not found")

    if judul is not None:
        project.judul = judul
    if deskripsi is not None:
        project.deskripsi = deskripsi
    if kategori_id is not None:
        if not Kategori.query.get(kategori_id):
            raise ValueError("Kategori tidak valid")
        project.kategori_id = kategori_id
    if gambar_url is not None:
        project.gambar_url = gambar_url
    if status is not None:
        valid_statuses = ["Aktif", "Selesai", "Ditutup"]
        if status not in valid_statuses:
            raise ValueError("Status tidak valid")
        project.status = status

    project.updated_at = datetime.utcnow()
    db.session.commit()

    current_app.logger.info(f"Project updated: {project.judul}")
    return project


def delete_project(project_id: int) -> bool:
    """Delete a project.

    Args:
        project_id: Project ID to delete

    Returns:
        bool: True if deleted successfully

    Raises:
        ValueError: If project not found
    """
    project = get_project_by_id(project_id)
    if not project:
        raise ValueError("Project not found")

    db.session.delete(project)
    db.session.commit()

    current_app.logger.info(f"Project deleted: {project.judul}")
    return True


def get_user_projects(user_id: int, page: int = 1, per_page: int = 10):
    """Get paginated projects for a user.

    Args:
        user_id: Owner user ID
        page: Page number
        per_page: Items per page

    Returns:
        Pagination: Paginated projects
    """
    return (
        Project.query.filter_by(pengguna_id=user_id)
        .order_by(Project.timestamp.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )


def get_recent_projects(page: int = 1, per_page: int = 10, status: str = None):
    """Get recently created projects.

    Args:
        page: Page number
        per_page: Items per page
        status: Optional status filter

    Returns:
        Pagination: Paginated recent projects
    """
    query = Project.query

    if status:
        query = query.filter_by(status=status)
    else:
        # Default to active projects only
        query = query.filter_by(status="Aktif")

    return query.order_by(Project.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)


def get_all_projects(
    page: int = 1, per_page: int = None, status: str = None, kategori_id: int = None, search: str = None
):
    """Get all projects with optional filters.

    Args:
        page: Page number
        per_page: Items per page
        status: Status filter
        kategori_id: Category filter
        search: Search query

    Returns:
        Pagination: Paginated projects
    """
    if per_page is None:
        per_page = current_app.config.get("ITEMS_PER_PAGE", 12)

    query = Project.query

    if status:
        query = query.filter_by(status=status)
    if kategori_id:
        query = query.filter_by(kategori_id=kategori_id)
    if search:
        query = query.filter(db.or_(Project.judul.contains(search), Project.deskripsi.contains(search)))

    return query.order_by(Project.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)


def get_project_stats(project_id: int = None) -> Dict[str, Any]:
    """Get project statistics.

    Args:
        project_id: Optional specific project ID

    Returns:
        Dict: Statistics data
    """
    if project_id:
        project = get_project_by_id(project_id)
        if not project:
            return {}

        return {
            "total_kebutuhan": project.kebutuhan.count(),
            "kebutuhan_by_status": {
                "diajukan": project.kebutuhan.filter_by(status="Diajukan").count(),
                "diproses": project.kebutuhan.filter_by(status="Diproses").count(),
                "selesai": project.kebutuhan.filter_by(status="Selesai").count(),
                "ditolak": project.kebutuhan.filter_by(status="Ditolak").count(),
            },
            "completion_percentage": project.completion_percentage,
            "total_support": project.total_support,
            "view_count": project.view_count,
            "collaborators_count": project.collaborators.count(),
            "created_at": project.timestamp,
            "updated_at": project.updated_at,
        }

    # Global stats
    total = Project.query.count()
    by_status = db.session.query(Project.status, db.func.count(Project.id)).group_by(Project.status).all()

    by_category = (
        db.session.query(Kategori.nama, db.func.count(Project.id))
        .join(Project, Kategori.id == Project.kategori_id)
        .group_by(Kategori.nama)
        .all()
    )

    return {
        "total": total,
        "active": Project.query.filter_by(status="Aktif").count(),
        "completed": Project.query.filter_by(status="Selesai").count(),
        "closed": Project.query.filter_by(status="Ditutup").count(),
        "by_status": dict(by_status),
        "by_category": dict(by_category),
    }


def bulk_update_projects(project_ids: List[int], action: str) -> Dict[str, Any]:
    """Perform bulk action on multiple projects.

    Args:
        project_ids: List of project IDs
        action: Action to perform

    Returns:
        Dict: Result summary

    Raises:
        ValueError: If invalid action
    """
    if not project_ids:
        return {"affected": 0, "errors": []}

    affected = 0
    errors = []

    try:
        if action == "activate":
            affected = Project.query.filter(Project.id.in_(project_ids)).update(
                {"status": "Aktif"}, synchronize_session=False
            )

        elif action == "complete":
            affected = Project.query.filter(Project.id.in_(project_ids)).update(
                {"status": "Selesai"}, synchronize_session=False
            )

        elif action == "close":
            affected = Project.query.filter(Project.id.in_(project_ids)).update(
                {"status": "Ditutup"}, synchronize_session=False
            )

        elif action == "delete":
            projects_to_delete = Project.query.filter(Project.id.in_(project_ids)).all()

            for project in projects_to_delete:
                db.session.delete(project)
                affected += 1

        else:
            raise ValueError(f"Invalid action: {action}")

        db.session.commit()
        current_app.logger.info(f"Bulk {action} performed on {affected} projects")

    except Exception as e:
        db.session.rollback()
        errors.append(str(e))
        current_app.logger.error(f"Bulk action error: {e}")

    return {"affected": affected, "errors": errors}


def add_collaborator(
    project_id: int, user_id: int, role: str = "Contributor", added_by: int = None
) -> ProjectCollaborator:
    """Add a collaborator to a project.

    Args:
        project_id: Project ID
        user_id: User ID to add as collaborator
        role: Collaborator role
        added_by: User ID who added the collaborator

    Returns:
        ProjectCollaborator: Created collaborator record

    Raises:
        ValueError: If project not found, user not found, or already collaborator
    """
    project = get_project_by_id(project_id)
    if not project:
        raise ValueError("Project tidak ditemukan")

    user = Pengguna.query.get(user_id)
    if not user:
        raise ValueError("User tidak ditemukan")

    # Check if already a collaborator
    existing = ProjectCollaborator.query.filter_by(project_id=project_id, user_id=user_id).first()
    if existing:
        raise ValueError("User sudah menjadi kolaborator")

    # Check if user is the project owner
    if project.pengguna_id == user_id:
        raise ValueError("Owner project tidak perlu ditambahkan sebagai kolaborator")

    collaborator = ProjectCollaborator(project_id=project_id, user_id=user_id, role=role, added_by=added_by)

    db.session.add(collaborator)
    db.session.commit()

    current_app.logger.info(f"Added collaborator {user_id} to project {project_id}")
    return collaborator


def remove_collaborator(project_id: int, user_id: int) -> bool:
    """Remove a collaborator from a project.

    Args:
        project_id: Project ID
        user_id: User ID to remove

    Returns:
        bool: True if removed successfully

    Raises:
        ValueError: If collaborator not found
    """
    collaborator = ProjectCollaborator.query.filter_by(project_id=project_id, user_id=user_id).first()

    if not collaborator:
        raise ValueError("Kolaborator tidak ditemukan")

    db.session.delete(collaborator)
    db.session.commit()

    current_app.logger.info(f"Removed collaborator {user_id} from project {project_id}")
    return True


def get_project_collaborators(project_id: int) -> List[ProjectCollaborator]:
    """Get all collaborators for a project.

    Args:
        project_id: Project ID

    Returns:
        List[ProjectCollaborator]: List of collaborators
    """
    return ProjectCollaborator.query.filter_by(project_id=project_id).all()


def search_projects(query: str, category_id: int = None, status: str = None, page: int = 1, per_page: int = None):
    """Search projects.

    Args:
        query: Search query
        category_id: Optional category filter
        status: Optional status filter
        page: Page number
        per_page: Items per page

    Returns:
        Pagination: Search results
    """
    if per_page is None:
        per_page = current_app.config.get("ITEMS_PER_PAGE", 12)

    search_query = Project.query.filter(
        db.or_(Project.judul.ilike(f"%{query}%"), Project.deskripsi.ilike(f"%{query}%"))
    )

    if category_id:
        search_query = search_query.filter_by(kategori_id=category_id)
    if status:
        search_query = search_query.filter_by(status=status)

    return search_query.order_by(Project.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)


def get_popular_projects(limit: int = 10) -> List[Project]:
    """Get popular projects based on kebutuhan count and support.

    Args:
        limit: Maximum number of projects to return

    Returns:
        List[Project]: Popular projects
    """
    return (
        Project.query.join(Project.kebutuhan)
        .group_by(Project.id)
        .order_by(db.func.count(Project.kebutuhan).desc(), Project.view_count.desc())
        .limit(limit)
        .all()
    )
