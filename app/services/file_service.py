from typing import Optional
from app.utils.file_utils import save_file
from flask import current_app


def save_project_image(file, project_id: Optional[int] = None) -> Optional[str]:
    """Save project image file.

    Args:
        file: Uploaded file
        project_id: Optional project ID for filename

    Returns:
        str: Saved file path or None
    """
    upload_folder = current_app.config.get("UPLOAD_FOLDER")
    return save_file(file, "project", project_id, upload_folder)


def save_kebutuhan_image(file, kebutuhan_id: Optional[int] = None) -> Optional[str]:
    """Save kebutuhan image file.

    Args:
        file: Uploaded file
        kebutuhan_id: Optional kebutuhan ID for filename

    Returns:
        str: Saved file path or None
    """
    upload_folder = current_app.config.get("UPLOAD_FOLDER")
    return save_file(file, "kebutuhan", kebutuhan_id, upload_folder)


def save_comment_image(file) -> Optional[str]:
    """Save comment image file.

    Args:
        file: Uploaded file

    Returns:
        str: Saved file path or None
    """
    upload_folder = current_app.config.get("UPLOAD_FOLDER")
    return save_file(file, "komentar", None, upload_folder)
