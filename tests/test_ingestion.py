"""Tests for src.pipeline.ingestion."""

import textwrap
from pathlib import Path

import pandas as pd
import pytest

from src.pipeline.ingestion import (
    load_csv,
    load_studies,
    load_resources,
    load_quality_report,
    load_all,
    STUDIES_REQUIRED_COLS,
    RESOURCES_REQUIRED_COLS,
    QUALITY_REQUIRED_COLS,
    _validate_schema,
    _coerce_types,
)


# --- Fixtures ---

@pytest.fixture
def sample_dir():
    """Path to the sample data directory."""
    return Path(__file__).resolve().parents[1] / "data" / "sample"


@pytest.fixture
def tmp_csv(tmp_path):
    """Create a minimal valid studies CSV in a temp dir."""
    csv_text = textwrap.dedent("""\
        study_id,title,year,organization,url,abstract,quality_flags,get_microdata_url
        1,Test Study,2022,NISR,https://example.com,An abstract,,https://example.com/data
    """)
    p = tmp_path / "studies.csv"
    p.write_text(csv_text)
    return tmp_path


# --- Schema validation ---

class TestSchemaValidation:
    def test_valid_schema_passes(self):
        df = pd.DataFrame({"study_id": [1], "title": ["T"], "year": [2022],
                           "organization": ["O"], "url": ["http://x"]})
        _validate_schema(df, STUDIES_REQUIRED_COLS, "test")  # should not raise

    def test_missing_column_raises(self):
        df = pd.DataFrame({"study_id": [1], "title": ["T"]})
        with pytest.raises(ValueError, match="Missing required columns"):
            _validate_schema(df, STUDIES_REQUIRED_COLS, "test")


# --- Type coercion ---

class TestTypeCoercion:
    def test_year_coerced_to_int(self):
        df = pd.DataFrame({"year": ["2022", "bad", None]})
        result = _coerce_types(df)
        assert result["year"].dtype.name == "Int64"
        assert result["year"].iloc[0] == 2022
        assert pd.isna(result["year"].iloc[1])

    def test_missing_field_count_coerced(self):
        df = pd.DataFrame({"missing_field_count": ["0", "3", None]})
        result = _coerce_types(df)
        assert result["missing_field_count"].dtype.name == "Int64"


# --- CSV loading ---

class TestLoadCSV:
    def test_load_from_sample_dir(self, sample_dir):
        df = load_csv("studies.csv", STUDIES_REQUIRED_COLS, data_dir=sample_dir)
        assert len(df) > 0
        assert "study_id" in df.columns

    def test_load_from_tmp(self, tmp_csv):
        df = load_csv("studies.csv", STUDIES_REQUIRED_COLS, data_dir=tmp_csv)
        assert len(df) == 1
        assert df["year"].iloc[0] == 2022

    def test_file_not_found_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_csv("nonexistent.csv", [], data_dir=tmp_path)


# --- Convenience loaders ---

class TestConvenienceLoaders:
    def test_load_studies(self, sample_dir):
        df = load_studies(data_dir=sample_dir)
        assert "title" in df.columns
        assert len(df) == 3

    def test_load_resources(self, sample_dir):
        df = load_resources(data_dir=sample_dir)
        assert "type" in df.columns

    def test_load_quality_report(self, sample_dir):
        df = load_quality_report(data_dir=sample_dir)
        assert "missing_field_count" in df.columns

    def test_load_all_returns_three(self, sample_dir):
        studies, resources, quality = load_all(data_dir=sample_dir)
        assert len(studies) > 0
        assert len(resources) > 0
        assert len(quality) > 0
