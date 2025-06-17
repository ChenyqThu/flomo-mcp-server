# Flomo MCP Server 架构设计文档

## 1. 架构概述

### 1.1 整体架构
Flomo MCP Server 采用分层架构设计，确保系统的可扩展性、可维护性和高性能。整体架构包含以下核心层次：

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Assistant Layer                       │
│                 (Claude, GPT, etc.)                        │
└─────────────────────┬───────────────────────────────────────┘
                      │ MCP Protocol
┌─────────────────────┴───────────────────────────────────────┐
│                  MCP Server Layer                          │
│  ┌─────────────────┬─────────────────┬─────────────────┐   │
│  │   Tool Handler  │  Session Mgr    │   Error Handler │   │
│  └─────────────────┴─────────────────┴─────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │ Internal API
┌─────────────────────┴───────────────────────────────────────┐
│                 Business Logic Layer                       │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐ │
│  │   Search    │ Recommend   │  Analysis   │   Export    │ │
│  │   Service   │  Service    │  Service    │  Service    │ │
│  └─────────────┴─────────────┴─────────────┴─────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │ Data Access Interface
┌─────────────────────┴───────────────────────────────────────┐
│                  Data Access Layer                         │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐ │
│  │   Flomo     │   Cache     │   Local     │   File      │ │
│  │   Client    │   Manager   │   Storage   │   Manager   │ │
│  └─────────────┴─────────────┴─────────────┴─────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │ External API / Storage
┌─────────────────────┴───────────────────────────────────────┐
│                 External Services                          │
│     ┌─────────────────┐              ┌─────────────────┐    │
│     │   Flomo API     │              │  Local Storage  │    │
│     │  (flomoapp.com) │              │   (SQLite/JSON) │    │
│     └─────────────────┘              └─────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 设计原则
- **模块化**：清晰的模块划分，低耦合高内聚
- **可扩展**：支持新功能的快速添加和现有功能的扩展
- **高性能**：通过缓存和优化算法提升响应速度
- **容错性**：优雅处理各种异常情况，确保系统稳定
- **安全性**：保护用户数据和系统安全

## 2. 核心组件设计

### 2.1 MCP Server Layer

#### 2.1.1 Tool Handler
**职责**：处理来自 AI 助手的工具调用请求

**核心功能**：
- 工具注册和管理
- 参数验证和转换
- 调用结果格式化
- 工具权限控制

**接口设计**：
```python
class ToolHandler:
    def register_tool(self, tool_name: str, handler: Callable) -> None
    def validate_parameters(self, tool_name: str, params: dict) -> bool
    def execute_tool(self, tool_name: str, params: dict) -> ToolResult
    def format_response(self, result: Any) -> MCPResponse
```

#### 2.1.2 Session Manager
**职责**：管理会话状态和上下文信息

**核心功能**：
- 会话创建和销毁
- 上下文状态管理
- 用户认证信息管理
- 会话超时处理

**接口设计**：
```python
class SessionManager:
    def create_session(self, user_token: str) -> Session
    def get_session(self, session_id: str) -> Optional[Session]
    def update_context(self, session_id: str, context: dict) -> None
    def cleanup_expired_sessions(self) -> None
```

#### 2.1.3 Error Handler
**职责**：统一的错误处理和异常管理

**核心功能**：
- 异常捕获和分类
- 错误信息格式化
- 重试机制实现
- 错误日志记录

### 2.2 Business Logic Layer

#### 2.2.1 Search Service
**职责**：提供智能搜索和检索功能

**核心模块**：
```python
class SearchService:
    def __init__(self, data_access: DataAccessLayer):
        self.data_access = data_access
        self.text_processor = TextProcessor()
        self.index_manager = IndexManager()
    
    def search_memos(self, query: SearchQuery) -> SearchResult:
        """多维度搜索备忘录"""
        pass
    
    def build_search_index(self, memos: List[Memo]) -> None:
        """构建搜索索引"""
        pass
    
    def update_index(self, memo: Memo) -> None:
        """增量更新索引"""
        pass
```

