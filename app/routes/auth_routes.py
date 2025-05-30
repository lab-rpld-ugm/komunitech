from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user
from werkzeug.urls import url_parse
from app.forms import LoginForm, RegisterForm
from app.services.auth_service import register_user, authenticate_user
from app.utils.auth_utils import redirect_authenticated_user

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if redirect_authenticated_user():
        return redirect(url_for("main.beranda"))

    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = authenticate_user(form.username.data, form.password.data)
            if user:
                login_user(user)
                next_page = request.args.get("next")
                if not next_page or url_parse(next_page).netloc != "":
                    next_page = url_for("main.beranda")
                return redirect(next_page)
            flash("Invalid username or password")
        except Exception as e:
            flash(str(e))

    return render_template("auth/login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if redirect_authenticated_user():
        return redirect(url_for("main.beranda"))

    form = RegisterForm()
    if form.validate_on_submit():
        try:
            register_user(
                username=form.username.data,
                email=form.email.data,
                nama=form.nama.data,
                password=form.password.data,
            )
            flash("Registration successful! Please login.")
            return redirect(url_for("auth.login"))
        except ValueError as e:
            flash(str(e))

    return render_template("auth/daftar.html", form=form)


@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.beranda"))
