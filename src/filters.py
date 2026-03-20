"""
Filter Utilities — Enhanced multi-faceted filtering for the discovery page.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import pandas as pd


def filter_by_year_range(
    df: pd.DataFrame,
    year_range: Optional[Tuple[int, int]] = None,
) -> pd.DataFrame:
    """Filter studies to those within [min_year, max_year]."""
    if year_range is None:
        return df
    min_yr, max_yr = year_range
    return df[df["year"].between(min_yr, max_yr)]


def filter_by_organization(
    df: pd.DataFrame,
    organizations: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Filter to studies matching any of the given organizations."""
    if not organizations:
        return df
    return df[df["organization"].isin(organizations)]


def filter_by_resource_type(
    df: pd.DataFrame,
    resource_types: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Filter to studies that have at least one of the given resource types."""
    if not resource_types:
        return df
    mask = df["resource_types"].apply(
        lambda types: bool(set(types) & set(resource_types))
    )
    return df[mask]


def filter_by_quality_level(
    df: pd.DataFrame,
    levels: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Filter by quality_level (good / warning / critical)."""
    if not levels:
        return df
    return df[df["quality_level"].isin(levels)]


def filter_by_has_microdata(
    df: pd.DataFrame,
    has_microdata: Optional[bool] = None,
) -> pd.DataFrame:
    """Filter by has_microdata flag."""
    if has_microdata is None:
        return df
    return df[df["has_microdata"] == has_microdata]


def apply_filters(
    df: pd.DataFrame,
    year_range: Optional[Tuple[int, int]] = None,
    organizations: Optional[List[str]] = None,
    resource_types: Optional[List[str]] = None,
    quality_levels: Optional[List[str]] = None,
    has_microdata: Optional[bool] = None,
) -> pd.DataFrame:
    """Apply all filters in sequence. Returns the filtered DataFrame."""
    result = df
    result = filter_by_year_range(result, year_range)
    result = filter_by_organization(result, organizations)
    result = filter_by_resource_type(result, resource_types)
    result = filter_by_quality_level(result, quality_levels)
    result = filter_by_has_microdata(result, has_microdata)
    return result
