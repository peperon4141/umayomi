"""convert_local_folder_to_parquetのテスト"""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from src.jrdb_scraper.convert_local_folder_to_parquet import (
    convert_local_folder_to_parquet,
    convert_single_local_file,
    find_lzh_files_in_folder
)
from src.jrdb_scraper.entities.jrdb import JRDBDataType
from src.jrdb_scraper.converter import convert_lzh_to_parquet


class TestFindLzhFilesInFolder:
    """find_lzh_files_in_folderのテスト"""

    def test_find_all_lzh_files(self, tmp_path):
        """全てのLZHファイルを検索"""
        # テスト用LZHファイルを作成
        (tmp_path / "SED_2024.lzh").write_bytes(b"test lzh data")
        (tmp_path / "BAC_2024.lzh").write_bytes(b"test lzh data")
        (tmp_path / "KYI_2024.lzh").write_bytes(b"test lzh data")
        (tmp_path / "other.txt").write_text("not lzh")

        files = find_lzh_files_in_folder(tmp_path)
        assert len(files) == 3
        assert all(f.suffix == ".lzh" for f in files)

    def test_find_specific_data_type(self, tmp_path):
        """特定のデータタイプのLZHファイルを検索"""
        (tmp_path / "SED_2024.lzh").write_bytes(b"test lzh data")
        (tmp_path / "BAC_2024.lzh").write_bytes(b"test lzh data")
        (tmp_path / "KYI_2024.lzh").write_bytes(b"test lzh data")

        files = find_lzh_files_in_folder(tmp_path, JRDBDataType.SED)
        assert len(files) == 1
        assert "SED" in files[0].name

    def test_find_nonexistent_folder(self):
        """存在しないフォルダ"""
        files = find_lzh_files_in_folder(Path("/nonexistent/path"))
        assert len(files) == 0


class TestConvertSingleLocalFile:
    """convert_single_local_fileのテスト"""

    @patch('src.jrdb_scraper.convert_local_folder_to_parquet.convert_lzh_to_parquet')
    def test_convert_success(self, mock_convert, tmp_path):
        """正常に変換できる場合"""
        # テスト用LZHファイルを作成
        lzh_file = tmp_path / "SED_2024.lzh"
        lzh_file.write_bytes(b"test lzh data")

        # モックの設定
        mock_convert.return_value = (JRDBDataType.SED, [{"場コード": 1, "回": 1, "日": "1", "R": 1, "年月日": 20240101}])

        output_dir = tmp_path / "output"
        result = convert_single_local_file(lzh_file, JRDBDataType.SED, 2024, output_dir)

        assert result["success"] is True
        assert result["dataType"] == "SED"
        assert result["year"] == 2024
        assert result["recordCount"] == 1
        assert mock_convert.called

    def test_convert_file_not_found(self, tmp_path):
        """ファイルが見つからない場合"""
        lzh_file = tmp_path / "nonexistent.lzh"
        output_dir = tmp_path / "output"

        result = convert_single_local_file(lzh_file, JRDBDataType.SED, 2024, output_dir)

        assert result["success"] is False
        assert "見つかりません" in result["error"]


