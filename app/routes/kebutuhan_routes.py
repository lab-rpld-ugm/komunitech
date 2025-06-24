# app/routes/kebutuhan_routes.py - Complete Fixed Version
from flask import Blueprint, render_template, flash, redirect, url_for, abort, request
from flask_login import login_required, current_user
from app.forms import KebutuhanForm, KomentarForm, StatusUpdateForm
from app.services.kebutuhan_service import (
    create_kebutuhan, get_kebutuhan_by_id, update_kebutuhan,
    delete_kebutuhan as delete_kebutuhan_service,
    get_project_kebutuhan
)
from app.services.project_service import get_project_by_id
from app.services.comment_service import create_comment, get_kebutuhan_comments
from app.services.support_service import has_supported
from app.services.file_service import save_kebutuhan_image, save_comment_image
from app.services.notification_service import create_notification
from app.utils.file_utils import delete_file
from app.utils.decorators import admin_required
from app.database.base import db

kebutuhan_bp = Blueprint("kebutuhan", __name__, url_prefix="/kebutuhan")


@kebutuhan_bp.route("/project/<int:project_id>/create", methods=["GET", "POST"])
@login_required
def create(project_id):
    """Create new kebutuhan for a project."""
    project = get_project_by_id(project_id)
    if not project:
        abort(404)
    
    # Check if project is active
    if project.status != "Aktif":
        flash("Tidak dapat menambahkan kebutuhan pada project yang tidak aktif.", "warning")
        return redirect(url_for("project.detail", id=project_id))
    
    form = KebutuhanForm()

    if form.validate_on_submit():
        try:
            image_url = None
            if form.gambar.data:
                image_url = save_kebutuhan_image(form.gambar.data)
                
            kebutuhan = create_kebutuhan(
                judul=form.judul.data,
                deskripsi=form.deskripsi.data,
                pengaju_id=current_user.id,
                project_id=project_id,
                kategori_id=form.kategori.data,
                prioritas=form.prioritas.data,
                gambar_url=image_url
            )
            
            # Notify project owner
            if project.pengguna_id != current_user.id:
                create_notification(
                    user_id=project.pengguna_id,
                    type="new_kebutuhan",
                    title="Kebutuhan baru pada project Anda",
                    message=f"{current_user.nama} mengajukan kebutuhan '{kebutuhan.judul}' pada project '{project.judul}'",
                    link=url_for("kebutuhan.detail", project_id=project_id, id=kebutuhan.id)
                )
            
            flash("Kebutuhan berhasil diajukan!", "success")
            return redirect(url_for("kebutuhan.detail", project_id=project_id, id=kebutuhan.id))
        except Exception as e:
            db.session.rollback()
            if 'image_url' in locals() and image_url:
                delete_file(image_url)
            flash(f"Terjadi kesalahan: {str(e)}", "danger")

    return render_template("kebutuhan/create.html", form=form, project=project)


