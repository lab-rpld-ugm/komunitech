from flask import Blueprint, render_template, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from app.forms import KebutuhanForm
from app.services.kebutuhan_service import (
    create_kebutuhan,
    get_kebutuhan_by_id,
)
from app.services.project_service import get_project_by_id
from app.services.file_service import save_kebutuhan_image

kebutuhan_bp = Blueprint("kebutuhan", __name__, url_prefix="/")


@kebutuhan_bp.route("/project/<int:project_id>/ajukan", methods=["GET", "POST"])
@login_required
def create(project_id):
    project = get_project_by_id(project_id)
    form = KebutuhanForm()

    if form.validate_on_submit():
        try:
            image_url = (
                save_kebutuhan_image(form.gambar.data) if form.gambar.data else None
            )
            kebutuhan = create_kebutuhan(
                judul=form.judul.data,
                deskripsi=form.deskripsi.data,
                pengaju_id=current_user.id,
                project_id=project_id,
                kategori_id=form.kategori.data,
                prioritas=form.prioritas.data,
                gambar_url=image_url,
            )
            flash("Kebutuhan submitted successfully!")
            return redirect(
                url_for("kebutuhan.detail", project_id=project_id, id=kebutuhan.id)
            )
        except Exception as e:
            flash(str(e))

    return render_template("kebutuhan/create.html", form=form, project=project)


@kebutuhan_bp.route("/project/<int:project_id>/kebutuhan/<int:id>", methods=["GET"])
def detail(project_id, id):
    project = get_project_by_id(project_id)
    kebutuhan = get_kebutuhan_by_id(id)

    if kebutuhan.project_id != project.id:
        abort(404)

    return render_template(
        "kebutuhan/detail.html", project=project, kebutuhan=kebutuhan
    )
