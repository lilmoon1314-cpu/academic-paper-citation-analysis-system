from services.neo4j_service import get_session
from services.graph_service import get_community_display_label
from config import MAX_CACHE_SIZE

_recommend_cache = {}


def get_recommendations(paper_id):
    if not paper_id:
        return []

    if paper_id in _recommend_cache:
        return _recommend_cache[paper_id]

    with get_session() as session:
        result = session.run("""
            MATCH (center:Paper)
            WHERE toString(elementId(center)) = $paper_id
            MATCH (center)-[:CITES]->(common:Paper)<-[:CITES]-(rec:Paper)
            WHERE rec <> center
            WITH rec, count(common) AS sharedCitations,
                 rec.pagerank AS pr, rec.year AS yr
            ORDER BY sharedCitations DESC, pr DESC, yr DESC
            LIMIT 50
            RETURN toString(elementId(rec)) AS id,
                   rec.title              AS name,
                   rec.authors            AS authors,
                   rec.year               AS year,
                   rec.pagerank           AS pagerank,
                   rec.communityGroup     AS community,
                   sharedCitations
            ORDER BY year DESC, sharedCitations DESC, pagerank DESC
            LIMIT 8
        """, paper_id=paper_id)

        recs = [{
            "id":              r["id"],
            "name":            r["name"] or "Unknown",
            "authors":         r["authors"] or "",
            "year":            r["year"] or 0,
            "pagerank":        float(r["pagerank"] or 0),
            "pagerankRaw":     float(r["pagerank"] or 0),
            "community":       int(r["community"] or 0),
            "communityLabel":  get_community_display_label(int(r["community"] or 0)),
            "sharedCitations": r["sharedCitations"],
            "recReason":       "共同引用",
        } for r in result]

        existing_ids = [r["id"] for r in recs] + [paper_id]

        if len(recs) < 5:
            needed = 8 - len(recs)
            result2 = session.run("""
                MATCH (center:Paper)
                WHERE toString(elementId(center)) = $paper_id
                MATCH (citer:Paper)-[:CITES]->(center)
                MATCH (citer)-[:CITES]->(rec:Paper)
                WHERE rec <> center
                  AND NOT toString(elementId(rec)) IN $existing_ids
                WITH rec, count(DISTINCT citer) AS coCitCount
                ORDER BY coCitCount DESC, rec.pagerank DESC
                LIMIT $needed
                RETURN toString(elementId(rec)) AS id,
                       rec.title            AS name,
                       rec.authors          AS authors,
                       rec.year             AS year,
                       rec.pagerank         AS pagerank,
                       rec.communityGroup   AS community,
                       coCitCount
            """, paper_id=paper_id, existing_ids=existing_ids, needed=needed)

            for r in result2:
                recs.append({
                    "id":              r["id"],
                    "name":            r["name"] or "Unknown",
                    "authors":         r["authors"] or "",
                    "year":            r["year"] or 0,
                    "pagerank":        float(r["pagerank"] or 0),
                    "community":       int(r["community"] or 0),
                    "communityLabel":  get_community_display_label(int(r["community"] or 0)),
                    "sharedCitations": r["coCitCount"],
                    "recReason":       "共被引用",
                })
            existing_ids = [r["id"] for r in recs] + [paper_id]

        if len(recs) < 5:
            needed = 8 - len(recs)
            result3 = session.run("""
                MATCH (center:Paper)
                WHERE toString(elementId(center)) = $paper_id
                MATCH (rec:Paper)
                WHERE rec.communityGroup = center.communityGroup
                  AND rec <> center
                  AND NOT toString(elementId(rec)) IN $existing_ids
                RETURN toString(elementId(rec)) AS id,
                       rec.title          AS name,
                       rec.authors        AS authors,
                       rec.year           AS year,
                       rec.pagerank       AS pagerank,
                       rec.communityGroup AS community
                ORDER BY rec.pagerank DESC, rec.year DESC
                LIMIT $needed
            """, paper_id=paper_id, existing_ids=existing_ids, needed=needed)

            for r in result3:
                recs.append({
                    "id":              r["id"],
                    "name":            r["name"] or "Unknown",
                    "authors":         r["authors"] or "",
                    "year":            r["year"] or 0,
                    "pagerank":        float(r["pagerank"] or 0),
                    "community":       int(r["community"] or 0),
                    "communityLabel":  get_community_display_label(int(r["community"] or 0)),
                    "sharedCitations": 0,
                    "recReason":       "同研究领域",
                })

        if len(_recommend_cache) > MAX_CACHE_SIZE:
            _recommend_cache.pop(next(iter(_recommend_cache)))
        _recommend_cache[paper_id] = recs

        return recs