@kebutuhan_bp.route("/project/<int:project_id>/kebutuhan/<int:id>", methods=["GET", "POST"])
def detail(project_id, id):
    """View kebutuhan detail with comments."""
    project = get_project_by_id(project_id)
    kebutuhan = get_kebutuhan_by_id(id)
    
    if not project or not kebutuhan:
        abort(404)
    
    if kebutuhan.project_id != project.id:
        abort(404)
    
    # Increment view count
    kebutuhan.increment_views()
    
    # Initialize comment form
    form = KomentarForm()
    
    # Handle comment submission
    if form.validate_on_submit() and current_user.is_authenticated:
        try:
            image_url = None
            if form.gambar.data:
                image_url = save_comment_image(form.gambar.data)
                
            comment = create_comment(
                isi=form.isi.data,
                kebutuhan_id=id,
                penulis_id=current_user.id,
                gambar_url=image_url,
                parent_id=form.parent_id.data if form.parent_id.data else None
            )
            
            # Notify kebutuhan owner
            if kebutuhan.pengguna_id != current_user.id:
                create_notification(
                    user_id=kebutuhan.pengguna_id,
                    type="comment",
                    title="Komentar baru pada kebutuhan Anda",
                    message=f"{current_user.nama} mengomentari kebutuhan '{kebutuhan.judul}'",
                    link=url_for("kebutuhan.detail", project_id=project_id, id=id)
                )
            
            flash("Komentar berhasil ditambahkan!", "success")
            return redirect(url_for("kebutuhan.detail", project_id=project_id, id=id))
        except Exception as e:
            db.session.rollback()
            if 'image_url' in locals() and image_url:
                delete_file(image_url)
            flash(f"Terjadi kesalahan: {str(e)}", "danger")
    
    # Get comments
    komentar = get_kebutuhan_comments(id)
    
    # Check if user supported
    user_supported = False
    if current_user.is_authenticated:
        user_supported = has_supported(current_user.id, id)
    
    return render_template(
        "kebutuhan/detail.html", 
        project=project, 
        kebutuhan=kebutuhan,
        form=form,
        komentar=komentar,
        user_supported=user_supported
    )


