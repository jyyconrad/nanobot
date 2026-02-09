# AI本地文件管理系统 - API设计文档

## 1. REST API 规范

### 1.1 基础规范

- **协议**：HTTP/HTTPS
- **数据格式**：JSON
- **字符编码**：UTF-8
- **API 版本**：通过 URL 前缀指定（如 `/api/v1/`）
- **认证方式**：Bearer Token 或 API Key
- **跨域支持**：CORS（跨域资源共享）

### 1.2 错误处理

#### 1.2.1 错误响应格式

所有错误响应将遵循以下格式：

```json
{
  "error": {
    "code": "错误代码",
    "message": "错误描述",
    "details": "详细信息（可选）"
  }
}
```

#### 1.2.2 常见错误代码

| 错误代码 | HTTP 状态码 | 描述 |
|---------|-------------|------|
| `BAD_REQUEST` | 400 | 请求参数无效 |
| `UNAUTHORIZED` | 401 | 未认证或认证失败 |
| `FORBIDDEN` | 403 | 无权限访问 |
| `NOT_FOUND` | 404 | 资源未找到 |
| `CONFLICT` | 409 | 资源冲突 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |
| `SERVICE_UNAVAILABLE` | 503 | 服务不可用 |

### 1.3 分页规范

对于返回列表的接口，使用以下分页参数：

```json
{
  "page": 1,
  "per_page": 10,
  "total": 100,
  "data": [
    // 数据列表
  ]
}
```

## 2. API 端点定义

### 2.1 文件管理接口

#### 2.1.1 获取文件列表

```http
GET /api/v1/files
```

**查询参数**：
- `parent_id`：父文件夹 ID（可选）
- `type`：文件类型（可选）
- `page`：页码（默认 1）
- `per_page`：每页数量（默认 10）

**响应**：
```json
{
  "page": 1,
  "per_page": 10,
  "total": 25,
  "data": [
    {
      "id": 1,
      "name": "document.pdf",
      "path": "/documents/work/document.pdf",
      "size": 102400,
      "type": "document",
      "mime_type": "application/pdf",
      "created_at": "2023-12-25T10:30:00Z",
      "modified_at": "2023-12-26T14:45:00Z",
      "tags": ["工作", "文档"],
      "categories": ["文档"]
    },
    // 更多文件
  ]
}
```

#### 2.1.2 获取文件详情

```http
GET /api/v1/files/{id}
```

**路径参数**：
- `id`：文件 ID

**响应**：
```json
{
  "id": 1,
  "name": "document.pdf",
  "path": "/documents/work/document.pdf",
  "size": 102400,
  "type": "document",
  "mime_type": "application/pdf",
  "created_at": "2023-12-25T10:30:00Z",
  "modified_at": "2023-12-26T14:45:00Z",
  "tags": ["工作", "文档"],
  "categories": ["文档"],
  "hash": "a1b2c3d4e5f6",
  "summary": "这是一份关于项目进度的文档..."
}
```

#### 2.1.3 更新文件信息

```http
PUT /api/v1/files/{id}
```

**路径参数**：
- `id`：文件 ID

**请求体**：
```json
{
  "name": "new-document.pdf",
  "tags": ["工作", "文档", "项目"],
  "categories": ["文档", "项目"]
}
```

**响应**：
```json
{
  "id": 1,
  "name": "new-document.pdf",
  "path": "/documents/work/new-document.pdf",
  "size": 102400,
  "type": "document",
  "mime_type": "application/pdf",
  "created_at": "2023-12-25T10:30:00Z",
  "modified_at": "2023-12-27T09:15:00Z",
  "tags": ["工作", "文档", "项目"],
  "categories": ["文档", "项目"]
}
```

#### 2.1.4 删除文件

```http
DELETE /api/v1/files/{id}
```

**路径参数**：
- `id`：文件 ID

**响应**：
```json
{
  "success": true,
  "message": "文件已删除"
}
```

### 2.2 文件夹管理接口

#### 2.2.1 获取文件夹列表

```http
GET /api/v1/folders
```

**查询参数**：
- `parent_id`：父文件夹 ID（可选）
- `page`：页码（默认 1）
- `per_page`：每页数量（默认 10）

**响应**：
```json
{
  "page": 1,
  "per_page": 10,
  "total": 15,
  "data": [
    {
      "id": 1,
      "name": "工作文档",
      "path": "/documents/work",
      "created_at": "2023-12-25T10:30:00Z",
      "modified_at": "2023-12-26T14:45:00Z",
      "file_count": 5,
      "folder_count": 2
    },
    // 更多文件夹
  ]
}
```

