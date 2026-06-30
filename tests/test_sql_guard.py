"""sql_guard 单元测试，无需数据库连接"""

import os

import pytest

from yuppie_mcp_mssql.utils.sql_guard import SqlType, check_permission, detect_sql_type


class TestDetectSqlType:
    def test_select(self):
        assert detect_sql_type("SELECT * FROM users") == SqlType.SELECT

    def test_select_with_leading_whitespace(self):
        assert detect_sql_type("  \n  SELECT id FROM t") == SqlType.SELECT

    def test_select_with_comment(self):
        assert detect_sql_type("-- get users\nSELECT * FROM users") == SqlType.SELECT

    def test_with_cte(self):
        assert detect_sql_type("WITH cte AS (SELECT 1) SELECT * FROM cte") == SqlType.SELECT

    def test_insert(self):
        assert detect_sql_type("INSERT INTO t (a) VALUES (1)") == SqlType.INSERT

    def test_update(self):
        assert detect_sql_type("UPDATE t SET a=1 WHERE id=1") == SqlType.UPDATE

    def test_delete(self):
        assert detect_sql_type("DELETE FROM t WHERE id=1") == SqlType.DELETE

    def test_create(self):
        assert detect_sql_type("CREATE TABLE t (id INT)") == SqlType.DDL

    def test_drop(self):
        assert detect_sql_type("DROP TABLE t") == SqlType.DDL

    def test_alter(self):
        assert detect_sql_type("ALTER TABLE t ADD COLUMN x INT") == SqlType.DDL

    def test_truncate(self):
        assert detect_sql_type("TRUNCATE TABLE t") == SqlType.DDL

    def test_case_insensitive(self):
        assert detect_sql_type("select * from t") == SqlType.SELECT
        assert detect_sql_type("INSERT into t values (1)") == SqlType.INSERT


class TestCheckPermission:
    def test_select_always_allowed(self):
        assert check_permission(SqlType.SELECT) is None

    def test_insert_denied_by_default(self, monkeypatch):
        monkeypatch.delenv("DB_ALLOW_INSERT", raising=False)
        result = check_permission(SqlType.INSERT)
        assert result is not None
        assert "DB_ALLOW_INSERT" in result

    def test_insert_allowed_when_env_set(self, monkeypatch):
        monkeypatch.setenv("DB_ALLOW_INSERT", "true")
        assert check_permission(SqlType.INSERT) is None

    def test_update_denied_by_default(self, monkeypatch):
        monkeypatch.delenv("DB_ALLOW_UPDATE", raising=False)
        result = check_permission(SqlType.UPDATE)
        assert result is not None
        assert "DB_ALLOW_UPDATE" in result

    def test_delete_denied_by_default(self, monkeypatch):
        monkeypatch.delenv("DB_ALLOW_DELETE", raising=False)
        result = check_permission(SqlType.DELETE)
        assert result is not None
        assert "DB_ALLOW_DELETE" in result

    def test_ddl_denied_by_default(self, monkeypatch):
        monkeypatch.delenv("DB_ALLOW_DDL", raising=False)
        result = check_permission(SqlType.DDL)
        assert result is not None
        assert "DB_ALLOW_DDL" in result

    def test_env_value_1_is_truthy(self, monkeypatch):
        monkeypatch.setenv("DB_ALLOW_UPDATE", "1")
        assert check_permission(SqlType.UPDATE) is None

    def test_env_value_yes_is_truthy(self, monkeypatch):
        monkeypatch.setenv("DB_ALLOW_DELETE", "yes")
        assert check_permission(SqlType.DELETE) is None
