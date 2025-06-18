# app/services/file_service.py - Complete Implementation
import os
from typing import Optional, Tuple
from flask import current_app
from werkzeug.utils import secure_filename
from app.utils.file_utils import save_file, delete_file, allowed_file
from PIL import Image
import secrets
import string


def generate_unique_filename(original_filename: str, prefix: str = "") -> str:
    """Generate a unique filename."""
    # Get file extension
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    
    # Generate random string
    random_str = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
    
    # Create unique filename
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    
    if prefix:
        return f"{prefix}_{timestamp}_{random_str}.{ext}"
    else:
        return f"{timestamp}_{random_str}.{ext}"


def resize_image(image_path: str, max_size: Tuple[int, int]) -> None:
    """Resize image if larger than max_size."""
    try:
        with Image.open(image_path) as img:
            # Convert RGBA to RGB if necessary
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            
            # Calculate new size maintaining aspect ratio
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save with optimization
            img.save(
                image_path, 
                'JPEG', 
                quality=current_app.config.get('IMAGE_QUALITY', 85),
                optimize=True
            )
    except Exception as e:
        current_app.logger.error(f"Error resizing image: {e}")


def save_project_image(file, project_id: Optional[int] = None) -> Optional[str]:
    """Save project image file."""
    if not file or not allowed_file(file.filename):
        return None
    
    # Generate unique filename
    filename = generate_unique_filename(file.filename, f"project_{project_id}" if project_id else "project")
    
    # Create subdirectory
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'projects')
    os.makedirs(upload_folder, exist_ok=True)
    
    # Save file
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    
    # Resize if it's an image
    if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
        max_size = current_app.config.get('MEDIUM_SIZE', (800, 800))
        resize_image(filepath, max_size)
    
    # Return relative path
    return f"/static/uploads/projects/{filename}"


def save_kebutuhan_image(file, kebutuhan_id: Optional[int] = None) -> Optional[str]:
    """Save kebutuhan image file."""
    if not file or not allowed_file(file.filename):
        return None
    
    # Generate unique filename
    filename = generate_unique_filename(file.filename, f"kebutuhan_{kebutuhan_id}" if kebutuhan_id else "kebutuhan")
    
    # Create subdirectory
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'kebutuhan')
    os.makedirs(upload_folder, exist_ok=True)
    
    # Save file
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    
    # Resize if it's an image
    if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
        max_size = current_app.config.get('MEDIUM_SIZE', (800, 800))
        resize_image(filepath, max_size)
    
    # Return relative path
    return f"/static/uploads/kebutuhan/{filename}"


def save_comment_image(file) -> Optional[str]:
    """Save comment image file."""
    if not file or not allowed_file(file.filename):
        return None
    
    # Generate unique filename
    filename = generate_unique_filename(file.filename, "comment")
    
    # Create subdirectory
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'comments')
    os.makedirs(upload_folder, exist_ok=True)
    
    # Save file
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    
    # Resize if it's an image - smaller for comments
    if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
        max_size = (600, 600)
        resize_image(filepath, max_size)
    
    # Return relative path
    return f"/static/uploads/comments/{filename}"


def save_avatar_image(file, user_id: int) -> Optional[str]:
    """Save user avatar image."""
    if not file or not allowed_file(file.filename):
        return None
    
    # Generate unique filename
    filename = generate_unique_filename(file.filename, f"avatar_{user_id}")
    
    # Create subdirectory
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars')
    os.makedirs(upload_folder, exist_ok=True)
    
    # Save file
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    
    # Create thumbnail for avatar
    if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
        try:
            with Image.open(filepath) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                
                # Crop to square
                width, height = img.size
                size = min(width, height)
                left = (width - size) // 2
                top = (height - size) // 2
                right = left + size
                bottom = top + size
                img = img.crop((left, top, right, bottom))
                
                # Resize to standard avatar size
                avatar_size = (300, 300)
                img = img.resize(avatar_size, Image.Resampling.LANCZOS)
                
                # Save
                img.save(filepath, 'JPEG', quality=90, optimize=True)
        except Exception as e:
            current_app.logger.error(f"Error processing avatar: {e}")
    
    # Return relative path
    return f"/static/uploads/avatars/{filename}"


def save_temp_file(file) -> Optional[str]:
    """Save file temporarily for processing."""
    if not file:
        return None
    
    # Generate unique filename
    filename = generate_unique_filename(secure_filename(file.filename), "temp")
    
    # Create temp subdirectory
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp')
    os.makedirs(upload_folder, exist_ok=True)
    
    # Save file
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    
    # Return full path for processing
    return filepath


def cleanup_temp_files(age_hours: int = 24) -> int:
    """Clean up old temporary files."""
    from datetime import datetime, timedelta
    
    temp_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp')
    if not os.path.exists(temp_folder):
        return 0
    
    count = 0
    cutoff_time = datetime.now() - timedelta(hours=age_hours)
    
    for filename in os.listdir(temp_folder):
        filepath = os.path.join(temp_folder, filename)
        if os.path.isfile(filepath):
            file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
            if file_time < cutoff_time:
                try:
                    os.remove(filepath)
                    count += 1
                except Exception as e:
                    current_app.logger.error(f"Error deleting temp file {filename}: {e}")
    
    return count


def get_file_size(filepath: str) -> int:
    """Get file size in bytes."""
    try:
        return os.path.getsize(filepath)
    except:
        return 0


def validate_file_size(file) -> bool:
    """Validate file size against maximum allowed."""
    # Check Content-Length header
    if hasattr(file, 'content_length') and file.content_length:
        if file.content_length > current_app.config.get('MAX_FILE_SIZE', 5 * 1024 * 1024):
            return False
    
    # Save position
    pos = file.tell()
    
    # Seek to end
    file.seek(0, 2)
    size = file.tell()
    
    # Restore position
    file.seek(pos)
    
    return size <= current_app.config.get('MAX_FILE_SIZE', 5 * 1024 * 1024)


# Import datetime for timestamp generation
from datetime import datetime