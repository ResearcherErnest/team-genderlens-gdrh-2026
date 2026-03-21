"""Tests for src.schema_config — verify consistency of schema definitions."""

import zipfile
from pathlib import Path

import pandas as pd
import pytest

from src.schema_config import (
    DEFAULT_DATA_MODE,
    STUDIES_SCHEMA,
    RESOURCES_SCHEMA,
    QUALITY_SCHEMA,
    METADATA_FIELDS,
    QUALITY_WEIGHTS,
)


FULL_ZIP = Path(__file__).resolve().parents[1] / "data" / "full-data.zip"


class TestSchemaConstants:
    def test_default_data_mode_is_full(self):
        assert DEFAULT_DATA_MODE == "full"

    def test_quality_weights_sum_to_one(self):
        total = sum(QUALITY_WEIGHTS.values())
        assert abs(total - 1.0) < 1e-9, f"Weights sum to {total}, expected 1.0"

    def test_metadata_fields_non_empty(self):
        assert len(METADATA_FIELDS) > 0

    @pytest.mark.parametrize("schema,name", [
        (STUDIES_SCHEMA, "studies"),
        (RESOURCES_SCHEMA, "resources"),
        (QUALITY_SCHEMA, "quality"),
    ])
    def test_schema_has_expected_keys(self, schema, name):
        for key in ("filename", "required_cols", "optional_cols", "dtype_overrides"):
            assert key in schema, f"{name} schema missing key: {key}"

    @pytest.mark.parametrize("schema,name", [
        (STUDIES_SCHEMA, "studies"),
        (RESOURCES_SCHEMA, "resources"),
        (QUALITY_SCHEMA, "quality"),
    ])
    def test_dtype_overrides_reference_known_cols(self, schema, name):
        all_cols = set(schema["required_cols"] + schema["optional_cols"])
        for col in schema["dtype_overrides"]:
            assert col in all_cols, (
                f"{name}: dtype override for '{col}' not in required+optional cols"
            )


class TestFullDataZipConsistency:
    """Verify that full-data.zip contains all required columns."""

    @pytest.fixture(autouse=True)
    def _require_zip(self):
        if not FULL_ZIP.exists():
            pytest.skip("full-data.zip not present")

    @pytest.mark.parametrize("schema", [STUDIES_SCHEMA, RESOURCES_SCHEMA, QUALITY_SCHEMA])
    def test_zip_contains_required_columns(self, schema):
        with zipfile.ZipFile(FULL_ZIP) as zf:
            with zf.open(schema["filename"]) as f:
                df = pd.read_csv(f, nrows=0)
        missing = [c for c in schema["required_cols"] if c not in df.columns]
        assert not missing, f"Missing required cols in {schema['filename']}: {missing}"
