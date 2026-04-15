#!/usr/bin/env python3
"""
WiFi密码查询 MCP 服务器
当用户询问WiFi密码时，返回预设密码 123789
"""

import os
import json
import logging
import random
from typing import Any, List
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from mcp.types import Tool, TextContent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 显式设置格式化器，确保即使 Uvicorn 重新配置根日志，我们的logger仍保留时间格式
for handler in logger.handlers:
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(handler)
    logger.propagate = True

app = FastAPI(title="WiFi Query MCP Server", version="0.2.0")

# 配置默认值
DEFAULT_CONFIG = {
    "wifi_password": "123789",
    "menu": ["鲅鱼饺子", "葱麻鸡", "羊肉锅贴"],
    "queue": {
        "min_people": 5,
        "max_people": 30,
        "minutes_per_person": 8
    }
}

def load_config():
    """热加载配置：每次调用都重新读取config.json"""
    CONFIG_PATH = os.getenv("CONFIG_PATH", "config.json")
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        # 合并默认配置
        wifi_password = os.getenv("WIFI_PASSWORD", config.get("wifi_password", DEFAULT_CONFIG["wifi_password"]))
        menu = config.get("menu", DEFAULT_CONFIG["menu"])
        queue_config = config.get("queue", DEFAULT_CONFIG["queue"])
        return {
            "wifi_password": wifi_password,
            "menu": menu,
            "queue": queue_config
        }
    except Exception as e:
        logger.warning(f"配置文件加载失败: {str(e)}，使用默认配置")
        return {
            "wifi_password": os.getenv("WIFI_PASSWORD", DEFAULT_CONFIG["wifi_password"]),
            "menu": DEFAULT_CONFIG["menu"],
            "queue": DEFAULT_CONFIG["queue"]
        }

class CallToolRequest(BaseModel):
    name: str
    parameters: dict[str, Any]

class CallToolResponse(BaseModel):
    content: List[TextContent]
    is_error: bool = False

# 错误处理：请求验证异常
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证错误，返回符合MCP格式的错误响应"""
    return JSONResponse(
        content=CallToolResponse(
            content=[TextContent(type="text", text=f"请求验证失败: {str(exc)}")],
            is_error=True
        ).model_dump()
    )

# 错误处理：通用异常
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理所有未捕获的异常，返回符合MCP格式的错误响应"""
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        content=CallToolResponse(
            content=[TextContent(type="text", text=f"服务器内部错误: {str(exc)}")],
            is_error=True
        ).model_dump()
    )

@app.get("/")
async def root():
    return {
        "message": "WiFi Query MCP Server is running",
        "tools": ["get_wifi_password", "get_menu", "get_queue_status"]
    }

@app.get("/health")
async def health_check():
    """健康检查端点，用于监控"""
    return {"status": "healthy"}

@app.post("/mcp/list-tools")
async def list_tools():
    """列出可用工具"""
    return {
        "tools": [
            Tool(
                name="get_wifi_password",
                description="获取WiFi密码，当用户询问WiFi密码时调用此工具",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "用户关于WiFi密码的问题"
                        }
                    },
                    "required": ["question"]
                }
            ).model_dump(),
            Tool(
                name="get_menu",
                description="获取餐厅主要菜单，当用户询问菜单、吃什么、有什么菜时调用此工具",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "用户关于菜单的问题"
                        }
                    },
                    "required": ["question"]
                }
            ).model_dump(),
            Tool(
                name="get_queue_status",
                description="获取当前排队人数和预计等待时间，当用户询问排队、几号桌、等多久时调用此工具",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "用户关于排队的问题"
                        }
                    },
                    "required": ["question"]
                }
            ).model_dump()
        ]
    }

def format_wait_time(total_minutes: int) -> str:
    """格式化等待时间
    小于1小时 → 显示分钟
    大于1小时小于1天 → 显示X小时X分钟
    大于1天 → 显示X天X小时X分钟
    """
    if total_minutes < 60:
        return f"{total_minutes}分钟"
    elif total_minutes < 1440:
        hours = total_minutes // 60
        minutes = total_minutes % 60
        if minutes == 0:
            return f"{hours}小时"
        return f"{hours}小时{minutes}分钟"
    else:
        days = total_minutes // 1440
        remaining = total_minutes % 1440
        hours = remaining // 60
        minutes = remaining % 60
        parts = []
        parts.append(f"{days}天")
        if hours > 0:
            parts.append(f"{hours}小时")
        if minutes > 0:
            parts.append(f"{minutes}分钟")
        return "".join(parts)

