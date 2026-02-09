# AI本地文件管理系统 - 数据模型设计文档

## 1. 核心实体设计

### 1.1 文件实体 (File)

**描述**：表示系统中管理的文件

**属性**：
- `id`：唯一标识符（主键）
- `name`：文件名
- `path`：文件完整路径
- `size`：文件大小（字节）
- `type`：文件类型（如文本、图片、音频等）
- `mime_type`：MIME 类型
- `created_at`：创建时间
- `modified_at`：最后修改时间
- `accessed_at`：最后访问时间
- `hash`：文件内容哈希值（用于检测变化）
- `is_deleted`：是否已删除（逻辑删除）
- `deleted_at`：删除时间

### 1.2 文件夹实体 (Folder)

**描述**：表示文件系统中的文件夹

**属性**：
- `id`：唯一标识符（主键）
- `name`：文件夹名
- `path`：文件夹完整路径
- `created_at`：创建时间
- `modified_at`：最后修改时间
- `parent_id`：父文件夹 ID（外键）
- `is_deleted`：是否已删除（逻辑删除）
- `deleted_at`：删除时间

### 1.3 文件标签实体 (FileTag)

**描述**：表示文件的标签

**属性**：
- `id`：唯一标识符（主键）
- `file_id`：关联的文件 ID（外键）
- `tag_id`：关联的标签 ID（外键）
- `created_at`：创建时间
- `updated_at`：更新时间

### 1.4 标签实体 (Tag)

**描述**：表示标签信息

**属性**：
- `id`：唯一标识符（主键）
- `name`：标签名称
- `color`：标签颜色（用于可视化）
- `description`：标签描述
- `user_id`：创建标签的用户 ID（外键）
- `created_at`：创建时间
- `updated_at`：更新时间

### 1.5 文件分类实体 (FileCategory)

**描述**：表示文件的分类

**属性**：
- `id`：唯一标识符（主键）
- `file_id`：关联的文件 ID（外键）
- `category_id`：关联的分类 ID（外键）
- `confidence`：分类置信度（0-1）
- `created_at`：创建时间
- `updated_at`：更新时间

### 1.6 分类实体 (Category)

**描述**：表示文件分类信息

**属性**：
- `id`：唯一标识符（主键）
- `name`：分类名称
- `description`：分类描述
- `parent_id`：父分类 ID（外键）
- `color`：分类颜色（用于可视化）
- `user_id`：创建分类的用户 ID（外键）
- `created_at`：创建时间
- `updated_at`：更新时间

### 1.7 文件向量实体 (FileVector)

**描述**：存储文件内容的向量表示

**属性**：
- `id`：唯一标识符（主键）
- `file_id`：关联的文件 ID（外键）
- `vector`：向量数据（二进制存储）
- `model_id`：使用的模型 ID（外键）
- `created_at`：创建时间
- `updated_at`：更新时间

### 1.8 模型实体 (Model)

**描述**：表示使用的 AI 模型信息

**属性**：
- `id`：唯一标识符（主键）
- `name`：模型名称
- `type`：模型类型（如文本向量化、图像识别等）
- `version`：模型版本
- `description`：模型描述
- `path`：模型文件路径（本地存储）
- `api_key`：API 密钥（云端模型）
- `provider`：模型提供商（如 OpenAI、Google 等）
- `created_at`：创建时间
- `updated_at`：更新时间

### 1.9 用户实体 (User)

**描述**：表示系统用户

**属性**：
- `id`：唯一标识符（主键）
- `username`：用户名（唯一）
- `email`：电子邮件（唯一）
- `password_hash`：密码哈希值
- `full_name`：完整姓名
- `avatar`：头像路径
- `role`：用户角色（如管理员、普通用户）
- `preferences`：用户偏好设置（JSON 格式）
- `created_at`：创建时间
- `updated_at`：更新时间
- `last_login_at`：最后登录时间

### 1.10 搜索历史实体 (SearchHistory)

**描述**：记录用户搜索历史

**属性**：
- `id`：唯一标识符（主键）
- `user_id`：用户 ID（外键）
- `query`：搜索查询
- `query_type`：查询类型（语义搜索、关键词搜索等）
- `results_count`：搜索结果数量
- `selected_file_id`：用户选择的文件 ID（外键，可选）
- `search_time`：搜索耗时（毫秒）
- `created_at`：搜索时间

### 1.11 文件关联实体 (FileRelation)

**描述**：记录文件之间的关联关系

**属性**：
- `id`：唯一标识符（主键）
- `source_file_id`：源文件 ID（外键）
- `target_file_id`：目标文件 ID（外键）
- `relation_type`：关联类型（内容关联、使用关联等）
- `similarity`：相似度分数（0-1）
- `created_at`：创建时间
- `updated_at`：更新时间

### 1.12 系统配置实体 (SystemConfig)

**描述**：存储系统配置信息

**属性**：
- `id`：唯一标识符（主键）
- `key`：配置键（唯一）
- `value`：配置值
- `description`：配置描述
- `category`：配置分类
- `data_type`：数据类型（字符串、数字、布尔值等）
- `created_at`：创建时间
- `updated_at`：更新时间

## 2. 数据库表结构

### 2.1 文件表 (files)

```sql
CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    path TEXT NOT NULL UNIQUE,
    size INTEGER NOT NULL DEFAULT 0,
    type TEXT NOT NULL,
    mime_type TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    accessed_at DATETIME,
    hash TEXT,
    is_deleted BOOLEAN NOT NULL DEFAULT 0,
    deleted_at DATETIME
);
```

### 2.2 文件夹表 (folders)

