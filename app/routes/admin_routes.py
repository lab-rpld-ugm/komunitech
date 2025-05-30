from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required
from app.forms import KategoriForm
from app.services.category_service import (
    get_all_categories,
    create_category,
)
from app.utils.decorators import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/")


@admin_bp.route("/categories", methods=["GET", "POST"])
@login_required
@admin_required
def categories():
    form = KategoriForm()
    if form.validate_on_submit():
        try:
            create_category(nama=form.nama.data, deskripsi=form.deskripsi.data)
            flash("Category created successfully!")
            return redirect(url_for("admin.categories"))
        except ValueError as e:
            flash(str(e))

    categories = get_all_categories()
    return render_template("admin/categories.html", form=form, categories=categories)
