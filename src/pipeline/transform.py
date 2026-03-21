"""
Transformation Layer — Joins, enrichment, and derived field computation.

Combines studies, resources, and quality data into a single enriched DataFrame
ready for search, filtering, and presentation.
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple

import pandas as pd

from src.schema_config import ORGANIZATION_ALIASES

logger = logging.getLogger(__name__)


def join_studies_resources(
    studies: pd.DataFrame,
    resources: pd.DataFrame,
) -> pd.DataFrame:
    """Compute per-study resource aggregates and merge back into studies."""
    # Aggregate resource info per study
    res_agg = (
        resources.groupby("study_id")
        .agg(
            resource_count_computed=("study_id", "size"),
            resource_types=("type", lambda x: sorted(set(x.dropna()))),
        )
        .reset_index()
    )

    merged = studies.merge(res_agg, on="study_id", how="left")

    # Fill NaN for studies with no resources
    merged["resource_count_computed"] = (
        merged["resource_count_computed"].fillna(0).astype(int)
    )
    merged["resource_types"] = merged["resource_types"].apply(
        lambda x: x if isinstance(x, list) else []
    )

    # Has microdata flag
    merged["has_microdata"] = merged["get_microdata_url"].notna() & (
        merged["get_microdata_url"].astype(str).str.strip() != ""
    )

    return merged


def join_quality(
    studies: pd.DataFrame,
    quality: pd.DataFrame,
) -> pd.DataFrame:
    """Merge quality report into studies (left join on study_id)."""
    # Avoid column collisions — quality also has 'title'
    quality_cols = [
        c for c in quality.columns if c not in studies.columns or c == "study_id"
    ]
    merged = studies.merge(quality[quality_cols], on="study_id", how="left")

    # Fill quality NaNs
    merged["missing_field_count"] = (
        merged["missing_field_count"].fillna(0).astype(int)
    )

    return merged


def build_search_text(df: pd.DataFrame) -> pd.DataFrame:
    """Create concatenated search_text field from title + abstract."""
    parts = []
    for col in ("title", "abstract", "organization"):
        if col in df.columns:
            parts.append(df[col].fillna(""))
    df["search_text"] = parts[0].str.cat(parts[1:], sep=" ").str.strip()
    return df


def normalize_organization(df: pd.DataFrame) -> pd.DataFrame:
    """Replace verbose organization names with canonical abbreviations.

    The original name is preserved in ``organization_full``.  Rules are
    defined in ``src.schema_config.ORGANIZATION_ALIASES`` — edit there,
    not here.
    """
    if "organization" not in df.columns:
        return df

    df["organization_full"] = df["organization"]

    def _abbreviate(name: str) -> str:
        if not isinstance(name, str):
            return name
        name_lower = name.lower()
        for fragment, abbr in ORGANIZATION_ALIASES:
            if fragment.lower() in name_lower:
                return abbr
        return name  # unchanged when no rule matches

    df["organization"] = df["organization"].apply(_abbreviate)
    return df


def parse_quality_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Split semicolon-separated quality_flags into a list column."""
    if "quality_flags" in df.columns:
        df["quality_flags_list"] = (
            df["quality_flags"]
            .fillna("")
            .apply(lambda x: [f.strip() for f in x.split(";") if f.strip()])
        )
    else:
        df["quality_flags_list"] = [[] for _ in range(len(df))]
    return df


def transform(
    studies: pd.DataFrame,
    resources: pd.DataFrame,
    quality: pd.DataFrame,
) -> pd.DataFrame:
    """Full transformation pipeline: join → enrich → return enriched DataFrame."""
    logger.info("Starting transformation pipeline …")

    # Step 1: join resources
    df = join_studies_resources(studies, resources)
    logger.info("After resource join: %d rows", len(df))

    # Step 2: join quality
    df = join_quality(df, quality)
    logger.info("After quality join: %d rows", len(df))

    # Step 3: normalize organization names to abbreviations
    df = normalize_organization(df)

    # Step 4: build search text (uses the abbreviated organization)
    df = build_search_text(df)

    # Step 5: parse quality flags
    df = parse_quality_flags(df)

    logger.info("Transformation complete: %d rows × %d cols", len(df), len(df.columns))
    return df
