# app/routes/search_routes.py - New File
from flask import Blueprint, render_template, request, jsonify
from app.forms import SearchForm
from app.services.search_service import (
    search_projects, search_kebutuhan, search_users,
    get_search_suggestions, search_all
)
from app.utils.pagination import get_pagination_args

search_bp = Blueprint("search", __name__, url_prefix="/search")


@search_bp.route("/", methods=["GET", "POST"])
def search():
    """Main search page."""
    form = SearchForm()
    results = {
        'projects': [],
        'kebutuhan': [],
        'users': [],
        'total': 0
    }
    
    if form.validate_on_submit() or request.args.get('q'):
        query = form.query.data or request.args.get('q', '')
        category = form.category.data or request.args.get('category', 0, type=int)
        search_type = form.search_type.data or request.args.get('type', 'all')
        
        page, per_page = get_pagination_args()
        
        if search_type == 'all':
            results = search_all(query, category, page, per_page)
        elif search_type == 'projects':
            results['projects'] = search_projects(query, category, page, per_page)
            results['total'] = results['projects'].total if results['projects'] else 0
        elif search_type == 'kebutuhan':
            results['kebutuhan'] = search_kebutuhan(query, category, page, per_page)
            results['total'] = results['kebutuhan'].total if results['kebutuhan'] else 0
        
        # Update form data for GET requests
        if request.method == 'GET':
            form.query.data = query
            form.category.data = category
            form.search_type.data = search_type
    
    return render_template(
        "search/results.html",
        form=form,
        results=results,
        query=request.args.get('q', '')
    )


@search_bp.route("/suggestions")
def suggestions():
    """Get search suggestions (autocomplete)."""
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    suggestions = get_search_suggestions(query, limit=10)
    return jsonify(suggestions)


@search_bp.route("/advanced")
def advanced_search():
    """Advanced search page with more filters."""
    return render_template("search/advanced.html")