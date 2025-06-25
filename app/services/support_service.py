from typing import List, Dict, Any, Optional
from flask import current_app
from app.database.models import Dukungan, Kebutuhan, Pengguna
from app.database.base import db


def create_support(kebutuhan_id: int, supporter_id: int) -> Dukungan:
    """Create a new support record.

    Args:
        kebutuhan_id: Supported kebutuhan ID
        supporter_id: Supporter user ID

    Returns:
        Dukungan: Created support record

    Raises:
        ValueError: If already supported or invalid
    """
    # Check if already supported
    if Dukungan.query.filter_by(
        pengguna_id=supporter_id, kebutuhan_id=kebutuhan_id
    ).first():
        raise ValueError("Already supported this kebutuhan")

    # Check if supporting own kebutuhan
    kebutuhan = Kebutuhan.query.get(kebutuhan_id)
    if not kebutuhan:
        raise ValueError("Kebutuhan not found")
        
    if kebutuhan.pengguna_id == supporter_id:
        raise ValueError("Cannot support your own kebutuhan")

    dukungan = Dukungan(pengguna_id=supporter_id, kebutuhan_id=kebutuhan_id)

    db.session.add(dukungan)
    db.session.commit()

    current_app.logger.info(f"User {supporter_id} supported kebutuhan {kebutuhan_id}")
    return dukungan


def remove_support(user_id: int, kebutuhan_id: int) -> bool:
    """Remove support from a kebutuhan.

    Args:
        user_id: User ID
        kebutuhan_id: Kebutuhan ID

    Returns:
        bool: True if removed successfully

    Raises:
        ValueError: If support not found
    """
    support = Dukungan.query.filter_by(
        pengguna_id=user_id, 
        kebutuhan_id=kebutuhan_id
    ).first()
    
    if not support:
        raise ValueError("Support not found")
    
    db.session.delete(support)
    db.session.commit()
    
    current_app.logger.info(f"User {user_id} removed support from kebutuhan {kebutuhan_id}")
    return True


def get_support_by_id(support_id: int) -> Optional[Dukungan]:
    """Get support by ID.

    Args:
        support_id: Support ID

    Returns:
        Dukungan: Support object or None if not found
    """
    return Dukungan.query.get(support_id)


