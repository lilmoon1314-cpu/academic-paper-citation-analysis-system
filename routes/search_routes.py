from flask import Blueprint, jsonify, request
from services.search_service import search_suggest, check_fulltext_index, create_fulltext_index

search_bp = Blueprint('search', __name__)


@search_bp.route('/search_suggest')
def suggest():
    keyword = request.args.get('q', '').strip()
    results = search_suggest(keyword)
    return jsonify(results)


@search_bp.route('/api/check_index')
def check_index():
    result = check_fulltext_index()
    return jsonify(result)


@search_bp.route('/api/create_index')
def create_index():
    result = create_fulltext_index()
    return jsonify(result)
