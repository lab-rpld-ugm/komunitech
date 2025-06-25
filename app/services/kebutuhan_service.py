from typing import List, Optional, Dict, Any
from flask import current_app
from app.database.models import Kebutuhan, Project, Kategori
from app.database.base import db
from datetime import datetime


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


def get_kebutuhan_by_id(kebutuhan_id: int) -> Optional[Kebutuhan]:
    """Get kebutuhan by ID.

    Args:
        kebutuhan_id: Kebutuhan ID

    Returns:
        Kebutuhan: Kebutuhan object or None if not found
    """
    return Kebutuhan.query.get(kebutuhan_id)


def update_kebutuhan(
    kebutuhan_id: int,
    judul: str = None,
    deskripsi: str = None,
    kategori_id: int = None,
    prioritas: str = None,
    gambar_url: str = None,
    status: str = None
) -> Kebutuhan:
    """Update an existing kebutuhan.

    Args:
        kebutuhan_id: Kebutuhan ID to update
        judul: New title
        deskripsi: New description
        kategori_id: New category ID
        prioritas: New priority level
        gambar_url: New image URL
        status: New status

    Returns:
        Kebutuhan: Updated kebutuhan

    Raises:
        ValueError: If kebutuhan not found
    """
    kebutuhan = get_kebutuhan_by_id(kebutuhan_id)
    if not kebutuhan:
        raise ValueError("Kebutuhan not found")

    if judul is not None:
        kebutuhan.judul = judul
    if deskripsi is not None:
        kebutuhan.deskripsi = deskripsi
    if kategori_id is not None:
        kebutuhan.kategori_id = kategori_id
    if prioritas is not None:
        kebutuhan.prioritas = prioritas
    if gambar_url is not None:
        kebutuhan.gambar_url = gambar_url
    if status is not None:
        kebutuhan.status = status

    kebutuhan.updated_at = datetime.utcnow()
    db.session.commit()

    current_app.logger.info(f"Kebutuhan updated: {kebutuhan.judul}")
    return kebutuhan


def delete_kebutuhan(kebutuhan_id: int) -> bool:
    """Delete a kebutuhan.

    Args:
        kebutuhan_id: Kebutuhan ID to delete

    Returns:
        bool: True if deleted successfully

    Raises:
        ValueError: If kebutuhan not found
    """
    kebutuhan = get_kebutuhan_by_id(kebutuhan_id)
    if not kebutuhan:
        raise ValueError("Kebutuhan not found")

    db.session.delete(kebutuhan)
    db.session.commit()

    current_app.logger.info(f"Kebutuhan deleted: {kebutuhan.judul}")
    return True


def get_project_kebutuhan(project_id: int, status: str = None) -> List[Kebutuhan]:
    """Get all kebutuhan for a project.

    Args:
        project_id: Project ID
        status: Optional status filter

    Returns:
        List[Kebutuhan]: List of kebutuhan
    """
    query = Kebutuhan.query.filter_by(project_id=project_id)
    
    if status:
        query = query.filter_by(status=status)
    
    return query.order_by(Kebutuhan.timestamp.desc()).all()


