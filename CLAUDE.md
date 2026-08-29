# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个 MCP (Model Context Protocol) Server，用于让 AI 助手连接和操作 SQL Server 数据库。核心特性是**无需安装任何原生驱动**（基于纯 Python 的 `python-tds` 库）。

## 开发命令

```bash
# 安装开发依赖（workspace 双包）
uv sync --all-packages --all-extras

# 运行测试
uv run pytest -v

# 代码检查
ruff check packages/ tests/
ruff format --check packages/ tests/

# 类型检查
mypy packages/*/src

# 本地运行 MCP Server（stdio 模式）
DB_HOST=localhost DB_USER=sa DB_PASSWORD=xxx uvx jewei-mcp-mssql

# 本地运行 MCP Server（HTTP 模式）
MCP_TRANSPORT=streamable-http MCP_PORT=8000 DB_HOST=localhost DB_USER=sa DB_PASSWORD=xxx uvx jewei-mcp-mssql
```

## 双包结构

本仓库拆分为两个 PyPI 包（workspace 结构）：

- **库包 `yuppie-mssql`**（`packages/yuppie-mssql/`）：纯 MSSQL 客户端，无 mcp 无 pydantic 依赖
- **壳包 `yuppie-mcp-mssql`**（`packages/yuppie-mcp-mssql/`）：MCP Server，依赖库包

## 架构设计

### 核心模块

- **`packages/yuppie-mcp-mssql/src/yuppie_mcp_mssql/server.py`**: MCP Server 入口，使用 MCPServer 框架（mcp SDK 2.x）注册 5 个工具
- **`packages/yuppie-mssql/src/yuppie_mssql/connection.py`**: 基于 `pytds` 的数据库连接管理，用 `asyncio.run_in_executor` 包装同步调用
- **`packages/yuppie-mssql/src/yuppie_mssql/sql_guard.py`**: SQL 类型检测和权限校验，默认只读，通过环境变量控制写权限
- **`packages/yuppie-mcp-mssql/src/yuppie_mcp_mssql/tools/execute.py`**: 执行 SQL 语句的核心工具，支持输出格式切换（markdown/json）
- **`packages/yuppie-mcp-mssql/src/yuppie_mcp_mssql/tools/schema.py`**: 数据库元信息查询工具（库信息、列表、表结构）

### 权限控制机制

`sql_guard.py` 通过正则匹配检测 SQL 类型，结合环境变量实现细粒度权限控制：

- `DB_ALLOW_INSERT` / `DB_ALLOW_UPDATE` / `DB_ALLOW_DELETE` / `DB_ALLOW_DDL`
- 默认全部禁用，只有 `SELECT` 始终允许
- 检测逻辑会跳过单行注释（`-- comment`），避免误判

### 传输模式

支持两种 MCP 传输模式，通过 `MCP_TRANSPORT` 环境变量切换：
- `stdio`（默认）：标准输入/输出通信
- `streamable-http`：HTTP 通信，host/port 通过 `run()` 的 `MCP_HOST`（默认 127.0.0.1）/ `MCP_PORT`（默认 8000）指定

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
