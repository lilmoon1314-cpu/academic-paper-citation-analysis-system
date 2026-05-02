from flask import Blueprint, jsonify, request
from services.metrics_service import compute_network_metrics
from config import DEFAULT_HOPS, DEFAULT_MAX_NODES

metrics_bp = Blueprint('metrics', __name__)


@metrics_bp.route('/network_metrics')
def network_metrics():
    paper_id  = request.args.get('id', '').strip()
    hops      = int(request.args.get('hops', DEFAULT_HOPS))
    max_nodes = int(request.args.get('max_nodes', DEFAULT_MAX_NODES))

    if not paper_id:
        return jsonify({"error": "missing id"}), 400

    result = compute_network_metrics(paper_id, hops, max_nodes)
    if result is None:
        return jsonify({"error": "paper not found"}), 404

    return jsonify(result)
