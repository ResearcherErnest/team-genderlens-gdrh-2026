"""
Advocacy Toolkit — Policy brief generator page.
"""

import streamlit as st
from pathlib import Path

from src.pipeline.ingestion import load_all
from src.pipeline.transform import transform
from src.pipeline.quality import compute_quality_scores
from src.export import generate_policy_brief, export_studies_csv, generate_comparison_report
from src.provenance import format_citation, format_provenance_note
from src.quality_badges import quality_badge_html, trust_score_bar

# --- Page config ---
st.set_page_config(page_title="Advocacy Toolkit — GenderLens RW", page_icon="📋", layout="wide")

css_path = Path(__file__).resolve().parents[1] / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


@st.cache_data(show_spinner="Loading data …")
def get_data():
    studies, resources, quality = load_all()
    df = transform(studies, resources, quality)
    df = compute_quality_scores(df)
    return df


df = get_data()

# --- Header ---
st.markdown("# Advocacy Toolkit")
st.markdown("Generate policy-ready briefs with citations, quality caveats, and data provenance")
st.markdown("---")

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["Policy Brief Generator", "Data Export", "Provenance Viewer"])

# --------------------------------------------------------------------
# TAB 1: Policy Brief Generator
# --------------------------------------------------------------------
with tab1:
    st.markdown("### Select a Study")

    selected_title = st.selectbox(
        "Choose a study to generate a policy brief",
        df["title"].tolist(),
        key="advocacy_study",
    )

    scenario = st.selectbox(
        "Advocacy scenario",
        ["General", "Gender Gap in Agriculture", "Health and Demographics",
         "Education Access", "Economic Empowerment", "District-Level Advocacy"],
        key="advocacy_scenario",
    )

    if st.button("Generate Policy Brief", key="gen_brief"):
        row = df[df["title"] == selected_title].iloc[0]
        brief = generate_policy_brief(row, scenario=scenario.lower())

        st.markdown("---")
        st.markdown("### Generated Policy Brief")

        # Display study quality summary
        col_q1, col_q2, col_q3 = st.columns(3)
        with col_q1:
            st.markdown(
                f"**Quality**: {quality_badge_html(row.get('quality_level', 'unknown'))}",
                unsafe_allow_html=True,
            )
        with col_q2:
            st.markdown(f"**Trust**: {trust_score_bar(row.get('trust_score', 0))}")
        with col_q3:
            st.markdown(f"**Completeness**: {row.get('completeness_score', 0):.0%}")

        st.markdown("---")

        # Brief content
        st.markdown(brief)

        # Download button
        st.download_button(
            "Download Brief (.md)",
            data=brief,
            file_name=f"policy_brief_{row.get('study_id', 'unknown')}.md",
            mime="text/markdown",
        )

# --------------------------------------------------------------------
# TAB 2: Data Export
# --------------------------------------------------------------------
with tab2:
    st.markdown("### Export Study Data")

    st.markdown("Download a CSV summary of all studies with quality scores.")

    csv_data = export_studies_csv(df)
    st.download_button(
        "Download All Studies (CSV)",
        data=csv_data,
        file_name="genderlens_studies_export.csv",
        mime="text/csv",
    )

    st.markdown("---")

    st.markdown("### Comparison Report")
    st.markdown("Select multiple studies to generate a comparison report.")

    selected_studies = st.multiselect(
        "Select studies to compare",
        df["title"].tolist(),
        key="compare_studies",
    )

    if selected_studies:
        compare_df = df[df["title"].isin(selected_studies)]
        report = generate_comparison_report(compare_df)

        st.markdown(report)

        st.download_button(
            "Download Comparison Report (.md)",
            data=report,
            file_name="genderlens_comparison_report.md",
            mime="text/markdown",
        )

# --------------------------------------------------------------------
# TAB 3: Provenance Viewer
# --------------------------------------------------------------------
with tab3:
    st.markdown("### Data Provenance")
    st.markdown("Review the source and citation information for each study.")

    for _, row in df.iterrows():
        with st.expander(row.get('title', 'Untitled'), expanded=False):
            # Provenance note
            note = format_provenance_note(
                title=row.get("title", ""),
                institution=row.get("organization", "Unknown"),
                url=row.get("url", ""),
                year=row.get("year", "N/A"),
            )
            st.markdown(note, unsafe_allow_html=True)

            st.markdown("---")

            # Citation
            citation = format_citation(
                title=row.get("title", ""),
                organization=row.get("organization", "Unknown"),
                year=row.get("year", "N/A"),
                url=row.get("url", ""),
            )
            st.code(citation, language=None)