**搜索算法**：
- **全文搜索**：基于 TF-IDF 的文本相似度计算
- **标签匹配**：支持精确匹配和模糊匹配
- **时间筛选**：灵活的时间范围查询
- **组合搜索**：多条件的 AND/OR/NOT 逻辑组合

#### 2.2.2 Recommendation Service
**职责**：提供智能推荐和关联发现

**核心算法**：
```python
class RecommendationService:
    def __init__(self, data_access: DataAccessLayer):
        self.data_access = data_access
        self.similarity_calculator = SimilarityCalculator()
        self.graph_builder = GraphBuilder()
    
    def get_related_memos(self, memo_id: str, threshold: float) -> List[RelatedMemo]:
        """获取相关推荐"""
        pass
    
    def build_similarity_matrix(self, memos: List[Memo]) -> np.ndarray:
        """构建相似度矩阵"""
        pass
    
    def discover_topic_clusters(self, memos: List[Memo]) -> List[TopicCluster]:
        """发现主题聚类"""
        pass
```

**推荐策略**：
- **内容相似度**：基于 TF-IDF 和余弦相似度
- **标签关联**：基于标签共现和层级关系
- **时间关联**：考虑时间邻近性的推荐
- **用户行为**：基于历史查询和交互模式

#### 2.2.3 Analysis Service
**职责**：提供深度分析和洞察提取

**核心功能**：
```python
class AnalysisService:
    def __init__(self, data_access: DataAccessLayer):
        self.data_access = data_access
        self.nlp_processor = NLPProcessor()
        self.statistics_engine = StatisticsEngine()
    
    def analyze_tags(self, analysis_type: str, time_range: str) -> TagAnalysisResult:
        """标签分析"""
        pass
    
    def extract_insights(self, memos: List[Memo], insight_type: str) -> List[Insight]:
        """提取关键洞察"""
        pass
    
    def analyze_trends(self, memos: List[Memo], granularity: str) -> TrendAnalysis:
        """趋势分析"""
        pass
```

**分析算法**：
- **关键词提取**：TF-IDF + TextRank 算法
- **情感分析**：基于词典和机器学习的混合方法
- **主题建模**：LDA (Latent Dirichlet Allocation)
- **趋势分析**：时间序列分析和变点检测

#### 2.2.4 Export Service
**职责**：数据导出和格式转换

**支持格式**：
- Markdown：结构化文档导出
- JSON：原始数据导出
- CSV：统计数据导出
- 思维导图：MindMap 格式

### 2.3 Data Access Layer

#### 2.3.1 Flomo Client
**职责**：与 Flomo API 的交互管理

**核心功能**：
```python
class FlomoClient:
    def __init__(self, token: str):
        self.token = token
        self.session = requests.Session()
        self.rate_limiter = RateLimiter()
        self.retry_handler = RetryHandler()
    
    def get_memos(self, params: dict) -> List[Memo]:
        """获取备忘录列表"""
        pass
    
    def get_recommendations(self, memo_id: str) -> List[RecommendedMemo]:
        """获取推荐内容"""
        pass
    
    def get_file_info(self, file_ids: List[str]) -> List[FileInfo]:
        """获取文件信息"""
        pass
```

**特性实现**：
- **签名算法**：MD5 签名的自动计算和验证
- **速率限制**：智能的请求频率控制
- **错误重试**：指数退避的重试机制
- **数据解析**：HTML 内容的清理和结构化

#### 2.3.2 Cache Manager
**职责**：多层缓存管理和优化

**缓存策略**：
```python
class CacheManager:
    def __init__(self):
        self.memory_cache = MemoryCache(max_size=1000)
        self.disk_cache = DiskCache(cache_dir="./cache")
        self.cache_policy = CachePolicy()
    
    def get(self, key: str) -> Optional[Any]:
        """多层缓存获取"""
        pass
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """多层缓存设置"""
        pass
    
    def invalidate(self, pattern: str) -> None:
        """缓存失效处理"""
        pass
```

**缓存层级**：
- **L1 缓存**：内存缓存，存储热点数据
- **L2 缓存**：磁盘缓存，存储完整数据集
- **L3 缓存**：索引缓存，存储搜索索引

#### 2.3.3 Local Storage
**职责**：本地数据存储和管理

