import random


def build_adjacency(node_ids, edges):
    adj = {nid: [] for nid in node_ids}
    for src, tgt in edges:
        adj[src].append(tgt)
        adj[tgt].append(src)
    return adj


def find_connected_components(node_ids, adj):
    visited = set()
    components = []
    for nid in node_ids:
        if nid not in visited:
            stack = [nid]
            visited.add(nid)
            comp = []
            while stack:
                cur = stack.pop()
                comp.append(cur)
                for nb in adj.get(cur, []):
                    if nb not in visited:
                        visited.add(nb)
                        stack.append(nb)
            components.append(comp)
    components.sort(key=len, reverse=True)
    return components


def compute_density(N, E):
    if N <= 1:
        return 0.0
    return (2.0 * E) / (N * (N - 1))


def compute_average_path_length(node_ids, adj, sample_size=40):
    N = len(node_ids)
    actual_sample = min(sample_size, N)
    sampled = random.sample(list(node_ids), actual_sample) if N > actual_sample else list(node_ids)

    total_paths = 0
    total_dist = 0
    for start in sampled:
        dist = {start: 0}
        queue = [start]
        while queue:
            cur = queue.pop(0)
            for nb in adj.get(cur, []):
                if nb not in dist:
                    dist[nb] = dist[cur] + 1
                    queue.append(nb)
        for end in sampled:
            if start < end and end in dist:
                total_dist += dist[end]
                total_paths += 1

    if total_paths == 0:
        return 0.0
    return round(total_dist / total_paths, 3)


def compute_modularity(node_ids, edges, adj, node_comm):
    m = len(edges)
    if m == 0:
        return 0.0

    communities = set(node_comm.values())
    k = {nid: len(adj.get(nid, [])) for nid in node_ids}
    two_m = 2.0 * m
    Q = 0.0

    for c in communities:
        e_ii = 0.0
        for src, tgt in edges:
            if node_comm.get(src) == c and node_comm.get(tgt) == c:
                e_ii += 1.0
        e_ii /= m

        a_i = 0.0
        for nid in node_ids:
            if node_comm.get(nid) == c:
                a_i += k.get(nid, 0)
        a_i /= two_m

        Q += e_ii - a_i * a_i

    return round(Q, 4)
