from flask import Blueprint, flash, redirect, url_for
from flask_login import login_required, current_user
from app.services.support_service import create_support, has_supported
from app.services.kebutuhan_service import get_kebutuhan_by_id

support_bp = Blueprint("support", __name__, url_prefix="/")


@support_bp.route("/kebutuhan/<int:kebutuhan_id>/support", methods=["POST"])
@login_required
def support(kebutuhan_id):
    kebutuhan = get_kebutuhan_by_id(kebutuhan_id)

    try:
        if has_supported(current_user.id, kebutuhan_id):
            flash("You already supported this kebutuhan")
        else:
            create_support(kebutuhan_id, current_user.id)
            flash("Support recorded successfully!")
    except ValueError as e:
        flash(str(e))

    return redirect(
        url_for("kebutuhan.detail", project_id=kebutuhan.project_id, id=kebutuhan_id)
    )
