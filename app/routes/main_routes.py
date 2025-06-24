from flask import Blueprint, render_template
from app.database.models import Project


main_bp = Blueprint("main", __name__, url_prefix="/")


@main_bp.route("/")
def beranda():
    # Ambil beberapa project terbaru untuk ditampilkan di homepage
    projects = Project.query.order_by(Project.timestamp.desc()).limit(6).all()
    return render_template("index.html", title="Beranda", projects=projects)


@main_bp.route("/tentang")
def tentang():
    return render_template("tentang.html", title="Tentang KomuniTech")
