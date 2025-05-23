from typing import List
from flask import current_app
from app.database.models import Dukungan, Kebutuhan
from app.database.base import db


def create_support(kebutuhan_id: int, supporter_id: int) -> Dukungan:
    """Create a new support record.

    Args:
        kebutuhan_id: Supported kebutuhan ID
        supporter_id: Supporter user ID

    Returns:
        Dukungan: Created support record

    Raises:
        ValueError: If already supported or invalid
    """
    # Check if already supported
    if Dukungan.query.filter_by(
        pengguna_id=supporter_id, kebutuhan_id=kebutuhan_id
    ).first():
        raise ValueError("Already supported this kebutuhan")

    # Check if supporting own kebutuhan
    kebutuhan = Kebutuhan.query.get(kebutuhan_id)
    if kebutuhan.pengguna_id == supporter_id:
        raise ValueError("Cannot support your own kebutuhan")

    dukungan = Dukungan(pengguna_id=supporter_id, kebutuhan_id=kebutuhan_id)

    db.session.add(dukungan)
    db.session.commit()

    current_app.logger.info(f"User {supporter_id} supported kebutuhan {kebutuhan_id}")
    return dukungan


def get_user_supports(
    user_id: int, page: int = 1, per_page: int = 10
) -> List[Dukungan]:
    """Get paginated supports by a user.

    Args:
        user_id: Supporter user ID
        page: Page number
        per_page: Items per page

    Returns:
        List[Dukungan]: List of support records
    """
    return (
        Dukungan.query.filter_by(pengguna_id=user_id)
        .order_by(Dukungan.timestamp.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )


def has_supported(user_id: int, kebutuhan_id: int) -> bool:
    """Check if user has supported a kebutuhan.

    Args:
        user_id: User ID to check
        kebutuhan_id: Kebutuhan ID to check

    Returns:
        bool: True if supported, False otherwise
    """
    return (
        Dukungan.query.filter_by(pengguna_id=user_id, kebutuhan_id=kebutuhan_id).first()
        is not None
    )