class TestConvertLocalFolderToParquet:
    """convert_local_folder_to_parquetのテスト"""

    @patch('src.jrdb_scraper.convert_local_folder_to_parquet.convert_lzh_to_parquet')
    def test_convert_with_race_key_validation(self, mock_convert, tmp_path):
        """race_keyが仕様どおり作成されることを確認"""
        # テスト用LZHファイルを作成
        lzh_file = tmp_path / "SED_2024.lzh"
        lzh_file.write_bytes(b"test lzh data")

        # テスト用レコードを作成（race_key生成に必要なカラムを含む）
        test_records = [
            {
                "場コード": 6,
                "年": 24,
                "回": 4,
                "日": "7",
                "R": 1,
                "年月日": 20240101,
                "馬番": 1,
                "着順": 1,
            },
            {
                "場コード": 6,
                "年": 24,
                "回": 4,
                "日": "7",
                "R": 2,
                "年月日": 20240101,
                "馬番": 2,
                "着順": 2,
            },
            {
                "場コード": 1,
                "年": 24,
                "回": 1,
                "日": "1",
                "R": 1,
                "年月日": 20240224,
                "馬番": 1,
                "着順": 1,
            },
        ]

        # モックの設定
        def mock_convert_side_effect(lzh_buffer, data_type, year, output_path):
            # 実際のconvert_to_parquetを呼び出してrace_keyを生成
            from src.jrdb_scraper.converter import convert_to_parquet
            convert_to_parquet(test_records, output_path, data_type)
            return (data_type, test_records)

        mock_convert.side_effect = mock_convert_side_effect

        output_dir = tmp_path / "output"
        results = convert_local_folder_to_parquet(
            folderPath=tmp_path,
            year=2024,
            dataTypes=[JRDBDataType.SED],
            outputDir=output_dir
        )

        # 結果を確認
        assert len(results) == 1
        assert results[0]["success"] is True

        # 生成されたParquetファイルを読み込んでrace_keyを確認
        parquet_file = Path(results[0]["outputPath"])
        assert parquet_file.exists()

        df = pd.read_parquet(parquet_file)

        # race_keyが存在することを確認
        assert "race_key" in df.columns, "race_keyカラムが存在する必要があります"

        # race_keyの形式を確認
        race_keys = df["race_key"].dropna().unique()
        assert len(race_keys) > 0, "race_keyが生成されている必要があります"

        for race_key in race_keys:
            # race_keyの形式: YYYYMMDD_場コード_回_日_R
            parts = str(race_key).split("_")
            assert len(parts) == 5, f"race_keyは5つの部分に分割される必要があります: {race_key}"

            # 日付部分（YYYYMMDD）を確認
            date_part = parts[0]
            assert len(date_part) == 8, f"日付部分は8桁である必要があります: {date_part}"
            assert date_part.isdigit(), f"日付部分は数字である必要があります: {date_part}"

            # 場コード部分を確認（2桁）
            place_code = parts[1]
            assert len(place_code) == 2, f"場コード部分は2桁である必要があります: {place_code}"
            assert place_code.isdigit(), f"場コード部分は数字である必要があります: {place_code}"

            # 回部分を確認（2桁）
            round_part = parts[2]
            assert len(round_part) == 2, f"回部分は2桁である必要があります: {round_part}"
            assert round_part.isdigit(), f"回部分は数字である必要があります: {round_part}"

            # 日部分を確認（小文字または数字）
            day_part = parts[3]
            assert day_part.islower() or day_part.isdigit(), f"日部分は小文字または数字である必要があります: {day_part}"

            # R部分を確認（2桁）
            race_part = parts[4]
            assert len(race_part) == 2, f"R部分は2桁である必要があります: {race_part}"
            assert race_part.isdigit(), f"R部分は数字である必要があります: {race_part}"

        # 具体的な値の確認
        # 1つ目のレコード: 2024年1月1日、場コード6、回4、日7、R1
        expected_key_1 = "20240101_06_04_7_01"
        assert expected_key_1 in race_keys, f"期待されるrace_keyが見つかりません: {expected_key_1}"

        # 2つ目のレコード: 2024年1月1日、場コード6、回4、日7、R2
        expected_key_2 = "20240101_06_04_7_02"
        assert expected_key_2 in race_keys, f"期待されるrace_keyが見つかりません: {expected_key_2}"

        # 3つ目のレコード: 2024年2月24日、場コード1、回1、日1、R1
        expected_key_3 = "20240224_01_01_1_01"
        assert expected_key_3 in race_keys, f"期待されるrace_keyが見つかりません: {expected_key_3}"

        # race_keyが全ての行に存在することを確認
        assert df["race_key"].notna().all(), "全ての行にrace_keyが存在する必要があります"

    @patch('src.jrdb_scraper.convert_local_folder_to_parquet.convert_lzh_to_parquet')
    def test_convert_multiple_data_types(self, mock_convert, tmp_path):
        """複数のデータタイプを変換"""
        # テスト用LZHファイルを作成
        (tmp_path / "SED_2024.lzh").write_bytes(b"test lzh data")
        (tmp_path / "BAC_2024.lzh").write_bytes(b"test lzh data")

        # モックの設定
        def mock_convert_side_effect(lzh_buffer, data_type, year, output_path):
            test_records = [{"場コード": 1, "年": 24, "回": 1, "日": "1", "R": 1, "年月日": 20240101}]
            from src.jrdb_scraper.converter import convert_to_parquet
            convert_to_parquet(test_records, output_path, data_type)
            return (data_type, test_records)

        mock_convert.side_effect = mock_convert_side_effect

        output_dir = tmp_path / "output"
        results = convert_local_folder_to_parquet(
            folderPath=tmp_path,
            year=2024,
            dataTypes=[JRDBDataType.SED, JRDBDataType.BAC],
            outputDir=output_dir
        )

        assert len(results) == 2
        assert all(r["success"] for r in results)

        # 両方のParquetファイルでrace_keyが生成されていることを確認
        for result in results:
            parquet_file = Path(result["outputPath"])
            df = pd.read_parquet(parquet_file)
            assert "race_key" in df.columns
            assert df["race_key"].notna().all()

    def test_convert_no_files_found(self, tmp_path):
        """LZHファイルが見つからない場合"""
        output_dir = tmp_path / "output"
        results = convert_local_folder_to_parquet(
            folderPath=tmp_path,
            year=2024,
            dataTypes=[JRDBDataType.SED],
            outputDir=output_dir
        )

        assert len(results) == 1
        assert results[0]["success"] is False
        assert "見つかりません" in results[0]["error"]

