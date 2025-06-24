# app/services/search_service.py - New File
from typing import List, Dict, Any
from flask import current_app
from sqlalchemy import or_, and_, func
from app.database.models import Project, Kebutuhan, Pengguna, Kategori
from app.database.base import db


def search_projects(query: str, category_id: int = None, page: int = 1, per_page: int = None):
    """Search projects by query and optional category."""
    if per_page is None:
        per_page = current_app.config.get('ITEMS_PER_PAGE', 12)
    
    search = Project.query
    
    if query:
        search = search.filter(
            or_(
                Project.judul.ilike(f'%{query}%'),
                Project.deskripsi.ilike(f'%{query}%')
            )
        )
    
    if category_id and category_id > 0:
        search = search.filter_by(kategori_id=category_id)
    
    # Only show active projects in search
    search = search.filter_by(status='Aktif')
    
    return search.order_by(Project.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )


def search_kebutuhan(query: str, category_id: int = None, page: int = 1, per_page: int = None):
    """Search kebutuhan by query and optional category."""
    if per_page is None:
        per_page = current_app.config.get('ITEMS_PER_PAGE', 12)
    
    search = Kebutuhan.query
    
    if query:
        search = search.filter(
            or_(
                Kebutuhan.judul.ilike(f'%{query}%'),
                Kebutuhan.deskripsi.ilike(f'%{query}%')
            )
        )
    
    if category_id and category_id > 0:
        search = search.filter_by(kategori_id=category_id)
    
    # Exclude rejected kebutuhan
    search = search.filter(Kebutuhan.status != 'Ditolak')
    
    return search.order_by(Kebutuhan.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )


def search_users(query: str, page: int = 1, per_page: int = None):
    """Search users by username or name."""
    if per_page is None:
        per_page = current_app.config.get('ITEMS_PER_PAGE', 12)
    
    search = Pengguna.query.filter(
        or_(
            Pengguna.username.ilike(f'%{query}%'),
            Pengguna.nama.ilike(f'%{query}%')
        )
    )
    
    # Only show active users
    search = search.filter_by(is_active=True)
    
    return search.order_by(Pengguna.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )


def search_all(query: str, category_id: int = None, page: int = 1, per_page: int = None) -> Dict[str, Any]:
    """Search across all entities."""
    if per_page is None:
        per_page = current_app.config.get('ITEMS_PER_PAGE', 12)
    
    # Limit results per type for overview
    limit_per_type = 5
    
    results = {
        'projects': search_projects(query, category_id, 1, limit_per_type),
        'kebutuhan': search_kebutuhan(query, category_id, 1, limit_per_type),
        'users': search_users(query, 1, limit_per_type) if not category_id else None,
        'total': 0
    }
    
    # Calculate total
    results['total'] = (
        (results['projects'].total if results['projects'] else 0) +
        (results['kebutuhan'].total if results['kebutuhan'] else 0) +
        (results['users'].total if results['users'] else 0)
    )
    
    return results