def get_user_supports(
    user_id: int, page: int = 1, per_page: int = 10
):
    """Get paginated supports by a user.

    Args:
        user_id: Supporter user ID
        page: Page number
        per_page: Items per page

    Returns:
        Pagination: Paginated support records
    """
    return (
        Dukungan.query.filter_by(pengguna_id=user_id)
        .order_by(Dukungan.timestamp.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )


def get_kebutuhan_supporters(
    kebutuhan_id: int, 
    page: int = 1, 
    per_page: int = 20
):
    """Get paginated supporters for a kebutuhan.

    Args:
        kebutuhan_id: Kebutuhan ID
        page: Page number
        per_page: Items per page

    Returns:
        Pagination: Paginated support records
    """
    return (
        Dukungan.query.filter_by(kebutuhan_id=kebutuhan_id)
        .order_by(Dukungan.timestamp.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )


def has_supported(user_id: int, kebutuhan_id: int) -> bool:
    """Check if user has supported a kebutuhan.

    Args:
        user_id: User ID to check
        kebutuhan_id: Kebutuhan ID to check

    Returns:
        bool: True if supported, False otherwise
    """
    return (
        Dukungan.query.filter_by(pengguna_id=user_id, kebutuhan_id=kebutuhan_id).first()
        is not None
    )


def get_user_support_stats(user_id: int) -> Dict[str, Any]:
    """Get user's support statistics.

    Args:
        user_id: User ID

    Returns:
        Dict: Statistics data
    """
    total_supports = Dukungan.query.filter_by(pengguna_id=user_id).count()
    
    # Get kebutuhan categories the user has supported
    supported_categories = db.session.query(
        Kebutuhan.kategori_id,
        db.func.count(Dukungan.id).label('count')
    ).join(
        Dukungan, Kebutuhan.id == Dukungan.kebutuhan_id
    ).filter(
        Dukungan.pengguna_id == user_id
    ).group_by(Kebutuhan.kategori_id).all()
    
    # Get kebutuhan statuses the user has supported
    supported_statuses = db.session.query(
        Kebutuhan.status,
        db.func.count(Dukungan.id).label('count')
    ).join(
        Dukungan, Kebutuhan.id == Dukungan.kebutuhan_id
    ).filter(
        Dukungan.pengguna_id == user_id
    ).group_by(Kebutuhan.status).all()
    
    # Get recent supports
    recent_supports = Dukungan.query.filter_by(
        pengguna_id=user_id
    ).order_by(Dukungan.timestamp.desc()).limit(5).all()
    
    return {
        'total_supports': total_supports,
        'by_category': dict(supported_categories),
        'by_status': dict(supported_statuses),
        'recent_supports': [
            {
                'id': s.id,
                'kebutuhan_id': s.kebutuhan_id,
                'kebutuhan_title': s.kebutuhan_didukung.judul,
                'supported_at': s.timestamp,
                'project_title': s.kebutuhan_didukung.project.judul
            } for s in recent_supports
        ]
    }


def get_support_statistics() -> Dict[str, Any]:
    """Get global support statistics.

    Returns:
        Dict: Global statistics
    """
    total_supports = Dukungan.query.count()
    unique_supporters = db.session.query(
        db.func.count(db.func.distinct(Dukungan.pengguna_id))
    ).scalar()
    
    # Most supported kebutuhan
    most_supported = db.session.query(
        Kebutuhan.id,
        Kebutuhan.judul,
        db.func.count(Dukungan.id).label('support_count')
    ).join(
        Dukungan, Kebutuhan.id == Dukungan.kebutuhan_id
    ).group_by(
        Kebutuhan.id, Kebutuhan.judul
    ).order_by(
        db.func.count(Dukungan.id).desc()
    ).limit(10).all()
    
    # Most active supporters
    most_active = db.session.query(
        Pengguna.id,
        Pengguna.nama,
        db.func.count(Dukungan.id).label('support_count')
    ).join(
        Dukungan, Pengguna.id == Dukungan.pengguna_id
    ).group_by(
        Pengguna.id, Pengguna.nama
    ).order_by(
        db.func.count(Dukungan.id).desc()
    ).limit(10).all()
    
    return {
        'total_supports': total_supports,
        'unique_supporters': unique_supporters,
        'most_supported_kebutuhan': [
            {
                'id': item[0],
                'title': item[1],
                'support_count': item[2]
            } for item in most_supported
        ],
        'most_active_supporters': [
            {
                'id': item[0],
                'name': item[1],
                'support_count': item[2]
            } for item in most_active
        ]
    }


def get_trending_kebutuhan(days: int = 7, limit: int = 10) -> List[Kebutuhan]:
    """Get trending kebutuhan based on recent support activity.

    Args:
        days: Number of days to look back
        limit: Maximum number of kebutuhan to return

    Returns:
        List[Kebutuhan]: Trending kebutuhan
    """
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    trending = db.session.query(
        Kebutuhan.id,
        db.func.count(Dukungan.id).label('recent_support_count')
    ).join(
        Dukungan, Kebutuhan.id == Dukungan.kebutuhan_id
    ).filter(
        Dukungan.timestamp >= cutoff_date
    ).group_by(
        Kebutuhan.id
    ).order_by(
        db.func.count(Dukungan.id).desc()
    ).limit(limit).all()
    
    kebutuhan_ids = [item[0] for item in trending]
    
    return Kebutuhan.query.filter(
        Kebutuhan.id.in_(kebutuhan_ids)
    ).order_by(
        db.case(
            {kebutuhan_id: index for index, kebutuhan_id in enumerate(kebutuhan_ids)},
            value=Kebutuhan.id
        )
    ).all()