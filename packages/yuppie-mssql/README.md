# yuppie-mssql

MSSQL 客户端库(纯 Python,基于 `python-tds`),**无需安装任何本地驱动**。不含 MCP 依赖。

## 安装

```bash
pip install yuppie-mssql
```

## 快速开始

```python
from yuppie_mssql.connection import execute, handle_db_error
from yuppie_mssql.sql_guard import check_permission, detect_sql_type

# 权限检查(SELECT 始终允许,写操作由环境变量 DB_ALLOW_* 控制)
sql_type = detect_sql_type("SELECT * FROM dbo.Orders")
denied = check_permission(sql_type)
if denied:
    print(denied)
else:
    rows = await execute("SELECT * FROM dbo.Orders")
```

连接参数通过环境变量读取:`DB_HOST`(默认 localhost)、`DB_PORT`(默认 1433)、`DB_NAME`、`DB_USER`、`DB_PASSWORD`。

## License

MIT
