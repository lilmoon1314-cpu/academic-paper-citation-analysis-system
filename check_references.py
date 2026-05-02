import csv

# 读取 papers.csv 中的所有 ID
paper_ids = set()
with open('papers.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        paper_ids.add(row['id'])

print(f"papers.csv 中共有 {len(paper_ids)} 个论文ID")

# 读取 references.csv 并检查 ID 匹配情况
missing_source = set()
missing_target = set()
valid_edges = 0
total_edges = 0

with open('references.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        total_edges += 1
        source_id = row['source']
        target_id = row['target']
        
        if source_id not in paper_ids:
            missing_source.add(source_id)
        if target_id not in paper_ids:
            missing_target.add(target_id)
        
        if source_id in paper_ids and target_id in paper_ids:
            valid_edges += 1

print(f"\nreferences.csv 分析结果:")
print(f"总引用关系数: {total_edges}")
print(f"有效引用关系数: {valid_edges}")
print(f"无效引用关系数: {total_edges - valid_edges}")
print(f"缺失的源节点ID数量: {len(missing_source)}")
print(f"缺失的目标节点ID数量: {len(missing_target)}")

if missing_source:
    print(f"\n缺失的源节点ID示例: {list(missing_source)[:10]}")
if missing_target:
    print(f"缺失的目标节点ID示例: {list(missing_target)[:10]}")

# 检查 papers.csv 中的 ID 范围
paper_id_nums = [int(id) for id in paper_ids if id.isdigit()]
if paper_id_nums:
    print(f"\n论文ID范围: {min(paper_id_nums)} - {max(paper_id_nums)}")

# 检查 references.csv 中的 ID 范围
ref_ids = set()
with open('references.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        ref_ids.add(row['source'])
        ref_ids.add(row['target'])

ref_id_nums = [int(id) for id in ref_ids if id.isdigit()]
if ref_id_nums:
    print(f"引用关系ID范围: {min(ref_id_nums)} - {max(ref_id_nums)}")

print(f"\n有效引用关系比例: {valid_edges/total_edges*100:.2f}%")