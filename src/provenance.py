"""
Provenance Tracker — Source institution, URL logging, and citation formatting.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# In-memory provenance log (study_id → list of records)
_provenance_log: Dict[int, List[Dict]] = {}


def log_access(
    study_id: int,
    institution: str,
    url: str,
    status: str = "accessed",
) -> Dict:
    """Log a data access event for provenance tracking."""
    record = {
        "study_id": study_id,
        "institution": institution,
        "url": url,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _provenance_log.setdefault(study_id, []).append(record)
    logger.debug("Provenance logged: study %d from %s", study_id, institution)
    return record


def get_provenance(study_id: int) -> List[Dict]:
    """Get all provenance records for a study."""
    return _provenance_log.get(study_id, [])


def format_citation(
    title: str,
    organization: str,
    year: object,
    url: str,
) -> str:
    """
    Format a citation string per the required format:
    Organization (Year). Title. Retrieved from URL. Accessed YYYY-MM-DD.
    """
    yr = str(year) if not pd.isna(year) else "n.d."
    accessed = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"{organization} ({yr}). {title}. Retrieved from {url}. Accessed {accessed}."


def format_provenance_note(
    title: str,
    institution: str,
    url: str,
    year: object,
) -> str:
    """Format a provenance note for export/display."""
    return (
        f"**Source**: {institution}  \n"
        f"**Study**: {title}  \n"
        f"**Year**: {year}  \n"
        f"**URL**: [{url}]({url})  \n"
        f"**Accessed**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
    )


def clear_provenance() -> None:
    """Clear the provenance log."""
    _provenance_log.clear()
