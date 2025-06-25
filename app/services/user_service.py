# app/services/user_service.py
from typing import Dict, Any, Optional, List
from flask import current_app
from app.database.models import Pengguna, Project, Kebutuhan, Dukungan, Komentar
from app.database.base import db
from datetime import datetime


def get_all_users(page: int = 1, per_page: int = None):
    """Get all users with pagination.

    Args:
        page: Page number
        per_page: Items per page

    Returns:
        Pagination: Paginated users
    """
    if per_page is None:
        per_page = current_app.config.get('ITEMS_PER_PAGE_ADMIN', 20)
    
    return Pengguna.query.order_by(Pengguna.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )


def get_user_by_id(user_id: int) -> Optional[Pengguna]:
    """Get user by ID.

    Args:
        user_id: User ID

    Returns:
        Pengguna: User object or None if not found
    """
    return Pengguna.query.get(user_id)


def get_user_by_username(username: str) -> Optional[Pengguna]:
    """Get user by username.

    Args:
        username: Username

    Returns:
        Pengguna: User object or None if not found
    """
    return Pengguna.query.filter_by(username=username).first()


def get_user_by_email(email: str) -> Optional[Pengguna]:
    """Get user by email.

    Args:
        email: Email address

    Returns:
        Pengguna: User object or None if not found
    """
    return Pengguna.query.filter_by(email=email).first()


def update_user(
    user_id: int,
    nama: str = None,
    email: str = None,
    role: str = None,
    is_active: bool = None,
    email_verified: bool = None,
    bio: str = None,
    avatar_url: str = None,
    new_password: str = None
) -> Pengguna:
    """Update user information.

    Args:
        user_id: User ID to update
        nama: New name
        email: New email
        role: New role
        is_active: Active status
        email_verified: Email verification status
        bio: User bio
        avatar_url: Avatar URL
        new_password: New password

    Returns:
        Pengguna: Updated user

    Raises:
        ValueError: If user not found or email already exists
    """
    user = get_user_by_id(user_id)
    if not user:
        raise ValueError("User tidak ditemukan")
    
    if nama is not None:
        user.nama = nama
    
    if email is not None and email != user.email:
        # Check if email already exists
        existing = Pengguna.query.filter_by(email=email).first()
        if existing and existing.id != user_id:
            raise ValueError("Email sudah digunakan")
        user.email = email
    
    if role is not None:
        valid_roles = ['Regular', 'Developer', 'Admin']
        if role not in valid_roles:
            raise ValueError("Role tidak valid")
        user.role = role
    
    if is_active is not None:
        user.is_active = is_active
    
    if email_verified is not None:
        user.email_verified = email_verified
    
    if bio is not None:
        user.bio = bio
    
    if avatar_url is not None:
        user.avatar_url = avatar_url
    
    if new_password:
        user.set_password(new_password)
    
    # Update last seen
    user.last_seen = datetime.utcnow()
    
    db.session.commit()
    
    current_app.logger.info(f"User updated: {user.username}")
    return user


def delete_user(user_id: int) -> bool:
    """Delete a user and all associated data.

    Args:
        user_id: User ID to delete

    Returns:
        bool: True if deleted successfully

    Raises:
        ValueError: If user not found
    """
    user = get_user_by_id(user_id)
    if not user:
        raise ValueError("User tidak ditemukan")
    
    # Note: With cascade delete configured in models, 
    # all related data will be deleted automatically
    db.session.delete(user)
    db.session.commit()
    
    current_app.logger.info(f"User deleted: {user.username}")
    return True


def deactivate_user(user_id: int) -> bool:
    """Deactivate a user account (soft delete).

    Args:
        user_id: User ID to deactivate

    Returns:
        bool: True if deactivated successfully

    Raises:
        ValueError: If user not found
    """
    user = get_user_by_id(user_id)
    if not user:
        raise ValueError("User tidak ditemukan")
    
    user.is_active = False
    db.session.commit()
    
    current_app.logger.info(f"User deactivated: {user.username}")
    return True


