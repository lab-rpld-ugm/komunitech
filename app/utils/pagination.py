from flask import url_for, request


def generate_pagination_links(paginated_query, endpoint: str, **kwargs):
    """Generate next and previous pagination links.

    Args:
        paginated_query: Paginated query object
        endpoint: Endpoint name to generate URLs for
        **kwargs: Additional arguments to include in URLs

    Returns:
        tuple: (next_url, prev_url)
    """
    next_url = (
        url_for(endpoint, halaman=paginated_query.next_num, **kwargs)
        if paginated_query.has_next
        else None
    )

    prev_url = (
        url_for(endpoint, halaman=paginated_query.prev_num, **kwargs)
        if paginated_query.has_prev
        else None
    )

    return next_url, prev_url


def get_pagination_args(default_page: int = 1, default_per_page: int = 10):
    """Get pagination arguments from request.

    Args:
        default_page: Default page number
        default_per_page: Default items per page

    Returns:
        tuple: (page, per_page)
    """
    page = request.args.get("halaman", default_page, type=int)
    per_page = request.args.get("per_halaman", default_per_page, type=int)
    return page, per_page