**存储方案**：
- **SQLite**：结构化数据存储
- **JSON 文件**：配置和元数据存储
- **索引文件**：搜索索引的持久化

```python
class LocalStorage:
    def __init__(self, db_path: str):
        self.db = sqlite3.connect(db_path)
        self.json_storage = JSONStorage()
        self.index_storage = IndexStorage()
    
    def save_memos(self, memos: List[Memo]) -> None:
        """保存备忘录数据"""
        pass
    
    def load_memos(self, filters: dict) -> List[Memo]:
        """加载备忘录数据"""
        pass
    
    def update_memo(self, memo: Memo) -> None:
        """更新备忘录数据"""
        pass
```

## 3. 数据模型设计

### 3.1 核心数据结构

#### 3.1.1 Memo 数据模型
```python
@dataclass
class Memo:
    id: str
    slug: str
    content: str
    plain_text: str  # HTML 解析后的纯文本
    summary: str     # 自动生成的摘要
    tags: List[str]
    creator_id: int
    source: str
    pin: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]
    linked_count: int
    linked_memos: List[str]
    backlinked_memos: List[str]
    files: List[FileInfo]
    
    # 计算字段
    word_count: int
    reading_time: int
    sentiment_score: float
    keywords: List[str]
```

#### 3.1.2 Tag 数据模型
```python
@dataclass
class Tag:
    id: Optional[int]
    name: str
    full_path: str  # 完整路径，如 "读书/心理学/认知偏见"
    level: int      # 层级深度
    parent: Optional[str]
    children: List[str]
    icon_type: Optional[str]
    icon_value: Optional[str]
    pin: int
    order: int
    usage_count: int
    first_used: datetime
    last_used: datetime
```

#### 3.1.3 SearchQuery 数据模型
```python
@dataclass
class SearchQuery:
    keywords: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    tag_logic: str = "AND"  # AND, OR, NOT
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    content_type: str = "all"  # all, text_only, with_images, with_links
    sort_by: str = "relevance"  # relevance, created_at, updated_at
    sort_order: str = "desc"
    limit: int = 50
    offset: int = 0
    
    # 高级搜索选项
    include_deleted: bool = False
    min_word_count: Optional[int] = None
    max_word_count: Optional[int] = None
    sentiment_filter: Optional[str] = None  # positive, negative, neutral
```

### 3.2 数据库设计

#### 3.2.1 SQLite 表结构
```sql
-- 备忘录表
CREATE TABLE memos (
    id TEXT PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,
    content TEXT NOT NULL,
    plain_text TEXT NOT NULL,
    summary TEXT,
    creator_id INTEGER,
    source TEXT,
    pin INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP,
    linked_count INTEGER DEFAULT 0,
    word_count INTEGER,
    sentiment_score REAL,
    INDEX(created_at),
    INDEX(updated_at),
    INDEX(creator_id)
);

-- 标签表
CREATE TABLE tags (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    full_path TEXT UNIQUE NOT NULL,
    level INTEGER,
    parent_path TEXT,
    icon_type TEXT,
    icon_value TEXT,
    pin INTEGER DEFAULT 0,
    order_index INTEGER DEFAULT 0,
    usage_count INTEGER DEFAULT 0,
    first_used TIMESTAMP,
    last_used TIMESTAMP,
    INDEX(name),
    INDEX(full_path),
    INDEX(parent_path)
);

-- 备忘录标签关联表
CREATE TABLE memo_tags (
    memo_id TEXT,
    tag_path TEXT,
    PRIMARY KEY (memo_id, tag_path),
    FOREIGN KEY (memo_id) REFERENCES memos(id),
    FOREIGN KEY (tag_path) REFERENCES tags(full_path)
);

-- 文件表
CREATE TABLE files (
    id INTEGER PRIMARY KEY,
    memo_id TEXT,
    type TEXT,
    name TEXT,
    path TEXT,
    size INTEGER,
    url TEXT,
    thumbnail_url TEXT,
    FOREIGN KEY (memo_id) REFERENCES memos(id)
);

-- 关联关系表
CREATE TABLE memo_relations (
    from_memo_id TEXT,
    to_memo_id TEXT,
    relation_type TEXT, -- linked, backlinked, similar
    strength REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (from_memo_id, to_memo_id, relation_type)
);
```

