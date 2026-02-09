---
name: security
description: "安全技能 - 识别和修复安全漏洞。用于安全审计、代码审查、漏洞检测等任务。"
version: "1.0.0"
metadata:
  nanobot:
    emoji: "🔒"
    keywords: ["安全", "漏洞", "安全审计", "security", "vulnerability"]
---

# Security Skill

安全技能 - 识别和修复安全漏洞。

## 何时使用此技能

当任务涉及以下内容时使用：
- 安全审计
- 代码审查中的安全检查
- 漏洞检测和修复
- 安全最佳实践
- 安全测试

## 安全原则

### 1. 最小权限原则

赋予最小必要的权限：
- 代码应只拥有执行任务所需的权限
- 避免使用 root 或管理员权限运行
- 权限分离

### 2. 输入验证

始终验证和清理输入：
- 防止 SQL 注入、XSS、CSRF 等攻击
- 使用白名单验证而非黑名单
- 对用户输入进行适当的转义

### 3. 安全编码

安全编码最佳实践：
- 使用安全的函数和库
- 避免硬编码密码和敏感信息
- 正确处理密码和凭证

### 4. 错误处理

安全的错误处理：
- 避免在错误消息中暴露敏感信息
- 记录详细的错误信息但不显示给用户
- 限制错误消息的详细程度

## 常见安全漏洞

### SQL 注入

**漏洞示例**：
```python
# 不安全的代码
query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
```

**修复方案**：
```python
# 使用参数化查询
cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
```

### XSS（跨站脚本）

**漏洞示例**：
```python
# 不安全的代码
@app.route('/profile')
def profile():
    username = request.args.get('username')
    return f"<h1>欢迎 {username}</h1>"
```

**修复方案**：
```python
# 使用模板引擎自动转义
from flask import Flask, render_template_string

@app.route('/profile')
def profile():
    username = request.args.get('username')
    return render_template_string("<h1>欢迎 {{ username }}</h1>", username=username)
```

### CSRF（跨站请求伪造）

**修复方案**：
```python
# 使用 CSRF 令牌
from flask_wtf import CSRFProtect

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key'
CSRFProtect(app)
```

### 命令注入

**漏洞示例**：
```python
# 不安全的代码
import os

@app.route('/run')
def run_command():
    cmd = request.args.get('cmd')
    output = os.popen(cmd).read()
    return output
```

**修复方案**：
```python
# 避免直接执行用户输入
@app.route('/run')
def run_command():
    allowed_commands = ['list', 'status']
    cmd = request.args.get('cmd')
    if cmd in allowed_commands:
        output = execute_allowed_command(cmd)
        return output
    return "命令不允许"
```

## 安全检查清单

### 代码审查检查

在代码审查中检查：
- [ ] 输入验证和清理
- [ ] SQL 查询是否参数化
- [ ] 是否使用安全的密码存储
- [ ] 错误消息是否包含敏感信息
- [ ] 是否有适当的访问控制

### 依赖检查

- [ ] 检查依赖库的安全漏洞
- [ ] 定期更新依赖
- [ ] 使用 dependency-scan 工具

### 配置检查

- [ ] 密码和敏感信息是否硬编码
- [ ] 配置文件权限是否正确
- [ ] 日志文件是否包含敏感信息

## 加密和认证

### 密码存储

**不推荐**：
```python
# 不安全的密码存储
password_hash = hash(password)
```

**推荐**：
```python
# 使用 bcrypt
import bcrypt

hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# 验证密码
if bcrypt.checkpw(input_password.encode('utf-8'), hashed_password):
    print("密码正确")
```

### 会话管理

**安全的会话管理**：
```python
from flask import session
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True  # 生产环境启用
```

## 安全工具

### Python 安全工具

- **bandit**：静态代码分析
- **safety**：依赖库安全检查
- **checkov**：基础设施即代码安全检查
- **snyk**：依赖库漏洞扫描

### JavaScript 安全工具

- **eslint-plugin-security**：代码安全检查
- **npm audit**：依赖库安全检查
- **snyk**：依赖库漏洞扫描

### 使用方法

```bash
# 安装 bandit
pip install bandit

# 运行检查
bandit -r src/

# 安装 safety
pip install safety

# 检查依赖
safety check
```

## 安全最佳实践

### 1. 定期更新

- 定期更新依赖库
- 及时应用安全补丁
- 使用自动更新工具

### 2. 安全培训

- 代码审查时考虑安全
- 对开发团队进行安全培训
- 定期进行安全演练

### 3. 监控和日志

- 记录安全相关事件
- 定期审查日志
- 使用入侵检测系统

### 4. 渗透测试

- 定期进行渗透测试
- 邀请外部安全专家评估
- 修复发现的问题

## 常见安全场景

### 文件上传

**安全的文件上传**：
```python
from werkzeug.utils import secure_filename

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "没有文件"
    file = request.files['file']
    if file.filename == '':
        return "没有选择文件"
    
    # 验证文件类型
    allowed_extensions = {'txt', 'pdf', 'png', 'jpg'}
    filename = secure_filename(file.filename)
    if filename.split('.')[-1] not in allowed_extensions:
        return "文件类型不允许"
    
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return "文件上传成功"
```

### API 安全

**API 安全最佳实践**：
- 使用 HTTPS
- 认证和授权
- 请求限制
- 输入验证
- 输出编码

## 参考资源

详见 [SECURITY_PATTERNS.md](references/SECURITY_PATTERNS.md) 了解常见安全模式。
详见 [VULNERABILITY_GUIDE.md](references/VULNERABILITY_GUIDE.md) 了解常见漏洞和修复方案。

## 工具使用

此技能通常配合以下工具使用：
- `ReadFileTool` - 读取代码文件
- `ExecTool` - 运行安全检查工具
- `WebSearchTool` - 查找安全最佳实践

记住：安全是一个持续的过程，而不是一次性的任务。
