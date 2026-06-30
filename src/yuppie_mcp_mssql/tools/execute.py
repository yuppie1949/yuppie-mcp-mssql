"""mssql_execute_sql 工具实现"""

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from yuppie_mcp_mssql.utils.connection import execute, handle_db_error
from yuppie_mcp_mssql.utils.sql_guard import check_permission, detect_sql_type


class ExecuteSqlInput(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )

    sql: str = Field(..., description="要执行的 SQL 语句", min_length=1)
    max_rows: int = Field(
        default=100,
        description="SELECT 查询最大返回行数（1-500）",
        ge=1,
        le=500,
    )
    response_format: str = Field(
        default="markdown",
        description="输出格式：markdown 或 json",
        pattern="^(markdown|json)$",
    )


def _rows_to_markdown(rows: list[dict[str, Any]], affected_only: bool = False) -> str:
    if affected_only or not rows:
        affected = rows[0].get("affected_rows", 0) if rows else 0
        return f"执行成功，影响行数：**{affected}**"

    keys = list(rows[0].keys())
    header = "| " + " | ".join(str(k) for k in keys) + " |"
    sep = "| " + " | ".join("---" for _ in keys) + " |"
    body = "\n".join("| " + " | ".join(str(row.get(k, "")) for k in keys) + " |" for row in rows)
    return f"{header}\n{sep}\n{body}"


async def execute_sql(params: ExecuteSqlInput) -> str:
    sql_type = detect_sql_type(params.sql)
    denied = check_permission(sql_type)
    if denied:
        return denied

    try:
        rows = await execute(params.sql)
    except Exception as e:
        return handle_db_error(e)

    is_query = rows and "affected_rows" not in rows[0]

    if is_query:
        truncated = rows[: params.max_rows]
        note = f"\n\n> 共返回 {len(truncated)} 行" + (
            f"（结果已截断，共 {len(rows)} 行，可调整 max_rows 参数）"
            if len(rows) > params.max_rows
            else ""
        )
    else:
        truncated = rows
        note = ""

    if params.response_format == "json":
        suffix = f"\n// {len(rows)} rows, showing {len(truncated)}" if note else ""
        return json.dumps(truncated, ensure_ascii=False, default=str) + suffix

    return _rows_to_markdown(truncated, affected_only=not is_query) + note
