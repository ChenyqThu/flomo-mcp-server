# Flomo API 完整接口文档

## 概述

Flomo API 提供了访问和管理 Flomo 备忘录数据的完整功能，包括备忘录获取、智能推荐、文件管理等。所有 API 都需要认证，并使用统一的签名机制。

## 认证

### Authorization Header
```
Authorization: Bearer {token}
```

### 获取 Token
1. 登录 [Flomo 网页版](https://flomoapp.com/)
2. 打开浏览器开发者工具 (F12)
3. 在 Network 标签页找到任意 API 请求
4. 复制 Request Headers 中的 `Authorization` 值

## 签名机制

所有 API 请求都需要包含签名参数，签名算法如下：

### 基础参数
```javascript
{
  "timestamp": "1748484699",        // 当前 Unix 时间戳
  "api_key": "flomo_web",          // 固定值
  "app_version": "4.0",            // 应用版本
  "platform": "web",              // 平台标识
  "webp": "1"                      // WebP 支持
}
```

### 签名计算
```javascript
// 1. 将所有参数按 key 字母顺序排序
// 2. 拼接成 key1=value1&key2=value2 格式
// 3. 末尾加上固定 salt
const salt = "dbbc3dd73364b4084c3a69346e0ce2b2";
const paramStr = "api_key=flomo_web&app_version=4.0&timestamp=1748484699&...";
const sign = md5(paramStr + salt);
```

---

## 1. 备忘录管理

### 1.1 获取备忘录列表

**接口地址**
```
GET https://flomoapp.com/api/v1/memo/updated/
```

**请求参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| timestamp | string | 是 | - | 当前时间戳 |
| api_key | string | 是 | flomo_web | 固定值 |
| app_version | string | 是 | 4.0 | 应用版本 |
| platform | string | 是 | web | 平台标识 |
| webp | string | 是 | 1 | WebP 支持 |
| tz | string | 是 | 8:0 | 时区设置 |
| limit | string | 否 | 200 | 每页数量限制 |
| latest_slug | string | 否 | - | 分页参数：上一页最后一条的 slug |
| latest_updated_at | string | 否 | - | 分页参数：上一页最后一条的更新时间戳 |
| sign | string | 是 | - | MD5 签名 |

**响应示例**
```json
{
  "code": 0,
  "message": "",
  "data": [
    {
      "content": "<p>备忘录内容...</p>",
      "creator_id": 518148,
      "source": "web",
      "tags": ["标签1", "标签2"],
      "pin": 0,
      "created_at": "2024-12-21 11:25:11",
      "updated_at": "2024-12-21 22:47:24",
      "deleted_at": null,
      "slug": "MTUyNjcyMzEw",
      "linked_count": 0,
      "linked_memos": [],
      "backlinked_memos": [],
      "files": [
        {
          "id": 3829107,
          "creator_id": 518148,
          "type": "image",
          "name": "example.png",
          "path": "file/2022-05-02/518148/...",
          "size": 164348,
          "url": "https://static.flomoapp.com/...",
          "thumbnail_url": "https://static.flomoapp.com/..."
        }
      ]
    }
  ]
}
```

**分页说明**
- 首次请求不传 `latest_slug` 和 `latest_updated_at`
- 后续分页请求传入上一页最后一条记录的对应值
- 当返回数据少于 `limit` 时表示已到最后一页

---

### 1.2 获取相关推荐

**接口地址**
```
GET https://flomoapp.com/api/v1/memo/{memo_slug}/recommended
```

**路径参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| memo_slug | string | 是 | 备忘录的唯一标识符 |

**请求参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| type | string | 否 | 1 | 推荐类型 |
| no_same_tag | string | 否 | 0 | 是否排除相同标签 (0=不排除, 1=排除) |
| timestamp | string | 是 | - | 当前时间戳 |
| api_key | string | 是 | flomo_web | 固定值 |
| app_version | string | 是 | 4.0 | 应用版本 |
| platform | string | 是 | web | 平台标识 |
| webp | string | 是 | 1 | WebP 支持 |
| sign | string | 是 | - | MD5 签名 |

**响应示例**
```json
{
  "code": 0,
  "message": "",
  "data": [
    {
      "memo_id": 152672310,
      "similarity": "0.9225680185894993",
      "memo": {
        "content": "<p>相关备忘录内容...</p>",
        "creator_id": 518148,
        "tags": ["相关标签"],
        "created_at": "2024-12-21 11:25:11",
        "slug": "MTUyNjcyMzEw",
        "files": []
      }
    }
  ]
}
```

**相似度说明**
- `similarity` 范围：0.0 - 1.0
- 数值越高表示相关性越强
- 建议使用 > 0.85 作为高相关性阈值

---

## 2. 文件管理

### 2.1 获取文件信息

**接口地址**
```
GET https://flomoapp.com/api/v1/file/
```

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| ids[] | array | 是 | 文件 ID 数组，格式：ids[]=123&ids[]=456 |
| timestamp | string | 是 | 当前时间戳 |
| api_key | string | 是 | flomo_web |
| app_version | string | 是 | 4.0 |
| platform | string | 是 | web |
| webp | string | 是 | 1 |
| sign | string | 是 | MD5 签名 |

**请求示例**
```
GET /api/v1/file/?ids[]=7158509&ids[]=5299446&timestamp=...&sign=...
```

**响应示例**
```json
{
  "code": 0,
  "message": "",
  "data": [
    {
      "id": 7158509,
      "creator_id": 518148,
      "type": "image",
      "name": "example.jpg",
      "path": "file/2022-10-18/518148/...",
      "size": 397183,
      "url": "https://static.flomoapp.com/file/...",
      "thumbnail_url": "https://static.flomoapp.com/file/.../thumbnailwebp"
    }
  ]
}
```

---

## 3. 错误处理

### 通用错误码

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| -1 | 设备时间校验失败 |
| -10 | 请先登录 |

### 错误响应格式
```json
{
  "code": -1,
  "message": "设备时间校验失败，请检查设备时间与真实时间一致",
  "data": null
}
```

### 常见错误及解决方案

**认证失败 (-10)**
- 检查 Authorization token 是否正确
- 确认 token 格式：`Bearer {actual_token}`
- 重新获取最新的 token

**时间校验失败 (-1)**
- 确保使用当前真实时间戳
- 避免使用固定或未来的时间戳
- 签名必须基于当前时间戳重新计算

---

## 4. SDK 使用示例

### Python SDK

```python
import requests
import hashlib
from datetime import datetime

class FlomoAPI:
    def __init__(self, token):
        self.token = token
        self.salt = "dbbc3dd73364b4084c3a69346e0ce2b2"
        self.base_url = "https://flomoapp.com/api/v1"
    
    def _generate_params(self, extra_params=None):
        params = {
            "timestamp": str(int(datetime.now().timestamp())),
            "api_key": "flomo_web",
            "app_version": "4.0",
            "platform": "web",
            "webp": "1"
        }
        if extra_params:
            params.update(extra_params)
        
        param_str = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
        sign = hashlib.md5((param_str + self.salt).encode("utf-8")).hexdigest()
        params["sign"] = sign
        return params
    
    def get_memos(self, limit=200):
        params = self._generate_params({"limit": str(limit), "tz": "8:0"})
        headers = {"Authorization": self.token}
        
        response = requests.get(f"{self.base_url}/memo/updated/", 
                              params=params, headers=headers)
        return response.json()
    
    def get_recommendations(self, memo_slug, rec_type=1):
        params = self._generate_params({"type": str(rec_type), "no_same_tag": "0"})
        headers = {"Authorization": self.token}
        
        response = requests.get(f"{self.base_url}/memo/{memo_slug}/recommended", 
                              params=params, headers=headers)
        return response.json()

# 使用示例
api = FlomoAPI("Bearer your_token_here")
memos = api.get_memos(limit=10)
```

### JavaScript SDK

```javascript
class FlomoAPI {
    constructor(token) {
        this.token = token;
        this.salt = "dbbc3dd73364b4084c3a69346e0ce2b2";
        this.baseUrl = "https://flomoapp.com/api/v1";
    }
    
    async generateParams(extraParams = {}) {
        const params = {
            timestamp: Math.floor(Date.now() / 1000).toString(),
            api_key: "flomo_web",
            app_version: "4.0",
            platform: "web",
            webp: "1",
            ...extraParams
        };
        
        const paramStr = Object.keys(params)
            .sort()
            .map(key => `${key}=${params[key]}`)
            .join('&');
        
        const sign = await this.md5(paramStr + this.salt);
        params.sign = sign;
        return params;
    }
    
    async getMemos(limit = 200) {
        const params = await this.generateParams({
            limit: limit.toString(),
            tz: "8:0"
        });
        
        const url = new URL(`${this.baseUrl}/memo/updated/`);
        Object.keys(params).forEach(key => 
            url.searchParams.append(key, params[key])
        );
        
        const response = await fetch(url, {
            headers: { Authorization: this.token }
        });
        
        return response.json();
    }
}
```

---

## 5. 最佳实践

### 5.1 请求频率控制
- 建议在请求间添加 0.5-1 秒延迟
- 避免短时间内大量并发请求
- 使用分页获取大量数据

### 5.2 数据缓存策略
- 备忘录数据可缓存较长时间（如 1 小时）
- 推荐数据建议缓存较短时间（如 15 分钟）
- 文件 URL 包含过期时间，注意及时更新

### 5.3 错误重试机制
- 网络错误：指数退避重试，最多 3 次
- 认证错误：立即停止，提示用户重新授权
- 限流错误：等待后重试

### 5.4 数据处理建议
- HTML 内容可使用 BeautifulSoup 或类似库解析
- 支持 Markdown 转换以便后续处理
- 建议提取标签、链接等结构化数据

---

## 6. 高级功能

### 6.1 本地搜索实现

由于 Flomo API 不直接支持搜索，建议实现本地搜索：

```python
def search_memos(memos, keyword):
    """在备忘录中搜索关键词"""
    results = []
    for memo in memos:
        content = BeautifulSoup(memo['content'], 'html.parser').get_text()
        if keyword.lower() in content.lower():
            results.append(memo)
    return results
```

### 6.2 智能推荐系统

基于 API 的推荐功能构建更复杂的推荐系统：

```python
def build_recommendation_network(api, memo_slugs):
    """构建备忘录推荐网络"""
    network = {}
    for slug in memo_slugs:
        recommendations = api.get_recommendations(slug)
        network[slug] = recommendations
    return network
```

### 6.3 数据导出

```python
def export_to_markdown(memos, filename):
    """导出备忘录为 Markdown 格式"""
    with open(filename, 'w', encoding='utf-8') as f:
        for memo in memos:
            content = html2text(memo['content'])
            f.write(f"# {memo['created_at']}\n\n")
            f.write(f"{content}\n\n")
            if memo['tags']:
                f.write(f"标签: {', '.join(memo['tags'])}\n\n")
            f.write("---\n\n")
```

---

## 7. 附录

### 7.1 时区列表
- `8:0` - 北京时间 (UTC+8)
- `0:0` - UTC 时间
- `-5:0` - 美国东部时间 (UTC-5)

### 7.2 文件类型
- `image` - 图片文件
- `audio` - 音频文件  
- `video` - 视频文件
- `document` - 文档文件

### 7.3 备忘录来源
- `web` - 网页版
- `ios` - iOS 应用
- `android` - Android 应用
- `wechat` - 微信小程序

---

## 3. 标签管理

### 3.1 获取标签列表

**接口地址**
```
GET https://flomoapp.com/api/v1/tag/updated/
```

**重要说明**
> ⚠️ 此接口仅返回**顶级标签**（父级标签），不包含带有层级分隔符 `/` 的完整标签。要获取所有标签，需要从备忘录数据中提取。

**请求参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| timestamp | string | 是 | - | 当前时间戳 |
| api_key | string | 是 | flomo_web | 固定值 |
| app_version | string | 是 | 4.0 | 应用版本 |
| platform | string | 是 | web | 平台标识 |
| webp | string | 是 | 1 | WebP 支持 |
| tz | string | 是 | 8:0 | 时区设置 |
| limit | string | 否 | 200 | 每页数量限制 |
| latest_updated_at | string | 否 | - | 分页参数：上一页最后一条的更新时间戳 |
| sign | string | 是 | - | MD5 签名 |

**响应示例**
```json
{
  "code": 0,
  "message": "",
  "data": [
    {
      "id": 224918,
      "name": "设计人生",
      "icon_type": "emoji",
      "icon_value": "🌈",
      "pin": 0,
      "order": 0,
      "updated_at": "2022-04-11 14:52:18",
      "deleted_at": null
    },
    {
      "id": 225001,
      "name": "读书",
      "icon_type": "emoji", 
      "icon_value": "📚",
      "pin": 0,
      "order": 1,
      "updated_at": "2022-04-12 09:30:45",
      "deleted_at": null
    }
  ]
}
```

**字段说明**

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | number | 标签唯一ID |
| name | string | 标签名称（仅顶级） |
| icon_type | string | 图标类型（emoji/image） |
| icon_value | string | 图标值 |
| pin | number | 是否置顶（0=否，1=是） |
| order | number | 排序顺序 |
| updated_at | string | 更新时间 |
| deleted_at | string | 删除时间（null=未删除） |

---

### 3.2 获取完整标签列表（推荐方法）

由于标签 API 只返回顶级标签，获取完整标签列表的推荐方法是**从备忘录数据中提取**：

**实现方案**
```python
def get_all_tags_from_memos(api_client):
    """从备忘录中提取所有标签"""
    # 1. 获取所有备忘录
    all_memos = api_client.get_all_memos()
    
    # 2. 提取所有标签
    all_tags = set()
    tag_stats = {}
    
    for memo in all_memos:
        tags = memo.get('tags', [])
        for tag in tags:
            all_tags.add(tag)
            tag_stats[tag] = tag_stats.get(tag, 0) + 1
    
    # 3. 构建标签层级结构
    tag_hierarchy = build_tag_hierarchy(list(all_tags))
    
    return {
        'all_tags': list(all_tags),
        'tag_stats': tag_stats,
        'tag_hierarchy': tag_hierarchy,
        'total_count': len(all_tags)
    }

def build_tag_hierarchy(tags):
    """构建标签层级结构"""
    hierarchy = {}
    
    for tag in tags:
        if '/' in tag:
            parts = tag.split('/')
            current = hierarchy
            
            for i, part in enumerate(parts):
                if part not in current:
                    current[part] = {} if i < len(parts) - 1 else tag
                current = current[part] if isinstance(current[part], dict) else {}
    
    return hierarchy
```

**标签层级说明**
- Flomo 使用 `/` 作为标签层级分隔符
- 支持多级嵌套，如：`读书/心理学/认知偏见`
- 常见层级深度为 2-3 级
- 顶级标签通常是分类（如：读书、项目、兴趣）

**完整标签获取示例**
```python
# 获取完整标签信息
tag_data = get_all_tags_from_memos(flomo_api)

print(f"总标签数: {tag_data['total_count']}")
print(f"热门标签: {sorted(tag_data['tag_stats'].items(), key=lambda x: x[1], reverse=True)[:10]}")

# 按层级显示
for parent, children in tag_data['tag_hierarchy'].items():
    print(f"{parent}/")
    if isinstance(children, dict):
        for child in children:
            print(f"  └── {child}")
```

---

## 更新日志

- **v1.0** (2025-05-29): 初始版本，包含基础 API 文档
- 支持备忘录获取、推荐、文件管理等核心功能
- 提供完整的认证和签名机制说明
- 包含 Python 和 JavaScript 使用示例

---

*本文档基于 Flomo API v4.0 编写，如有更新请参考最新版本。*