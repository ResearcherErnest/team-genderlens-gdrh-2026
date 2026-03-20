"""Tests for src.pipeline.transform."""

from pathlib import Path

import pandas as pd
import pytest

from src.pipeline.ingestion import load_all
from src.pipeline.transform import (
    join_studies_resources,
    join_quality,
    build_search_text,
    parse_quality_flags,
    transform,
)


@pytest.fixture
def sample_data():
    sample_dir = Path(__file__).resolve().parents[1] / "data" / "sample"
    return load_all(data_dir=sample_dir)


@pytest.fixture
def simple_dfs():
    studies = pd.DataFrame({
        "study_id": [1, 2],
        "title": ["Study A", "Study B"],
        "year": [2020, 2022],
        "organization": ["NISR", "NISR"],
        "url": ["http://a", "http://b"],
        "abstract": ["About agriculture", "About health"],
        "get_microdata_url": ["http://a/data", None],
        "quality_flags": ["", "missing_study_type;generic_resource_type"],
    })
    resources = pd.DataFrame({
        "study_id": [1, 1, 2],
        "type": ["pdf", "csv", "pdf"],
        "name": ["r1", "r2", "r3"],
        "url": ["http://r1", "http://r2", "http://r3"],
    })
    quality = pd.DataFrame({
        "study_id": [1, 2],
        "title": ["Study A", "Study B"],
        "missing_field_count": [0, 2],
        "resource_count": [2, 1],
        "quality_flags": ["", "missing_study_type;generic_resource_type"],
    })
    return studies, resources, quality


class TestJoinStudiesResources:
    def test_resource_count_computed(self, simple_dfs):
        studies, resources, _ = simple_dfs
        result = join_studies_resources(studies, resources)
        assert result.loc[result.study_id == 1, "resource_count_computed"].iloc[0] == 2
        assert result.loc[result.study_id == 2, "resource_count_computed"].iloc[0] == 1

    def test_resource_types_are_lists(self, simple_dfs):
        studies, resources, _ = simple_dfs
        result = join_studies_resources(studies, resources)
        types_1 = result.loc[result.study_id == 1, "resource_types"].iloc[0]
        assert isinstance(types_1, list)
        assert "csv" in types_1
        assert "pdf" in types_1

    def test_has_microdata_flag(self, simple_dfs):
        studies, resources, _ = simple_dfs
        result = join_studies_resources(studies, resources)
        assert result.loc[result.study_id == 1, "has_microdata"].iloc[0] == True
        assert result.loc[result.study_id == 2, "has_microdata"].iloc[0] == False


class TestJoinQuality:
    def test_missing_field_count_merged(self, simple_dfs):
        studies, _, quality = simple_dfs
        result = join_quality(studies, quality)
        assert "missing_field_count" in result.columns
        assert result.loc[result.study_id == 2, "missing_field_count"].iloc[0] == 2


class TestBuildSearchText:
    def test_search_text_contains_title_and_abstract(self, simple_dfs):
        studies, _, _ = simple_dfs
        result = build_search_text(studies)
        text = result.loc[0, "search_text"]
        assert "Study A" in text
        assert "agriculture" in text


class TestParseQualityFlags:
    def test_empty_flags_give_empty_list(self, simple_dfs):
        studies, _, _ = simple_dfs
        result = parse_quality_flags(studies)
        assert result.loc[0, "quality_flags_list"] == []

    def test_semicolon_flags_are_split(self, simple_dfs):
        studies, _, _ = simple_dfs
        result = parse_quality_flags(studies)
        flags = result.loc[1, "quality_flags_list"]
        assert "missing_study_type" in flags
        assert "generic_resource_type" in flags


class TestFullTransform:
    def test_transform_returns_enriched_df(self, simple_dfs):
        studies, resources, quality = simple_dfs
        result = transform(studies, resources, quality)
        expected_cols = [
            "search_text", "quality_flags_list", "has_microdata",
            "resource_count_computed", "resource_types",
        ]
        for col in expected_cols:
            assert col in result.columns, f"Missing column: {col}"

    def test_transform_with_sample_data(self, sample_data):
        studies, resources, quality = sample_data
        result = transform(studies, resources, quality)
        assert len(result) == len(studies)
