# import_to_neo4j.py
from neo4j import GraphDatabase
import csv

URI      = "neo4j://127.0.0.1:7687"   # 本地Neo4j地址
USER     = "neo4j"
PASSWORD = "wrnhkl1314"                # ← 改成你设的密码

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

def run(query, **kwargs):
    with driver.session() as s:
        s.run(query, **kwargs)

# 1. 清空旧数据
print("清空旧数据...")
run("MATCH ()-[r]->() DELETE r")
run("MATCH (n) DELETE n")

# 2. 建索引
print("建立索引...")
run("CREATE INDEX paper_id IF NOT EXISTS FOR (p:Paper) ON (p.id)")

# 3. 导入节点（分批，每批500条）
print("导入论文节点...")
batch = []
with open("papers.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        batch.append(row)
        if len(batch) >= 1000:
            with driver.session() as s:
                s.run("""
                    UNWIND $batch AS row
                    CREATE (:Paper {
                        id: row.id, title: row.title,
                        authors: row.authors,
                        year: toInteger(row.year),
                        venue: row.venue
                    })
                """, batch=batch)
            batch = []
if batch:
    with driver.session() as s:
        s.run("""
            UNWIND $batch AS row
            CREATE (:Paper {
                id: row.id, title: row.title,
                authors: row.authors,
                year: toInteger(row.year),
                venue: row.venue
            })
        """, batch=batch)
print("  ✅ 节点导入完成")

# 4. 导入关系（分批）
print("导入引用关系...")
batch = []
with open("references.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        batch.append(row)
        if len(batch) >= 1000:
            with driver.session() as s:
                s.run("""
                    UNWIND $batch AS row
                    MATCH (a:Paper {id: row.source})
                    MATCH (b:Paper {id: row.target})
                    CREATE (a)-[:CITES]->(b)
                """, batch=batch)
            batch = []
if batch:
    with driver.session() as s:
        s.run("""
            UNWIND $batch AS row
            MATCH (a:Paper {id: row.source})
            MATCH (b:Paper {id: row.target})
            CREATE (a)-[:CITES]->(b)
        """, batch=batch)
print("  ✅ 关系导入完成")

driver.close()
print("\n🎉 全部完成！请在 Neo4j Browser 验证：")
print("   MATCH (n:Paper) RETURN count(n)")
print("   MATCH ()-[r:CITES]->() RETURN count(r)")