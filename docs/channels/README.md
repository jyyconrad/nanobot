# 渠道配置指南

本文档介绍 nanobot 支持的各种消息渠道及其配置方法。

## 支持的渠道

| 渠道 | 状态 | 说明 |
|------|------|------|
| TUI | ✅ 默认 | 本地终端交互 |
| Telegram | ✅ | Bot API 集成 |
| 飞书 | ✅ | WebSocket 长连接 |
| WhatsApp | ✅ | WebSocket Bridge |
| Matrix | ✅ | Element/ElementX 集成 |

## 渠道配置

所有渠道配置在 `config.json` 的 `channels` 字段中：

```json
{
  "channels": {
    "tui": {
      "enabled": true
    },
    "telegram": {
      "enabled": false,
      "token": "your-bot-token"
    },
    "feishu": {
      "enabled": false,
      "app_id": "your-app-id",
      "app_secret": "your-app-secret"
    },
    "whatsapp": {
      "enabled": false,
      "bridge_url": "ws://localhost:3001"
    },
    "matrix": {
      "enabled": false,
      "homeserver": "https://matrix.org",
      "user_id": "@bot:matrix.org",
      "access_token": "your-access-token",
      "device_id": "your-device-id",
      "e2ee_enabled": true,
      "group_policy": "open"
    }
  }
}
```

## 各渠道详细配置

### Telegram

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| enabled | bool | false | 启用/禁用 |
| token | string | - | Bot API Token |
| allow_from | list | [] | 用户白名单 |
| proxy | string | null | 代理服务器 |

### 飞书

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| enabled | bool | false | 启用/禁用 |
| app_id | string | - | 应用 ID |
| app_secret | string | - | 应用密钥 |
| encrypt_key | string | - | 加密密钥（可选） |
| verification_token | string | - | 验证令牌（可选） |

### Matrix

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| enabled | bool | false | 启用/禁用 |
| homeserver | string | https://matrix.org | Matrix 服务器 |
| user_id | string | - | 机器人用户 ID |
| access_token | string | - | 访问令牌 |
| device_id | string | - | 设备 ID |
| e2ee_enabled | bool | true | 端到端加密 |
| group_policy | string | open | 群组策略 |
| allow_from | list | [] | 用户白名单 |

### Matrix 群组策略

- `open`: 允许所有群组消息
- `mention`: 仅处理 @ 提及的消息
- `allowlist`: 仅处理白名单群组的消息

## 安装渠道依赖

```bash
# 飞书渠道
pip install nanobot-ai[feishu]

# Matrix 渠道
pip install nanobot-ai[matrix]
```
