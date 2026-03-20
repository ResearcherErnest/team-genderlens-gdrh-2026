"""Tests for src.pipeline.quality."""

import pandas as pd
import pytest

from src.pipeline.quality import (
    completeness_score,
    freshness_score,
    quality_level,
    trust_score,
    compute_quality_scores,
    CURRENT_YEAR,
)


class TestCompletenessScore:
    def test_all_fields_present(self):
        row = pd.Series({
            "title": "T", "year": 2022, "organization": "O",
            "url": "http://x", "abstract": "A", "quality_flags": "f",
            "get_microdata_url": "http://d",
        })
        assert completeness_score(row) == 1.0

    def test_all_fields_missing(self):
        row = pd.Series({
            "title": None, "year": None, "organization": None,
            "url": None, "abstract": None, "quality_flags": None,
            "get_microdata_url": None,
        })
        assert completeness_score(row) == 0.0

    def test_partial_fields(self):
        row = pd.Series({
            "title": "T", "year": 2022, "organization": "",
            "url": "http://x", "abstract": None, "quality_flags": "",
            "get_microdata_url": None,
        })
        score = completeness_score(row)
        assert 0 < score < 1


class TestFreshnessScore:
    def test_current_year_is_1(self):
        assert freshness_score(CURRENT_YEAR) == 1.0

    def test_old_year_decays(self):
        score = freshness_score(CURRENT_YEAR - 5)
        assert score == 0.5

    def test_very_old_is_zero(self):
        assert freshness_score(CURRENT_YEAR - 20) == 0.0

    def test_null_year_is_zero(self):
        assert freshness_score(None) == 0.0

    def test_invalid_year_is_zero(self):
        assert freshness_score("bad") == 0.0


class TestQualityLevel:
    def test_zero_is_good(self):
        assert quality_level(0) == "good"

    def test_one_is_warning(self):
        assert quality_level(1) == "warning"

    def test_two_is_warning(self):
        assert quality_level(2) == "warning"

    def test_three_is_critical(self):
        assert quality_level(3) == "critical"

    def test_none_defaults_good(self):
        assert quality_level(None) == "good"


class TestTrustScore:
    def test_perfect_scores(self):
        score = trust_score(1.0, 1.0, 20)
        assert score == 1.0

    def test_zero_scores(self):
        score = trust_score(0.0, 0.0, 0)
        assert score == 0.0

    def test_resource_cap_at_20(self):
        # 100 resources should score same as 20
        assert trust_score(0.5, 0.5, 100) == trust_score(0.5, 0.5, 20)


class TestComputeQualityScores:
    def test_adds_score_columns(self):
        df = pd.DataFrame({
            "study_id": [1],
            "title": ["T"],
            "year": [2022],
            "organization": ["O"],
            "url": ["http://x"],
            "abstract": ["A"],
            "quality_flags": [""],
            "get_microdata_url": ["http://d"],
            "missing_field_count": [0],
            "resource_count": [5],
        })
        result = compute_quality_scores(df)
        assert "completeness_score" in result.columns
        assert "freshness_score" in result.columns
        assert "quality_level" in result.columns
        assert "trust_score" in result.columns
        assert result["quality_level"].iloc[0] == "good"
