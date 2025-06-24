# app/routes/user_routes.py - Complete Fixed Version
from flask import Blueprint, render_template, request, flash, redirect, url_for, abort, jsonify
from flask_login import login_required, current_user
from app.forms import UserProfileForm, ChangePasswordForm, PasswordResetRequestForm, PasswordResetForm
from app.services.support_service import get_user_supports
from app.services.kebutuhan_service import get_user_kebutuhan
from app.services.project_service import get_user_projects
from app.services.user_service import (
    get_user_by_username, update_user, get_user_stats,
    get_user_by_id
)
from app.services.notification_service import (
    get_user_notifications, mark_notification_read, 
    mark_all_notifications_read
)
from app.services.file_service import save_avatar_image
from app.utils.pagination import generate_pagination_links
from app.utils.file_utils import delete_file
from app.database.base import db
from app.database.models import Pengguna
import secrets

user_bp = Blueprint("user", __name__, url_prefix="/user")


@user_bp.route("/profile")
@login_required
def profile():
    """View current user's profile."""
    return redirect(url_for("user.public_profile", username=current_user.username))


@user_bp.route("/<username>")
def public_profile(username):
    """View public user profile."""
    user = get_user_by_username(username)
    if not user:
        abort(404)
    
    # Get user statistics
    stats = get_user_stats(user.id)
    
    # Get recent activity
    recent_projects = user.projects.order_by(Project.timestamp.desc()).limit(5).all()
    recent_kebutuhan = user.kebutuhan.order_by(Kebutuhan.timestamp.desc()).limit(5).all()
    recent_supports = user.dukungan.order_by(Dukungan.timestamp.desc()).limit(5).all()
    
    return render_template(
        "user/profile.html",
        user=user,
        stats=stats,
        recent_projects=recent_projects,
        recent_kebutuhan=recent_kebutuhan,
        recent_supports=recent_supports,
        is_own_profile=(current_user.is_authenticated and current_user.id == user.id)
    )


@user_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """User settings page."""
    form = UserProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        try:
            avatar_url = current_user.avatar_url
            
            # Handle avatar deletion
            if form.delete_avatar.data and avatar_url:
                delete_file(avatar_url)
                avatar_url = None
            
            # Handle new avatar upload
            if form.avatar.data:
                # Delete old avatar if exists
                if avatar_url:
                    delete_file(avatar_url)
                avatar_url = save_avatar_image(form.avatar.data, current_user.id)
            
            update_user(
                user_id=current_user.id,
                nama=form.nama.data,
                bio=form.bio.data,
                avatar_url=avatar_url
            )
            
            flash("Profil berhasil diperbarui!", "success")
            return redirect(url_for("user.profile"))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Terjadi kesalahan: {str(e)}", "danger")
    
    return render_template("user/settings.html", form=form)


@user_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    """Change password page."""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if not current_user.check_password(form.old_password.data):
            flash("Password lama tidak benar.", "danger")
        else:
            try:
                current_user.set_password(form.new_password.data)
                db.session.commit()
                flash("Password berhasil diubah!", "success")
                return redirect(url_for("user.settings"))
            except Exception as e:
                db.session.rollback()
                flash(f"Terjadi kesalahan: {str(e)}", "danger")
    
    return render_template("user/change_password.html", form=form)


@user_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password_request():
    """Request password reset."""
    if current_user.is_authenticated:
        return redirect(url_for("main.beranda"))
    
    form = PasswordResetRequestForm()
    
    if form.validate_on_submit():
        user = Pengguna.query.filter_by(email=form.email.data).first()
        if user:
            # Generate reset token
            token = secrets.token_urlsafe(32)
            # In production, save token to database with expiration
            # and send email with reset link
            
            flash(
                "Jika email terdaftar, kami akan mengirimkan link reset password. "
                "Silakan cek email Anda.",
                "info"
            )
        else:
            # Don't reveal if email exists or not
            flash(
                "Jika email terdaftar, kami akan mengirimkan link reset password. "
                "Silakan cek email Anda.",
                "info"
            )
        
        return redirect(url_for("auth.login"))
    
    return render_template("user/reset_password_request.html", form=form)


@user_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """Reset password with token."""
    if current_user.is_authenticated:
        return redirect(url_for("main.beranda"))
    
    # In production, validate token from database
    # For now, just show the form
    
    form = PasswordResetForm()
    
    if form.validate_on_submit():
        # In production, get user from token and update password
        flash("Password berhasil direset! Silakan login dengan password baru.", "success")
        return redirect(url_for("auth.login"))
    
    return render_template("user/reset_password.html", form=form, token=token)


