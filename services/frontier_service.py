from services.graph_service import fetch_subgraph, get_community_display_label
from utils.graph_utils import build_adjacency
from config import CURRENT_YEAR


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

    recent_threshold = CURRENT_YEAR - 2

    recent_papers = []
    for n in all_nodes:
        nid = str(n.element_id)
        yr = node_year.get(nid, 0)
        if yr >= recent_threshold:
            deg = len(adj.get(nid, []))
            recent_papers.append({
                "id":             nid,
                "name":           n.get("title", "Unknown"),
                "authors":        n.get("authors", ""),
                "year":           yr,
                "pagerank":       node_pr.get(nid, 0),
                "degree":         deg,
                "community":      node_comm.get(nid, 0),
                "communityLabel": get_community_display_label(node_comm.get(nid, 0)),
                "growth_score":   round(node_pr.get(nid, 0) * (1 + deg * 0.1), 4),
            })
    recent_papers.sort(key=lambda x: x["growth_score"], reverse=True)
    fastest_growing = recent_papers[:5]

    comm_recent = {}
    for p in recent_papers:
        c = p["community"]
        if c not in comm_recent:
            comm_recent[c] = {"count": 0, "total_pr": 0.0, "papers": []}
        comm_recent[c]["count"] += 1
        comm_recent[c]["total_pr"] += p["pagerank"]
        comm_recent[c]["papers"].append(p)

    emerging_hotspots = []
    for c, info in comm_recent.items():
        avg_pr = info["total_pr"] / info["count"] if info["count"] > 0 else 0
        emerging_hotspots.append({
            "community":      c,
            "communityLabel": get_community_display_label(c),
            "recent_count":   info["count"],
            "avg_pagerank":   round(avg_pr, 6),
            "hot_score":      round(info["count"] * avg_pr * 100, 4),
            "top_paper":      info["papers"][0]["name"] if info["papers"] else "",
        })
    emerging_hotspots.sort(key=lambda x: x["hot_score"], reverse=True)
    emerging_hotspots = emerging_hotspots[:5]

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
            bridge_score = cross_count * (1 + len(cross_comms) * 0.5) * node_pr.get(nid, 0)
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
                "bridge_score":      round(bridge_score, 6),
            })
    bridge_papers.sort(key=lambda x: x["bridge_score"], reverse=True)
    bridge_papers = bridge_papers[:5]

    return {
        "fastest_growing":   fastest_growing,
        "emerging_hotspots": emerging_hotspots,
        "bridge_papers":     bridge_papers,
    }
