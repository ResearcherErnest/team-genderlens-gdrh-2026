"""
Quality Badges — Emoji and HTML rendering for quality levels.
"""

from __future__ import annotations


QUALITY_EMOJI = {
    "good": "🟢",
    "warning": "🟡",
    "critical": "🔴",
}

QUALITY_LABELS = {
    "good": "Good",
    "warning": "Warning",
    "critical": "Critical",
}

QUALITY_COLORS = {
    "good": "#10B981",
    "warning": "#F59E0B",
    "critical": "#EF4444",
}


def quality_emoji(level: str) -> str:
    """Return emoji for a quality level."""
    return QUALITY_EMOJI.get(level, "⚪")


def quality_label(level: str) -> str:
    """Return human label for a quality level."""
    return QUALITY_LABELS.get(level, "Unknown")


def quality_badge_html(level: str) -> str:
    """Return styled HTML badge for a quality level."""
    color = QUALITY_COLORS.get(level, "#94A3B8")
    label = quality_label(level)
    emoji = quality_emoji(level)
    return (
        f'<span class="quality-badge" style="'
        f"background: {color}20; color: {color}; "
        f'border: 1px solid {color}40;">'
        f"{emoji} {label}</span>"
    )


def trust_score_bar(score: float) -> str:
    """Return a simple text progress bar for trust score (0–1)."""
    filled = int(score * 10)
    empty = 10 - filled
    return f"{'█' * filled}{'░' * empty} {score:.0%}"
