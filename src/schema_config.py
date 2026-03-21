"""
Schema Config — Single source of truth for CSV schemas, types, and data settings.

Edit this file to add/remove/rename columns, change type coercions,
adjust quality weights, or switch the default data mode.
"""

from __future__ import annotations

# Data-mode default (overridable via GENDERLENS_DATA_MODE env var)
# ---------------------------------------------------------------------------
DEFAULT_DATA_MODE = "full"  # "sample" | "full"


# Studies schema  (data/*/studies.csv)
# ---------------------------------------------------------------------------
STUDIES_SCHEMA = {
    "filename": "studies.csv",
    "required_cols": [
        "study_id",
        "title",
        "year",
        "organization",
        "url",
    ],
    "optional_cols": [
        # -- full-data extras (36 total in full-data.zip) --
        "collection",
        "created",
        "modified",
        "views",
        "catalog_page",
        "get_microdata_url",
        "data_access_type",
        "country",
        "study_type",
        "id_number",
        "production_date",
        "abstract",
        "scope_notes",
        "notes",
        "kind_of_data",
        "units_of_analysis",
        "geographic_coverage",
        "geographic_unit",
        "universe",
        "producers_and_sponsors",
        "primary_investigator",
        "other_producers",
        "funding",
        "overview_summary",
        "data_description_summary",
        "documentation_summary",
        "resource_count",
        "quality_flags",
        "study_description",
        "data_description",
        "documentation",
    ],
    "dtype_overrides": {
        "study_id": "Int64",
        "year": "Int64",
        "views": "Int64",
        "resource_count": "Int64",
    },
}


# Resources schema  (data/*/study_resources.csv)
# ---------------------------------------------------------------------------
RESOURCES_SCHEMA = {
    "filename": "study_resources.csv",
    "required_cols": [
        "study_id",
        "type",
        "name",
        "url",
    ],
    "optional_cols": [
        "label",
        "filename",
        "quality_flags",
    ],
    "dtype_overrides": {
        "study_id": "Int64",
    },
}


# ---------------------------------------------------------------------------
# Quality-report schema  (data/*/quality_report.csv)
# ---------------------------------------------------------------------------
QUALITY_SCHEMA = {
    "filename": "quality_report.csv",
    "required_cols": [
        "study_id",
        "title",
        "missing_field_count",
        "resource_count",
    ],
    "optional_cols": [
        "quality_flags",
        "resource_quality_flags",
    ],
    "dtype_overrides": {
        "study_id": "Int64",
        "missing_field_count": "Int64",
        "resource_count": "Int64",
    },
}


# ---------------------------------------------------------------------------
# Quality scoring settings
# ---------------------------------------------------------------------------

# Metadata fields expected to be present for a "complete" study
METADATA_FIELDS = [
    "title",
    "year",
    "organization",
    "url",
    "abstract",
    "quality_flags",
    "get_microdata_url",
]

# Weights for composite trust score  (must sum to 1.0)
QUALITY_WEIGHTS = {
    "completeness": 0.40,
    "freshness": 0.30,
    "resources": 0.30,
}