def get_user_kebutuhan(
    user_id: int, page: int = 1, per_page: int = 10
):
    """Get paginated kebutuhan submitted by a user.

    Args:
        user_id: Submitter user ID
        page: Page number
        per_page: Items per page

    Returns:
        Pagination: Paginated kebutuhan
    """
    return (
        Kebutuhan.query.filter_by(pengguna_id=user_id)
        .order_by(Kebutuhan.timestamp.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )


def get_all_kebutuhan(
    page: int = 1,
    per_page: int = None,
    status: str = None,
    prioritas: str = None,
    kategori_id: int = None,
    search: str = None
):
    """Get all kebutuhan with optional filters.

    Args:
        page: Page number
        per_page: Items per page
        status: Status filter
        prioritas: Priority filter
        kategori_id: Category filter
        search: Search query

    Returns:
        Pagination: Paginated kebutuhan
    """
    if per_page is None:
        per_page = current_app.config.get('ITEMS_PER_PAGE', 12)

    query = Kebutuhan.query

    if status:
        query = query.filter_by(status=status)
    if prioritas:
        query = query.filter_by(prioritas=prioritas)
    if kategori_id:
        query = query.filter_by(kategori_id=kategori_id)
    if search:
        query = query.filter(
            db.or_(
                Kebutuhan.judul.contains(search),
                Kebutuhan.deskripsi.contains(search)
            )
        )

    return query.order_by(Kebutuhan.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )


def get_kebutuhan_stats(kebutuhan_id: int = None) -> Dict[str, Any]:
    """Get kebutuhan statistics.

    Args:
        kebutuhan_id: Optional specific kebutuhan ID

    Returns:
        Dict: Statistics data
    """
    if kebutuhan_id:
        kebutuhan = get_kebutuhan_by_id(kebutuhan_id)
        if not kebutuhan:
            return {}
        
        return {
            'total_support': kebutuhan.jumlah_dukungan,
            'total_comments': kebutuhan.jumlah_komentar,
            'view_count': kebutuhan.view_count,
            'status': kebutuhan.status,
            'prioritas': kebutuhan.prioritas,
            'created_at': kebutuhan.timestamp,
            'updated_at': kebutuhan.updated_at
        }
    
    # Global stats
    total = Kebutuhan.query.count()
    by_status = db.session.query(
        Kebutuhan.status, 
        db.func.count(Kebutuhan.id)
    ).group_by(Kebutuhan.status).all()
    
    by_priority = db.session.query(
        Kebutuhan.prioritas,
        db.func.count(Kebutuhan.id)
    ).group_by(Kebutuhan.prioritas).all()
    
    return {
        'total': total,
        'by_status': dict(by_status),
        'by_priority': dict(by_priority),
        'pending': Kebutuhan.query.filter_by(status='Diajukan').count(),
        'in_progress': Kebutuhan.query.filter_by(status='Diproses').count(),
        'completed': Kebutuhan.query.filter_by(status='Selesai').count(),
        'rejected': Kebutuhan.query.filter_by(status='Ditolak').count()
    }


def bulk_update_kebutuhan(kebutuhan_ids: List[int], action: str) -> Dict[str, Any]:
    """Perform bulk action on multiple kebutuhan.

    Args:
        kebutuhan_ids: List of kebutuhan IDs
        action: Action to perform ('approve', 'reject', 'delete', etc.)

    Returns:
        Dict: Result summary

    Raises:
        ValueError: If invalid action
    """
    if not kebutuhan_ids:
        return {'affected': 0, 'errors': []}

    affected = 0
    errors = []

    try:
        if action == 'approve':
            affected = Kebutuhan.query.filter(
                Kebutuhan.id.in_(kebutuhan_ids)
            ).update({'status': 'Diproses'}, synchronize_session=False)
            
        elif action == 'reject':
            affected = Kebutuhan.query.filter(
                Kebutuhan.id.in_(kebutuhan_ids)
            ).update({'status': 'Ditolak'}, synchronize_session=False)
            
        elif action == 'complete':
            affected = Kebutuhan.query.filter(
                Kebutuhan.id.in_(kebutuhan_ids)
            ).update({'status': 'Selesai'}, synchronize_session=False)
            
        elif action == 'delete':
            kebutuhan_to_delete = Kebutuhan.query.filter(
                Kebutuhan.id.in_(kebutuhan_ids)
            ).all()
            
            for kebutuhan in kebutuhan_to_delete:
                db.session.delete(kebutuhan)
                affected += 1
                
        else:
            raise ValueError(f"Invalid action: {action}")

        db.session.commit()
        current_app.logger.info(f"Bulk {action} performed on {affected} kebutuhan")
        
    except Exception as e:
        db.session.rollback()
        errors.append(str(e))
        current_app.logger.error(f"Bulk action error: {e}")

    return {
        'affected': affected,
        'errors': errors
    }


def get_recent_kebutuhan(limit: int = 10) -> List[Kebutuhan]:
    """Get recent kebutuhan.

    Args:
        limit: Maximum number of kebutuhan to return

    Returns:
        List[Kebutuhan]: Recent kebutuhan
    """
    return Kebutuhan.query.order_by(
        Kebutuhan.timestamp.desc()
    ).limit(limit).all()


def get_popular_kebutuhan(limit: int = 10) -> List[Kebutuhan]:
    """Get popular kebutuhan by support count.

    Args:
        limit: Maximum number of kebutuhan to return

    Returns:
        List[Kebutuhan]: Popular kebutuhan
    """
    return Kebutuhan.query.join(
        Kebutuhan.dukungan
    ).group_by(
        Kebutuhan.id
    ).order_by(
        db.func.count(Kebutuhan.dukungan).desc()
    ).limit(limit).all()