## 4. 接口设计

### 4.1 MCP 工具接口规范

#### 4.1.1 搜索相关工具
```python
# 搜索备忘录
{
    "name": "search_memos",
    "description": "搜索备忘录，支持关键词、标签、时间范围等多维度筛选",
    "parameters": {
        "type": "object",
        "properties": {
            "keywords": {
                "type": "string",
                "description": "搜索关键词，支持多个词用空格分隔"
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "标签列表，支持层级标签"
            },
            "tag_logic": {
                "type": "string",
                "enum": ["AND", "OR", "NOT"],
                "default": "AND",
                "description": "标签逻辑关系"
            },
            "date_range": {
                "type": "string",
                "description": "时间范围，如 '7days', '1month', '3months', '1year'"
            },
            "limit": {
                "type": "integer",
                "default": 20,
                "minimum": 1,
                "maximum": 100,
                "description": "返回结果数量限制"
            },
            "sort_by": {
                "type": "string",
                "enum": ["relevance", "created_at", "updated_at"],
                "default": "relevance",
                "description": "排序方式"
            }
        }
    }
}

# 获取最近备忘录
{
    "name": "get_recent_memos",
    "description": "获取最近的备忘录列表",
    "parameters": {
        "type": "object",
        "properties": {
            "days": {
                "type": "integer",
                "default": 7,
                "minimum": 1,
                "maximum": 365,
                "description": "获取最近几天的备忘录"
            },
            "limit": {
                "type": "integer",
                "default": 20,
                "minimum": 1,
                "maximum": 100
            }
        }
    }
}
```

#### 4.1.2 推荐相关工具
```python
# 获取相关推荐
{
    "name": "get_related_memos",
    "description": "获取与指定备忘录相关的推荐内容",
    "parameters": {
        "type": "object",
        "properties": {
            "memo_id": {
                "type": "string",
                "description": "备忘录ID或关键词"
            },
            "similarity_threshold": {
                "type": "number",
                "default": 0.7,
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "相似度阈值"
            },
            "exclude_same_tags": {
                "type": "boolean",
                "default": false,
                "description": "是否排除相同标签的内容"
            },
            "limit": {
                "type": "integer",
                "default": 10,
                "minimum": 1,
                "maximum": 50
            }
        },
        "required": ["memo_id"]
    }
}

# 发现主题聚类
{
    "name": "discover_topic_clusters",
    "description": "发现备忘录中的主题聚类",
    "parameters": {
        "type": "object",
        "properties": {
            "seed_keywords": {
                "type": "array",
                "items": {"type": "string"},
                "description": "种子关键词，用于指定聚类方向"
            },
            "cluster_count": {
                "type": "integer",
                "default": 5,
                "minimum": 2,
                "maximum": 20,
                "description": "聚类数量"
            },
            "min_cluster_size": {
                "type": "integer",
                "default": 3,
                "minimum": 2,
                "description": "最小聚类大小"
            }
        }
    }
}
```

#### 4.1.3 分析相关工具
```python
# 标签分析
{
    "name": "analyze_tags",
    "description": "分析标签使用情况和层级结构",
    "parameters": {
        "type": "object",
        "properties": {
            "analysis_type": {
                "type": "string",
                "enum": ["hierarchy", "statistics", "trends", "suggestions"],
                "default": "hierarchy",
                "description": "分析类型"
            },
            "time_range": {
                "type": "string",
                "description": "分析时间范围"
            },
            "include_stats": {
                "type": "boolean",
                "default": true,
                "description": "是否包含统计信息"
            },
            "top_n": {
                "type": "integer",
                "default": 20,
                "minimum": 5,
                "maximum": 100,
                "description": "返回Top N标签"
            }
        }
    }
}

# 提取洞察
{
    "name": "extract_insights",
    "description": "从备忘录中提取关键洞察和观点",
    "parameters": {
        "type": "object",
        "properties": {
            "date_range": {
                "type": "string",
                "description": "分析时间范围"
            },
            "insight_type": {
                "type": "string",
                "enum": ["key_points", "questions", "conclusions", "trends"],
                "default": "key_points",
                "description": "洞察类型"
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "限定分析的标签范围"
            },
            "min_importance": {
                "type": "number",
                "default": 0.5,
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "最小重要性阈值"
            }
        }
    }
}
```

