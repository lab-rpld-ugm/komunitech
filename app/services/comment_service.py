# app/services/comment_service.py - Complete Implementation
from typing import List, Optional, Dict, Any
from flask import current_app
from app.database.models import Komentar, Kebutuhan
from app.database.base import db
from datetime import datetime, timedelta


def create_comment(
    isi: str,
    kebutuhan_id: int,
    penulis_id: int,
    gambar_url: Optional[str] = None,
    parent_id: Optional[int] = None
) -> Komentar:
    """Create a new comment with optional threading."""
    # Validate kebutuhan exists
    kebutuhan = Kebutuhan.query.get(kebutuhan_id)
    if not kebutuhan:
        raise ValueError("Kebutuhan tidak ditemukan")
    
    # Validate parent comment if provided
    if parent_id:
        parent = Komentar.query.get(parent_id)
        if not parent:
            raise ValueError("Komentar induk tidak ditemukan")
        if parent.kebutuhan_id != kebutuhan_id:
            raise ValueError("Komentar induk tidak sesuai dengan kebutuhan")
        
        # Check nesting depth
        depth = get_comment_depth(parent_id)
        max_depth = current_app.config.get('MAX_COMMENT_DEPTH', 3)
        if depth >= max_depth:
            raise ValueError(f"Maksimal kedalaman reply adalah {max_depth} level")
    
    komentar = Komentar(
        isi=isi,
        kebutuhan_id=kebutuhan_id,
        pengguna_id=penulis_id,
        gambar_url=gambar_url,
        parent_id=parent_id
    )
    
    db.session.add(komentar)
    db.session.commit()
    
    current_app.logger.info(f"New comment created on kebutuhan {kebutuhan_id}")
    return komentar


def update_comment(
    comment_id: int,
    user_id: int,
    new_content: str
) -> Komentar:
    """Update an existing comment."""
    comment = Komentar.query.get(comment_id)
    if not comment:
        raise ValueError("Komentar tidak ditemukan")
    
    # Check if user can edit
    if not comment.can_edit(user_id):
        raise ValueError("Anda tidak dapat mengedit komentar ini")
    
    # Update content
    comment.isi = new_content
    comment.is_edited = True
    comment.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    current_app.logger.info(f"Comment {comment_id} updated by user {user_id}")
    return comment


def delete_comment(comment_id: int, user_id: int, is_admin: bool = False) -> bool:
    """Delete a comment (soft delete if has replies)."""
    comment = Komentar.query.get(comment_id)
    if not comment:
        raise ValueError("Komentar tidak ditemukan")
    
    # Check permission
    if not is_admin and comment.pengguna_id != user_id:
        raise ValueError("Anda tidak memiliki izin untuk menghapus komentar ini")
    
    # Check if has replies
    if comment.replies.count() > 0:
        # Soft delete - replace content
        comment.isi = "[Komentar ini telah dihapus]"
        comment.gambar_url = None
        comment.is_edited = True
        db.session.commit()
        current_app.logger.info(f"Comment {comment_id} soft deleted")
    else:
        # Hard delete
        db.session.delete(comment)
        db.session.commit()
        current_app.logger.info(f"Comment {comment_id} hard deleted")
    
    return True


def get_kebutuhan_comments(kebutuhan_id: int, threaded: bool = True) -> List[Komentar]:
    """Get all comments for a kebutuhan, optionally in threaded format."""
    # Get root comments (no parent)
    root_comments = Komentar.query.filter_by(
        kebutuhan_id=kebutuhan_id,
        parent_id=None
    ).order_by(Komentar.timestamp.asc()).all()
    
    if not threaded:
        # Return flat list
        return Komentar.query.filter_by(
            kebutuhan_id=kebutuhan_id
        ).order_by(Komentar.timestamp.asc()).all()
    
    # Build threaded structure
    def build_thread(comment):
        """Recursively build comment thread."""
        thread = {
            'comment': comment,
            'replies': []
        }
        
        for reply in comment.replies.order_by(Komentar.timestamp.asc()):
            thread['replies'].append(build_thread(reply))
        
        return thread
    
    threads = [build_thread(comment) for comment in root_comments]
    return threads


def get_comment_depth(comment_id: int) -> int:
    """Get the depth of a comment in the thread."""
    depth = 0
    comment = Komentar.query.get(comment_id)
    
    while comment and comment.parent_id:
        depth += 1
        comment = comment.parent
    
    return depth


def get_user_comments(
    user_id: int,
    page: int = 1,
    per_page: int = 20
):
    """Get paginated comments by a user."""
    return Komentar.query.filter_by(pengguna_id=user_id)\
        .order_by(Komentar.timestamp.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)


def get_recent_comments(
    limit: int = 10,
    kebutuhan_id: Optional[int] = None,
    user_id: Optional[int] = None
) -> List[Komentar]:
    """Get recent comments with optional filters."""
    query = Komentar.query
    
    if kebutuhan_id:
        query = query.filter_by(kebutuhan_id=kebutuhan_id)
    if user_id:
        query = query.filter_by(pengguna_id=user_id)
    
    return query.order_by(Komentar.timestamp.desc()).limit(limit).all()


def moderate_comment(
    comment_id: int,
    action: str,
    moderator_id: int,
    reason: Optional[str] = None
) -> bool:
    """Moderate a comment (admin action)."""
    comment = Komentar.query.get(comment_id)
    if not comment:
        raise ValueError("Komentar tidak ditemukan")
    
    if action == 'hide':
        comment.isi = f"[Komentar ini disembunyikan oleh moderator{': ' + reason if reason else ''}]"
        comment.gambar_url = None
    elif action == 'delete':
        return delete_comment(comment_id, moderator_id, is_admin=True)
    else:
        raise ValueError("Aksi moderasi tidak valid")
    
    db.session.commit()
    
    # Log moderation action
    from app.services.audit_service import log_admin_action
    log_admin_action(
        user_id=moderator_id,
        action=f"moderate_comment_{action}",
        entity_type="comment",
        entity_id=comment_id,
        new_value=reason
    )
    
    return True


def get_comment_stats(kebutuhan_id: Optional[int] = None) -> Dict[str, Any]:
    """Get comment statistics."""
    query = Komentar.query
    
    if kebutuhan_id:
        query = query.filter_by(kebutuhan_id=kebutuhan_id)
    
    total = query.count()
    
    # Comments in last 24 hours
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent = query.filter(Komentar.timestamp >= yesterday).count()
    
    # Users who commented
    unique_users = db.session.query(
        db.func.count(db.func.distinct(Komentar.pengguna_id))
    ).filter_by(kebutuhan_id=kebutuhan_id).scalar() if kebutuhan_id else 0
    
    # Average comments per kebutuhan
    if not kebutuhan_id:
        kebutuhan_count = Kebutuhan.query.count()
        avg_per_kebutuhan = total / kebutuhan_count if kebutuhan_count > 0 else 0
    else:
        avg_per_kebutuhan = total
    
    return {
        'total': total,
        'recent_24h': recent,
        'unique_users': unique_users,
        'avg_per_kebutuhan': round(avg_per_kebutuhan, 2)
    }