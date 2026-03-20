"""
Search Engine — TF-IDF semantic search with fuzzy matching fallback.

Uses scikit-learn TfidfVectorizer for vector search and stdlib difflib
for fuzzy matching when TF-IDF returns no results.
"""

from __future__ import annotations

import difflib
import logging
import re
from typing import List, Optional, Tuple

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class SearchEngine:
    """TF-IDF + fuzzy search over a DataFrame's search_text column."""

    def __init__(self, df: pd.DataFrame, text_column: str = "search_text"):
        self.df = df.copy()
        self.text_column = text_column
        self._corpus = self.df[text_column].fillna("").tolist()
        self._vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=5000,
            ngram_range=(1, 2),
        )
        self._tfidf_matrix = self._vectorizer.fit_transform(self._corpus)
        logger.info(
            "SearchEngine initialized: %d docs, %d features",
            len(self._corpus),
            self._tfidf_matrix.shape[1],
        )

    # --- TF-IDF search ---

    def tfidf_search(
        self, query: str, top_k: int = 20
    ) -> List[Tuple[int, float]]:
        """
        Return list of (df_index, similarity_score) sorted descending.

        Only includes results with score > 0.
        """
        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._tfidf_matrix).flatten()

        # Pairs with score > 0, sorted desc
        results = [
            (idx, float(score))
            for idx, score in enumerate(scores)
            if score > 0
        ]
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    # --- Fuzzy fallback ---

    def fuzzy_search(
        self, query: str, top_k: int = 20, cutoff: float = 0.3
    ) -> List[Tuple[int, float]]:
        """Fuzzy match using difflib.SequenceMatcher."""
        query_lower = query.lower()
        results: List[Tuple[int, float]] = []

        for idx, text in enumerate(self._corpus):
            ratio = difflib.SequenceMatcher(
                None, query_lower, text.lower()
            ).ratio()
            if ratio >= cutoff:
                results.append((idx, ratio))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    # --- Combined search ---

    def search(
        self, query: str, top_k: int = 20
    ) -> pd.DataFrame:
        """
        Search with TF-IDF, falling back to fuzzy if no TF-IDF results.

        Returns a DataFrame slice with an added `relevance_score` column.
        """
        if not query or not query.strip():
            result = self.df.copy()
            result["relevance_score"] = 0.0
            return result

        # Try TF-IDF first
        results = self.tfidf_search(query, top_k)

        # Fallback to fuzzy
        if not results:
            logger.info("TF-IDF returned 0 results — falling back to fuzzy")
            results = self.fuzzy_search(query, top_k)

        if not results:
            empty = self.df.iloc[:0].copy()
            empty["relevance_score"] = []
            return empty

        indices, scores = zip(*results)
        out = self.df.iloc[list(indices)].copy()
        out["relevance_score"] = list(scores)
        return out

    # --- Highlight helper ---

    @staticmethod
    def highlight_terms(text: str, query: str) -> str:
        """Wrap query terms in **bold** markdown for display."""
        if not text or not query:
            return text or ""
        for word in query.split():
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            text = pattern.sub(lambda m: f"**{m.group()}**", text)
        return text