```sql
CREATE TABLE folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    path TEXT NOT NULL UNIQUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    parent_id INTEGER,
    is_deleted BOOLEAN NOT NULL DEFAULT 0,
    deleted_at DATETIME,
    FOREIGN KEY (parent_id) REFERENCES folders(id)
);
```

### 2.3 文件标签关联表 (file_tags)

```sql
CREATE TABLE file_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files(id),
    FOREIGN KEY (tag_id) REFERENCES tags(id),
    UNIQUE(file_id, tag_id)
);
```

### 2.4 标签表 (tags)

```sql
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    color TEXT,
    description TEXT,
    user_id INTEGER,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 2.5 文件分类关联表 (file_categories)

```sql
CREATE TABLE file_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    confidence REAL NOT NULL DEFAULT 1.0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files(id),
    FOREIGN KEY (category_id) REFERENCES categories(id),
    UNIQUE(file_id, category_id)
);
```

### 2.6 分类表 (categories)

```sql
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    parent_id INTEGER,
    color TEXT,
    user_id INTEGER,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES categories(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 2.7 文件向量表 (file_vectors)

```sql
CREATE TABLE file_vectors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    vector BLOB NOT NULL,
    model_id INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files(id),
    FOREIGN KEY (model_id) REFERENCES models(id),
    UNIQUE(file_id, model_id)
);
```

### 2.8 模型表 (models)

```sql
CREATE TABLE models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    version TEXT NOT NULL,
    description TEXT,
    path TEXT,
    api_key TEXT,
    provider TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### 2.9 用户表 (users)

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    avatar TEXT,
    role TEXT NOT NULL DEFAULT 'user',
    preferences TEXT, -- JSON 格式
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at DATETIME
);
```

### 2.10 搜索历史表 (search_histories)

```sql
CREATE TABLE search_histories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    query TEXT NOT NULL,
    query_type TEXT NOT NULL,
    results_count INTEGER NOT NULL DEFAULT 0,
    selected_file_id INTEGER,
    search_time INTEGER NOT NULL DEFAULT 0, -- 毫秒
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (selected_file_id) REFERENCES files(id)
);
```

### 2.11 文件关联表 (file_relations)

```sql
CREATE TABLE file_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file_id INTEGER NOT NULL,
    target_file_id INTEGER NOT NULL,
    relation_type TEXT NOT NULL,
    similarity REAL NOT NULL DEFAULT 0.0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_file_id) REFERENCES files(id),
    FOREIGN KEY (target_file_id) REFERENCES files(id),
    UNIQUE(source_file_id, target_file_id, relation_type)
);
```

### 2.12 系统配置表 (system_configs)

```sql
CREATE TABLE system_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value TEXT NOT NULL,
    description TEXT,
    category TEXT,
    data_type TEXT NOT NULL DEFAULT 'string',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

## 3. 索引设计

### 3.1 主键索引

- 所有表的 `id` 字段均为自动递增主键，默认创建主键索引

### 3.2 唯一索引

- `files.path`：确保文件路径唯一
- `folders.path`：确保文件夹路径唯一
- `users.username` 和 `users.email`：确保用户名和电子邮件唯一
- `system_configs.key`：确保配置键唯一

### 3.3 普通索引

- `files.name`：加速文件名搜索
- `files.type` 和 `files.mime_type`：加速按文件类型搜索
- `files.created_at` 和 `files.modified_at`：加速按时间搜索
- `tags.name`：加速标签搜索
- `categories.name`：加速分类搜索
- `file_tags.file_id` 和 `file_tags.tag_id`：加速文件-标签关联查询
- `file_categories.file_id` 和 `file_categories.category_id`：加速文件-分类关联查询
- `search_histories.user_id`：加速用户搜索历史查询
- `file_relations.source_file_id` 和 `file_relations.target_file_id`：加速文件关联查询

### 3.4 全文搜索索引

- 对于需要全文搜索的字段（如文件内容），将使用专门的全文索引引擎（如 Whoosh 或 Elasticsearch）而不是数据库索引

## 4. 数据关系图

```mermaid
erDiagram
    USERS ||--o{ FILES : owns
    USERS ||--o{ TAGS : creates
    USERS ||--o{ CATEGORIES : creates
    USERS ||--o{ SEARCH_HISTORIES : records
    FILES ||--|{ FILE_TAGS : has
    FILES ||--|{ FILE_CATEGORIES : belongs to
    FILES ||--|{ FILE_VECTORS : has
    FILES ||--o{ FILE_RELATIONS : related to
    TAGS ||--|{ FILE_TAGS : attached to
    CATEGORIES ||--|{ FILE_CATEGORIES : includes
    CATEGORIES ||--o{ CATEGORIES : parent-child
    MODELS ||--|{ FILE_VECTORS : generates
```

### 4.1 用户与文件关系

一个用户可以拥有多个文件，但一个文件只能属于一个用户。

### 4.2 用户与标签关系

一个用户可以创建多个标签，但一个标签只能属于一个用户。

### 4.3 用户与分类关系

一个用户可以创建多个分类，分类可以有子分类（树形结构）。

### 4.4 文件与标签关系

一个文件可以有多个标签，一个标签可以应用于多个文件（多对多关系）。

### 4.5 文件与分类关系

一个文件可以属于多个分类，一个分类可以包含多个文件（多对多关系）。

### 4.6 文件与向量关系

一个文件可以有多个向量表示（使用不同模型），一个向量表示属于一个文件。

### 4.7 文件与关联关系

一个文件可以与多个文件关联，关联关系可以有多种类型（内容关联、使用关联等）。

### 4.8 模型与向量关系

一个模型可以生成多个文件向量，一个向量由一个模型生成。

### 4.9 用户与搜索历史关系

一个用户可以有多个搜索历史记录，一个搜索历史记录属于一个用户。
