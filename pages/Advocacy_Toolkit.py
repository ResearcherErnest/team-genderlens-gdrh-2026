"""
Advocacy Toolkit — Policy brief generator, data export, and provenance viewer.
"""

import re
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from src.pipeline.ingestion import load_all
from src.pipeline.transform import transform
from src.pipeline.quality import compute_quality_scores
from src.export import export_studies_csv, generate_comparison_report, generate_policy_brief
from src.provenance import format_citation
from src.quality_badges import quality_badge_html, trust_score_bar

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Advocacy Toolkit: GenderLens RW",
    page_icon="📋",
    layout="wide",
)

css_path = Path(__file__).resolve().parents[1] / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


# Data
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading data …")
def get_data():
    studies, resources, quality = load_all()
    df = transform(studies, resources, quality)
    return compute_quality_scores(df)


df = get_data()


# Scenario inference  (AI keyword matching)
# ---------------------------------------------------------------------------
_SCENARIO_KEYWORDS: dict[str, list[str]] = {
    "Gender Gap in Agriculture":  ["agri", "farm", "crop", "livestock", "food security", "rural"],
    "Health and Demographics":    ["health", "malaria", "nutrition", "mortality", "hiv", "dhs"],
    "Education Access":           ["school", "education", "literacy", "enrol"],
    "Economic Empowerment":       ["enterprise", "business", "finance", "finscope", "employment", "labour"],
    "District-Level Advocacy":    ["district", "province", "village", "local", "sector"],
}


def infer_scenario(title: str, abstract: str) -> str:
    """Return the most likely advocacy scenario inferred from study content."""
    text = f"{title} {abstract}".lower()
    scores = {s: sum(1 for kw in kws if kw in text) for s, kws in _SCENARIO_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "General"


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("# Advocacy Toolkit")
st.caption(
    "Generate policy-ready briefs with AI &middot; export study data &middot; review data provenance"
)
st.markdown("---")

# Three clearly-separated tabs
# ---------------------------------------------------------------------------
tab_brief, tab_export, tab_prov = st.tabs([
    "  Policy Brief Generator  ",
    "  Data Export  ",
    "  Provenance Viewer  ",
])


# TAB 1 — Policy Brief Generator
# ═══════════════════════════════════════════════════════════════════════════════
with tab_brief:
    st.markdown("")

    sel_title = st.selectbox(
        "Select a study",
        df["title"].tolist(),
        key="brief_study",
        help="Choose a study to generate a tailored policy brief.",
    )

    row = df[df["title"] == sel_title].iloc[0]

    # AI-based scenario auto-suggestion
    suggested = infer_scenario(
        row.get("title", ""),
        str(row.get("abstract", "")),
    )
    _SCENARIO_OPTIONS = [
        "General",
        "Gender Gap in Agriculture",
        "Health and Demographics",
        "Education Access",
        "Economic Empowerment",
        "District-Level Advocacy",
    ]
    default_idx = _SCENARIO_OPTIONS.index(suggested) if suggested in _SCENARIO_OPTIONS else 0

    st.info(
        f"**AI-suggested scenario**: *{suggested}* — detected from study topic keywords.  "
        "You can override this below."
    )

    scenario = st.selectbox(
        "Advocacy scenario",
        _SCENARIO_OPTIONS,
        index=default_idx,
        key="brief_scenario",
        help="Auto-selected from study content. Override as needed.",
    )

    st.markdown("")  # visual gap before the action button

    if st.button("Generate Policy Brief", key="gen_brief"):
        brief = generate_policy_brief(row, scenario=scenario.lower())

        st.markdown("---")
        st.markdown("#### Generated Policy Brief")

        meta_c1, meta_c2, meta_c3 = st.columns(3)
        with meta_c1:
            st.markdown(
                f"**Quality**: {quality_badge_html(row.get('quality_level', 'unknown'))}",
                unsafe_allow_html=True,
            )
        with meta_c2:
            st.markdown(
                f"**Trust Score**: {trust_score_bar(row.get('trust_score', 0))}",
                unsafe_allow_html=True,
            )
        with meta_c3:
            st.markdown(f"**Completeness**: {row.get('completeness_score', 0):.0%}")

        st.markdown("---")
        st.markdown(brief)

        st.markdown("")
        st.download_button(
            "⬇️  Download Brief (.md)",
            data=brief,
            file_name=f"policy_brief_{row.get('study_id', 'unknown')}.md",
            mime="text/markdown",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Data Export
# ═══════════════════════════════════════════════════════════════════════════════
with tab_export:
    st.markdown("")

    st.markdown("#### Export Full Study Catalog")
    st.markdown(
        "Download a CSV containing all studies with quality scores, trust ratings, "
        "and metadata completeness flags."
    )

    csv_data = export_studies_csv(df)

    st.download_button(
        "⬇️  Download All Studies (CSV)",
        data=csv_data,
        file_name="genderlens_studies_export.csv",
        mime="text/csv",
        key="export_all_csv",
    )

    st.markdown("---")

    st.markdown("#### Comparison Report")
    st.markdown("Select two or more studies to generate a side-by-side comparison report.")

    compare_titles = st.multiselect(
        "Select studies to compare",
        df["title"].tolist(),
        key="compare_studies",
    )

    if len(compare_titles) >= 2:
        compare_df = df[df["title"].isin(compare_titles)]
        report = generate_comparison_report(compare_df)
        st.markdown(report)

        st.download_button(
            "⬇️  Download Comparison Report (.md)",
            data=report,
            file_name="genderlens_comparison_report.md",
            mime="text/markdown",
            key="export_comparison",
        )
    elif compare_titles:
        st.info("Select at least two studies to generate a comparison.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Provenance Viewer
# ═══════════════════════════════════════════════════════════════════════════════
with tab_prov:
    st.markdown("")
    st.markdown(
        "Full provenance record for each study — source institution, catalog link, "
        "coverage, and citation."
    )
    st.markdown("")

    accessed_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d at %H:%M UTC")

    for _, row in df.iterrows():
        title    = row.get("title", "Untitled")
        org      = row.get("organization", "Unknown")
        year     = row.get("year", "N/A")
        url      = row.get("url", "")
        abstract = str(row.get("abstract", "")).strip()
        coverage = str(row.get("geographic_coverage", "")).strip()
        geo_unit = str(row.get("geographic_unit", "")).strip()

        with st.expander(f"**{title}**", expanded=False):
            # --- Provenance fields ---
            st.markdown(f"**Title:** {title}")
            st.markdown(f"**Organization:** {org}")

            if url:
                st.markdown(
                    f"**Year:** {year} &nbsp;&middot;&nbsp; "
                    f"[View in Catalog]({url}) &nbsp;&middot;&nbsp; "
                    f"*Last accessed: {accessed_ts}*",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(f"**Year:** {year}")

            # --- Coverage ---
            cov_parts = [p for p in [coverage, geo_unit] if p and p.lower() != "nan"]
            if cov_parts:
                st.markdown(f"**Coverage:** {' — '.join(cov_parts)}")

            # --- Brief description ---
            if abstract and abstract.lower() != "nan":
                short = abstract[:1000] + ("…" if len(abstract) > 1000 else "")
                st.markdown(f"**Description:** {short}")

            st.markdown("---")

            # --- Citation ---
            st.markdown("**Citation**")
            citation = format_citation(title, org, year, url)
            st.code(citation, language=None)
