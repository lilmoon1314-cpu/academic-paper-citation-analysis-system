from services.graph_service import fetch_subgraph, get_community_display_label
from utils.graph_utils import build_adjacency


def discover_frontier_papers(paper_id, hops, max_nodes):
    center_node, all_nodes, node_ids, edges = fetch_subgraph(paper_id, hops, max_nodes)
    if center_node is None:
        return None

    adj = build_adjacency(node_ids, edges)

    node_comm = {}
    node_year = {}
    node_pr = {}
    for n in all_nodes:
        nid = str(n.element_id)
        node_comm[nid] = int(n.get("communityGroup") or n.get("community") or 0)
        node_year[nid] = int(n.get("year") or 0)
        node_pr[nid] = float(n.get("pagerank") or 0)

    latest_papers = []
    for n in all_nodes:
        nid = str(n.element_id)
        yr = node_year.get(nid, 0)
        if yr > 0:
            latest_papers.append({
                "id":             nid,
                "name":           n.get("title", "Unknown"),
                "authors":        n.get("authors", ""),
                "year":           yr,
                "pagerank":       node_pr.get(nid, 0),
                "community":      node_comm.get(nid, 0),
                "communityLabel": get_community_display_label(node_comm.get(nid, 0)),
            })
    latest_papers.sort(key=lambda x: x["year"], reverse=True)
    latest_papers = latest_papers[:10]

    bridge_papers = []
    for n in all_nodes:
        nid = str(n.element_id)
        my_comm = node_comm.get(nid, 0)
        neighbors = adj.get(nid, [])
        if not neighbors:
            continue
        cross_count = 0
        cross_comms = set()
        for nb in neighbors:
            nb_comm = node_comm.get(nb, -1)
            if nb_comm != my_comm:
                cross_count += 1
                cross_comms.add(nb_comm)
        if cross_count > 0:
            bridge_papers.append({
                "id":                nid,
                "name":              n.get("title", "Unknown"),
                "authors":           n.get("authors", ""),
                "year":              node_year.get(nid, 0),
                "pagerank":          node_pr.get(nid, 0),
                "community":         my_comm,
                "communityLabel":    get_community_display_label(my_comm),
                "cross_edges":       cross_count,
                "cross_communities": len(cross_comms),
            })
    bridge_papers.sort(key=lambda x: x["cross_communities"], reverse=True)
    bridge_papers = bridge_papers[:10]

    return {
        "latest_papers":  latest_papers,
        "bridge_papers":  bridge_papers,
    }
