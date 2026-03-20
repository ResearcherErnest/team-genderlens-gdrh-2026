"""
Ingestion Layer — Schema-validated CSV loading with type coercion.

Supports both sample data (data/sample/) and full data (data/full-data.zip).
Set env var GENDERLENS_DATA_MODE=full to use the full dataset.
"""

from __future__ import annotations

import logging
import os
import zipfile
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

# --- Schema definitions ---
STUDIES_REQUIRED_COLS = [
    "study_id", "title", "year", "organization", "url",
]
RESOURCES_REQUIRED_COLS = [
    "study_id", "type", "name", "url",
]
QUALITY_REQUIRED_COLS = [
    "study_id", "title", "missing_field_count", "resource_count",
]

# Where data lives relative to the repo root
DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SAMPLE_DIR = DATA_DIR / "sample"
FULL_ZIP = DATA_DIR / "full-data.zip"
FULL_DIR = DATA_DIR / "full"


# --- Helpers ---

def _validate_schema(df: pd.DataFrame, required: list[str], name: str) -> None:
    """Raise ValueError if any required column is missing."""
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"[{name}] Missing required columns: {missing}")


def _coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    """Best-effort type coercion for known columns."""
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    if "missing_field_count" in df.columns:
        df["missing_field_count"] = pd.to_numeric(
            df["missing_field_count"], errors="coerce"
        ).astype("Int64")
    if "resource_count" in df.columns:
        df["resource_count"] = pd.to_numeric(
            df["resource_count"], errors="coerce"
        ).astype("Int64")
    if "study_id" in df.columns:
        df["study_id"] = pd.to_numeric(df["study_id"], errors="coerce").astype("Int64")
    return df


def _resolve_data_dir() -> Path:
    """Return the directory to load CSVs from, based on env var."""
    mode = os.getenv("GENDERLENS_DATA_MODE", "sample").lower()

    if mode == "full":
        if FULL_DIR.exists() and any(FULL_DIR.glob("*.csv")):
            logger.info("Using pre-extracted full data from %s", FULL_DIR)
            return FULL_DIR
        if FULL_ZIP.exists():
            logger.info("Extracting full-data.zip → %s", FULL_DIR)
            FULL_DIR.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(FULL_ZIP, "r") as zf:
                zf.extractall(FULL_DIR)
            return FULL_DIR
        logger.warning(
            "Full data requested but %s not found — falling back to sample", FULL_ZIP
        )

    return SAMPLE_DIR


# --- Public API ---

def load_csv(
    filename: str,
    required_cols: list[str],
    data_dir: Optional[Path] = None,
) -> pd.DataFrame:
    """Load a single CSV with schema validation and type coercion."""
    directory = data_dir or _resolve_data_dir()
    filepath = directory / filename

    if not filepath.exists():
        raise FileNotFoundError(f"Data file not found: {filepath}")

    df = pd.read_csv(filepath)
    _validate_schema(df, required_cols, filename)
    df = _coerce_types(df)

    logger.info("Loaded %s: %d rows × %d cols", filename, len(df), len(df.columns))
    return df


def load_studies(data_dir: Optional[Path] = None) -> pd.DataFrame:
    """Load studies.csv."""
    return load_csv("studies.csv", STUDIES_REQUIRED_COLS, data_dir)


def load_resources(data_dir: Optional[Path] = None) -> pd.DataFrame:
    """Load study_resources.csv."""
    return load_csv("study_resources.csv", RESOURCES_REQUIRED_COLS, data_dir)


def load_quality_report(data_dir: Optional[Path] = None) -> pd.DataFrame:
    """Load quality_report.csv."""
    return load_csv("quality_report.csv", QUALITY_REQUIRED_COLS, data_dir)


def load_all(
    data_dir: Optional[Path] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load all three datasets. Returns (studies, resources, quality)."""
    d = data_dir or _resolve_data_dir()
    return load_studies(d), load_resources(d), load_quality_report(d)
