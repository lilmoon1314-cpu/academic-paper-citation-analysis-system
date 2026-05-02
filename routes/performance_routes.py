import time
from flask import Blueprint, jsonify
from services.neo4j_service import get_session

performance_bp = Blueprint('performance', __name__)


@performance_bp.route('/api/performance')
def performance_check():
    try:
        with get_session() as session:
            t0 = time.time()
            session.run("MATCH (p:Paper) RETURN count(p) AS total")
            count_time = time.time() - t0

            t0 = time.time()
            session.run("""
                MATCH (p:Paper) WITH p LIMIT 1
                MATCH path = (p)-[:CITES*1..2]-(neighbor:Paper)
                RETURN count(DISTINCT neighbor) AS neighbors LIMIT 1
            """)
            path_time = time.time() - t0

            return jsonify({
                "database_status": "connected",
                "performance": {
                    "count_query_ms": round(count_time * 1000, 2),
                    "path_query_ms":  round(path_time * 1000, 2),
                },
                "tips": [
                    "为 Paper.communityGroup 创建复合索引可加速社区查询",
                    "为 Paper.pagerank 创建索引可加速 ORDER BY pagerank",
                    "APOC 插件可将图展开速度提升 3-5 倍",
                ]
            })
    except Exception as e:
        return jsonify({"database_status": "error", "error": str(e)})
