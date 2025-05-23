from flask import Blueprint, render_template, flash, redirect, url_for, request, abort
from flask_login import login_required, current_user
from app.forms import ProjectForm
from app.services.project_service import (
    create_project,
    get_project_by_id,
    update_project,
    get_user_projects,
    get_recent_projects,
)
from app.services.file_service import save_project_image
from app.utils.pagination import generate_pagination_links
from app.utils.helpers import is_owner_or_admin

project_bp = Blueprint("project", __name__, url_prefix="/project")


@project_bp.route("/", methods=["GET"])
def list_projects():
    page = request.args.get("page", 1, type=int)
    projects = get_recent_projects() if page == 1 else get_user_projects(page=page)

    next_url, prev_url = generate_pagination_links(projects, "project.list_projects")

    return render_template(
        "project/list.html",
        projects=projects.items,
        next_url=next_url,
        prev_url=prev_url,
    )


@project_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    form = ProjectForm()
    if form.validate_on_submit():
        try:
            image_url = (
                save_project_image(form.gambar.data) if form.gambar.data else None
            )
            project = create_project(
                judul=form.judul.data,
                deskripsi=form.deskripsi.data,
                pemilik_id=current_user.id,
                kategori_id=form.kategori.data,
                gambar_url=image_url,
            )
            flash("Project created successfully!")
            return redirect(url_for("project.detail", id=project.id))
        except Exception as e:
            flash(str(e))

    return render_template("project/create.html", form=form)


@project_bp.route("/<int:id>", methods=["GET"])
def detail(id):
    project = get_project_by_id(id)
    return render_template("project/detail.html", project=project)


@project_bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit(id):
    project = get_project_by_id(id)
    if not is_owner_or_admin(project.pengguna_id):
        abort(403)

    form = ProjectForm()
    if form.validate_on_submit():
        try:
            image_url = (
                save_project_image(form.gambar.data, id) if form.gambar.data else None
            )
            update_project(
                project_id=id,
                judul=form.judul.data,
                deskripsi=form.deskripsi.data,
                kategori_id=form.kategori.data,
                gambar_url=image_url,
            )
            flash("Project updated successfully!")
            return redirect(url_for("project.detail", id=id))
        except Exception as e:
            flash(str(e))
    elif request.method == "GET":
        form.judul.data = project.judul
        form.deskripsi.data = project.deskripsi
        form.kategori.data = project.kategori_id

    return render_template("project/edit.html", form=form, project=project)
