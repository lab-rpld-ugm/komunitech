# app/routes/admin_routes.py - Complete Fixed Version
from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify, abort
from flask_login import login_required, current_user
from app.forms import (
    KategoriForm, AdminUserForm, BulkActionForm, 
    StatusUpdateForm, SearchForm
)
from app.services.category_service import (
    get_all_categories, create_category, update_category, 
    delete_category, get_category_by_id
)
from app.services.user_service import (
    get_all_users, get_user_by_id, update_user, 
    delete_user, get_user_stats
)
from app.services.project_service import (
    get_all_projects, get_project_stats, bulk_update_projects
)
from app.services.kebutuhan_service import (
    get_all_kebutuhan, get_kebutuhan_stats, bulk_update_kebutuhan
)
from app.services.audit_service import (
    log_admin_action, get_audit_logs
)
from app.utils.decorators import admin_required
from app.utils.pagination import get_pagination_args
from app.database.base import db
from app.database.models import Project, Kebutuhan, Pengguna, Komentar, Dukungan
from datetime import datetime, timedelta
import json

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    """Admin dashboard with statistics and overview."""
    # Get statistics
    stats = {
        'total_users': Pengguna.query.count(),
        'active_users': Pengguna.query.filter_by(is_active=True).count(),
        'total_projects': Project.query.count(),
        'active_projects': Project.query.filter_by(status='Aktif').count(),
        'total_kebutuhan': Kebutuhan.query.count(),
        'pending_kebutuhan': Kebutuhan.query.filter_by(status='Diajukan').count(),
        'total_comments': Komentar.query.count(),
        'total_supports': Dukungan.query.count(),
    }
    
    # Get recent activities
    recent_projects = Project.query.order_by(Project.timestamp.desc()).limit(5).all()
    recent_kebutuhan = Kebutuhan.query.order_by(Kebutuhan.timestamp.desc()).limit(5).all()
    recent_users = Pengguna.query.order_by(Pengguna.created_at.desc()).limit(5).all()
    
    # Get trend data (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    daily_stats = []
    for i in range(7):
        date = week_ago + timedelta(days=i)
        next_date = date + timedelta(days=1)
        daily_stats.append({
            'date': date.strftime('%Y-%m-%d'),
            'projects': Project.query.filter(
                Project.timestamp >= date,
                Project.timestamp < next_date
            ).count(),
            'kebutuhan': Kebutuhan.query.filter(
                Kebutuhan.timestamp >= date,
                Kebutuhan.timestamp < next_date
            ).count(),
            'users': Pengguna.query.filter(
                Pengguna.created_at >= date,
                Pengguna.created_at < next_date
            ).count()
        })
    
    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_projects=recent_projects,
        recent_kebutuhan=recent_kebutuhan,
        recent_users=recent_users,
        daily_stats=daily_stats
    )


@admin_bp.route("/categories", methods=["GET", "POST"])
@login_required
@admin_required
def categories():
    """Manage categories."""
    form = KategoriForm()
    if form.validate_on_submit():
        try:
            category = create_category(
                nama=form.nama.data, 
                deskripsi=form.deskripsi.data
            )
            log_admin_action(
                user_id=current_user.id,
                action="create_category",
                entity_type="category",
                entity_id=category.id,
                new_value=f"nama: {category.nama}"
            )
            flash("Kategori berhasil ditambahkan!", "success")
            return redirect(url_for("admin.categories"))
        except ValueError as e:
            flash(str(e), "danger")

    categories = get_all_categories()
    return render_template(
        "admin/categories.html", 
        form=form, 
        categories=categories
    )


@admin_bp.route("/categories/<int:id>/edit", methods=["POST"])
@login_required
@admin_required
def edit_category(id):
    """Edit a category."""
    category = get_category_by_id(id)
    if not category:
        abort(404)
    
    nama = request.form.get('nama')
    deskripsi = request.form.get('deskripsi')
    
    try:
        old_value = f"nama: {category.nama}, deskripsi: {category.deskripsi}"
        update_category(id, nama=nama, deskripsi=deskripsi)
        log_admin_action(
            user_id=current_user.id,
            action="update_category",
            entity_type="category",
            entity_id=id,
            old_value=old_value,
            new_value=f"nama: {nama}, deskripsi: {deskripsi}"
        )
        flash("Kategori berhasil diperbarui!", "success")
    except ValueError as e:
        flash(str(e), "danger")
    
    return redirect(url_for("admin.categories"))


