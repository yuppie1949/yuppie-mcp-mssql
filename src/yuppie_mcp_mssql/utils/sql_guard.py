"""SQL 类型检测与权限校验"""

import os
import re
from enum import Enum


class SqlType(str, Enum):
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    DDL = "ddl"
    OTHER = "other"


_PATTERNS = [
    (SqlType.SELECT, re.compile(r"^\s*(select|with)\b", re.IGNORECASE)),
    (SqlType.INSERT, re.compile(r"^\s*insert\b", re.IGNORECASE)),
    (SqlType.UPDATE, re.compile(r"^\s*update\b", re.IGNORECASE)),
    (SqlType.DELETE, re.compile(r"^\s*delete\b", re.IGNORECASE)),
    (SqlType.DDL, re.compile(r"^\s*(create|drop|alter|truncate|rename)\b", re.IGNORECASE)),
]


def detect_sql_type(sql: str) -> SqlType:
    """检测 SQL 语句类型，去除单行注释后匹配首个有效关键词"""
    cleaned = re.sub(r"--[^\n]*", "", sql).strip()
    for sql_type, pattern in _PATTERNS:
        if pattern.match(cleaned):
            return sql_type
    return SqlType.OTHER


def _env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in ("true", "1", "yes")


def check_permission(sql_type: SqlType) -> str | None:
    """
    检查是否有权限执行该类型 SQL。
    返回 None 表示允许，返回字符串则为拒绝原因。
    """
    if sql_type == SqlType.SELECT:
        return None

    checks = {
        SqlType.INSERT: ("DB_ALLOW_INSERT", "INSERT"),
        SqlType.UPDATE: ("DB_ALLOW_UPDATE", "UPDATE"),
        SqlType.DELETE: ("DB_ALLOW_DELETE", "DELETE"),
        SqlType.DDL: ("DB_ALLOW_DDL", "DDL（CREATE/DROP/ALTER/TRUNCATE）"),
    }

    if sql_type in checks:
        env_var, label = checks[sql_type]
        if not _env_bool(env_var):
            return f"权限拒绝：{label} 操作未启用。如需允许，请设置环境变量 {env_var}=true"
        return None

    return "权限拒绝：无法识别的 SQL 类型，仅允许 SELECT/INSERT/UPDATE/DELETE/DDL"