### 4.2 响应数据格式

#### 4.2.1 搜索结果格式
```json
{
    "total_count": 156,
    "page_info": {
        "current_page": 1,
        "total_pages": 8,
        "has_next": true
    },
    "results": [
        {
            "id": "MTUyNjcyMzEw",
            "content": "备忘录内容...",
            "summary": "内容摘要...",
            "plain_text": "纯文本内容...",
            "tags": ["标签1", "标签2"],
            "created_at": "2024-12-21T11:25:11Z",
            "updated_at": "2024-12-21T22:47:24Z",
            "word_count": 128,
            "reading_time": 1,
            "relevance_score": 0.95,
            "highlight": {
                "content": "高亮显示的匹配内容...",
                "tags": ["匹配的标签"]
            },
            "files": [
                {
                    "id": 3829107,
                    "type": "image",
                    "name": "example.png",
                    "url": "https://static.flomoapp.com/...",
                    "thumbnail_url": "https://static.flomoapp.com/..."
                }
            ]
        }
    ],
    "aggregations": {
        "tags": [
            {"name": "读书", "count": 45},
            {"name": "思考", "count": 32}
        ],
        "date_distribution": [
            {"date": "2024-12", "count": 28},
            {"date": "2024-11", "count": 35}
        ]
    }
}
```

#### 4.2.2 推荐结果格式
```json
{
    "source_memo": {
        "id": "MTUyNjcyMzEw",
        "summary": "源备忘录摘要..."
    },
    "recommendations": [
        {
            "memo": {
                "id": "MTUyNjcyMzEx",
                "content": "推荐备忘录内容...",
                "summary": "推荐内容摘要...",
                "tags": ["相关标签"],
                "created_at": "2024-12-20T10:15:30Z"
            },
            "similarity_score": 0.87,
            "relation_type": "content_similar",
            "reason": "内容相似度高，都涉及机器学习概念",
            "common_elements": {
                "keywords": ["机器学习", "算法", "数据"],
                "tags": ["技术", "学习"]
            }
        }
    ],
    "clusters": [
        {
            "topic": "机器学习",
            "memo_count": 12,
            "keywords": ["算法", "模型", "训练"],
            "memo_ids": ["id1", "id2", "id3"]
        }
    ]
}
```

#### 4.2.3 分析结果格式
```json
{
    "analysis_type": "tag_hierarchy",
    "time_range": "2024-01-01 to 2024-12-31",
    "total_tags": 156,
    "total_memos": 1248,
    "hierarchy": {
        "读书": {
            "count": 245,
            "percentage": 19.6,
            "children": {
                "心理学": {"count": 67, "percentage": 5.4},
                "技术": {"count": 89, "percentage": 7.1},
                "历史": {"count": 34, "percentage": 2.7}
            }
        },
        "工作": {
            "count": 189,
            "percentage": 15.1,
            "children": {
                "项目管理": {"count": 45, "percentage": 3.6},
                "团队协作": {"count": 32, "percentage": 2.6}
            }
        }
    },
    "trends": [
        {
            "tag": "AI",
            "timeline": [
                {"month": "2024-01", "count": 5},
                {"month": "2024-02", "count": 8},
                {"month": "2024-03", "count": 15}
            ],
            "trend": "increasing",
            "growth_rate": 0.67
        }
    ],
    "insights": [
        "AI 相关标签使用量增长 67%",
        "读书类备忘录占总量的 19.6%",
        "工作相关思考主要集中在项目管理"
    ],
    "suggestions": [
        "建议将 'ML' 和 '机器学习' 标签合并",
        "考虑为 '工作/产品设计' 创建子标签",
        "'思考' 标签使用过于宽泛，建议细分"
    ]
}
```

## 5. 部署架构

