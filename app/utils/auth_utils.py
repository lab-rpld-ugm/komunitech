from flask import redirect, request, url_for
from werkzeug.urls import url_parse
from flask_login import current_user


def get_redirect_target(param_name: str = "next") -> str:
    """Get safe redirect target from request args.

    Args:
        param_name: Name of the redirect parameter (default 'next')

    Returns:
        str: Safe redirect target or None
    """
    next_page = request.args.get(param_name)

    if not next_page or url_parse(next_page).netloc != "":
        return None

    return next_page


def redirect_authenticated_user(default_endpoint: str = "beranda"):
    """Get redirect response for authenticated users.

    Args:
        default_endpoint: Default endpoint to redirect to

    Returns:
        Response: Redirect response if user is authenticated, None otherwise
    """
    if current_user.is_authenticated:
        next_page = get_redirect_target() or url_for(default_endpoint)
        return redirect(next_page)
    return None
