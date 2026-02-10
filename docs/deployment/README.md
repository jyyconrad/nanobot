# 部署和运维文档

Nanobot 部署和运维指南。

---

## 📚 文档列表

- [部署指南](DEPLOYMENT.md) - 安装和配置

---

## 🚀 快速部署

### 1. 安装依赖

```bash
pip install nanobot-ai
```

### 2. 配置

创建 `~/.nanobot/config.json`:

```json
{
  "providers": {
    "openai": {
      "apiKey": "your-api-key"
    }
  }
}
```

### 3. 启动 Gateway

```bash
nanobot gateway --port 18791
```

---

## 📋 生产部署

### 系统服务 (systemd)

创建 `/etc/systemd/system/nanobot.service`:

```ini
[Unit]
Description=Nanobot Gateway
After=network.target

[Service]
Type=simple
User=nanobot
WorkingDirectory=/opt/nanobot
ExecStart=/opt/nanobot/venv/bin/nanobot gateway --port 18791
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务:

```bash
sudo systemctl enable nanobot
sudo systemctl start nanobot
sudo systemctl status nanobot
```

### Docker 部署

```bash
docker build -t nanobot .
docker run -d -p 18791:18791 \
  -e OPENAI_API_KEY=your-key \
  --name nanobot nanobot
```

---

## 📊 监控

### 日志

```bash
# 查看日志
tail -f ~/.nanobott/logs/gateway.log

# 查看错误
grep ERROR ~/.nanobot/logs/gateway.log
```

### 健康检查

```bash
curl http://localhost:18791/health
```

---

## 🔧 故障排查

### 常见问题

1. **端口占用**
   ```bash
   lsof -i :18791
   ```

2. **配置错误**
   ```bash
   nanobot --validate-config
   ```

3. **日志查看**
   ```bash
   cat ~/.nanobot/logs/gateway.log
   ```

---

**注意**: 详细运维文档待补充。
