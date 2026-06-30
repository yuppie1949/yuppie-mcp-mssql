"""MSSQL MCP Server 主入口"""

import os
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from yuppie_mcp_mssql.tools.execute import ExecuteSqlInput, execute_sql
from yuppie_mcp_mssql.tools.export import ExportToCsvInput, export_to_csv
from yuppie_mcp_mssql.tools.schema import (
    DescribeTableInput,
    ListTablesInput,
    describe_table,
    get_db_info,
    list_tables,
)

mcp = FastMCP("mssql_mcp")


@mcp.tool(
    name="mssql_execute_sql",
    annotations=ToolAnnotations(
        title="执行 SQL 语句",
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_execute_sql(
    sql: Annotated[str, Field(description="要执行的 SQL 语句", min_length=1)],
    max_rows: Annotated[
        int,
        Field(description="SELECT 查询最大返回行数，默认 100，最大 500", ge=1, le=500),
    ] = 100,
    response_format: Annotated[
        str,
        Field(description="输出格式：markdown 或 json", pattern="^(markdown|json)$"),
    ] = "markdown",
) -> str:
    """执行 SQL 语句。

    支持 SELECT 查询以及可选的 INSERT / UPDATE / DELETE / DDL 操作。
    写操作权限通过环境变量控制：
    - DB_ALLOW_INSERT=true   启用 INSERT
    - DB_ALLOW_UPDATE=true   启用 UPDATE
    - DB_ALLOW_DELETE=true   启用 DELETE
    - DB_ALLOW_DDL=true      启用 DDL（CREATE/DROP/ALTER/TRUNCATE）

    默认仅允许 SELECT，所有写操作均被拒绝。
    """
    return await execute_sql(
        ExecuteSqlInput(sql=sql, max_rows=max_rows, response_format=response_format)
    )


@mcp.tool(
    name="mssql_get_db_info",
    annotations=ToolAnnotations(
        title="获取数据库基本信息",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def tool_get_db_info(
    response_format: Annotated[
        str,
        Field(description="输出格式：markdown 或 json", pattern="^(markdown|json)$"),
    ] = "markdown",
) -> str:
    """获取当前数据库的基本信息，包括数据库名称、服务器名称、版本、当前用户等。"""
    return await get_db_info(response_format=response_format)


@mcp.tool(
    name="mssql_list_tables",
    annotations=ToolAnnotations(
        title="列出数据表",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def tool_list_tables(
    table_schema: Annotated[str, Field(description="Schema 名称，默认 dbo")] = "dbo",
    response_format: Annotated[
        str,
        Field(description="输出格式：markdown 或 json", pattern="^(markdown|json)$"),
    ] = "markdown",
) -> str:
    """列出当前数据库下的所有表。"""
    return await list_tables(
        ListTablesInput(table_schema=table_schema, response_format=response_format)
    )


@mcp.tool(
    name="mssql_describe_table",
    annotations=ToolAnnotations(
        title="描述表结构",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def tool_describe_table(
    table_name: Annotated[str, Field(description="表名", min_length=1)],
    table_schema: Annotated[str, Field(description="Schema 名称，默认 dbo")] = "dbo",
    response_format: Annotated[
        str,
        Field(description="输出格式：markdown 或 json", pattern="^(markdown|json)$"),
    ] = "markdown",
) -> str:
    """获取指定表的列结构，包括列名、数据类型、最大长度、可空性和默认值。"""
    return await describe_table(
        DescribeTableInput(
            table_name=table_name,
            table_schema=table_schema,
            response_format=response_format,
        )
    )


@mcp.tool(
    name="mssql_export_to_csv",
    annotations=ToolAnnotations(
        title="导出查询结果到 CSV",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_export_to_csv(
    query: Annotated[str, Field(description="SQL 查询语句或 .sql 文件路径", min_length=1)],
    output_path: Annotated[
        str, Field(description="CSV 文件输出路径（文件路径或目录路径，目录会自动生成 export.csv）", min_length=1)
    ],
    delimiter: Annotated[
        str, Field(description="分隔符：逗号(,)、制表符(\\t)、分号(;) 等，默认逗号")
    ] = ",",
) -> str:
    """将 SQL 查询结果导出到本地 CSV 文件。

    支持：
    - 直接传入 SQL 语句
    - 传入 .sql 文件路径（自动读取文件内容）
    - 自定义分隔符（逗号、制表符、分号等）

    仅允许 SELECT 查询，写操作会被拒绝。

    格式：UTF-8 编码，包含表头。
    """
    return await export_to_csv(
        ExportToCsvInput(query=query, output_path=output_path, delimiter=delimiter)
    )


def main() -> None:
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport == "streamable-http":
        mcp.settings.port = int(os.getenv("MCP_PORT", "8000"))
        mcp.run(transport="streamable-http")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
