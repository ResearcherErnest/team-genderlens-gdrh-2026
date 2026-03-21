"""
Ingestion Layer — Schema-validated CSV loading with type coercion.

Supports both sample data (data/sample/) and full data (data/full-data.zip).
Set env var GENDERLENS_DATA_MODE=full|sample to override the default mode
defined in schema_config.
"""

from __future__ import annotations

import logging
import os
import zipfile
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd

from src.schema_config import (
    DEFAULT_DATA_MODE,
    STUDIES_SCHEMA,
    RESOURCES_SCHEMA,
    QUALITY_SCHEMA,
)

logger = logging.getLogger(__name__)

# --- Re-export required cols so existing imports keep working ---
STUDIES_REQUIRED_COLS = STUDIES_SCHEMA["required_cols"]
RESOURCES_REQUIRED_COLS = RESOURCES_SCHEMA["required_cols"]
QUALITY_REQUIRED_COLS = QUALITY_SCHEMA["required_cols"]

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


def _coerce_types(df: pd.DataFrame, dtype_overrides: Dict[str, str] | None = None) -> pd.DataFrame:
    """Apply type coercion based on *dtype_overrides* mapping.

    Falls back to a sensible default set when no overrides are given.
    """
    overrides: Dict[str, str] = dtype_overrides or {
        "year": "Int64",
        "missing_field_count": "Int64",
        "resource_count": "Int64",
        "study_id": "Int64",
    }
    for col, dtype in overrides.items():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype(dtype)
    return df


def _resolve_data_dir() -> Path:
    """Return the directory to load CSVs from, based on env var."""
    mode = os.getenv("GENDERLENS_DATA_MODE", DEFAULT_DATA_MODE).lower()

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
    dtype_overrides: Dict[str, str] | None = None,
) -> pd.DataFrame:
    """Load a single CSV with schema validation and type coercion."""
    directory = data_dir or _resolve_data_dir()
    filepath = directory / filename

    if not filepath.exists():
        raise FileNotFoundError(f"Data file not found: {filepath}")

    df = pd.read_csv(filepath)
    _validate_schema(df, required_cols, filename)
    df = _coerce_types(df, dtype_overrides)

    logger.info("Loaded %s: %d rows × %d cols", filename, len(df), len(df.columns))
    return df


def load_studies(data_dir: Optional[Path] = None) -> pd.DataFrame:
    """Load studies.csv."""
    return load_csv(
        STUDIES_SCHEMA["filename"],
        STUDIES_SCHEMA["required_cols"],
        data_dir,
        STUDIES_SCHEMA["dtype_overrides"],
    )


def load_resources(data_dir: Optional[Path] = None) -> pd.DataFrame:
    """Load study_resources.csv."""
    return load_csv(
        RESOURCES_SCHEMA["filename"],
        RESOURCES_SCHEMA["required_cols"],
        data_dir,
        RESOURCES_SCHEMA["dtype_overrides"],
    )


def load_quality_report(data_dir: Optional[Path] = None) -> pd.DataFrame:
    """Load quality_report.csv."""
    return load_csv(
        QUALITY_SCHEMA["filename"],
        QUALITY_SCHEMA["required_cols"],
        data_dir,
        QUALITY_SCHEMA["dtype_overrides"],
    )


def load_all(
    data_dir: Optional[Path] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load all three datasets. Returns (studies, resources, quality)."""
    d = data_dir or _resolve_data_dir()
    return load_studies(d), load_resources(d), load_quality_report(d)
