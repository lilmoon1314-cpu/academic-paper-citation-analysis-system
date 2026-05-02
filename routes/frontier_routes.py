from flask import Blueprint, jsonify, request
from services.frontier_service import discover_frontier_papers
from config import DEFAULT_HOPS, DEFAULT_MAX_NODES

frontier_bp = Blueprint('frontier', __name__)


@frontier_bp.route('/frontier_papers')
def frontier_papers():
    paper_id  = request.args.get('id', '').strip()
    hops      = int(request.args.get('hops', DEFAULT_HOPS))
    max_nodes = int(request.args.get('max_nodes', DEFAULT_MAX_NODES))

    if not paper_id:
        return jsonify({"error": "missing id"}), 400

    result = discover_frontier_papers(paper_id, hops, max_nodes)
    if result is None:
        return jsonify({"error": "paper not found"}), 404

    return jsonify(result)