#### 2.2.2 创建文件夹

```http
POST /api/v1/folders
```

**请求体**：
```json
{
  "name": "项目文档",
  "parent_id": 1
}
```

**响应**：
```json
{
  "id": 2,
  "name": "项目文档",
  "path": "/documents/work/project-docs",
  "created_at": "2023-12-27T09:15:00Z",
  "modified_at": "2023-12-27T09:15:00Z",
  "file_count": 0,
  "folder_count": 0
}
```

### 2.3 搜索接口

#### 2.3.1 语义搜索

```http
POST /api/v1/search/semantic
```

**请求体**：
```json
{
  "query": "项目进度报告",
  "type": "document", // 可选，文件类型过滤
  "page": 1,
  "per_page": 10
}
```

**响应**：
```json
{
  "page": 1,
  "per_page": 10,
  "total": 3,
  "data": [
    {
      "id": 1,
      "name": "project-progress.pdf",
      "path": "/documents/work/project-progress.pdf",
      "score": 0.95,
      "type": "document",
      "created_at": "2023-12-25T10:30:00Z"
    },
    // 更多结果
  ]
}
```

#### 2.3.2 关键词搜索

```http
POST /api/v1/search/keyword
```

**请求体**：
```json
{
  "query": "report",
  "type": "document", // 可选，文件类型过滤
  "page": 1,
  "per_page": 10
}
```

**响应**：
```json
{
  "page": 1,
  "per_page": 10,
  "total": 5,
  "data": [
    {
      "id": 1,
      "name": "project-progress.pdf",
      "path": "/documents/work/project-progress.pdf",
      "score": 0.92,
      "type": "document",
      "created_at": "2023-12-25T10:30:00Z"
    },
    // 更多结果
  ]
}
```

#### 2.3.3 获取搜索历史

```http
GET /api/v1/search/history
```

**查询参数**：
- `page`：页码（默认 1）
- `per_page`：每页数量（默认 10）

**响应**：
```json
{
  "page": 1,
  "per_page": 10,
  "total": 20,
  "data": [
    {
      "id": 1,
      "query": "项目进度报告",
      "query_type": "semantic",
      "results_count": 3,
      "selected_file_id": 1,
      "search_time": 500,
      "created_at": "2023-12-27T09:15:00Z"
    },
    // 更多历史
  ]
}
```

### 2.4 标签管理接口

#### 2.4.1 获取标签列表

```http
GET /api/v1/tags
```

**查询参数**：
- `page`：页码（默认 1）
- `per_page`：每页数量（默认 10）

**响应**：
```json
{
  "page": 1,
  "per_page": 10,
  "total": 15,
  "data": [
    {
      "id": 1,
      "name": "工作",
      "color": "#FF0000",
      "file_count": 5,
      "created_at": "2023-12-25T10:30:00Z"
    },
    // 更多标签
  ]
}
```

#### 2.4.2 创建标签

```http
POST /api/v1/tags
```

**请求体**：
```json
{
  "name": "重要",
  "color": "#FF0000",
  "description": "重要文件的标签"
}
```

**响应**：
```json
{
  "id": 2,
  "name": "重要",
  "color": "#FF0000",
  "description": "重要文件的标签",
  "file_count": 0,
  "created_at": "2023-12-27T09:15:00Z"
}
```

### 2.5 分类管理接口

#### 2.5.1 获取分类列表

```http
GET /api/v1/categories
```

**查询参数**：
- `parent_id`：父分类 ID（可选）
- `page`：页码（默认 1）
- `per_page`：每页数量（默认 10）

**响应**：
```json
{
  "page": 1,
  "per_page": 10,
  "total": 10,
  "data": [
    {
      "id": 1,
      "name": "文档",
      "color": "#00FF00",
      "file_count": 8,
      "created_at": "2023-12-25T10:30:00Z"
    },
    // 更多分类
  ]
}
```

#### 2.5.2 创建分类

```http
POST /api/v1/categories
```

**请求体**：
```json
{
  "name": "项目文档",
  "parent_id": 1,
  "color": "#0000FF",
  "description": "项目相关文档的分类"
}
```

**响应**：
```json
{
  "id": 2,
  "name": "项目文档",
  "color": "#0000FF",
  "description": "项目相关文档的分类",
  "file_count": 0,
  "created_at": "2023-12-27T09:15:00Z"
}
```

