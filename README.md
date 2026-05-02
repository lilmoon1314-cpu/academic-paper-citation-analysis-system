# Citation Network Visualization & Analysis Platform

学术论文引用网络可视化分析平台 —— 基于 Neo4j 图数据库与 ECharts 的大规模学术引用关系交互式探索工具。

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.x-brightgreen.svg)](https://neo4j.com/)
[![ECharts](https://img.shields.io/badge/ECharts-5.4.3-orange.svg)](https://echarts.apache.org/)

---

## 目录

- [项目简介](#项目简介)
- [核心功能](#核心功能)
- [技术架构](#技术架构)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [数据集说明](#数据集说明)
- [数据清洗与预处理](#数据清洗与预处理)
- [项目结构](#项目结构)
- [API 接口文档](#api-接口文档)
- [前端使用说明](#前端使用说明)
- [算法说明](#算法说明)
- [性能优化](#性能优化)
- [开发路线图](#开发路线图)

---

## 项目简介

本系统以 **DBLP Citation Network V18** 大规模学术引用数据集为基础，利用 Neo4j 图数据库存储论文节点与引用关系，通过 Flask 提供 RESTful API，前端基于 ECharts 实现四种可视化布局模式的交互式引用网络探索。系统集成了社区发现、PageRank 影响力评估、智能论文推荐、网络指标分析、前沿论文发现等分析能力。

### 适用场景

- 学术文献调研：快速了解某篇论文的引用上下游关系
- 研究领域概览：通过社区聚类识别不同研究方向及其关联
- 前沿趋势发现：定位近年高增长论文与跨学科桥梁论文
- 文献推荐：基于共同引用与共被引关系发现相关论文

---

## 核心功能

| 模块 | 功能 | 说明 |
|------|------|------|
| 🔍 智能搜索 | 全文索引 + 模糊匹配 | 支持论文标题/作者实时搜索建议，优先使用 Neo4j 全文索引，自动回退 CONTAINS 查询 |
| 📊 多跳网络 | 3-6 跳可配置 | 以选中论文为中心，按 PageRank 排序展开多跳引用网络，支持 50/100/200/300 节点规模 |
| 🗺️ 四种布局 | 力导向 / 社区聚类 / 时间演化 / 放射引用 | 一键切换布局模式，社区聚类使用自定义力模拟算法，时间演化支持年份滑块筛选 |
| 📄 论文详情 | 节点点击展示 | 展示标题、作者、年份、PageRank、社区归属、网络排名、社区内排名 |
| 💡 智能推荐 | 三级推荐策略 | 共同引用 → 共被引 → 同社区补充，最多返回 8 条推荐，含推荐理由标签 |
| 📈 网络指标 | 6 项图指标 | 节点数、边数、网络密度、平均路径长度、最大连通分量、社区模块度 + Top 10 中心性排名 |
| 🚀 前沿发现 | 三类前沿分析 | 近 2 年增长最快论文、新兴社区热点、跨社区桥梁论文 |
| 🔗 引用链高亮 | 上下游追踪 | 一键高亮上游引用链（谁引用了这条链）或下游引用链（这条链引用了谁） |
| ⚡ 性能监控 | 数据库性能检测 | `/api/performance` 端点检测 Neo4j 连接状态与查询耗时 |

---

## 技术架构

### 架构分层

```
┌──────────────────────────────────────────────────────┐
│                    Frontend Layer                     │
│  citation_network.html  +  static/main.js            │
│  static/style.css        +  ECharts 5.4.3            │
├──────────────────────────────────────────────────────┤
│                    Routes Layer                       │
│  graph_routes   search_routes   recommend_routes     │
│  metrics_routes frontier_routes performance_routes   │
├──────────────────────────────────────────────────────┤
│                   Services Layer                      │
│  graph_service  search_service  recommend_service    │
│  metrics_service frontier_service neo4j_service      │
├──────────────────────────────────────────────────────┤
│                    Utils Layer                        │
│  graph_utils (BFS/DFS/Modularity/Density)            │
│  text_utils  (NLP keyword extraction)                │
├──────────────────────────────────────────────────────┤
│                    Data Layer                         │
│  Neo4j Graph Database (Paper nodes + CITES edges)    │
└──────────────────────────────────────────────────────┘
```

### 技术栈

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 后端框架 | Flask | ≥2.3.0 | RESTful API 服务，Blueprint 模块化路由 |
| 跨域处理 | Flask-CORS | ≥4.0.0 | 前后端分离跨域支持 |
| 图数据库 | Neo4j | 5.x | 论文节点与引用关系存储、图遍历查询 |
| 数据库驱动 | neo4j (Python) | ≥5.14.0 | Python 连接 Neo4j 官方驱动 |
| 图算法加速 | APOC | 5.x | Neo4j APOC 插件，subgraphNodes 加速子图展开 |
| 前端可视化 | ECharts | 5.4.3 | 力导向图渲染，CDN 引入 |
| 数据格式 | JSONL / CSV | — | 原始数据为 JSONL，清洗后输出 CSV |

### 设计模式

- **Application Factory**：`app.py` 使用 `create_app()` 工厂函数创建 Flask 实例
- **Blueprint 路由**：6 个 Blueprint 模块独立注册，职责清晰
- **Service 层分离**：路由层仅处理请求/响应，业务逻辑全部在 services 层
- **单例数据库连接**：`neo4j_service.py` 维护全局 `_driver` 单例，避免重复创建连接
- **客户端缓存**：前端 `dataCache` (Map) 缓存网络数据，LRU 淘汰策略（上限 12 条）
- **服务端缓存**：推荐结果使用字典缓存，上限 200 条

---

## 环境要求

### 必需环境

| 软件 | 最低版本 | 说明 |
|------|----------|------|
| Python | 3.10+ | 后端运行环境 |
| Neo4j | 5.x (Community/Enterprise) | 图数据库，需安装 APOC 插件 |
| pip | 22.0+ | Python 包管理器 |
| 浏览器 | Chrome 90+ / Firefox 90+ / Edge 90+ | 前端运行环境 |

### 可选环境

- Neo4j APOC 插件：大幅提升子图展开性能（3-5 倍），强烈推荐安装
- Neo4j Bloom：可选的图可视化探索工具（用于数据库端验证）

---

## 快速开始

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd graph
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

`requirements.txt` 内容：
```
flask>=2.3.0
flask-cors>=4.0.0
neo4j>=5.14.0
```

### 3. 配置 Neo4j 连接

编辑 `config.py`，修改为你的 Neo4j 连接信息：

```python
NEO4J_URI      = "neo4j://127.0.0.1:7687"
NEO4J_USER     = "neo4j"
NEO4J_PASSWORD = "your_password_here"    # ← 修改为你的密码

DEFAULT_HOPS      = 6      # 默认查询跳数
DEFAULT_MAX_NODES = 200    # 默认最大节点数
MAX_CACHE_SIZE    = 200    # 推荐缓存上限
CURRENT_YEAR      = 2025   # 当前年份（用于前沿论文判定）
```

### 4. 准备数据

#### 方式一：使用项目自带清洗脚本（推荐）

```bash
# 步骤 1：清洗原始 JSONL 数据，生成过滤后的 CSV
cd data
python clean.py
# 输出：data/papers_filtered.csv  +  data/references_filtered.csv

# 步骤 2：将 CSV 导入 Neo4j
python dataimport.py
```

#### 方式二：使用 neo4j-admin 批量导入（大数据量推荐）

```bash
# 先运行 clean.py 生成 CSV，然后使用 neo4j-admin import
neo4j-admin database import full \
  --nodes=Paper=data/papers_filtered.csv \
  --relationships=CITES=data/references_filtered.csv
```

### 5. 创建全文索引（首次运行必须）

启动后端后，访问以下端点创建全文索引：

```
GET http://127.0.0.1:5000/api/create_index
```

或在 Neo4j Browser 中手动执行：

```cypher
CREATE FULLTEXT INDEX paperTitleIndex
FOR (p:Paper) ON EACH [p.title, p.authors]
```

### 6. 启动后端服务

```bash
python app.py
```

服务默认运行在 `http://127.0.0.1:5000`。

### 7. 打开前端页面

直接用浏览器打开 `citation_network.html`，或部署到任意静态文件服务器。

> **注意**：前端通过 `const API = 'http://127.0.0.1:5000'` 连接后端，如果后端地址不同，请修改 `static/main.js` 第 1 行。

---

## 数据集说明

### 数据来源

**DBLP Citation Network V18** —— 截至 2025 年 4 月的最新版本，包含数千万篇学术论文及其引用关系。

- 原始文件：`data/DBLP-Citation-network-V18.jsonl`
- 格式：每行一个 JSON 对象
- 论文数量：数千万级（全量）
- 引用关系：数十亿级（全量）

### JSONL 单条数据结构

```json
{
  "id": "53e997b4b7602d9701e4c2b0",
  "title": "Attention Is All You Need",
  "authors": [
    {"name": "Ashish Vaswani"},
    {"name": "Noam Shazeer"}
  ],
  "year": 2017,
  "references": ["id1", "id2", "id3", ...],
  "venue": "NeurIPS"
}
```

### Neo4j 数据模型

**节点标签**：`:Paper`

| 属性 | 类型 | 说明 |
|------|------|------|
| `id` | String | DBLP 论文唯一标识 |
| `title` | String | 论文标题 |
| `authors` | String | 作者列表（分号分隔） |
| `year` | Integer | 发表年份 |
| `venue` | String | 发表会议/期刊 |
| `pagerank` | Float | PageRank 值（需预先计算） |
| `communityGroup` | Integer | Louvain 社区编号（需预先计算） |

**关系类型**：`[:CITES]`（有向边，A → B 表示 A 引用了 B）

---

## 数据清洗与预处理

### 清洗策略

原始 DBLP V18 数据集包含数千万论文，直接全量导入对个人设备不现实。本项目的清洗脚本 `data/clean.py` 采用以下策略：

#### 过滤规则

| 规则 | 阈值 | 目的 |
|------|------|------|
| 出度过滤 | `len(references) >= 11` | 仅保留引用关系丰富的论文，过滤孤立节点和低质量论文 |
| 引用边过滤 | 两端节点均在过滤后集合内 | 确保所有引用边的 source 和 target 都存在 |

#### 两遍扫描算法

```
第一遍：遍历 JSONL → 统计每篇论文的出度 → 筛选出度 >= 11 的论文 ID → 存入 eligible_ids 集合
第二遍：遍历 JSONL → 对每条符合条件的论文 → 写入 nodes CSV → 遍历其 references → 仅写入两端都在集合内的边
```

#### 输出格式

使用 `csv.QUOTE_ALL` 模式，所有字段用双引号包裹，避免标题中的特殊字符（逗号、引号、换行符）干扰 CSV 解析。

**节点 CSV 表头**（neo4j-admin 格式）：
```csv
"paperId:ID(Paper)","title","authors","year:int","communityGroup:int","pagerank:float",":LABEL"
```

**关系 CSV 表头**：
```csv
":START_ID(Paper)",":END_ID(Paper)",":TYPE"
```

#### 字段清洗

- 去除 `\r`、`\n` 换行符
- 作者列表从 JSON 数组转为分号分隔字符串
- 标题截断至 5000 字符，作者截断至 2000 字符
- 年份非整数时默认设为 0

### 数据导入

`data/dataimport.py` 使用分批 UNWIND 方式导入（每批 1000 条），避免单次事务过大：

```python
# 节点导入
UNWIND $batch AS row
CREATE (:Paper {id: row.id, title: row.title, authors: row.authors, ...})

# 关系导入
UNWIND $batch AS row
MATCH (a:Paper {id: row.source})
MATCH (b:Paper {id: row.target})
CREATE (a)-[:CITES]->(b)
```

### 数据验证

`check_references.py` 用于验证导入后的数据完整性：

- 检查 references.csv 中的 source/target ID 是否都在 papers.csv 中存在
- 统计有效/无效引用关系比例
- 输出缺失 ID 示例

---

## 项目结构

```
graph/
├── app.py                          # Flask 应用入口（工厂模式）
├── config.py                       # Neo4j 连接配置 + 全局常量
├── requirements.txt                # Python 依赖清单
├── citation_network.html           # 前端主页面（单文件 SPA）
├── check_references.py             # 数据完整性验证脚本
│
├── routes/                         # 路由层（Blueprint）
│   ├── __init__.py
│   ├── graph_routes.py             # GET /graph            — 引用网络查询
│   ├── search_routes.py            # GET /search_suggest   — 论文搜索建议
│   │                               # GET /api/check_index  — 检查全文索引
│   │                               # GET /api/create_index — 创建全文索引
│   ├── recommend_routes.py         # GET /recommend        — 论文推荐
│   ├── metrics_routes.py           # GET /network_metrics  — 网络指标分析
│   ├── frontier_routes.py          # GET /frontier_papers  — 前沿论文发现
│   └── performance_routes.py       # GET /api/performance  — 数据库性能检测
│
├── services/                       # 服务层（业务逻辑）
│   ├── __init__.py
│   ├── neo4j_service.py            # Neo4j 连接管理（单例驱动）
│   ├── graph_service.py            # 子图查询 + 响应构建 + 社区标签生成
│   ├── search_service.py           # 全文索引搜索 + CONTAINS 回退
│   ├── recommend_service.py        # 三级推荐策略 + 缓存
│   ├── metrics_service.py          # 网络指标计算编排
│   └── frontier_service.py         # 前沿论文发现算法
│
├── utils/                          # 工具层（纯函数）
│   ├── __init__.py
│   ├── graph_utils.py              # BFS/DFS、连通分量、密度、平均路径、模块度
│   └── text_utils.py               # 搜索关键词清洗、社区关键词提取（NLP）
│
├── static/                         # 前端静态资源
│   ├── main.js                     # 核心 JS（图表渲染、布局算法、交互逻辑）
│   └── style.css                   # 暗色主题样式（Grid 布局）
│
└── data/                           # 数据处理脚本 + 数据文件
    ├── DBLP-Citation-network-V18.jsonl  # 原始数据集（需自行下载）
    ├── clean.py                         # JSONL → CSV 清洗脚本
    ├── dataimport.py                    # CSV → Neo4j 导入脚本
    ├── papers_filtered.csv              # 清洗后的论文节点 CSV
    └── references_filtered.csv          # 清洗后的引用关系 CSV
```

---

## API 接口文档

### 1. 论文搜索建议

```
GET /search_suggest?q=<keyword>
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `q` | string | 是 | 搜索关键词（支持英文） |

**响应示例**：
```json
[
  {
    "id": "4:xxx:0",
    "title": "Attention Is All You Need",
    "authors": "Ashish Vaswani; Noam Shazeer",
    "year": 2017,
    "pagerank": 0.000123
  }
]
```

**实现策略**：优先 Neo4j 全文索引（`paperTitleIndex`），结果不足 8 条时回退 `CONTAINS` 查询。

---

### 2. 引用网络查询

```
GET /graph?id=<paper_id>&hops=<n>&max_nodes=<n>
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `id` | string | — | 中心论文的 Neo4j elementId |
| `hops` | int | 6 | 查询跳数（3-6） |
| `max_nodes` | int | 200 | 最大返回节点数 |

**响应示例**：
```json
{
  "nodes": [
    {
      "id": "4:xxx:0",
      "name": "Attention Is All You Need",
      "authors": "Ashish Vaswani;...",
      "year": 2017,
      "pagerank": 0.85,
      "pagerankRaw": 1234.5,
      "community": 3,
      "communityLabel": "Natural Language · Transformer",
      "isCenter": true
    }
  ],
  "edges": [
    {
      "source": "4:xxx:0",
      "target": "4:yyy:1",
      "direction": "out"
    }
  ],
  "metadata": {
    "total_nodes": 200,
    "total_edges": 450,
    "hops": 6,
    "max_nodes": 200
  }
}
```

**边方向说明**：

| direction | 含义 | 前端颜色 |
|-----------|------|----------|
| `out` | 中心节点 → 引用目标 | 蓝色 `#5c7cfa` |
| `in` | 被引用方 → 中心节点 | 红色 `#ee6666` |
| `forward` | 向外延伸引用 | 绿色 `#91cc75` |
| `backward` | 向内引用关系 | 黄色 `#fac858` |
| `lateral` | 邻居节点之间 | 灰色 `#8b92b3` |

**查询优化**：优先使用 APOC `apoc.path.subgraphNodes`（需安装 APOC 插件），失败时回退标准 Cypher 路径查询。

---

### 3. 论文推荐

```
GET /recommend?id=<paper_id>
```

**三级推荐策略**：

| 优先级 | 策略 | Cypher 逻辑 |
|--------|------|-------------|
| 1 | 共同引用 | `(center)-[:CITES]->(common)<-[:CITES]-(rec)` |
| 2 | 共被引 | `(citer)-[:CITES]->(center)` 且 `(citer)-[:CITES]->(rec)` |
| 3 | 同社区补充 | `rec.communityGroup = center.communityGroup` |

**响应示例**：
```json
[
  {
    "id": "4:xxx:1",
    "name": "BERT: Pre-training of Deep Bidirectional Transformers",
    "authors": "Jacob Devlin;...",
    "year": 2019,
    "pagerank": 0.72,
    "community": 3,
    "communityLabel": "Natural Language · Transformer",
    "sharedCitations": 15,
    "recReason": "共同引用"
  }
]
```

---

### 4. 网络指标分析

```
GET /network_metrics?id=<paper_id>&hops=<n>&max_nodes=<n>
```

**返回指标**：

| 指标 | 计算方式 | 说明 |
|------|----------|------|
| `density` | 2E / N(N-1) | 网络密度，值越高越紧密 |
| `avg_path_length` | BFS 采样（40 节点） | 平均最短路径长度 |
| `largest_component` | DFS 连通分量 | 最大连通分量大小/占比/分量总数 |
| `modularity` | Newman-Girvan 公式 | 社区结构强度 |
| `top10_centrality` | PageRank + Degree | Top 10 中心节点 |

---

### 5. 前沿论文发现

```
GET /frontier_papers?id=<paper_id>&hops=<n>&max_nodes=<n>
```

**三类前沿分析**：

| 类别 | 算法 |
|------|------|
| 增长最快 | 筛选近 2 年论文，按 `growth_score = pagerank × (1 + degree × 0.1)` 排序 |
| 新兴热点 | 按社区聚合近年论文，按 `hot_score = count × avg_pagerank × 100` 排序 |
| 桥梁论文 | 统计邻居跨社区数量，按 `bridge_score = cross_edges × (1 + cross_communities × 0.5) × pagerank` 排序 |

---

### 6. 性能检测

```
GET /api/performance
```

返回 Neo4j 连接状态、计数查询耗时、路径查询耗时及优化建议。

---

## 前端使用说明

### 界面布局

```
┌────────────── 顶栏 ──────────────┐
│ 品牌标识  │  搜索框  │  网络统计  │
├──── 左侧面板 ──┤ 中间图区 ├── 右侧面板 ──┤
│ 网络配置       │          │ 论文详情     │
│ 布局模式       │ ECharts  │ 智能推荐     │
│ 操作按钮       │ 力导向图  │ 网络指标     │
│ 边方向图例     │          │ 前沿发现     │
│ 社区图例       │          │              │
│ 节点大小说明   │          │              │
└────────────────┴──────────┴──────────────┘
```

### 四种布局模式

| 布局 | 适用场景 | 技术实现 |
|------|----------|----------|
| **力导向** | 自由探索引用关系 | ECharts 原生 force 布局，高排斥力 + 低摩擦力 |
| **社区聚类** | 观察研究领域分布 | 自定义力模拟算法：社区中心圆形排列 + 社区内弹簧力 + 节点间排斥力 |
| **时间演化** | 观察引用关系随时间变化 | X 轴 = 年份线性映射，Y 轴 = PageRank 排序，底部年份滑块筛选 |
| **放射引用** | 观察引用层级深度 | BFS 计算距离 → 同心圆环排列，中心节点位于原点 |

### 操作指南

1. **搜索**：在顶栏输入关键词（支持英文），从下拉列表选择论文
2. **切换布局**：点击左侧面板的布局按钮（力导向/社区聚类/时间演化/放射引用）
3. **调整参数**：修改节点规模（50/100/200/300）和跳数（3/6）后自动重建
4. **节点交互**：点击节点查看详情 + 推荐，拖拽平移，滚轮缩放
5. **引用链高亮**：选中节点后点击「高亮上游/下游引用链」
6. **复制论文名**：在右侧详情面板点击「复制论文名称」，然后到 Semantic Scholar / Google Scholar / arXiv 搜索全文

### 可视化编码

| 视觉元素 | 编码含义 |
|----------|----------|
| 节点颜色 | 所属研究社区（12 色调色板），中心节点固定红色 |
| 节点大小 | PageRank 值（√ 归一化，10-50px） |
| 边颜色 | 引用方向（蓝=出/红=入/绿=前/黄=后/灰=同级） |
| 边粗细 | 方向重要性（主要方向 1.5px，次要 0.8px） |
| 节点光晕 | 中心节点红色光晕 30px，大节点 12px，小节点 4px |

---

## 算法说明

### 1. 社区标签自动生成

传统方案使用硬编码映射表（如"社区 0 = 计算机科学"），本项目改为**动态关键词提取**：

1. 从社区内随机采样最多 300 篇论文标题
2. 分词 → 去停用词 → 统计 bigram + unigram 频率
3. 优先选择高频 bigram（如 "Neural Network"），去重后取 Top 3
4. 小社区（< 10 篇）标记为"小研究方向"
5. 结果缓存，避免重复计算

### 2. 社区聚类自定义力模拟

ECharts 原生 force 不支持社区聚类，本项目实现了独立的力模拟算法：

```
for iteration in 1..50:
    for each node pair:
        计算排斥力（近距离强排斥，远距离弱排斥）
    for each node:
        计算向社区中心的引力
    for each edge within community:
        计算弹簧力（理想距离 200px）
    限制速度上限 15px/帧
    限制节点不超出社区半径
```

### 3. 网络指标计算

所有图算法在 `utils/graph_utils.py` 中纯 Python 实现，不依赖 Neo4j 图算法库：

- **连通分量**：DFS 栈迭代
- **平均路径长度**：BFS + 随机采样（40 节点），避免 O(N²) 全对全
- **模块度**：Newman-Girvan 标准公式 `Q = Σ(e_ii - a_i²)`
- **邻接表**：从边列表构建无向邻接表

### 4. PageRank 归一化

原始 PageRank 值可能非常大（取决于图规模），后端在 `build_graph_response` 中计算 `pr_max`，前端渲染时除以 `pr_max` 得到归一化值（0-1 区间），用于节点大小映射。

---

## 性能优化

### 后端优化

| 策略 | 实现位置 | 效果 |
|------|----------|------|
| APOC 子图展开 | `graph_service.py` → `apoc.path.subgraphNodes` | 3-5x 查询加速 |
| 全文索引 | Neo4j `paperTitleIndex` | 搜索从 O(N) 降至 O(log N) |
| 推荐缓存 | `recommend_service.py` → `_recommend_cache` | 避免重复 Cypher 查询 |
| 数据库连接单例 | `neo4j_service.py` → `_driver` | 避免重复 TCP 握手 |
| 社区标签缓存 | `graph_service.py` → `_community_label_cache` | 避免重复关键词提取 |

### 前端优化

| 策略 | 实现位置 | 效果 |
|------|----------|------|
| 网络数据缓存 | `main.js` → `dataCache` (Map) | 切换布局无需重新请求 |
| 渲染防抖 | `main.js` → `renderBusy` 标志位 | 防止快速点击导致并发请求 |
| 搜索防抖 | `main.js` → `suggestTimer` (280ms) | 减少不必要的 API 调用 |
| 非力导向布局禁用动画 | `force.layoutAnimation = false` | 社区/时间/放射模式即时渲染 |
| Canvas 渲染器 | `echarts.init(dom, null, {renderer:'canvas'})` | 大数据量下优于 SVG |

---

## 开发路线图

### 已完成

- [x] Flask Blueprint 模块化架构
- [x] Neo4j 图数据库集成 + APOC 优化
- [x] 全文索引搜索 + CONTAINS 回退
- [x] 四种可视化布局模式
- [x] 三级推荐策略 + 缓存
- [x] 6 项网络指标分析
- [x] 三类前沿论文发现
- [x] 引用链上下游高亮
- [x] 动态社区标签生成
- [x] 暗色主题 UI
- [x] 性能监控端点

### 计划中

- [ ] Docker 一键部署支持
- [ ] 论文摘要/关键词展示
- [ ] 导出 PNG/SVG 高清图片
- [ ] 用户自定义社区颜色
- [ ] 多中心节点对比模式
- [ ] 时间线动画播放
- [ ] 后端单元测试 + 集成测试

---

## License

MIT License

---

**最后更新**：2025 年 4 月
