from flask import Blueprint, flash, redirect, url_for
from flask_login import login_required, current_user
from app.forms import KomentarForm
from app.services.comment_service import create_comment
from app.services.kebutuhan_service import get_kebutuhan_by_id
from app.services.file_service import save_comment_image

comment_bp = Blueprint("komentar", __name__, url_prefix="/")


@comment_bp.route("/kebutuhan/<int:kebutuhan_id>/comment", methods=["POST"])
@login_required
def create(kebutuhan_id):
    form = KomentarForm()
    kebutuhan = get_kebutuhan_by_id(kebutuhan_id)

    if form.validate_on_submit():
        try:
            image_url = (
                save_comment_image(form.gambar.data) if form.gambar.data else None
            )
            create_comment(
                isi=form.isi.data,
                kebutuhan_id=kebutuhan_id,
                penulis_id=current_user.id,
                gambar_url=image_url,
            )
            flash("Comment added successfully!")
        except Exception as e:
            flash(str(e))

    return redirect(
        url_for("kebutuhan.detail", project_id=kebutuhan.project_id, id=kebutuhan_id)
    )
