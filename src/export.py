"""
Export Engine — Generate downloadable CSV summaries and text reports.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Optional

import pandas as pd

from src.provenance import format_citation

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Gender distribution extraction helpers
# ---------------------------------------------------------------------------
_GENDER_PATTERNS: list[tuple[str, str]] = [
    # Female-headed households
    (r"(\d+(?:\.\d+)?)\s*%[^.]*?female[^.]*?head",     "Female-headed households: {0}%"),
    (r"female[^.]*?head[^.]*?(\d+(?:\.\d+)?)\s*%",     "Female-headed households: {0}%"),
    # Male-headed households
    (r"(\d+(?:\.\d+)?)\s*%[^.]*?male[^.]*?head",       "Male-headed households: {0}%"),
    (r"male[^.]*?head[^.]*?(\d+(?:\.\d+)?)\s*%",       "Male-headed households: {0}%"),
    # Mostly male / female headed phrasing
    (r"mostly\s+male.headed",                            "Predominantly male-headed households"),
    (r"mostly\s+female.headed",                          "Predominantly female-headed households"),
    # Women participation / proportion
    (r"(\d+(?:\.\d+)?)\s*%[^.]*?women",                "Women's share: {0}%"),
    (r"women[^.]*?(\d+(?:\.\d+)?)\s*%",                "Women-related statistic: {0}%"),
    # Gender gap
    (r"gender\s+gap[^.]*?(\d+(?:\.\d+)?)\s*%",         "Gender gap: {0}%"),
    # Girls education
    (r"(\d+(?:\.\d+)?)\s*%[^.]*?girls",                "Girls share: {0}%"),
]


def _extract_gender_stats(abstract: str) -> list[str]:
    """Extract gender-related statistics from a study abstract."""
    found: list[str] = []
    seen_labels: set[str] = set()

    for pattern, template in _GENDER_PATTERNS:
        m = re.search(pattern, abstract, re.IGNORECASE)
        if m:
            if m.lastindex:
                label = template.format(m.group(1))
            else:
                label = template.format("")  # boolean patterns (mostly male/female)

            # Deduplicate by label prefix
            prefix = label.split(":")[0]
            if prefix not in seen_labels:
                seen_labels.add(prefix)
                found.append(label)

        if len(found) >= 5:
            break

    return found


def export_studies_csv(df: pd.DataFrame) -> str:
    """Export studies DataFrame to CSV string (for st.download_button)."""
    export_cols = [
        c for c in [
            "study_id", "title", "year", "organization", "url",
            "quality_level", "trust_score", "completeness_score",
            "freshness_score", "resource_count_computed", "has_microdata",
        ]
        if c in df.columns
    ]
    return df[export_cols].to_csv(index=False)


def generate_policy_brief(
    study_row: pd.Series,
    scenario: str = "general",
) -> str:
    """Generate a formatted policy brief for a single study (returns Markdown)."""
    title          = study_row.get("title", "Untitled Study")
    org            = study_row.get("organization", "Unknown")
    year           = study_row.get("year", "N/A")
    abstract       = str(study_row.get("abstract", "No abstract available."))
    url            = study_row.get("url", "")
    quality        = study_row.get("quality_level", "unknown")
    trust          = study_row.get("trust_score", 0)
    completeness   = study_row.get("completeness_score", 0)
    flags          = study_row.get("quality_flags_list", [])
    resource_count = study_row.get("resource_count_computed", 0)

    citation = format_citation(title, org, year, url)

    # Quality caveat block
    if quality == "critical":
        caveat = (
            "> ⚠️ **Data Quality Caveat**: This dataset has critical quality issues. "
            "Verify findings independently before citing.\n\n"
        )
    elif quality == "warning":
        caveat = (
            "> ℹ️ **Data Quality Note**: Some metadata fields are missing. "
            "Note this limitation when citing.\n\n"
        )
    else:
        caveat = ""

    flag_text = (
        "**Quality flags**: " + ", ".join(flags) + "\n\n"
        if flags else ""
    )

    # Gender distribution section
    gender_stats = _extract_gender_stats(abstract)
    if gender_stats:
        gender_lines = "\n".join(f"- {s}" for s in gender_stats)
        gender_section = (
            "## Gender Distribution Analysis\n\n"
            "Key gender metrics identified in this dataset:\n\n"
            f"{gender_lines}\n\n"
            "> These figures are extracted from the study abstract. "
            "Consult the full dataset for complete gender-disaggregated tables.\n\n"
        )
    else:
        gender_section = (
            "## Gender Distribution Analysis\n\n"
            "> No explicit gender distribution data was found in the study abstract. "
            "Consult the full dataset for gender-disaggregated statistics "
            "(e.g., female-headed household rates, women's labour participation).\n\n"
        )

    return f"""# Policy Brief: {title}

**Prepared**: {datetime.now(timezone.utc).strftime("%d %B %Y")}  
**Source**: {org} ({year})  
**Advocacy Scenario**: {scenario.title()}

---

## Background & Key Findings

{abstract}

---

{gender_section}---

## Data Quality Assessment

| Metric | Value |
|---|---|
| Trust Score | {trust:.0%} |
| Completeness | {completeness:.0%} |
| Quality Level | {quality.title()} |
| Resources Available | {int(resource_count)} |

{caveat}{flag_text}---

## Citation

{citation}

---

*Generated by GenderLens RW — Smart Gender Data Discovery Platform*  
*Data source: [NISR Microdata Catalog]({url if url else "https://microdata.statistics.gov.rw"})*
"""


def generate_comparison_report(df: pd.DataFrame) -> str:
    """Generate a comparison report across multiple studies."""
    now = datetime.now(timezone.utc).strftime("%d %B %Y")

    report = f"# GenderLens RW — Data Comparison Report\n\n"
    report += f"**Generated**: {now}  \n"
    report += f"**Studies compared**: {len(df)}\n\n---\n\n"

    for _, row in df.iterrows():
        title = row.get("title", "Untitled")
        org = row.get("organization", "Unknown")
        year = row.get("year", "N/A")
        trust = row.get("trust_score", 0)
        quality = row.get("quality_level", "unknown")
        report += f"### {title}\n"
        report += f"- **Organization**: {org}\n"
        report += f"- **Year**: {year}\n"
        report += f"- **Trust Score**: {trust:.0%}\n"
        report += f"- **Quality**: {quality.title()}\n\n"

    report += "---\n\n*Generated by GenderLens RW*\n"
    return report
