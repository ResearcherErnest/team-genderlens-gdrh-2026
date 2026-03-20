"""Tests for src.filters."""

import pandas as pd
import pytest

from src.filters import (
    filter_by_year_range,
    filter_by_organization,
    filter_by_resource_type,
    filter_by_quality_level,
    filter_by_has_microdata,
    apply_filters,
)


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "study_id": [1, 2, 3],
        "title": ["Study A", "Study B", "Study C"],
        "year": [2017, 2020, 2022],
        "organization": ["NISR", "WHO", "NISR"],
        "resource_types": [["pdf", "csv"], ["pdf"], ["csv"]],
        "quality_level": ["good", "warning", "critical"],
        "has_microdata": [True, False, True],
    })


class TestFilterByYearRange:
    def test_filters_within_range(self, sample_df):
        result = filter_by_year_range(sample_df, (2018, 2022))
        assert len(result) == 2
        assert 1 not in result.study_id.values

    def test_none_returns_all(self, sample_df):
        result = filter_by_year_range(sample_df, None)
        assert len(result) == 3


class TestFilterByOrganization:
    def test_filters_by_org(self, sample_df):
        result = filter_by_organization(sample_df, ["NISR"])
        assert len(result) == 2

    def test_empty_list_returns_all(self, sample_df):
        result = filter_by_organization(sample_df, [])
        assert len(result) == 3


class TestFilterByResourceType:
    def test_filters_by_type(self, sample_df):
        result = filter_by_resource_type(sample_df, ["csv"])
        assert len(result) == 2  # Study A has csv, Study C has csv

    def test_none_returns_all(self, sample_df):
        result = filter_by_resource_type(sample_df, None)
        assert len(result) == 3


class TestFilterByQualityLevel:
    def test_single_level(self, sample_df):
        result = filter_by_quality_level(sample_df, ["good"])
        assert len(result) == 1

    def test_multiple_levels(self, sample_df):
        result = filter_by_quality_level(sample_df, ["good", "warning"])
        assert len(result) == 2


class TestFilterByHasMicrodata:
    def test_true_filter(self, sample_df):
        result = filter_by_has_microdata(sample_df, True)
        assert len(result) == 2

    def test_false_filter(self, sample_df):
        result = filter_by_has_microdata(sample_df, False)
        assert len(result) == 1

    def test_none_returns_all(self, sample_df):
        result = filter_by_has_microdata(sample_df, None)
        assert len(result) == 3


class TestApplyFilters:
    def test_combined_filters(self, sample_df):
        result = apply_filters(
            sample_df,
            year_range=(2018, 2022),
            organizations=["NISR"],
        )
        assert len(result) == 1
        assert result.iloc[0]["title"] == "Study C"

    def test_no_filters_returns_all(self, sample_df):
        result = apply_filters(sample_df)
        assert len(result) == 3
