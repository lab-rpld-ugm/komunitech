# app/services/audit_service.py
from typing import Optional, Dict, Any
from flask import current_app, request
from app.database.models import AuditLog, Pengguna
from app.database.base import db
from datetime import datetime


def log_admin_action(
    user_id: int,
    action: str,
    entity_type: str = None,
    entity_id: int = None,
    old_value: str = None,
    new_value: str = None
) -> AuditLog:
    """Log an admin action for audit trail.

    Args:
        user_id: User performing the action
        action: Action description
        entity_type: Type of entity being modified
        entity_id: ID of the entity
        old_value: Previous value
        new_value: New value

    Returns:
        AuditLog: Created audit log entry
    """
    # Get request context if available
    ip_address = None
    user_agent = None
    
    if request:
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')[:200]  # Limit length
    
    log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address,
        user_agent=user_agent
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
    """Get audit logs with filters.

    Args:
        page: Page number
        per_page: Items per page
        user_id: Filter by user ID
        action: Filter by action (partial match)
        entity_type: Filter by entity type
        date_from: Filter from date (YYYY-MM-DD format)
        date_to: Filter to date (YYYY-MM-DD format)

    Returns:
        Pagination: Paginated audit logs
    """
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
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(AuditLog.timestamp >= date_from_obj)
        except ValueError:
            current_app.logger.warning(f"Invalid date_from format: {date_from}")
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            # Add one day to include the full day
            date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
            query = query.filter(AuditLog.timestamp <= date_to_obj)
        except ValueError:
            current_app.logger.warning(f"Invalid date_to format: {date_to}")
    
    return query.order_by(AuditLog.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )


def get_user_audit_logs(user_id: int, limit: int = 50) -> list:
    """Get recent audit logs for a specific user.

    Args:
        user_id: User ID
        limit: Maximum number of logs to return

    Returns:
        list: List of audit log entries
    """
    return AuditLog.query.filter_by(user_id=user_id)\
        .order_by(AuditLog.timestamp.desc())\
        .limit(limit).all()


def get_entity_audit_logs(entity_type: str, entity_id: int, limit: int = 20) -> list:
    """Get audit logs for a specific entity.

    Args:
        entity_type: Type of entity
        entity_id: Entity ID
        limit: Maximum number of logs to return

    Returns:
        list: List of audit log entries
    """
    return AuditLog.query.filter_by(
        entity_type=entity_type,
        entity_id=entity_id
    ).order_by(AuditLog.timestamp.desc()).limit(limit).all()


def get_audit_stats() -> Dict[str, Any]:
    """Get audit log statistics.

    Returns:
        Dict: Statistics data
    """
    total_logs = AuditLog.query.count()
    
    # Count by action
    by_action = db.session.query(
        AuditLog.action,
        db.func.count(AuditLog.id)
    ).group_by(AuditLog.action).order_by(
        db.func.count(AuditLog.id).desc()
    ).limit(10).all()
    
    # Count by entity type
    by_entity_type = db.session.query(
        AuditLog.entity_type,
        db.func.count(AuditLog.id)
    ).group_by(AuditLog.entity_type).order_by(
        db.func.count(AuditLog.id).desc()
    ).all()
    
    # Count by user
    by_user = db.session.query(
        Pengguna.nama,
        db.func.count(AuditLog.id)
    ).join(
        AuditLog, Pengguna.id == AuditLog.user_id
    ).group_by(
        Pengguna.nama
    ).order_by(
        db.func.count(AuditLog.id).desc()
    ).limit(10).all()
    
    # Get recent activity
    recent_logs = AuditLog.query.order_by(
        AuditLog.timestamp.desc()
    ).limit(10).all()
    
    return {
        'total_logs': total_logs,
        'top_actions': dict(by_action),
        'by_entity_type': dict(by_entity_type),
        'top_users': dict(by_user),
        'recent_activity': [
            {
                'id': log.id,
                'user_id': log.user_id,
                'action': log.action,
                'entity_type': log.entity_type,
                'entity_id': log.entity_id,
                'timestamp': log.timestamp.isoformat(),
                'ip_address': log.ip_address
            } for log in recent_logs
        ]
    }


def clean_old_audit_logs(days: int = 365) -> int:
    """Clean up old audit logs.

    Args:
        days: Number of days to keep

    Returns:
        int: Number of logs deleted
    """
    from datetime import timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    count = AuditLog.query.filter(
        AuditLog.timestamp < cutoff_date
    ).delete()
    
    db.session.commit()
    
    current_app.logger.info(f"Cleaned up {count} old audit logs (older than {days} days)")
    return count


def log_login_attempt(user_id: int = None, username: str = None, success: bool = True):
    """Log a login attempt.

    Args:
        user_id: User ID if login successful
        username: Username attempted
        success: Whether login was successful
    """
    action = "login_success" if success else "login_failed"
    entity_type = "user"
    
    # If login failed, we might not have user_id
    if not user_id and username:
        user = Pengguna.query.filter_by(username=username).first()
        if user:
            user_id = user.id
    
    if user_id:
        log_admin_action(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=user_id,
            new_value=f"username: {username}" if username else None
        )


def log_password_change(user_id: int):
    """Log a password change.

    Args:
        user_id: User ID
    """
    log_admin_action(
        user_id=user_id,
        action="password_changed",
        entity_type="user",
        entity_id=user_id
    )


def log_file_upload(user_id: int, filename: str, file_type: str, entity_type: str = None, entity_id: int = None):
    """Log a file upload.

    Args:
        user_id: User ID
        filename: Name of uploaded file
        file_type: Type of file
        entity_type: Associated entity type
        entity_id: Associated entity ID
    """
    log_admin_action(
        user_id=user_id,
        action="file_upload",
        entity_type=entity_type,
        entity_id=entity_id,
        new_value=f"filename: {filename}, type: {file_type}"
    )


def log_bulk_action(user_id: int, action: str, entity_type: str, entity_ids: list):
    """Log a bulk action.

    Args:
        user_id: User ID
        action: Action performed
        entity_type: Type of entities
        entity_ids: List of entity IDs
    """
    log_admin_action(
        user_id=user_id,
        action=f"bulk_{action}",
        entity_type=entity_type,
        new_value=f"entity_ids: {entity_ids}, count: {len(entity_ids)}"
    )


def log_security_event(user_id: int, event_type: str, details: str = None):
    """Log a security-related event.

    Args:
        user_id: User ID
        event_type: Type of security event
        details: Additional details
    """
    log_admin_action(
        user_id=user_id,
        action=f"security_{event_type}",
        entity_type="security",
        new_value=details
    )