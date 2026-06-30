# mssql_export_to_csv 工具设计文档

## 功能概述

新增 `mssql_export_to_csv` 工具，允许用户将 SQL Server 查询结果导出到本地 CSV 文件。

## 工具定义

### 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | string | 是 | SQL 查询语句或 .sql 文件路径 |
| `output_path` | string | 是 | CSV 文件输出路径（本地文件系统） |

### 参数处理逻辑

1. **query 参数检测**：
   - 如果是文件路径（以 `.sql` 结尾或文件存在），读取文件内容
   - 否则直接作为 SQL 语句

2. **权限检查**：
   - 复用现有的 `sql_guard.detect_sql_type()` 和 `check_permission()`
   - 只允许 SELECT 查询，拒绝写操作

### 返回值

- **成功**：返回确认消息，包含：
  - 导出行数
  - SQL 来源（语句 / 文件路径）
  - CSV 文件路径
  
  示例：`已成功导出 100 行（来源：SQL 语句）→ /Users/xxx/output.csv`

- **失败**：返回错误信息

## 实现架构

### 文件结构

```
src/yuppie_mcp_mssql/
├── tools/
│   ├── export.py          # 新增：export_to_csv 工具实现
│   ├── execute.py         # 现有：复用 execute() 函数
│   └── schema.py          # 现有：其他工具
├── utils/
│   ├── connection.py      # 现有：复用数据库连接
│   └── sql_guard.py       # 现有：复用权限检查
└── server.py              # 更新：注册新工具
```

### 复用现有组件

- `connection.execute()` - 执行 SQL 查询
- `sql_guard.detect_sql_type()` - 检测 SQL 类型
- `sql_guard.check_permission()` - 权限校验
- `handle_db_error()` - 错误处理

### 新增代码

**`tools/export.py`**：
- `ExportToCsvInput` - Pydantic 输入模型
- `export_to_csv()` - 主函数
- `_detect_file_path()` - 判断 query 是文件还是 SQL
- `_read_sql_file()` - 读取 .sql 文件
- `_write_csv()` - 写入 CSV 文件

## 数据流

```
用户调用 mssql_export_to_csv
  ↓
检测 query 类型（文件路径 vs SQL语句）
  ↓   ↓
是文件?      否（直接使用）
  ↓
读取文件内容
  ↓
SQL 类型检测 + 权限检查（复用 sql_guard）
  ↓
执行查询（复用 connection.execute）
  ↓
使用 csv.writer 写入文件
  ↓
返回成功消息
```

## CSV 格式规范

- **编码**：UTF-8
- **分隔符**：逗号 (`,`)
- **表头**：包含列名
- **引用**：字段包含逗号、换行符、引号时自动用双引号包裹
- **换行符**：`\n`

## 错误处理

| 错误类型 | 处理方式 | 返回消息 |
|----------|----------|----------|
| .sql 文件不存在 | 中止 | 错误：文件不存在 |
| SQL 语法错误 | 中止 | 错误：SQL 执行失败 — {详情} |
| 权限不足 | 中止 | 权限拒绝：{类型} 操作未启用 |
| 目录不存在 | 自动创建 | - |
| 文件写入权限不足 | 中止 | 错误：无权限写入文件 |
| 数据库连接失败 | 中止 | 错误：无法连接到 SQL Server |

## 测试计划

### 单元测试

1. **文件路径检测**：
   - 测试 `.sql` 结尾的字符串被识别为文件
   - 测试存在的文件路径被识别为文件
   - 测试普通 SQL 字符串不被误识别为文件

2. **文件读取**：
   - 模拟文件读取成功
   - 模拟文件不存在

3. **权限检查**：
   - 验证 SELECT 查询通过
   - 验证 INSERT/UPDATE/DELETE 被拒绝

### 集成测试

（可选）需要真实的 SQL Server 连接，测试完整的导出流程。

## 安全考虑

1. **路径遍历防护**：验证 `output_path` 是合法路径，不包含 `..` 等危险字符
2. **只读保证**：严格限制只允许 SELECT 查询
3. **文件大小限制**：可选，限制最大导出行数（如 10,000 行）

## 未来扩展

1. 支持自定义分隔符（TSV 等）
2. 支持自定义编码
3. 支持导出为 Excel 格式
4. 支持追加模式（不覆盖现有文件）
