import os
from werkzeug.utils import secure_filename
from flask import current_app
from typing import Optional

# Default allowed extensions
DEFAULT_ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


def allowed_file(filename: str, allowed_extensions: set = None) -> bool:
    """Check if the file extension is allowed.

    Args:
        filename: Name of the file to check
        allowed_extensions: Set of allowed extensions (defaults to DEFAULT_ALLOWED_EXTENSIONS)

    Returns:
        bool: True if allowed, False otherwise
    """
    if allowed_extensions is None:
        allowed_extensions = DEFAULT_ALLOWED_EXTENSIONS

    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def save_file(
    file, destination_type: str, id: Optional[int] = None, upload_folder: str = None
) -> Optional[str]:
    """Save uploaded file to the filesystem.

    Args:
        file: File object from request.files
        destination_type: Type of file (e.g., 'project', 'kebutuhan')
        id: Optional ID to include in filename
        upload_folder: Custom upload folder path

    Returns:
        str: Relative file path if successful, None otherwise
    """
    if upload_folder is None:
        upload_folder = os.path.join(current_app.root_path, "static/uploads")

    # Ensure upload directory exists
    os.makedirs(upload_folder, exist_ok=True)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = (
            f"{destination_type}_{id}_{filename}"
            if id
            else f"{destination_type}_{filename}"
        )
        filepath = os.path.join(upload_folder, unique_filename)

        try:
            file.save(filepath)
            return f"/static/uploads/{unique_filename}"
        except Exception as e:
            current_app.logger.error(f"Error saving file: {e}")
            return None

    return None


def validate_image(file_stream, max_size: int = 1024 * 1024 * 5) -> bool:
    """Validate image file before saving.

    Args:
        file_stream: File stream to validate
        max_size: Maximum allowed file size in bytes (default 5MB)

    Returns:
        bool: True if valid, False otherwise
    """
    if not file_stream:
        return False

    # Check file size
    file_stream.seek(0, 2)  # Seek to end
    file_size = file_stream.tell()
    file_stream.seek(0)  # Seek back to start

    if file_size > max_size:
        return False

    # TODO: Add more validation like actual image content checking
    return True


def delete_file(filepath: str) -> bool:
    """Delete a file from the filesystem.

    Args:
        filepath: Path to the file to delete (relative to static/uploads)

    Returns:
        bool: True if deletion was successful, False otherwise
    """
    try:
        # Remove "/static/uploads/" from the start of filepath if present
        if filepath.startswith("/static/uploads/"):
            filepath = filepath[16:]  # len("/static/uploads/") = 15

        # Construct absolute path
        abs_path = os.path.join(current_app.root_path, "static", "uploads", filepath)

        # Verify the file is within uploads directory to prevent directory traversal
        uploads_dir = os.path.join(current_app.root_path, "static/uploads")
        if not os.path.abspath(abs_path).startswith(os.path.abspath(uploads_dir)):
            current_app.logger.error(
                f"Attempted file deletion outside uploads directory: {abs_path}"
            )
            return False

        # Check if file exists before attempting deletion
        if os.path.exists(abs_path):
            os.remove(abs_path)
            return True
        else:
            current_app.logger.warning(f"File not found for deletion: {filepath}")
            return False

    except Exception as e:
        current_app.logger.error(f"Error deleting file {filepath}: {e}")
        return False
