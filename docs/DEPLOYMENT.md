# Nanobot 部署指南

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

复制并编辑配置文件：

```bash
cp config/config.yaml.example config/config.yaml
vi config/config.yaml
```

### 3. 启动服务

```bash
python -m nanobot.main
```

## Docker 部署

### 构建镜像

```bash
docker build -t nanobot:latest .
```

### 运行容器

```bash
docker run -d \
  --name nanobot \
  -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  nanobot:latest
```

## 配置说明

详细配置说明请参考 [deployment/](./deployment/) 目录。

## 环境变量

- `NANOBOT_LOG_LEVEL`: 日志级别
- `NANOBOT_API_KEY`: API 密钥
- `NANOBOT_DATABASE_URL`: 数据库连接字符串
