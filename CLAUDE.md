# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个 MCP (Model Context Protocol) Server，用于让 AI 助手连接和操作 SQL Server 数据库。核心特性是**无需安装任何原生驱动**（基于纯 Python 的 `python-tds` 库）。

## 开发命令

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest -v

# 代码检查
ruff check src/
ruff format --check src/

# 类型检查
mypy src/

# 本地运行 MCP Server（stdio 模式）
DB_HOST=localhost DB_USER=sa DB_PASSWORD=xxx uvx jewei-mcp-mssql

# 本地运行 MCP Server（HTTP 模式）
MCP_TRANSPORT=streamable-http MCP_PORT=8000 DB_HOST=localhost DB_USER=sa DB_PASSWORD=xxx uvx jewei-mcp-mssql
```

## 架构设计

### 核心模块

- **`server.py`**: MCP Server 入口，使用 FastMCP 框架注册 4 个工具
- **`utils/connection.py`**: 基于 `pytds` 的数据库连接管理，用 `asyncio.run_in_executor` 包装同步调用
- **`utils/sql_guard.py`**: SQL 类型检测和权限校验，默认只读，通过环境变量控制写权限
- **`tools/execute.py`**: 执行 SQL 语句的核心工具，支持输出格式切换（markdown/json）
- **`tools/schema.py`**: 数据库元信息查询工具（库信息、列表、表结构）

### 权限控制机制

`sql_guard.py` 通过正则匹配检测 SQL 类型，结合环境变量实现细粒度权限控制：

- `DB_ALLOW_INSERT` / `DB_ALLOW_UPDATE` / `DB_ALLOW_DELETE` / `DB_ALLOW_DDL`
- 默认全部禁用，只有 `SELECT` 始终允许
- 检测逻辑会跳过单行注释（`-- comment`），避免误判

### 传输模式

支持两种 MCP 传输模式，通过 `MCP_TRANSPORT` 环境变量切换：
- `stdio`（默认）：标准输入/输出通信
- `streamable-http`：HTTP 通信，通过 `MCP_PORT` 指定端口（默认 8000）

## 代码规范

- 使用 `ruff` 进行代码检查和格式化（line-length = 100）
- 使用 `mypy` 进行严格类型检查（`strict = true`）
- 使用 `pydantic` 进行输入验证，所有工具参数都通过 BaseModel 定义
- 异步函数命名使用 `async def`，同步数据库操作用 `run_in_executor` 包装

## 添加新工具

在 `tools/` 目录下创建新模块，定义：
1. 继承 `BaseModel` 的输入参数类
2. `async def` 工具实现函数
3. 在 `server.py` 中用 `@mcp.tool()` 装饰器注册

工具遵循统一模式：参数验证 → SQL 执行 → 结果格式化（markdown/json）。