### 2.6 索引管理接口

#### 2.6.1 开始索引任务

```http
POST /api/v1/indexing
```

**请求体**：
```json
{
  "paths": ["/documents/work", "/images"],
  "force_reindex": false // 是否强制重新索引
}
```

**响应**：
```json
{
  "task_id": "12345678-1234-1234-1234-123456789012",
  "status": "running",
  "message": "索引任务已开始"
}
```

#### 2.6.2 获取索引任务状态

```http
GET /api/v1/indexing/{task_id}
```

**路径参数**：
- `task_id`：任务 ID

**响应**：
```json
{
  "task_id": "12345678-1234-1234-1234-123456789012",
  "status": "completed",
  "progress": 100,
  "processed_files": 150,
  "total_files": 150,
  "message": "索引任务已完成"
}
```

### 2.7 系统配置接口

#### 2.7.1 获取系统配置

```http
GET /api/v1/config
```

**响应**：
```json
{
  "indexing_paths": ["/documents/work", "/images"],
  "ignore_patterns": ["*.tmp", "*.log"],
  "search_preferences": {
    "max_results": 50,
    "min_score": 0.7
  }
}
```

#### 2.7.2 更新系统配置

```http
PUT /api/v1/config
```

**请求体**：
```json
{
  "indexing_paths": ["/documents/work", "/images", "/downloads"],
  "ignore_patterns": ["*.tmp", "*.log", "*.cache"],
  "search_preferences": {
    "max_results": 100,
    "min_score": 0.6
  }
}
```

**响应**：
```json
{
  "success": true,
  "message": "配置已更新"
}
```

### 2.8 自然语言交互接口

#### 2.8.1 处理自然语言查询

```http
POST /api/v1/nlp/query
```

**请求体**：
```json
{
  "query": "找到所有关于项目进度的文档",
  "context": {
    "current_file": 1,
    "recent_files": [2, 3]
  }
}
```

**响应**：
```json
{
  "intent": "search",
  "entities": {
    "query": "项目进度",
    "type": "document"
  },
  "response": "找到了 3 个关于项目进度的文档",
  "results": [
    {
      "id": 1,
      "name": "project-progress.pdf",
      "path": "/documents/work/project-progress.pdf"
    },
    // 更多结果
  ]
}
```

## 3. WebSocket 接口

### 3.1 实时事件通知

**端点**：`/ws/events`

**事件类型**：
- `file_created`：文件创建
- `file_updated`：文件更新
- `file_deleted`：文件删除
- `indexing_progress`：索引进度
- `search_completed`：搜索完成

**事件格式**：
```json
{
  "event": "indexing_progress",
  "data": {
    "task_id": "12345678-1234-1234-1234-123456789012",
    "progress": 50,
    "processed_files": 75,
    "total_files": 150
  }
}
```

## 4. 文件上传与下载接口

### 4.1 文件上传

```http
POST /api/v1/files/upload
```

**请求体**：
- 表单数据，包含文件和元数据

**响应**：
```json
{
  "id": 10,
  "name": "new-file.pdf",
  "path": "/uploads/new-file.pdf",
  "size": 512000,
  "type": "document",
  "created_at": "2023-12-27T10:00:00Z"
}
```

### 4.2 文件下载

```http
GET /api/v1/files/{id}/download
```

**路径参数**：
- `id`：文件 ID

**响应**：
- 文件流（二进制数据）
- 响应头包含 `Content-Disposition: attachment; filename="filename.pdf"`

## 5. 安全考虑

### 5.1 API 认证

- 使用 Bearer Token 进行身份认证
- Token 有效期可配置（默认为 24 小时）
- 支持 Token 刷新机制

### 5.2 请求限制

- 对 API 请求进行频率限制
- 支持基于用户的请求限制
- 限制大文件上传大小

### 5.3 数据安全

- 对敏感数据进行加密存储
- 对文件内容进行安全处理
- 实现安全审计日志

### 5.4 跨域安全

- 配置适当的 CORS 策略
- 限制允许访问的域名
- 验证请求来源

## 6. 文档与测试

### 6.1 API 文档

- 使用 OpenAPI 3.0 规范
- 自动生成 API 文档页面
- 提供 API 测试工具

### 6.2 测试覆盖

- 单元测试覆盖核心 API 端点
- 集成测试覆盖业务流程
- 性能测试确保 API 响应时间