### 5.1 开发环境
```
┌─────────────────────────────────────────┐
│            Development Setup            │
│                                         │
│  ┌─────────────────┐  ┌─────────────────┐│
│  │   Local MCP     │  │   Test Client   ││
│  │    Server       │  │   (Claude/AI)   ││
│  │                 │  │                 ││
│  │  - Hot Reload   │  │  - MCP Protocol ││
│  │  - Debug Mode   │  │  - Tool Testing ││
│  │  - Local Cache  │  │                 ││
│  └─────────────────┘  └─────────────────┘│
│           │                      │       │
│           └──────────────────────┘       │
│                                         │
│  ┌─────────────────────────────────────┐ │
│  │         Local Storage               │ │
│  │  - SQLite Database                  │ │
│  │  - JSON Configuration               │ │
│  │  - Cache Files                      │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### 5.2 生产环境
```
┌─────────────────────────────────────────┐
│           Production Setup              │
│                                         │
│  ┌─────────────────┐  ┌─────────────────┐│
│  │   MCP Server    │  │  AI Assistants  ││
│  │    Instance     │  │                 ││
│  │                 │  │  - Claude       ││
│  │  - Process Mgr  │  │  - GPT          ││
│  │  - Health Check │  │  - Custom AI    ││
│  │  - Load Balance │  │                 ││
│  └─────────────────┘  └─────────────────┘│
│           │                      │       │
│           └──────────────────────┘       │
│                                         │
│  ┌─────────────────────────────────────┐ │
│  │      Persistent Storage             │ │
│  │  - Database (SQLite/PostgreSQL)    │ │
│  │  - File Storage                     │ │
│  │  - Configuration Management        │ │
│  │  - Backup & Recovery               │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### 5.3 容器化部署
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY src/ ./src/
COPY config/ ./config/

# 创建数据目录
RUN mkdir -p /app/data /app/cache /app/logs

# 设置环境变量
ENV PYTHONPATH=/app/src
ENV DATA_DIR=/app/data
ENV CACHE_DIR=/app/cache
ENV LOG_DIR=/app/logs

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# 启动命令
CMD ["python", "src/main.py"]
```

## 6. 性能优化策略

### 6.1 缓存策略
- **多层缓存**：内存 + 磁盘 + 分布式缓存
- **智能预热**：预加载热点数据
- **缓存失效**：基于时间和事件的失效策略
- **缓存压缩**：减少内存占用

### 6.2 数据库优化
- **索引优化**：为常用查询字段建立索引
- **查询优化**：使用 EXPLAIN 分析查询计划
- **分页优化**：游标分页替代 OFFSET
- **连接池**：复用数据库连接

### 6.3 算法优化
- **并行处理**：多线程/多进程处理
- **批量操作**：减少 API 调用次数
- **增量更新**：只处理变更数据
- **异步处理**：非阻塞的后台任务

### 6.4 网络优化
- **请求合并**：批量请求减少网络开销
- **压缩传输**：gzip 压缩响应数据
- **连接复用**：HTTP 连接池
- **超时控制**：合理的超时设置

## 7. 监控和运维

### 7.1 监控指标
- **性能指标**：响应时间、吞吐量、错误率
- **资源指标**：CPU、内存、磁盘、网络使用率
- **业务指标**：API 调用次数、缓存命中率、用户活跃度
- **错误监控**：异常统计、错误分类、告警机制

### 7.2 日志管理
```python
# 日志配置示例
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '{asctime} {name} {levelname} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': 'logs/flomo_mcp.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
        },
    },
    'loggers': {
        'flomo_mcp': {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
            'propagate': False,
        },
    },
}
```

### 7.3 健康检查
```python
class HealthChecker:
    def __init__(self, services: List[Service]):
        self.services = services
    
    def check_health(self) -> HealthStatus:
        """检查系统健康状态"""
        status = HealthStatus()
        
        for service in self.services:
            try:
                service_status = service.health_check()
                status.add_service_status(service.name, service_status)
            except Exception as e:
                status.add_service_error(service.name, str(e))
        
        return status
    
    def check_dependencies(self) -> DependencyStatus:
        """检查外部依赖状态"""
        # 检查 Flomo API 可用性
        # 检查数据库连接
        # 检查缓存服务
        pass
```

这个架构设计确保了 Flomo MCP Server 的高性能、高可用性和良好的可维护性，为用户提供稳定可靠的个人知识管理服务。 