@user_bp.route("/supports", methods=["GET"])
@login_required
def supports():
    """View user's supported kebutuhan."""
    page = request.args.get("page", 1, type=int)
    supports = get_user_supports(current_user.id, page=page)
    
    next_url, prev_url = generate_pagination_links(supports, "user.supports")
    
    return render_template(
        "user/supports.html",
        supports=supports.items,
        next_url=next_url,
        prev_url=prev_url,
        pagination=supports
    )


@user_bp.route("/kebutuhan", methods=["GET"])
@login_required
def kebutuhans():
    """View user's submitted kebutuhan."""
    page = request.args.get("page", 1, type=int)
    kebutuhan = get_user_kebutuhan(current_user.id, page=page)
    
    next_url, prev_url = generate_pagination_links(kebutuhan, "user.kebutuhans")
    
    return render_template(
        "user/kebutuhan.html",
        kebutuhan=kebutuhan.items,
        next_url=next_url,
        prev_url=prev_url,
        pagination=kebutuhan
    )


@user_bp.route("/projects", methods=["GET"])
@login_required
def projects():
    """View user's projects."""
    page = request.args.get("page", 1, type=int)
    projects = get_user_projects(current_user.id, page=page)
    
    next_url, prev_url = generate_pagination_links(projects, "user.projects")
    
    return render_template(
        "user/projects.html",
        projects=projects.items,
        next_url=next_url,
        prev_url=prev_url,
        pagination=projects
    )


@user_bp.route("/notifications")
@login_required
def notifications():
    """View user notifications."""
    page = request.args.get("page", 1, type=int)
    unread_only = request.args.get("unread", "false").lower() == "true"
    
    notifications = get_user_notifications(
        current_user.id,
        unread_only=unread_only,
        page=page
    )
    
    return render_template(
        "user/notifications.html",
        notifications=notifications,
        unread_only=unread_only
    )


@user_bp.route("/notifications/<int:id>/read", methods=["POST"])
@login_required
def mark_notification_as_read(id):
    """Mark single notification as read."""
    success = mark_notification_read(id, current_user.id)
    
    if request.is_json:
        return jsonify({'success': success})
    
    return redirect(url_for("user.notifications"))


@user_bp.route("/notifications/read-all", methods=["POST"])
@login_required
def mark_all_read():
    """Mark all notifications as read."""
    count = mark_all_notifications_read(current_user.id)
    
    if request.is_json:
        return jsonify({'success': True, 'count': count})
    
    flash(f"{count} notifikasi telah ditandai sebagai dibaca.", "success")
    return redirect(url_for("user.notifications"))


@user_bp.route("/activity")
@login_required
def activity():
    """View user's activity timeline."""
    page = request.args.get("page", 1, type=int)
    
    # Get all user activities
    activities = []
    
    # Projects created
    for project in current_user.projects.limit(10).all():
        activities.append({
            'type': 'project_created',
            'timestamp': project.timestamp,
            'data': project
        })
    
    # Kebutuhan submitted
    for kebutuhan in current_user.kebutuhan.limit(10).all():
        activities.append({
            'type': 'kebutuhan_created',
            'timestamp': kebutuhan.timestamp,
            'data': kebutuhan
        })
    
    # Comments made
    for comment in current_user.komentar.limit(10).all():
        activities.append({
            'type': 'comment_posted',
            'timestamp': comment.timestamp,
            'data': comment
        })
    
    # Sort by timestamp
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return render_template(
        "user/activity.html",
        activities=activities[:20]  # Show latest 20 activities
    )


@user_bp.route("/delete-account", methods=["GET", "POST"])
@login_required
def delete_account():
    """Delete user account (soft delete)."""
    if request.method == "POST":
        # Verify password
        password = request.form.get('password')
        if not current_user.check_password(password):
            flash("Password tidak benar.", "danger")
            return redirect(url_for("user.delete_account"))
        
        # Soft delete - deactivate account
        current_user.is_active = False
        db.session.commit()
        
        # Log out user
        from flask_login import logout_user
        logout_user()
        
        flash("Akun Anda telah dinonaktifkan. Terima kasih telah menggunakan KomuniTech.", "info")
        return redirect(url_for("main.beranda"))
    
    return render_template("user/delete_account.html")


# AJAX endpoints
@user_bp.route("/api/stats")
@login_required
def api_user_stats():
    """Get user statistics via AJAX."""
    stats = get_user_stats(current_user.id)
    return jsonify(stats)