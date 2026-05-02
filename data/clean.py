#!/usr/bin/env python3
"""
过滤 JSONL 数据：仅保留出度 > 10 的论文，并输出干净的 CSV 文件供 neo4j-admin 导入。
用法：python filter_papers.py
"""

import json
import csv
from pathlib import Path

# ========== 配置 ==========
INPUT_FILE = r"D:\Users\18539\Desktop\color\graph\DBLP-Citation-network-V18.jsonl"   # ← 改成你的实际文件路径
OUTPUT_NODES = "papers_filtered.csv"
OUTPUT_RELS  = "references_filtered.csv"
MIN_OUTDEGREE = 11                       # 保留出度 >= 11 的论文（即 references 列表长度 >= 11）
# ==========================

#!/usr/bin/env python3
"""
过滤 JSONL 数据：仅保留出度 > 10 的论文，并输出干净的 CSV 文件供 neo4j-admin 导入。
未手动转义双引号，由 csv.QUOTE_ALL 统一处理。
"""

def clean_field(value, max_len=5000):
    """去除换行符，保留其他字符"""
    if value is None:
        return ""
    value = str(value).replace("\r", " ").replace("\n", " ").strip()
    # 不手动处理双引号，交给 csv.QUOTE_ALL
    return value[:max_len]


def main():
    input_path = Path(INPUT_FILE)
    if not input_path.exists():
        print(f"❌ 文件不存在: {input_path.absolute()}")
        return

    eligible_ids = set()
    total_papers = 0
    print("第一遍扫描：筛选出度 > 10 的论文...")
    with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                paper = json.loads(line)
            except json.JSONDecodeError:
                continue
            total_papers += 1
            pid = str(paper.get("id", "")).strip()
            refs = paper.get("references", [])
            if not pid:
                continue
            if isinstance(refs, list) and len(refs) >= MIN_OUTDEGREE:
                eligible_ids.add(pid)

    print(f"  总论文数: {total_papers:,}")
    print(f"  出度 >= {MIN_OUTDEGREE} 的论文数: {len(eligible_ids):,}")

    print("第二遍：生成过滤后的 CSV (QUOTE_ALL)...")
    paper_count = 0
    rel_count = 0

    NODE_HEADER = [
        "paperId:ID(Paper)", "title", "authors", "year:int",
        "communityGroup:int", "pagerank:float", ":LABEL"
    ]
    REL_HEADER = [":START_ID(Paper)", ":END_ID(Paper)", ":TYPE"]

    with open(input_path, "r", encoding="utf-8", errors="ignore") as fin, \
         open(OUTPUT_NODES, "w", encoding="utf-8", newline="") as fout_n, \
         open(OUTPUT_RELS, "w", encoding="utf-8", newline="") as fout_r:

        # 关键：使用 QUOTE_ALL，确保所有字段都被双引号包围，避免特殊字符干扰
        node_writer = csv.writer(fout_n, quoting=csv.QUOTE_ALL)
        rel_writer = csv.writer(fout_r, quoting=csv.QUOTE_ALL)

        node_writer.writerow(NODE_HEADER)
        rel_writer.writerow(REL_HEADER)

        for line in fin:
            line = line.strip()
            if not line:
                continue
            try:
                paper = json.loads(line)
            except json.JSONDecodeError:
                continue

            pid = str(paper.get("id", "")).strip()
            if pid not in eligible_ids:
                continue

            title = clean_field(paper.get("title", ""))
            year = paper.get("year")
            try:
                year = int(year) if year is not None else 0
            except (ValueError, TypeError):
                year = 0

            authors_list = paper.get("authors", [])
            if isinstance(authors_list, list):
                author_str = "; ".join(
                    str(a.get("name", "")).strip()
                    for a in authors_list if a.get("name")
                )
            else:
                author_str = str(authors_list)
            authors = clean_field(author_str)[:2000]

            node_writer.writerow([pid, title, authors, year, 0, 0.0, "Paper"])
            paper_count += 1

            # 引用关系只保留两端都在集合内的
            refs = paper.get("references", [])
            if isinstance(refs, list):
                for ref_id in refs:
                    ref_id = str(ref_id).strip()
                    if ref_id and ref_id in eligible_ids:
                        rel_writer.writerow([pid, ref_id, "CITES"])
                        rel_count += 1

    print(f"\n✅ 完成！")
    print(f"   过滤后论文节点: {paper_count:,}")
    print(f"   过滤后引用关系: {rel_count:,}")


if __name__ == "__main__":
    main()