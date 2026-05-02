from flask import Blueprint, jsonify, request
from services.graph_service import fetch_subgraph, build_graph_response
from config import DEFAULT_HOPS, DEFAULT_MAX_NODES

graph_bp = Blueprint('graph', __name__)


@graph_bp.route('/graph')
def graph():
    paper_id  = request.args.get('id', '').strip()
    hops      = int(request.args.get('hops', DEFAULT_HOPS))
    max_nodes = int(request.args.get('max_nodes', DEFAULT_MAX_NODES))

    if not paper_id:
        return jsonify({"nodes": [], "edges": []})

    center_node, all_nodes, node_ids, edges = fetch_subgraph(paper_id, hops, max_nodes)
    if center_node is None:
        return jsonify({"nodes": [], "edges": []})

    result = build_graph_response(paper_id, center_node, all_nodes, node_ids, edges, hops, max_nodes)
    return jsonify(result)
