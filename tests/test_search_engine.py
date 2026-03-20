"""Tests for src.search_engine."""

import pandas as pd
import pytest

from src.search_engine import SearchEngine


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "study_id": [1, 2, 3],
        "title": [
            "Agricultural Household Survey 2017",
            "Demographic and Health Survey 2015",
            "Population and Housing Census 2022",
        ],
        "abstract": [
            "Agriculture and household indicators for policy analysis",
            "Health and demographic indicators with documentation",
            "Population and housing census findings by geography",
        ],
        "search_text": [
            "Agricultural Household Survey 2017 Agriculture and household indicators for policy analysis",
            "Demographic and Health Survey 2015 Health and demographic indicators with documentation",
            "Population and Housing Census 2022 Population and housing census findings by geography",
        ],
    })


@pytest.fixture
def engine(sample_df):
    return SearchEngine(sample_df, text_column="search_text")


class TestTfidfSearch:
    def test_returns_relevant_results(self, engine):
        results = engine.tfidf_search("agriculture household")
        assert len(results) > 0
        # First result should be study 1 (agriculture)
        assert results[0][0] == 0

    def test_scores_are_positive(self, engine):
        results = engine.tfidf_search("health")
        for _, score in results:
            assert score > 0


class TestFuzzySearch:
    def test_finds_similar_text(self, engine):
        results = engine.fuzzy_search("agricultural", cutoff=0.1)
        assert len(results) > 0

    def test_respects_cutoff(self, engine):
        results = engine.fuzzy_search("zzzzz", cutoff=0.9)
        assert len(results) == 0


class TestCombinedSearch:
    def test_empty_query_returns_all(self, engine, sample_df):
        result = engine.search("")
        assert len(result) == len(sample_df)

    def test_search_returns_dataframe(self, engine):
        result = engine.search("health")
        assert isinstance(result, pd.DataFrame)
        assert "relevance_score" in result.columns

    def test_no_results_returns_empty_df(self, engine):
        result = engine.search("xyznonexistent1234567890")
        assert len(result) == 0


class TestHighlight:
    def test_highlight_wraps_terms(self):
        text = "Agriculture and health indicators"
        highlighted = SearchEngine.highlight_terms(text, "health")
        assert "**health**" in highlighted

    def test_empty_query_returns_text(self):
        assert SearchEngine.highlight_terms("hello", "") == "hello"

    def test_none_text_returns_empty(self):
        assert SearchEngine.highlight_terms(None, "q") == ""
