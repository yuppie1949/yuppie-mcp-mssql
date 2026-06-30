"""mssql_export_to_csv 工具实现"""

import csv
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from yuppie_mcp_mssql.utils.connection import execute, handle_db_error
from yuppie_mcp_mssql.utils.sql_guard import check_permission, detect_sql_type


class ExportToCsvInput(BaseModel):
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )

    query: str = Field(..., description="SQL 查询语句或 .sql 文件路径", min_length=1)
    output_path: str = Field(
        ...,
        description="CSV 文件输出路径（文件路径或目录路径，目录会自动生成 export.csv）",
        min_length=1,
    )
    delimiter: str = Field(
        default=",",
        description="分隔符：逗号(,)、制表符(\t)、分号(;) 等，默认逗号",
    )


def _detect_file_path(query: str) -> bool:
    """判断 query 是否为文件路径

    规则：
    1. 以 .sql 结尾
    2. 文件存在
    """
    path = Path(query.strip())
    if path.suffix.lower() == ".sql":
        return True
    return path.exists()


def _read_sql_file(file_path: str) -> str:
    """读取 .sql 文件内容"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"SQL 文件不存在：{file_path}")
    return path.read_text(encoding="utf-8")


def _validate_output_path(output_path: str) -> None:
    """验证输出路径安全性，防止路径遍历攻击"""
    path = Path(output_path).resolve()
    normalized = Path(output_path).expanduser()

    if ".." in str(normalized.parts):
        raise ValueError("无效的输出路径：不允许包含 '..'")
    if not str(path).startswith(str(Path.cwd())) and not str(path).startswith(
        str(Path.home())
    ):
        raise ValueError("无效的输出路径：仅允许当前目录或用户主目录下的路径")


def _normalize_output_path(output_path: str) -> Path:
    """标准化输出路径，如果是目录则自动生成文件名"""
    path = Path(output_path).expanduser()

    # 如果路径以 / 结尾（表示目录），则自动生成文件名
    if str(output_path).endswith(("/", "\\")):
        return path.resolve() / "export.csv"

    resolved = path.resolve()

    # 如果路径存在且是目录，则自动生成文件名
    if resolved.exists() and resolved.is_dir():
        return resolved / "export.csv"

    # 如果路径不存在且没有扩展名（看起来像目录路径），则自动生成文件名
    if not resolved.exists() and resolved.suffix == "":
        return resolved / "export.csv"

    return resolved


def _write_csv(
    rows: list[dict[str, Any]], output_path: str, delimiter: str = ","
) -> tuple[int, str]:
    """写入 CSV 文件

    返回：(写入的行数, 实际输出文件路径)
    """
    if not rows:
        raise ValueError("查询结果为空，无法导出")

    path = _normalize_output_path(output_path)

    # 自动创建目录
    path.parent.mkdir(parents=True, exist_ok=True)

    # 写入 CSV
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys(), delimiter=delimiter)
        writer.writeheader()
        writer.writerows(rows)

    return len(rows), str(path)


async def export_to_csv(params: ExportToCsvInput) -> str:
    # 检测 query 类型（文件路径 vs SQL 语句）
    is_file = _detect_file_path(params.query)
    sql_source = "SQL 文件" if is_file else "SQL 语句"

    # 读取 SQL 文件或直接使用语句
    if is_file:
        try:
            sql = _read_sql_file(params.query)
        except FileNotFoundError as e:
            return f"错误：{e}"
    else:
        sql = params.query

    # SQL 类型检测 + 权限检查
    sql_type = detect_sql_type(sql)
    denied = check_permission(sql_type)
    if denied:
        return denied

    # 验证输出路径
    try:
        _validate_output_path(params.output_path)
    except ValueError as e:
        return f"错误：{e}"

    # 执行查询
    try:
        rows = await execute(sql)
    except Exception as e:
        return handle_db_error(e)

    # 写入 CSV
    try:
        row_count, actual_path = _write_csv(rows, params.output_path, params.delimiter)
    except ValueError as e:
        return f"错误：{e}"
    except PermissionError:
        return f"错误：无权限写入文件 {params.output_path}"
    except Exception as e:
        return f"错误：写入 CSV 文件失败 — {e}"

    delimiter_desc = "," if params.delimiter == "," else f"{params.delimiter!r}"
    return (
        f"已成功导出 {row_count} 行（分隔符：{delimiter_desc}，来源：{sql_source}）→ "
        f"{actual_path}"
    )