@app.post("/mcp/call-tool")
async def call_tool(request: CallToolRequest):
    """调用工具"""
    # 热加载：每次调用都重新读取配置
    config = load_config()
    wifi_password = config["wifi_password"]
    menu = config["menu"]
    queue_config = config["queue"]

    if request.name == "get_wifi_password":
        question = request.parameters.get("question", "").strip()
        logger.info(f"收到WiFi密码问题: {question}")

        # 返回从配置读取的WiFi密码
        return CallToolResponse(
            content=[
                TextContent(
                    type="text",
                    text=f"当前WiFi密码是: {wifi_password}"
                )
            ],
            is_error=False
        ).model_dump()
    elif request.name == "get_menu":
        question = request.parameters.get("question", "").strip()
        logger.info(f"收到菜单查询问题: {question}")

        # 从配置读取菜单并格式化输出
        menu_lines = ["餐厅主要菜单："]
        for item in menu:
            menu_lines.append(f"• {item}")
        menu_text = "\n".join(menu_lines)
        return CallToolResponse(
            content=[
                TextContent(
                    type="text",
                    text=menu_text
                )
            ],
            is_error=False
        ).model_dump()
    elif request.name == "get_queue_status":
        question = request.parameters.get("question", "").strip()
        logger.info(f"收到排队查询问题: {question}")

        # 生成随机排队人数
        min_people = queue_config.get("min_people", 5)
        max_people = queue_config.get("max_people", 30)
        minutes_per_person = queue_config.get("minutes_per_person", 8)
        queue_count = random.randint(min_people, max_people)
        # 根据人数估算等待时间
        estimated_minutes = queue_count * minutes_per_person
        wait_time_str = format_wait_time(estimated_minutes)

        result_text = f"当前排了 {queue_count} 人！估计需要 {wait_time_str}！"
        return CallToolResponse(
            content=[
                TextContent(
                    type="text",
                    text=result_text
                )
            ],
            is_error=False
        ).model_dump()
    else:
        return CallToolResponse(
            content=[TextContent(type="text", text=f"未知工具: {request.name}")],
            is_error=True
        ).model_dump()

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """MCP主端点，支持标准MCP streamable HTTP协议"""
    try:
        # 手动读取字节，尝试多种编码解码，解决中文Windows上的编码问题
        body_bytes = await request.body()
        # 尝试 UTF-8
        try:
            body_text = body_bytes.decode('utf-8')
        except UnicodeDecodeError:
            # UTF-8 失败，尝试 GBK（中文Windows常见）
            body_text = body_bytes.decode('gbk')
        body = json.loads(body_text)
        logger.info(f"MCP请求类型: {type(body)}, keys={list(body.keys()) if isinstance(body, dict) else 'not dict'}")

        if isinstance(body, dict):
            # 标准 JSON-RPC 格式: {jsonrpc: "2.0", method: "...", params: {...}, id: ...}
            if 'method' in body:
                method = body['method']
                params = body.get('params', {})
                logger.info(f"JSON-RPC method: {method}")

                if method == 'call_tool':
                    # call_tool 请求格式: params = {name: "...", parameters: {...}}
                    name = params.get('name')
                    parameters = params.get('parameters', {})
                    call_request = CallToolRequest(name=name, parameters=parameters)
                    return await call_tool(call_request)
                elif method in ('list_tools', 'tools/list'):
                    return await list_tools()

            # 兼容处理：直接调用（非JSON-RPC格式，{name: "...", parameters: {...}}）
            elif 'name' in body:
                call_request = CallToolRequest.model_validate(body)
                return await call_tool(call_request)

        # 默认返回工具列表（用于发现）
        logger.info("Returning tool list (default)")
        return await list_tools()
    except Exception as e:
        logger.error(f"MCP端点解析错误: {str(e)}", exc_info=True)
        return JSONResponse(
            content=CallToolResponse(
                content=[TextContent(type="text", text=f"MCP请求解析失败: {str(e)}")],
                is_error=True
            ).model_dump()
        )

if __name__ == "__main__":
    # 绑定到 127.0.0.1 仅本地访问，避免公网泄露信息
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))

    # 配置日志格式，让 Uvicorn 输出也带上时间戳
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "access": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout"
            },
            "access": {
                "formatter": "access",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout"
            }
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["default"],
                "level": "INFO",
                "propagate": False
            },
            "uvicorn.access": {
                "handlers": ["access"],
                "level": "INFO",
                "propagate": False
            },
            "uvicorn.error": {
                "handlers": ["default"],
                "level": "INFO",
                "propagate": False
            }
        }
    }

    uvicorn.run(app, host=host, port=port, log_config=log_config)