def activate_user(user_id: int) -> bool:
    """Activate a user account.

    Args:
        user_id: User ID to activate

    Returns:
        bool: True if activated successfully

    Raises:
        ValueError: If user not found
    """
    user = get_user_by_id(user_id)
    if not user:
        raise ValueError("User tidak ditemukan")
    
    user.is_active = True
    db.session.commit()
    
    current_app.logger.info(f"User activated: {user.username}")
    return True


def get_user_stats(user_id: int) -> Dict[str, Any]:
    """Get statistics for a user.

    Args:
        user_id: User ID

    Returns:
        Dict: User statistics

    Raises:
        ValueError: If user not found
    """
    user = get_user_by_id(user_id)
    if not user:
        raise ValueError("User tidak ditemukan")
    
    # Calculate account age
    account_age = (datetime.utcnow() - user.created_at).days
    
    # Get project stats
    total_projects = user.projects.count()
    active_projects = user.projects.filter_by(status='Aktif').count()
    completed_projects = user.projects.filter_by(status='Selesai').count()
    
    # Get kebutuhan stats
    total_kebutuhan = user.kebutuhan.count()
    pending_kebutuhan = user.kebutuhan.filter_by(status='Diajukan').count()
    approved_kebutuhan = user.kebutuhan.filter_by(status='Diproses').count()
    completed_kebutuhan = user.kebutuhan.filter_by(status='Selesai').count()
    
    # Get support and comment stats
    total_supports = user.dukungan.count()
    total_comments = user.komentar.count()
    
    # Get kebutuhan that received support
    supported_kebutuhan = Dukungan.query.join(
        Kebutuhan, Dukungan.kebutuhan_id == Kebutuhan.id
    ).filter(Kebutuhan.pengguna_id == user_id).count()
    
    return {
        'user_id': user_id,
        'username': user.username,
        'nama': user.nama,
        'role': user.role,
        'is_active': user.is_active,
        'email_verified': user.email_verified,
        'account_age_days': account_age,
        'last_seen': user.last_seen,
        'projects': {
            'total': total_projects,
            'active': active_projects,
            'completed': completed_projects,
            'closed': total_projects - active_projects - completed_projects
        },
        'kebutuhan': {
            'total': total_kebutuhan,
            'pending': pending_kebutuhan,
            'approved': approved_kebutuhan,
            'completed': completed_kebutuhan,
            'received_support': supported_kebutuhan
        },
        'activity': {
            'supports_given': total_supports,
            'comments_posted': total_comments
        }
    }


def search_users(
    query: str,
    role: str = None,
    is_active: bool = None,
    page: int = 1,
    per_page: int = None
):
    """Search users.

    Args:
        query: Search query (username, name, email)
        role: Optional role filter
        is_active: Optional active status filter
        page: Page number
        per_page: Items per page

    Returns:
        Pagination: Search results
    """
    if per_page is None:
        per_page = current_app.config.get('ITEMS_PER_PAGE', 12)

    search_query = Pengguna.query.filter(
        db.or_(
            Pengguna.username.ilike(f'%{query}%'),
            Pengguna.nama.ilike(f'%{query}%'),
            Pengguna.email.ilike(f'%{query}%')
        )
    )

    if role:
        search_query = search_query.filter_by(role=role)
    if is_active is not None:
        search_query = search_query.filter_by(is_active=is_active)

    return search_query.order_by(Pengguna.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )


def get_active_users(limit: int = None) -> List[Pengguna]:
    """Get active users.

    Args:
        limit: Optional limit on number of users

    Returns:
        List[Pengguna]: Active users
    """
    query = Pengguna.query.filter_by(is_active=True).order_by(Pengguna.last_seen.desc())
    
    if limit:
        query = query.limit(limit)
    
    return query.all()


def get_new_users(days: int = 7, limit: int = None) -> List[Pengguna]:
    """Get users who joined recently.

    Args:
        days: Number of days to look back
        limit: Optional limit on number of users

    Returns:
        List[Pengguna]: New users
    """
    from datetime import timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    query = Pengguna.query.filter(
        Pengguna.created_at >= cutoff_date
    ).order_by(Pengguna.created_at.desc())
    
    if limit:
        query = query.limit(limit)
    
    return query.all()


