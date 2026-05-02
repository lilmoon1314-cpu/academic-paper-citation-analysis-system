from services.neo4j_service import get_session
from utils.text_utils import extract_keywords
from config import DEFAULT_HOPS, DEFAULT_MAX_NODES

_community_label_cache = {}


def _sample_titles(community_id, sample_size=200):
    with get_session() as session:
        result = session.run("""
            MATCH (p:Paper)
            WHERE p.communityGroup = $cid
            WITH p, rand() AS r
            ORDER BY r
            RETURN p.title AS title
            LIMIT $limit
        """, cid=int(community_id), limit=sample_size)
        return [r["title"] for r in result if r["title"]]


def get_community_display_label(community_id):
    cid = int(community_id)
    if cid in _community_label_cache:
        return _community_label_cache[cid]

    try:
        with get_session() as session:
            size_result = session.run(
                "MATCH (p:Paper) WHERE p.communityGroup = $cid RETURN count(p) AS sz",
                cid=cid
            )
            rec = size_result.single()
            size = rec["sz"] if rec else 0
    except Exception:
        size = 0

    if size < 10:
        label = "小研究方向"
    else:
        sample_size = min(size, 300) if size >= 1000 else size
        titles = _sample_titles(cid, sample_size=sample_size)
        label = extract_keywords(titles) or "研究领域"

    _community_label_cache[cid] = label
    return label


def node_to_dict(n, pr_max=None):
    community_id = int(n.get("communityGroup") or n.get("community") or 0)
    raw_pr = float(n.get("pagerank") or 0)
    if pr_max and pr_max > 1:
        pagerank = raw_pr / pr_max
    else:
        pagerank = raw_pr
    return {
        "id":             str(n.element_id),
        "name":           n.get("title", "Unknown"),
        "authors":        n.get("authors", ""),
        "year":           n.get("year", 0),
        "pagerank":       float(pagerank),
        "pagerankRaw":    float(raw_pr),
        "community":      community_id,
        "communityLabel": get_community_display_label(community_id),
    }


def fetch_subgraph(paper_id, hops=DEFAULT_HOPS, max_nodes=DEFAULT_MAX_NODES):
    with get_session() as session:
        center_result = session.run("""
            MATCH (center:Paper)
            WHERE toString(elementId(center)) = $paper_id
            RETURN center
        """, paper_id=paper_id)
        center_record = center_result.single()
        if not center_record:
            return None, None, None, None
        center_node = center_record["center"]

        network_result = None
        try:
            network_result = session.run("""
                MATCH (center:Paper)
                WHERE toString(elementId(center)) = $paper_id
                CALL apoc.path.subgraphNodes(center, {
                    relationshipFilter: 'CITES>|<CITES',
                    minLevel: 1,
                    maxLevel: $hops,
                    limit: $max_nodes
                })
                YIELD node AS neighbor
                WHERE neighbor <> center
                RETURN neighbor
                ORDER BY neighbor.pagerank DESC
                LIMIT $max_nodes
            """, paper_id=paper_id, hops=hops, max_nodes=max_nodes)
        except Exception:
            pass

        if network_result is None:
            network_result = session.run("""
                MATCH (center:Paper)
                WHERE toString(elementId(center)) = $paper_id
                MATCH (center)-[:CITES*1..$hops]-(neighbor:Paper)
                WITH DISTINCT neighbor
                ORDER BY neighbor.pagerank DESC
                LIMIT $max_nodes
                RETURN neighbor
            """, paper_id=paper_id, hops=hops, max_nodes=max_nodes)

        all_nodes = [center_node]
        node_ids = {paper_id}
        for record in network_result:
            neighbor = record["neighbor"]
            nid = str(neighbor.element_id)
            if nid not in node_ids:
                node_ids.add(nid)
                all_nodes.append(neighbor)

        edge_result = session.run("""
            MATCH (a:Paper)-[r:CITES]->(b:Paper)
            WHERE toString(elementId(a)) IN $ids
              AND toString(elementId(b)) IN $ids
            RETURN toString(elementId(a)) AS source,
                   toString(elementId(b)) AS target
        """, ids=list(node_ids))

        edges = [(r["source"], r["target"]) for r in edge_result]

        return center_node, all_nodes, node_ids, edges


def build_graph_response(paper_id, center_node, all_nodes, node_ids, edges, hops, max_nodes):
    dist_map = {paper_id: 0}
    for n in all_nodes:
        nid = str(n.element_id)
        if nid not in dist_map:
            dist_map[nid] = hops + 1

    edge_list = []
    connected_ids = {paper_id}

    for src, tgt in edges:
        connected_ids.add(src)
        connected_ids.add(tgt)

        if src == paper_id:
            direction = "out"
        elif tgt == paper_id:
            direction = "in"
        else:
            d_src = dist_map.get(src, hops + 1)
            d_tgt = dist_map.get(tgt, hops + 1)
            if d_src < d_tgt:
                direction = "forward"
            elif d_src > d_tgt:
                direction = "backward"
            else:
                direction = "lateral"

        edge_list.append({"source": src, "target": tgt, "direction": direction})

    pr_vals = [float(n.get("pagerank") or 0) for n in all_nodes]
    pr_max = max(pr_vals) if pr_vals else 1.0

    nodes_raw = [node_to_dict(n, pr_max=pr_max) for n in all_nodes]
    seen = set()
    unique_nodes = []
    for n in nodes_raw:
        if n["id"] not in seen and n["id"] in connected_ids:
            seen.add(n["id"])
            n["isCenter"] = (n["id"] == paper_id)
            unique_nodes.append(n)

    if paper_id not in seen:
        center_dict = node_to_dict(center_node)
        center_dict["isCenter"] = True
        unique_nodes.insert(0, center_dict)

    return {
        "nodes": unique_nodes,
        "edges": edge_list,
        "metadata": {
            "total_nodes": len(unique_nodes),
            "total_edges": len(edge_list),
            "hops":        hops,
            "max_nodes":   max_nodes,
        }
    }
