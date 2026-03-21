"""
Quality Scoring Engine — Completeness, freshness, and trust scoring.

Computes per-study quality metrics and assigns a traffic-light quality level.
"""

from __future__ import annotations

import logging
from datetime import datetime

import pandas as pd

from src.schema_config import METADATA_FIELDS, QUALITY_WEIGHTS

logger = logging.getLogger(__name__)

# --- Constants ---
CURRENT_YEAR = datetime.now().year

# Weights for composite trust score (from schema_config)
WEIGHT_COMPLETENESS = QUALITY_WEIGHTS["completeness"]
WEIGHT_FRESHNESS = QUALITY_WEIGHTS["freshness"]
WEIGHT_RESOURCES = QUALITY_WEIGHTS["resources"]


# --- Scoring functions ---

def completeness_score(row: pd.Series) -> float:
    """Fraction of METADATA_FIELDS that are non-null and non-empty (0–1)."""
    filled = 0
    for field in METADATA_FIELDS:
        val = row.get(field)
        if pd.notna(val) and str(val).strip():
            filled += 1
    return round(filled / len(METADATA_FIELDS), 2)


def freshness_score(year: object) -> float:
    """Score 0–1 based on recency. Latest year = 1.0, decays ~0.1/yr."""
    if pd.isna(year):
        return 0.0
    try:
        age = CURRENT_YEAR - int(year)
    except (ValueError, TypeError):
        return 0.0
    return round(max(0.0, 1.0 - age * 0.1), 2)


def quality_level(missing_field_count: object) -> str:
    """Traffic-light level based on missing_field_count."""
    try:
        count = int(missing_field_count)
    except (ValueError, TypeError):
        count = 0
    if count == 0:
        return "good"
    elif count <= 2:
        return "warning"
    else:
        return "critical"


def trust_score(completeness: float, freshness: float, resource_count: int) -> float:
    """
    Weighted composite trust score (0–1).

    resource_count is normalized: cap at 20 for max score.
    """
    resource_norm = min(int(resource_count or 0), 20) / 20.0
    score = (
        WEIGHT_COMPLETENESS * completeness
        + WEIGHT_FRESHNESS * freshness
        + WEIGHT_RESOURCES * resource_norm
    )
    return round(score, 2)


# --- Public API ---

def compute_quality_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Add quality score columns to the enriched DataFrame."""
    logger.info("Computing quality scores for %d studies …", len(df))

    # Use resource_count from quality report if available, else computed
    rc_col = (
        "resource_count"
        if "resource_count" in df.columns
        else "resource_count_computed"
    )

    df["completeness_score"] = df.apply(completeness_score, axis=1)
    df["freshness_score"] = df["year"].apply(freshness_score)
    df["quality_level"] = df["missing_field_count"].apply(quality_level)
    df["trust_score"] = df.apply(
        lambda r: trust_score(
            r["completeness_score"],
            r["freshness_score"],
            r.get(rc_col, 0),
        ),
        axis=1,
    )

    logger.info("Quality scoring complete.")
    return df