def get_user_rankings(metric: str = 'projects', limit: int = 10) -> List[Dict[str, Any]]:
    """Get user rankings by various metrics.

    Args:
        metric: Ranking metric ('projects', 'kebutuhan', 'supports', 'comments')
        limit: Number of users to return

    Returns:
        List[Dict]: User rankings
    """
    if metric == 'projects':
        results = db.session.query(
            Pengguna.id,
            Pengguna.nama,
            Pengguna.username,
            db.func.count(Project.id).label('count')
        ).join(
            Project, Pengguna.id == Project.pengguna_id
        ).group_by(
            Pengguna.id, Pengguna.nama, Pengguna.username
        ).order_by(
            db.func.count(Project.id).desc()
        ).limit(limit).all()
    
    elif metric == 'kebutuhan':
        results = db.session.query(
            Pengguna.id,
            Pengguna.nama,
            Pengguna.username,
            db.func.count(Kebutuhan.id).label('count')
        ).join(
            Kebutuhan, Pengguna.id == Kebutuhan.pengguna_id
        ).group_by(
            Pengguna.id, Pengguna.nama, Pengguna.username
        ).order_by(
            db.func.count(Kebutuhan.id).desc()
        ).limit(limit).all()
    
    elif metric == 'supports':
        results = db.session.query(
            Pengguna.id,
            Pengguna.nama,
            Pengguna.username,
            db.func.count(Dukungan.id).label('count')
        ).join(
            Dukungan, Pengguna.id == Dukungan.pengguna_id
        ).group_by(
            Pengguna.id, Pengguna.nama, Pengguna.username
        ).order_by(
            db.func.count(Dukungan.id).desc()
        ).limit(limit).all()
    
    elif metric == 'comments':
        results = db.session.query(
            Pengguna.id,
            Pengguna.nama,
            Pengguna.username,
            db.func.count(Komentar.id).label('count')
        ).join(
            Komentar, Pengguna.id == Komentar.pengguna_id
        ).group_by(
            Pengguna.id, Pengguna.nama, Pengguna.username
        ).order_by(
            db.func.count(Komentar.id).desc()
        ).limit(limit).all()
    
    else:
        raise ValueError(f"Invalid metric: {metric}")
    
    return [
        {
            'rank': idx + 1,
            'user_id': result[0],
            'nama': result[1],
            'username': result[2],
            'count': result[3]
        }
        for idx, result in enumerate(results)
    ]


def update_user_last_seen(user_id: int):
    """Update user's last seen timestamp.

    Args:
        user_id: User ID
    """
    user = get_user_by_id(user_id)
    if user:
        user.last_seen = datetime.utcnow()
        db.session.commit()


def validate_user_data(username: str, email: str, nama: str) -> Dict[str, List[str]]:
    """Validate user data.

    Args:
        username: Username
        email: Email
        nama: Full name

    Returns:
        Dict: Validation errors
    """
    errors = {}
    
    # Validate username
    if not username or len(username.strip()) < 3:
        errors.setdefault('username', []).append('Username minimal 3 karakter')
    elif len(username) > 64:
        errors.setdefault('username', []).append('Username maksimal 64 karakter')
    elif not username.replace('_', '').replace('-', '').isalnum():
        errors.setdefault('username', []).append('Username hanya boleh mengandung huruf, angka, underscore, dan dash')
    
    # Validate email
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not email:
        errors.setdefault('email', []).append('Email harus diisi')
    elif not re.match(email_pattern, email):
        errors.setdefault('email', []).append('Format email tidak valid')
    elif len(email) > 120:
        errors.setdefault('email', []).append('Email maksimal 120 karakter')
    
    # Validate name
    if not nama or len(nama.strip()) < 3:
        errors.setdefault('nama', []).append('Nama minimal 3 karakter')
    elif len(nama) > 120:
        errors.setdefault('nama', []).append('Nama maksimal 120 karakter')
    
    return errors