def get_search_suggestions(query: str, limit: int = 10) -> List[Dict[str, str]]:
    """Get search suggestions for autocomplete."""
    suggestions = []
    
    # Search projects
    projects = Project.query.filter(
        Project.judul.ilike(f'%{query}%'),
        Project.status == 'Aktif'
    ).limit(limit // 3).all()
    
    for project in projects:
        suggestions.append({
            'type': 'project',
            'text': project.judul,
            'url': f'/project/{project.id}'
        })
    
    # Search kebutuhan
    kebutuhan = Kebutuhan.query.filter(
        Kebutuhan.judul.ilike(f'%{query}%'),
        Kebutuhan.status != 'Ditolak'
    ).limit(limit // 3).all()
    
    for k in kebutuhan:
        suggestions.append({
            'type': 'kebutuhan',
            'text': k.judul,
            'url': f'/kebutuhan/project/{k.project_id}/kebutuhan/{k.id}'
        })
    
    # Search users
    users = Pengguna.query.filter(
        or_(
            Pengguna.username.ilike(f'%{query}%'),
            Pengguna.nama.ilike(f'%{query}%')
        ),
        Pengguna.is_active == True
    ).limit(limit // 3).all()
    
    for user in users:
        suggestions.append({
            'type': 'user',
            'text': f'{user.nama} (@{user.username})',
            'url': f'/user/{user.username}'
        })
    
    return suggestions[:limit]


# app/services/notification_service.py - New File
from typing import List, Optional
from flask import current_app
from app.database.models import Notification, Pengguna
from app.database.base import db


def create_notification(
    user_id: int,
    type: str,
    title: str,
    message: str = None,
    link: str = None
) -> Notification:
    """Create a new notification for a user."""
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        link=link
    )
    
    db.session.add(notification)
    db.session.commit()
    
    current_app.logger.info(f"Notification created for user {user_id}: {title}")
    return notification


def mark_notification_read(notification_id: int, user_id: int) -> bool:
    """Mark a notification as read."""
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=user_id
    ).first()
    
    if notification:
        notification.is_read = True
        db.session.commit()
        return True
    return False


def mark_all_notifications_read(user_id: int) -> int:
    """Mark all notifications as read for a user."""
    count = Notification.query.filter_by(
        user_id=user_id,
        is_read=False
    ).update({'is_read': True})
    
    db.session.commit()
    return count


def get_user_notifications(
    user_id: int,
    unread_only: bool = False,
    page: int = 1,
    per_page: int = 20
):
    """Get paginated notifications for a user."""
    query = Notification.query.filter_by(user_id=user_id)
    
    if unread_only:
        query = query.filter_by(is_read=False)
    
    return query.order_by(Notification.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )


def delete_old_notifications(days: int = 30) -> int:
    """Delete notifications older than specified days."""
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    count = Notification.query.filter(
        Notification.created_at < cutoff_date
    ).delete()
    
    db.session.commit()
    return count


# app/services/user_service.py - New File
from typing import Dict, Any, Optional
from flask import current_app
from app.database.models import Pengguna, Project, Kebutuhan, Dukungan
from app.database.base import db
from app.services.audit_service import log_admin_action


def get_all_users(page: int = 1, per_page: int = None):
    """Get all users with pagination."""
    if per_page is None:
        per_page = current_app.config.get('ITEMS_PER_PAGE_ADMIN', 20)
    
    return Pengguna.query.order_by(Pengguna.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )


def get_user_by_id(user_id: int) -> Optional[Pengguna]:
    """Get user by ID."""
    return Pengguna.query.get(user_id)


def get_user_by_username(username: str) -> Optional[Pengguna]:
    """Get user by username."""
    return Pengguna.query.filter_by(username=username).first()


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
    """Update user information."""
    user = get_user_by_id(user_id)
    if not user:
        raise ValueError("User not found")
    
    if nama is not None:
        user.nama = nama
    if email is not None:
        # Check if email already exists
        existing = Pengguna.query.filter_by(email=email).first()
        if existing and existing.id != user_id:
            raise ValueError("Email already in use")
        user.email = email
    if role is not None:
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
    
    db.session.commit()
    return user


def delete_user(user_id: int) -> bool:
    """Delete a user and all associated data."""
    user = get_user_by_id(user_id)
    if not user:
        return False
    
    # Note: With cascade delete, all related data will be deleted
    db.session.delete(user)
    db.session.commit()
    return True


def get_user_stats(user_id: int) -> Dict[str, Any]:
    """Get statistics for a user."""
    user = get_user_by_id(user_id)
    if not user:
        return {}
    
    stats = {
        'total_projects': user.projects.count(),
        'active_projects': user.projects.filter_by(status='Aktif').count(),
        'total_kebutuhan': user.kebutuhan.count(),
        'pending_kebutuhan': user.kebutuhan.filter_by(status='Diajukan').count(),
        'total_supports': user.dukungan.count(),
        'total_comments': user.komentar.count(),
        'account_age_days': (datetime.utcnow() - user.created_at).days
    }
    
    return stats


# app/services/audit_service.py - New File
from typing import Optional
from flask import current_app, request
from app.database.models import AuditLog
from app.database.base import db


def log_admin_action(
    user_id: int,
    action: str,
    entity_type: str = None,
    entity_id: int = None,
    old_value: str = None,
    new_value: str = None
) -> AuditLog:
    """Log an admin action for audit trail."""
    log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        ip_address=request.remote_addr if request else None,
        user_agent=request.headers.get('User-Agent') if request else None
    )
    
    db.session.add(log)
    db.session.commit()
    
    current_app.logger.info(
        f"Audit log: User {user_id} performed {action} on {entity_type} {entity_id}"
    )
    
    return log


def get_audit_logs(
    page: int = 1,
    per_page: int = None,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    """Get audit logs with filters."""
    if per_page is None:
        per_page = current_app.config.get('ITEMS_PER_PAGE_ADMIN', 20)
    
    query = AuditLog.query
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    if action:
        query = query.filter(AuditLog.action.contains(action))
    if entity_type:
        query = query.filter_by(entity_type=entity_type)
    
    if date_from:
        from datetime import datetime
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(AuditLog.timestamp >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        from datetime import datetime
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(AuditLog.timestamp <= date_to_obj)
        except ValueError:
            pass
    
    return query.order_by(AuditLog.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )