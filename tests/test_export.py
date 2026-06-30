"""export 工具单元测试，无需数据库连接"""

import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from yuppie_mcp_mssql.tools.export import (
    ExportToCsvInput,
    _detect_file_path,
    _normalize_output_path,
    _read_sql_file,
    _validate_output_path,
    _write_csv,
)


class TestExportToCsvInput:
    def test_valid_input(self):
        params = ExportToCsvInput(query="SELECT * FROM t", output_path="/tmp/test.csv")
        assert params.query == "SELECT * FROM t"
        assert params.output_path == "/tmp/test.csv"
        assert params.delimiter == ","  # 默认逗号

    def test_custom_delimiter(self):
        params = ExportToCsvInput(
            query="SELECT * FROM t", output_path="/tmp/test.csv", delimiter="\t"
        )
        assert params.delimiter == "\t"

    def test_query_min_length_validation(self):
        with pytest.raises(ValidationError):
            ExportToCsvInput(query="", output_path="/tmp/test.csv")

    def test_output_path_min_length_validation(self):
        with pytest.raises(ValidationError):
            ExportToCsvInput(query="SELECT 1", output_path="")


class TestDetectFilePath:
    def test_sql_extension_detected(self):
        assert _detect_file_path("test.sql") is True
        assert _detect_file_path("path/to/query.SQL") is True
        assert _detect_file_path("path/to/query.sqL") is True

    def test_non_sql_extension_not_detected(self):
        assert _detect_file_path("SELECT * FROM t") is False
        assert _detect_file_path("test.txt") is False

    def test_existing_file_detected(self, tmp_path):
        existing_file = tmp_path / "data"
        existing_file.write_text("content")
        assert _detect_file_path(str(existing_file)) is True


class TestReadSqlFile:
    def test_read_existing_file(self, tmp_path):
        sql_file = tmp_path / "test.sql"
        sql_file.write_text("SELECT * FROM users", encoding="utf-8")
        content = _read_sql_file(str(sql_file))
        assert content == "SELECT * FROM users"

    def test_read_nonexistent_file(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="SQL 文件不存在"):
            _read_sql_file(str(tmp_path / "nonexistent.sql"))


class TestValidateOutputPath:
    def test_valid_path_in_cwd(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        _validate_output_path("output.csv")  # 不应抛出异常

    def test_valid_path_in_home(self, monkeypatch, tmp_path):
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        monkeypatch.setenv("HOME", str(home_dir))
        _validate_output_path(str(home_dir / "output.csv"))  # 不应抛出异常

    def test_path_traversal_rejected(self):
        with pytest.raises(ValueError, match="不允许包含 '\\.\\.'"):
            _validate_output_path("../../../etc/passwd")

    def test_normalized_path_with_double_dots_rejected(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(ValueError, match="不允许包含 '\\.\\.'"):
            _validate_output_path("../output.csv")


class TestNormalizeOutputPath:
    def test_file_path_unchanged(self, tmp_path):
        path = _normalize_output_path(str(tmp_path / "output.csv"))
        assert path == tmp_path / "output.csv"

    def test_directory_path_appends_filename(self, tmp_path):
        dir_path = tmp_path / "exports"
        dir_path.mkdir()
        path = _normalize_output_path(str(dir_path))
        assert path == dir_path / "export.csv"

    def test_nonexistent_directory_path_appends_filename(self, tmp_path):
        path = _normalize_output_path(str(tmp_path / "new_dir"))
        assert path == tmp_path / "new_dir" / "export.csv"

    def test_path_with_trailing_slash(self, tmp_path):
        path = _normalize_output_path(str(tmp_path / "exports" / ""))
        assert path == tmp_path / "exports" / "export.csv"


class TestWriteCsv:
    def test_write_csv_success(self, tmp_path):
        rows = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        output_path = tmp_path / "output.csv"
        row_count, actual_path = _write_csv(rows, str(output_path))
        assert row_count == 2
        assert actual_path == str(output_path)
        assert output_path.exists()

        content = output_path.read_text(encoding="utf-8")
        assert "id,name" in content
        assert "Alice" in content
        assert "Bob" in content

    def test_write_csv_to_directory_creates_export_csv(self, tmp_path):
        rows = [{"id": 1}]
        dir_path = tmp_path / "exports"
        row_count, actual_path = _write_csv(rows, str(dir_path))
        assert row_count == 1
        expected_file = dir_path / "export.csv"
        assert actual_path == str(expected_file)
        assert expected_file.exists()

    def test_write_csv_creates_directory(self, tmp_path):
        rows = [{"id": 1}]
        nested_path = tmp_path / "subdir" / "nested" / "output.csv"
        row_count, actual_path = _write_csv(rows, str(nested_path))
        assert row_count == 1
        assert nested_path.exists()

    def test_write_csv_empty_rows_raises_error(self):
        with pytest.raises(ValueError, match="查询结果为空"):
            _write_csv([], "/tmp/test.csv")

    def test_write_csv_with_special_characters(self, tmp_path):
        rows = [{"id": 1, "text": "Hello, world!"}, {"id": 2, "text": 'Line\nBreak'}]
        output_path = tmp_path / "special.csv"
        _write_csv(rows, str(output_path))
        content = output_path.read_text(encoding="utf-8")
        # CSV 应该正确处理逗号和换行符
        assert '"Hello, world!"' in content
        assert '"Line\nBreak"' in content

    def test_write_csv_with_tab_delimiter(self, tmp_path):
        rows = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        output_path = tmp_path / "output.tsv"
        row_count, actual_path = _write_csv(rows, str(output_path), delimiter="\t")
        assert row_count == 2
        content = output_path.read_text(encoding="utf-8")
        # 验证使用制表符分隔
        assert "id\tname" in content
        assert "Alice" in content

    def test_write_csv_with_semicolon_delimiter(self, tmp_path):
        rows = [{"id": 1, "name": "Alice"}]
        output_path = tmp_path / "output.semicolon"
        row_count, _ = _write_csv(rows, str(output_path), delimiter=";")
        assert row_count == 1
        content = output_path.read_text(encoding="utf-8")
        # 验证使用分号分隔
        assert "id;name" in content