@admin_bp.route("/categories/<int:id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_category(id):
    """Delete a category."""
    category = get_category_by_id(id)
    if not category:
        abort(404)
    
    if not category.can_delete():
        flash("Kategori tidak dapat dihapus karena sedang digunakan.", "danger")
        return redirect(url_for("admin.categories"))
    
    try:
        delete_category(id)
        log_admin_action(
            user_id=current_user.id,
            action="delete_category",
            entity_type="category",
            entity_id=id,
            old_value=f"nama: {category.nama}"
        )
        flash("Kategori berhasil dihapus!", "success")
    except Exception as e:
        flash(str(e), "danger")
    
    return redirect(url_for("admin.categories"))


@admin_bp.route("/users")
@login_required
@admin_required
def users():
    """List all users with pagination and search."""
    page, per_page = get_pagination_args()
    search_query = request.args.get('q', '')
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')
    
    # Build query
    query = Pengguna.query
    
    if search_query:
        query = query.filter(
            db.or_(
                Pengguna.username.contains(search_query),
                Pengguna.email.contains(search_query),
                Pengguna.nama.contains(search_query)
            )
        )
    
    if role_filter:
        query = query.filter_by(role=role_filter)
    
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)
    
    users = query.order_by(Pengguna.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template(
        "admin/users.html",
        users=users,
        search_query=search_query,
        role_filter=role_filter,
        status_filter=status_filter
    )


@admin_bp.route("/users/<int:id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_user(id):
    """Edit user details."""
    user = get_user_by_id(id)
    if not user:
        abort(404)
    
    form = AdminUserForm(obj=user)
    
    if form.validate_on_submit():
        try:
            changes = {}
            if user.nama != form.nama.data:
                changes['nama'] = (user.nama, form.nama.data)
            if user.email != form.email.data:
                changes['email'] = (user.email, form.email.data)
            if user.role != form.role.data:
                changes['role'] = (user.role, form.role.data)
            if user.is_active != form.is_active.data:
                changes['is_active'] = (user.is_active, form.is_active.data)
            
            update_user(
                user_id=id,
                nama=form.nama.data,
                email=form.email.data,
                role=form.role.data,
                is_active=form.is_active.data,
                email_verified=form.email_verified.data,
                new_password=form.new_password.data if form.new_password.data else None
            )
            
            # Log changes
            for field, (old_val, new_val) in changes.items():
                log_admin_action(
                    user_id=current_user.id,
                    action=f"update_user_{field}",
                    entity_type="user",
                    entity_id=id,
                    old_value=str(old_val),
                    new_value=str(new_val)
                )
            
            flash("User berhasil diperbarui!", "success")
            return redirect(url_for("admin.users"))
        except ValueError as e:
            flash(str(e), "danger")
    
    # Get user statistics
    stats = get_user_stats(id)
    
    return render_template(
        "admin/edit_user.html",
        form=form,
        user=user,
        stats=stats
    )


@admin_bp.route("/projects")
@login_required
@admin_required
def projects():
    """List all projects with filters."""
    page, per_page = get_pagination_args()
    search_query = request.args.get('q', '')
    status_filter = request.args.get('status', '')
    category_filter = request.args.get('category', '')
    
    # Build query
    query = Project.query
    
    if search_query:
        query = query.filter(
            db.or_(
                Project.judul.contains(search_query),
                Project.deskripsi.contains(search_query)
            )
        )
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    if category_filter:
        query = query.filter_by(kategori_id=category_filter)
    
    projects = query.order_by(Project.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get categories for filter
    categories = get_all_categories()
    
    return render_template(
        "admin/projects.html",
        projects=projects,
        categories=categories,
        search_query=search_query,
        status_filter=status_filter,
        category_filter=category_filter
    )


@admin_bp.route("/projects/<int:id>/status", methods=["GET", "POST"])
@login_required
@admin_required
def update_project_status(id):
    """Update project status."""
    project = Project.query.get_or_404(id)
    form = StatusUpdateForm(entity_type="project", obj=project)
    
    if form.validate_on_submit():
        old_status = project.status
        project.status = form.status.data
        db.session.commit()
        
        log_admin_action(
            user_id=current_user.id,
            action="update_project_status",
            entity_type="project",
            entity_id=id,
            old_value=old_status,
            new_value=form.status.data
        )
        
        flash("Status project berhasil diperbarui!", "success")
        return redirect(url_for("admin.projects"))
    
    return render_template(
        "admin/update_status.html",
        form=form,
        entity=project,
        entity_type="project"
    )


@admin_bp.route("/kebutuhan")
@login_required
@admin_required
def kebutuhan():
    """List all kebutuhan with filters."""
    page, per_page = get_pagination_args()
    search_query = request.args.get('q', '')
    status_filter = request.args.get('status', '')
    priority_filter = request.args.get('priority', '')
    
    # Build query
    query = Kebutuhan.query
    
    if search_query:
        query = query.filter(
            db.or_(
                Kebutuhan.judul.contains(search_query),
                Kebutuhan.deskripsi.contains(search_query)
            )
        )
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    if priority_filter:
        query = query.filter_by(prioritas=priority_filter)
    
    kebutuhan_list = query.order_by(Kebutuhan.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template(
        "admin/kebutuhan.html",
        kebutuhan=kebutuhan_list,
        search_query=search_query,
        status_filter=status_filter,
        priority_filter=priority_filter
    )


@admin_bp.route("/bulk-action", methods=["POST"])
@login_required
@admin_required
def bulk_action():
    """Handle bulk actions on entities."""
    form = BulkActionForm()
    
    if form.validate_on_submit():
        action = form.action.data
        items = json.loads(form.items.data)
        entity_type = request.form.get('entity_type', 'project')
        
        try:
            if entity_type == 'project':
                result = bulk_update_projects(items, action)
            elif entity_type == 'kebutuhan':
                result = bulk_update_kebutuhan(items, action)
            else:
                raise ValueError("Invalid entity type")
            
            log_admin_action(
                user_id=current_user.id,
                action=f"bulk_{action}_{entity_type}",
                entity_type=entity_type,
                new_value=f"items: {items}"
            )
            
            flash(f"Berhasil melakukan {action} pada {result['affected']} item.", "success")
        except Exception as e:
            flash(str(e), "danger")
    
    return redirect(request.referrer or url_for("admin.dashboard"))


@admin_bp.route("/audit-logs")
@login_required
@admin_required
def audit_logs():
    """View audit logs."""
    page, per_page = get_pagination_args()
    user_filter = request.args.get('user', '')
    action_filter = request.args.get('action', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    logs = get_audit_logs(
        page=page,
        per_page=per_page,
        user_id=user_filter,
        action=action_filter,
        date_from=date_from,
        date_to=date_to
    )
    
    # Get users for filter
    users = Pengguna.query.filter_by(role='Admin').all()
    
    return render_template(
        "admin/audit_logs.html",
        logs=logs,
        users=users,
        user_filter=user_filter,
        action_filter=action_filter,
        date_from=date_from,
        date_to=date_to
    )


@admin_bp.route("/settings")
@login_required
@admin_required
def settings():
    """Admin settings page."""
    return render_template("admin/settings.html")


# API endpoints for admin dashboard
@admin_bp.route("/api/stats")
@login_required
@admin_required
def api_stats():
    """Get statistics for dashboard charts."""
    period = request.args.get('period', 'week')
    
    if period == 'week':
        days = 7
    elif period == 'month':
        days = 30
    else:
        days = 365
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get daily stats
    stats = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        next_date = date + timedelta(days=1)
        
        stats.append({
            'date': date.strftime('%Y-%m-%d'),
            'projects': Project.query.filter(
                Project.timestamp >= date,
                Project.timestamp < next_date
            ).count(),
            'kebutuhan': Kebutuhan.query.filter(
                Kebutuhan.timestamp >= date,
                Kebutuhan.timestamp < next_date
            ).count(),
            'users': Pengguna.query.filter(
                Pengguna.created_at >= date,
                Pengguna.created_at < next_date
            ).count(),
            'supports': Dukungan.query.filter(
                Dukungan.timestamp >= date,
                Dukungan.timestamp < next_date
            ).count()
        })
    
    return jsonify({
        'success': True,
        'data': stats
    })