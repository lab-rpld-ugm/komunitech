from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from app.services.support_service import get_user_supports
from app.services.kebutuhan_service import get_user_kebutuhan
from app.services.project_service import get_user_projects
from app.utils.pagination import generate_pagination_links

user_bp = Blueprint("user", __name__, url_prefix="/")


@user_bp.route("/supports", methods=["GET"])
@login_required
def supports():
    page = request.args.get("page", 1, type=int)
    supports = get_user_supports(current_user.id, page=page)

    next_url, prev_url = generate_pagination_links(supports, "user.supports")

    return render_template(
        "user/supports.html",
        supports=supports.items,
        next_url=next_url,
        prev_url=prev_url,
    )


@user_bp.route("/kebutuhan", methods=["GET"])
@login_required
def kebutuhans():
    page = request.args.get("page", 1, type=int)
    kebutuhan = get_user_kebutuhan(current_user.id, page=page)

    next_url, prev_url = generate_pagination_links(kebutuhan, "user.kebutuhan")

    return render_template(
        "user/kebutuhan.html",
        kebutuhan=kebutuhan.items,
        next_url=next_url,
        prev_url=prev_url,
    )


@user_bp.route("/projects", methods=["GET"])
@login_required
def projects():
    page = request.args.get("page", 1, type=int)
    projects = get_user_projects(current_user.id, page=page)

    next_url, prev_url = generate_pagination_links(projects, "user.projects")

    return render_template(
        "user/projects.html",
        projects=projects.items,
        next_url=next_url,
        prev_url=prev_url,
    )
