from flask import Blueprint, jsonify, request
from services.recommend_service import get_recommendations

recommend_bp = Blueprint('recommend', __name__)


@recommend_bp.route('/recommend')
def recommend():
    paper_id = request.args.get('id', '').strip()
    recs = get_recommendations(paper_id)
    return jsonify(recs)
