from datetime import datetime
from flask import flash
from flask_login import current_user


def format_datetime(value: datetime, format: str = "%d %b %Y %H:%M") -> str:
    """Format datetime object for display.

    Args:
        value: Datetime object to format
        format: Format string (default '%d %b %Y %H:%M')

    Returns:
        str: Formatted datetime string
    """
    if value is None:
        return ""
    return value.strftime(format)


def flash_form_errors(form):
    """Flash all form validation errors.

    Args:
        form: WTForms form object
    """
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"Error in {getattr(form, field).label.text}: {error}", "error")


def is_owner_or_admin(resource_owner_id, admin_required=False):
    """Check if current user is owner or admin.

    Args:
        resource_owner_id: ID of the resource owner
        admin_required: Whether admin role is required

    Returns:
        bool: True if authorized, False otherwise
    """
    if not current_user.is_authenticated:
        return False

    if admin_required:
        return current_user.is_admin

    return current_user.id == resource_owner_id or current_user.is_admin