@kebutuhan_bp.route("/project/<int:project_id>/kebutuhan/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit(project_id, id):
    """Edit kebutuhan."""
    project = get_project_by_id(project_id)
    kebutuhan = get_kebutuhan_by_id(id)
    
    if not project or not kebutuhan:
        abort(404)
    
    if kebutuhan.project_id != project.id:
        abort(404)
    
    # Check permission
    if not kebutuhan.can_edit(current_user):
        flash("Anda tidak memiliki izin untuk mengedit kebutuhan ini.", "danger")
        return redirect(url_for("kebutuhan.detail", project_id=project_id, id=id))
    
    # Check if kebutuhan can be edited
    if kebutuhan.status not in ["Diajukan", "Diproses"]:
        flash("Kebutuhan yang sudah selesai atau ditolak tidak dapat diedit.", "warning")
        return redirect(url_for("kebutuhan.detail", project_id=project_id, id=id))
    
    form = KebutuhanForm(obj=kebutuhan)
    
    if form.validate_on_submit():
        try:
            image_url = kebutuhan.gambar_url
            
            # Handle image deletion
            if form.delete_gambar.data and image_url:
                delete_file(image_url)
                image_url = None
            
            # Handle new image upload
            if form.gambar.data:
                # Delete old image if exists
                if image_url:
                    delete_file(image_url)
                image_url = save_kebutuhan_image(form.gambar.data, id)
            
            update_kebutuhan(
                kebutuhan_id=id,
                judul=form.judul.data,
                deskripsi=form.deskripsi.data,
                kategori_id=form.kategori.data,
                prioritas=form.prioritas.data,
                gambar_url=image_url
            )
            
            flash("Kebutuhan berhasil diperbarui!", "success")
            return redirect(url_for("kebutuhan.detail", project_id=project_id, id=id))
        except Exception as e:
            db.session.rollback()
            flash(f"Terjadi kesalahan: {str(e)}", "danger")
    
    elif request.method == "GET":
        form.kategori.data = kebutuhan.kategori_id
        form.prioritas.data = kebutuhan.prioritas
    
    return render_template(
        "kebutuhan/edit.html", 
        form=form, 
        project=project, 
        kebutuhan=kebutuhan
    )


@kebutuhan_bp.route("/project/<int:project_id>/kebutuhan/<int:id>/delete", methods=["POST"])
@login_required
def delete(project_id, id):
    """Delete kebutuhan."""
    kebutuhan = get_kebutuhan_by_id(id)
    
    if not kebutuhan:
        abort(404)
    
    if kebutuhan.project_id != project_id:
        abort(404)
    
    # Check permission
    if not kebutuhan.can_edit(current_user):
        flash("Anda tidak memiliki izin untuk menghapus kebutuhan ini.", "danger")
        return redirect(url_for("kebutuhan.detail", project_id=project_id, id=id))
    
    # Check if kebutuhan can be deleted
    if kebutuhan.status == "Selesai":
        flash("Kebutuhan yang sudah selesai tidak dapat dihapus.", "warning")
        return redirect(url_for("kebutuhan.detail", project_id=project_id, id=id))
    
    try:
        # Delete associated image if exists
        if kebutuhan.gambar_url:
            delete_file(kebutuhan.gambar_url)
        
        delete_kebutuhan_service(id)
        flash("Kebutuhan berhasil dihapus!", "success")
        return redirect(url_for("project.detail", id=project_id))
    except Exception as e:
        db.session.rollback()
        flash(f"Terjadi kesalahan: {str(e)}", "danger")
        return redirect(url_for("kebutuhan.detail", project_id=project_id, id=id))


@kebutuhan_bp.route("/project/<int:project_id>/kebutuhan/<int:id>/status", methods=["GET", "POST"])
@login_required
def update_status(project_id, id):
    """Update kebutuhan status (for project owner or admin)."""
    kebutuhan = get_kebutuhan_by_id(id)
    
    if not kebutuhan or kebutuhan.project_id != project_id:
        abort(404)
    
    # Check permission - project owner or admin
    if not (current_user.id == kebutuhan.project.pengguna_id or current_user.is_admin):
        flash("Anda tidak memiliki izin untuk mengubah status kebutuhan ini.", "danger")
        return redirect(url_for("kebutuhan.detail", project_id=project_id, id=id))
    
    form = StatusUpdateForm(entity_type="kebutuhan", obj=kebutuhan)
    
    if form.validate_on_submit():
        try:
            old_status = kebutuhan.status
            kebutuhan.update_status(form.status.data, current_user.id)
            
            # Notify kebutuhan owner if status changed
            if old_status != form.status.data:
                create_notification(
                    user_id=kebutuhan.pengguna_id,
                    type="status_change",
                    title="Status kebutuhan Anda diperbarui",
                    message=f"Status kebutuhan '{kebutuhan.judul}' diubah dari {old_status} menjadi {form.status.data}",
                    link=url_for("kebutuhan.detail", project_id=project_id, id=id)
                )
            
            flash("Status kebutuhan berhasil diperbarui!", "success")
            return redirect(url_for("kebutuhan.detail", project_id=project_id, id=id))
        except Exception as e:
            db.session.rollback()
            flash(f"Terjadi kesalahan: {str(e)}", "danger")
    
    return render_template(
        "kebutuhan/update_status.html",
        form=form,
        project=kebutuhan.project,
        kebutuhan=kebutuhan
    )


@kebutuhan_bp.route("/list")
def list_all():
    """List all kebutuhan across all projects."""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('ITEMS_PER_PAGE', 12)
    
    # Filters
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    category = request.args.get('category', '')
    sort = request.args.get('sort', 'newest')
    
    # Build query
    query = Kebutuhan.query
    
    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(prioritas=priority)
    if category:
        query = query.filter_by(kategori_id=category)
    
    # Sorting
    if sort == 'newest':
        query = query.order_by(Kebutuhan.timestamp.desc())
    elif sort == 'oldest':
        query = query.order_by(Kebutuhan.timestamp.asc())
    elif sort == 'most_supported':
        query = query.join(Dukungan).group_by(Kebutuhan.id).order_by(
            db.func.count(Dukungan.id).desc()
        )
    elif sort == 'high_priority':
        query = query.order_by(
            db.case(
                (Kebutuhan.prioritas == 'Tinggi', 1),
                (Kebutuhan.prioritas == 'Sedang', 2),
                (Kebutuhan.prioritas == 'Rendah', 3)
            )
        )
    
    kebutuhan = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Get categories for filter
    from app.services.category_service import get_all_categories
    categories = get_all_categories()
    
    return render_template(
        "kebutuhan/list.html",
        kebutuhan=kebutuhan,
        categories=categories,
        current_filters={
            'status': status,
            'priority': priority,
            'category': category,
            'sort': sort
        }
    )