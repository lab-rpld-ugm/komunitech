# app/routes/support_routes.py - Complete Fixed Version
from flask import Blueprint, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app.services.support_service import (
    create_support, remove_support, has_supported, 
    get_support_by_id, get_kebutuhan_supporters
)
from app.services.kebutuhan_service import get_kebutuhan_by_id
from app.services.notification_service import create_notification
from app.database.base import db

support_bp = Blueprint("support", __name__, url_prefix="/support")


@support_bp.route("/kebutuhan/<int:kebutuhan_id>/toggle", methods=["GET", "POST"])
@login_required
def toggle_support(kebutuhan_id):
    """Toggle support for a kebutuhan (support/unsupport)."""
    kebutuhan = get_kebutuhan_by_id(kebutuhan_id)
    
    if not kebutuhan:
        flash("Kebutuhan tidak ditemukan.", "danger")
        return redirect(url_for("main.beranda"))
    
    # Check if user is the owner
    if kebutuhan.pengguna_id == current_user.id:
        flash("Anda tidak dapat mendukung kebutuhan yang Anda ajukan sendiri.", "warning")
        return redirect(url_for("kebutuhan.detail", project_id=kebutuhan.project_id, id=kebutuhan_id))
    
    try:
        if has_supported(current_user.id, kebutuhan_id):
            # Remove support
            remove_support(current_user.id, kebutuhan_id)
            flash("Dukungan Anda telah dicabut.", "info")
            action = "unsupported"
        else:
            # Add support
            support = create_support(kebutuhan_id, current_user.id)
            flash("Terima kasih atas dukungan Anda!", "success")
            action = "supported"
            
            # Create notification for kebutuhan owner
            create_notification(
                user_id=kebutuhan.pengguna_id,
                type="support",
                title="Kebutuhan Anda mendapat dukungan",
                message=f"{current_user.nama} mendukung kebutuhan '{kebutuhan.judul}'",
                link=url_for("kebutuhan.detail", project_id=kebutuhan.project_id, id=kebutuhan_id)
            )
            
            # Check if threshold reached
            if kebutuhan.jumlah_dukungan % 10 == 0:  # Every 10 supports
                # Notify project owner
                create_notification(
                    user_id=kebutuhan.project.pengguna_id,
                    type="milestone",
                    title="Milestone dukungan tercapai",
                    message=f"Kebutuhan '{kebutuhan.judul}' telah mencapai {kebutuhan.jumlah_dukungan} dukungan!",
                    link=url_for("kebutuhan.detail", project_id=kebutuhan.project_id, id=kebutuhan_id)
                )
        
        # If request is AJAX, return JSON response
        if request.is_json:
            return jsonify({
                'success': True,
                'action': action,
                'support_count': kebutuhan.jumlah_dukungan,
                'message': 'Dukungan berhasil diperbarui'
            })
            
    except ValueError as e:
        flash(str(e), "danger")
        if request.is_json:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
    except Exception as e:
        db.session.rollback()
        flash("Terjadi kesalahan. Silakan coba lagi.", "danger")
        if request.is_json:
            return jsonify({
                'success': False,
                'message': 'Terjadi kesalahan pada server'
            }), 500
    
    return redirect(url_for("kebutuhan.detail", project_id=kebutuhan.project_id, id=kebutuhan_id))


@support_bp.route("/kebutuhan/<int:kebutuhan_id>/support", methods=["GET", "POST"])
@login_required
def support(kebutuhan_id):
    """Legacy support route - redirects to toggle."""
    return redirect(url_for("support.toggle_support", kebutuhan_id=kebutuhan_id))


@support_bp.route("/kebutuhan/<int:kebutuhan_id>/supporters")
def get_supporters(kebutuhan_id):
    """Get list of supporters for a kebutuhan."""
    kebutuhan = get_kebutuhan_by_id(kebutuhan_id)
    if not kebutuhan:
        return jsonify({'error': 'Kebutuhan not found'}), 404
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    supporters = get_kebutuhan_supporters(kebutuhan_id, page=page, per_page=per_page)
    
    return jsonify({
        'success': True,
        'data': [{
            'id': s.pendukung.id,
            'nama': s.pendukung.nama,
            'username': s.pendukung.username,
            'avatar_url': s.pendukung.avatar_url,
            'supported_at': s.timestamp.isoformat()
        } for s in supporters.items],
        'pagination': {
            'page': supporters.page,
            'pages': supporters.pages,
            'per_page': supporters.per_page,
            'total': supporters.total,
            'has_next': supporters.has_next,
            'has_prev': supporters.has_prev
        }
    })


@support_bp.route("/stats")
@login_required
def my_support_stats():
    """Get current user's support statistics."""
    from app.services.support_service import get_user_support_stats
    
    stats = get_user_support_stats(current_user.id)
    
    return jsonify({
        'success': True,
        'data': stats
    })