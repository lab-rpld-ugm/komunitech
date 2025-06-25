# app/services/notification_service.py
from typing import List, Optional, Dict, Any
from flask import current_app
from app.database.models import Notification, Pengguna
from app.database.base import db
from datetime import datetime, timedelta


def create_notification(
    user_id: int,
    type: str,
    title: str,
    message: str = None,
    link: str = None
) -> Notification:
    """Create a new notification for a user.

    Args:
        user_id: Target user ID
        type: Notification type
        title: Notification title
        message: Optional notification message
        link: Optional link URL

    Returns:
        Notification: Created notification

    Raises:
        ValueError: If user not found
    """
    user = Pengguna.query.get(user_id)
    if not user:
        raise ValueError("User tidak ditemukan")

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
    """Mark a notification as read.

    Args:
        notification_id: Notification ID
        user_id: User ID (for security check)

    Returns:
        bool: True if marked as read

    Raises:
        ValueError: If notification not found or doesn't belong to user
    """
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=user_id
    ).first()
    
    if not notification:
        raise ValueError("Notifikasi tidak ditemukan")
    
    if not notification.is_read:
        notification.is_read = True
        db.session.commit()
        current_app.logger.info(f"Notification {notification_id} marked as read")
    
    return True


def mark_all_notifications_read(user_id: int) -> int:
    """Mark all notifications as read for a user.

    Args:
        user_id: User ID

    Returns:
        int: Number of notifications marked as read
    """
    count = Notification.query.filter_by(
        user_id=user_id,
        is_read=False
    ).update({'is_read': True})
    
    db.session.commit()
    current_app.logger.info(f"Marked {count} notifications as read for user {user_id}")
    return count


def get_user_notifications(
    user_id: int,
    unread_only: bool = False,
    page: int = 1,
    per_page: int = 20
):
    """Get paginated notifications for a user.

    Args:
        user_id: User ID
        unread_only: Whether to get only unread notifications
        page: Page number
        per_page: Items per page

    Returns:
        Pagination: Paginated notifications
    """
    query = Notification.query.filter_by(user_id=user_id)
    
    if unread_only:
        query = query.filter_by(is_read=False)
    
    return query.order_by(Notification.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )


def get_unread_count(user_id: int) -> int:
    """Get count of unread notifications for a user.

    Args:
        user_id: User ID

    Returns:
        int: Number of unread notifications
    """
    return Notification.query.filter_by(
        user_id=user_id,
        is_read=False
    ).count()


def delete_notification(notification_id: int, user_id: int) -> bool:
    """Delete a notification.

    Args:
        notification_id: Notification ID
        user_id: User ID (for security check)

    Returns:
        bool: True if deleted

    Raises:
        ValueError: If notification not found or doesn't belong to user
    """
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=user_id
    ).first()
    
    if not notification:
        raise ValueError("Notifikasi tidak ditemukan")
    
    db.session.delete(notification)
    db.session.commit()
    
    current_app.logger.info(f"Notification {notification_id} deleted")
    return True


def delete_old_notifications(days: int = 30) -> int:
    """Delete notifications older than specified days.

    Args:
        days: Number of days to keep

    Returns:
        int: Number of notifications deleted
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    count = Notification.query.filter(
        Notification.created_at < cutoff_date
    ).delete()
    
    db.session.commit()
    current_app.logger.info(f"Deleted {count} old notifications (older than {days} days)")
    return count


def bulk_create_notifications(
    user_ids: List[int],
    type: str,
    title: str,
    message: str = None,
    link: str = None
) -> List[Notification]:
    """Create notifications for multiple users.

    Args:
        user_ids: List of user IDs
        type: Notification type
        title: Notification title
        message: Optional notification message
        link: Optional link URL

    Returns:
        List[Notification]: Created notifications
    """
    notifications = []
    
    for user_id in user_ids:
        try:
            notification = Notification(
                user_id=user_id,
                type=type,
                title=title,
                message=message,
                link=link
            )
            db.session.add(notification)
            notifications.append(notification)
        except Exception as e:
            current_app.logger.error(f"Error creating notification for user {user_id}: {e}")
    
    db.session.commit()
    current_app.logger.info(f"Created {len(notifications)} bulk notifications")
    return notifications


def get_notification_stats(user_id: int = None) -> Dict[str, Any]:
    """Get notification statistics.

    Args:
        user_id: Optional user ID for user-specific stats

    Returns:
        Dict: Statistics data
    """
    if user_id:
        total = Notification.query.filter_by(user_id=user_id).count()
        unread = Notification.query.filter_by(user_id=user_id, is_read=False).count()
        
        by_type = db.session.query(
            Notification.type,
            db.func.count(Notification.id)
        ).filter_by(user_id=user_id).group_by(Notification.type).all()
        
        return {
            'total': total,
            'unread': unread,
            'read': total - unread,
            'by_type': dict(by_type)
        }
    
    # Global stats
    total = Notification.query.count()
    total_unread = Notification.query.filter_by(is_read=False).count()
    
    by_type = db.session.query(
        Notification.type,
        db.func.count(Notification.id)
    ).group_by(Notification.type).all()
    
    users_with_unread = db.session.query(
        db.func.count(db.func.distinct(Notification.user_id))
    ).filter_by(is_read=False).scalar()
    
    return {
        'total': total,
        'total_unread': total_unread,
        'by_type': dict(by_type),
        'users_with_unread': users_with_unread
    }


# Predefined notification types and their templates
NOTIFICATION_TYPES = {
    'comment': {
        'title_template': 'Komentar baru pada {entity}',
        'message_template': '{user} mengomentari {entity} Anda'
    },
    'support': {
        'title_template': 'Dukungan baru',
        'message_template': '{user} mendukung kebutuhan "{entity}"'
    },
    'status_change': {
        'title_template': 'Status diperbarui',
        'message_template': 'Status {entity} Anda diubah menjadi {status}'
    },
    'new_kebutuhan': {
        'title_template': 'Kebutuhan baru',
        'message_template': '{user} mengajukan kebutuhan baru pada project "{entity}"'
    },
    'milestone': {
        'title_template': 'Milestone tercapai',
        'message_template': '{entity} telah mencapai {milestone}'
    },
    'project_update': {
        'title_template': 'Project diperbarui',
        'message_template': 'Project "{entity}" telah diperbarui'
    }
}


def create_typed_notification(
    user_id: int,
    notification_type: str,
    entity_name: str,
    actor_name: str = None,
    link: str = None,
    **kwargs
) -> Notification:
    """Create a notification using predefined types.

    Args:
        user_id: Target user ID
        notification_type: Type of notification
        entity_name: Name of the entity (project, kebutuhan, etc.)
        actor_name: Name of the user performing the action
        link: Optional link URL
        **kwargs: Additional template variables

    Returns:
        Notification: Created notification

    Raises:
        ValueError: If notification type is not supported
    """
    if notification_type not in NOTIFICATION_TYPES:
        raise ValueError(f"Unsupported notification type: {notification_type}")
    
    template = NOTIFICATION_TYPES[notification_type]
    
    # Prepare template variables
    template_vars = {
        'entity': entity_name,
        'user': actor_name,
        **kwargs
    }
    
    title = template['title_template'].format(**template_vars)
    message = template['message_template'].format(**template_vars)
    
    return create_notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        message=message,
        link=link
    )