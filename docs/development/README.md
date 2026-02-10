# 开发指南

Nanobot 开发者指南。

---

## 📚 文档列表

- [贡献指南](CONTRIBUTING.md) - 如何贡献代码
- [测试指南](testing.md) - 测试策略和方法

---

## 🛠️ 开发环境设置

### 1. 克隆仓库

```bash
git clone https://github.com/jyyconrad/nanobot.git
cd nanobot
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -e ".[dev]"
```

### 4. 运行测试

```bash
pytest tests/
```

---

## 🧪 测试策略

### 运行测试

```bash
# 所有测试
pytest tests/

# 特定模块
pytest tests/test_prompt_system_v2.py

# 生成覆盖率
pytest tests/ --cov=nanobot --cov-report=html
```

### 测试结构

```
tests/
├── unit/           # 单元测试
├── integration/    # 集成测试
├── acceptance/     # 验收测试
└── performance/    # 性能测试
```

---

## 📝 代码规范

### 格式化

```bash
ruff format .
```

### 检查

```bash
ruff check .
```

### 类型检查

```bash
mypy nanobot/
```

---

## 🔀 分支策略

- `main`: 主分支，生产代码
- `dev`: 开发分支
- `feat/*`: 新功能分支
- `fix/*`: Bug 修复分支
- `docs/*`: 文档更新分支

---

## 📤 提交规范

使用 Conventional Commits:

```
feat: 添加新功能
fix: 修复 bug
docs: 更新文档
test: 添加测试
refactor: 重构代码
perf: 性能优化
chore: 构建/工具链更新
```

---

**注意**: 详细详细开发指南待补充。
