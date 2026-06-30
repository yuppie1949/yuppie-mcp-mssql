"""pytds 连接管理，用 run_in_executor 包装同步调用"""

import asyncio
import os
from functools import partial
from typing import Any

import pytds  # type: ignore[import-untyped]


def _get_conn_params() -> dict[str, Any]:
    return {
        "server": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "1433")),
        "database": os.getenv("DB_NAME") or "",
        "user": os.getenv("DB_USER", ""),
        "password": os.getenv("DB_PASSWORD", ""),
        "as_dict": True,
    }


def _sync_execute(sql: str, params: Any) -> list[dict[str, Any]]:
    with pytds.connect(**_get_conn_params()) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if cur.description:
                return list(cur.fetchall())
            conn.commit()
            return [{"affected_rows": cur.rowcount}]


async def execute(sql: str, params: Any = None) -> list[dict[str, Any]]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(_sync_execute, sql, params))


def handle_db_error(e: Exception) -> str:
    if isinstance(e, pytds.LoginError):
        return "错误：认证失败，请检查 DB_USER / DB_PASSWORD"
    if isinstance(e, pytds.DatabaseError):
        return f"错误：SQL 执行失败 — {e}"
    if isinstance(e, OSError):
        return "错误：无法连接到 SQL Server，请检查 DB_HOST / DB_PORT"
    return f"错误：{type(e).__name__}: {e}"
