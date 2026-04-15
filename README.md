# WiFi Password Query MCP Server

一个简单的 MCP (Model Context Protocol) 服务器，提供 WiFi 密码查询、餐厅菜单查询、排队状态查询。

## 功能

- 符合 MCP 协议规范 (Streamable HTTP)
- 提供三个工具：
  - `get_wifi_password` - 查询预设 WiFi 密码
  - `get_menu` - 查询餐厅主要菜单
  - `get_queue_status` - 查询当前排队人数和预计等待时间
- 配置通过 `config.json` 外部化，支持**热加载**（修改配置无需重启服务）
- 完善的错误处理，返回标准 MCP 错误格式
- 健康检查端点
- 所有日志带时间戳，便于调试

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动服务器

```bash
python server.py
```

默认配置：
- 地址: `http://127.0.0.1:8000`

### 配置说明

所有配置都在 `config.json`：

```json
{
  "wifi_password": "123789",
  "menu": [
    "鲅鱼饺子",
    "葱麻鸡",
    "羊肉锅贴"
  ],
  "queue": {
    "min_people": 5,
    "max_people": 30,
    "minutes_per_person": 8
  }
}
```

| 配置项 | 说明 |
|--------|------|
| `wifi_password` | WiFi 密码 |
| `menu` | 餐厅菜单列表 |
| `queue.min_people` | 最小排队人数（随机生成） |
| `queue.max_people` | 最大排队人数（随机生成） |
| `queue.minutes_per_person` | 每人预估等待分钟 |

**热加载特性**：修改 `config.json` 后无需重启服务，下次请求自动读取新配置。

### 环境变量

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `CONFIG_PATH` | 配置文件路径 | `config.json` |
| `WIFI_PASSWORD` | 覆盖 WiFi 密码（优先级高于配置文件） | - |
| `HOST` | 绑定地址 | `127.0.0.1` |
| `PORT` | 监听端口 | `8000` |

示例：
```bash
export WIFI_PASSWORD="my_wifi_password"
export HOST="0.0.0.0"
export PORT="9000"
python server.py
```

## MCP API

### `GET /` - 服务信息
返回服务状态和可用工具列表。

### `GET /health` - 健康检查
```json
{
  "status": "healthy"
}
```

### `POST /mcp` - MCP 主端点
支持标准 MCP Streamable HTTP 协议。

### `POST /mcp/list-tools` - 列出工具
返回所有可用工具定义。

### `POST /mcp/call-tool` - 调用工具

**WiFi 密码查询：**
```json
{
  "name": "get_wifi_password",
  "parameters": {
    "question": "请问WiFi密码是多少？"
  }
}
```

**菜单查询：**
```json
{
  "name": "get_menu",
  "parameters": {
    "question": "今天菜单有什么？"
  }
}
```

响应示例：
```json
{
  "content": [
    {
      "type": "text",
      "text": "餐厅主要菜单：\n• 鲅鱼饺子\n• 葱麻鸡\n• 羊肉锅贴\n• 牛肉锅贴"
    }
  ],
  "is_error": false
}
```

**排队状态查询：**
```json
{
  "name": "get_queue_status",
  "parameters": {
    "question": "现在前面排了多少人？"
  }
}
```

响应示例：
```json
{
  "content": [
    {
      "type": "text",
      "text": "当前排了 12 人！估计需要 1小时36分钟！"
    }
  ],
  "is_error": false
}
```

等待时间自动格式化：
- 小于 1 小时 → 显示 `XX分钟`
- 大于 1 小时小于 1 天 → 显示 `X小时X分钟`
- 大于 1 天 → 显示 `X天X小时X分钟`

## Claude Desktop / Claude Code 配置

在你的配置中添加：

```json
{
  "mcpServers": {
    "wifi-query": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

## 项目结构

```
├── server.py       # 主程序
├── config.json     # 配置文件（热加载）
├── requirements.txt
├── skill.json      # Claude Code Skill 定义
├── skill.md        # Claude Code Skill 文档
└── README.md
```

## 许可证

MIT
