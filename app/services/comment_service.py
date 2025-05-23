from typing import List, Optional
from flask import current_app
from app.database.models import Komentar
from app.database.base import db


def create_comment(
    isi: str, kebutuhan_id: int, penulis_id: int, gambar_url: Optional[str] = None
) -> Komentar:
    """Create a new comment.

    Args:
        isi: Comment content
        kebutuhan_id: Related kebutuhan ID
        penulis_id: Author user ID
        gambar_url: Optional image URL

    Returns:
        Komentar: Created comment
    """
    komentar = Komentar(
        isi=isi,
        kebutuhan_id=kebutuhan_id,
        pengguna_id=penulis_id,
        gambar_url=gambar_url,
    )

    db.session.add(komentar)
    db.session.commit()

    current_app.logger.info(f"New comment created on kebutuhan {kebutuhan_id}")
    return komentar


def get_kebutuhan_comments(kebutuhan_id: int) -> List[Komentar]:
    """Get all comments for a kebutuhan.

    Args:
        kebutuhan_id: Kebutuhan ID

    Returns:
        List[Komentar]: List of comments
    """
    return (
        Komentar.query.filter_by(kebutuhan_id=kebutuhan_id)
        .order_by(Komentar.timestamp.asc())
        .all()
    )
