import re
from services.neo4j_service import get_session
from utils.text_utils import clean_search_keyword


def search_suggest(keyword):
    if not keyword or not keyword.strip():
        return []

    with get_session() as session:
        suggestions = []

        try:
            clean_kw = clean_search_keyword(keyword)
            if clean_kw:
                phrase_kw = f'"{clean_kw}"'
                result = session.run("""
                    CALL db.index.fulltext.queryNodes('paperTitleIndex', $keyword)
                    YIELD node, score
                    RETURN toString(elementId(node)) AS id,
                           node.title   AS title,
                           node.authors AS authors,
                           node.year    AS year,
                           node.pagerank AS pagerank
                    ORDER BY score DESC, node.year DESC
                    LIMIT 15
                """, keyword=phrase_kw)

                suggestions = [{
                    "id":       r["id"],
                    "title":    r["title"],
                    "authors":  r["authors"] or "",
                    "year":     r["year"] or 0,
                    "pagerank": r["pagerank"] or 0
                } for r in result]
        except Exception as e:
            print(f"全文索引查询失败: {e}")

        if len(suggestions) < 8 and len(keyword) >= 2:
            try:
                existing_ids = {s["id"] for s in suggestions}
                result = session.run("""
                    MATCH (p:Paper)
                    WHERE toLower(p.title) CONTAINS toLower($keyword)
                    RETURN toString(elementId(p)) AS id,
                           p.title   AS title,
                           p.authors AS authors,
                           p.year    AS year,
                           p.pagerank AS pagerank
                    ORDER BY p.pagerank DESC, p.year DESC
                    LIMIT $limit
                """, keyword=keyword, limit=20 - len(suggestions))

                for r in result:
                    if r["id"] not in existing_ids:
                        suggestions.append({
                            "id":       r["id"],
                            "title":    r["title"],
                            "authors":  r["authors"] or "",
                            "year":     r["year"] or 0,
                            "pagerank": r["pagerank"] or 0
                        })
                        existing_ids.add(r["id"])
            except Exception as e:
                print(f"CONTAINS查询失败: {e}")

        suggestions.sort(key=lambda x: (x.get("pagerank", 0), x.get("year", 0)), reverse=True)
        return suggestions[:20]


def check_fulltext_index():
    try:
        with get_session() as session:
            result = session.run("""
                CALL db.indexes()
                YIELD name, type, labelsOrTypes, properties
                WHERE type = 'FULLTEXT' AND name = 'paperTitleIndex'
                RETURN name, labelsOrTypes, properties
            """)
            index_info = result.single()
            if index_info:
                return {"status": "exists", "name": index_info["name"]}
            return {"status": "not_found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def create_fulltext_index():
    try:
        with get_session() as session:
            session.run("""
                CALL db.index.fulltext.createNodeIndex(
                    'paperTitleIndex', ['Paper'], ['title', 'authors']
                )
            """)
            return {"status": "created"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
