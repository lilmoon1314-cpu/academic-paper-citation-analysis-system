from services.graph_service import fetch_subgraph
from utils.graph_utils import (
    build_adjacency,
    find_connected_components,
    compute_density,
    compute_average_path_length,
    compute_modularity,
)


def compute_network_metrics(paper_id, hops, max_nodes):
    center_node, all_nodes, node_ids, edges = fetch_subgraph(paper_id, hops, max_nodes)
    if center_node is None:
        return None

    N = len(node_ids)
    E = len(edges)

    adj = build_adjacency(node_ids, edges)

    density = compute_density(N, E)

    components = find_connected_components(node_ids, adj)
    largest_comp_size = len(components[0]) if components else 0
    largest_comp_pct = round(largest_comp_size / N * 100, 1) if N > 0 else 0
    component_count = len(components)

    avg_path_length = compute_average_path_length(node_ids, adj)

    node_comm = {}
    for n in all_nodes:
        nid = str(n.element_id)
        node_comm[nid] = int(n.get("communityGroup") or n.get("community") or 0)

    modularity = compute_modularity(node_ids, edges, adj, node_comm)

    pr_max_val = max(float(n.get("pagerank") or 0) for n in all_nodes)
    top10 = []
    for n in all_nodes:
        nid = str(n.element_id)
        raw_pr = float(n.get("pagerank") or 0)
        norm_pr = raw_pr / pr_max_val if pr_max_val > 1 else raw_pr
        deg = len(adj.get(nid, []))
        top10.append({
            "id":        nid,
            "name":      n.get("title", "Unknown"),
            "pagerank":  round(norm_pr, 6),
            "degree":    deg,
            "community": node_comm.get(nid, 0),
            "year":      n.get("year", 0),
        })
    top10.sort(key=lambda x: x["pagerank"], reverse=True)
    top10 = top10[:10]

    return {
        "density":           round(density, 6),
        "avg_path_length":   avg_path_length,
        "largest_component": {
            "size":             largest_comp_size,
            "percentage":       largest_comp_pct,
            "total_components": component_count,
        },
        "modularity":        modularity,
        "top10_centrality":  top10,
        "summary": {
            "nodes": N,
            "edges": E,
        }
    }
