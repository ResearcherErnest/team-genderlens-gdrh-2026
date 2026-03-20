"""
🔍 Discovery — Smart search & discovery page.
"""

import streamlit as st
from pathlib import Path

from src.pipeline.ingestion import load_all
from src.pipeline.transform import transform
from src.pipeline.quality import compute_quality_scores
from src.search_engine import SearchEngine
from src.filters import apply_filters
from src.quality_badges import quality_badge_html, quality_emoji, trust_score_bar

# --- Page config ---
st.set_page_config(page_title="Discovery — GenderLens RW", page_icon="🔍", layout="wide")

css_path = Path(__file__).resolve().parents[1] / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


# --- Data loading ---
@st.cache_data(show_spinner="Loading data …")
def get_data():
    studies, resources, quality = load_all()
    df = transform(studies, resources, quality)
    df = compute_quality_scores(df)
    return df


df = get_data()

# --- Title ---
st.markdown("# 🔍 Smart Discovery")
st.markdown("Search across studies using AI-powered semantic matching")

st.markdown("---")

# --- Search bar ---
query = st.text_input(
    "🔎 Search studies",
    placeholder="e.g. agricultural labour, health demographics, population census …",
    key="discovery_search",
)

# --- Sidebar filters ---
with st.sidebar:
    st.markdown("### 🎛️ Filters")

    # Year range
    if "year" in df.columns and df["year"].notna().any():
        min_yr = int(df["year"].min())
        max_yr = int(df["year"].max())
        year_range = st.slider("Year range", min_yr, max_yr, (min_yr, max_yr))
    else:
        year_range = None

    # Organization
    orgs = sorted(df["organization"].dropna().unique().tolist())
    selected_orgs = st.multiselect("Organization", orgs)

    # Quality level
    quality_options = ["good", "warning", "critical"]
    selected_quality = st.multiselect(
        "Quality level",
        quality_options,
        format_func=lambda x: f"{quality_emoji(x)} {x.title()}",
    )

    # Has microdata
    microdata_filter = st.radio(
        "Microdata availability",
        ["All", "With microdata", "Without microdata"],
    )
    has_microdata = (
        True if microdata_filter == "With microdata"
        else False if microdata_filter == "Without microdata"
        else None
    )

# --- Apply search + filters ---
# Search
engine = SearchEngine(df)
results = engine.search(query)

# Apply filters
results = apply_filters(
    results,
    year_range=year_range if year_range else None,
    organizations=selected_orgs or None,
    quality_levels=selected_quality or None,
    has_microdata=has_microdata,
)

# --- Results ---
st.markdown(f"### 📋 Results ({len(results)} studies)")

if len(results) == 0:
    st.info("No studies match your search and filter criteria. Try broadening your search.")
else:
    for _, row in results.iterrows():
        title = row.get("title", "Untitled")
        org = row.get("organization", "Unknown")
        year = row.get("year", "N/A")
        abstract = row.get("abstract", "No abstract available.")
        url = row.get("url", "")
        q_level = row.get("quality_level", "unknown")
        trust = row.get("trust_score", 0)
        score = row.get("relevance_score", 0)

        # Highlight terms in title and abstract if searching
        display_title = (
            SearchEngine.highlight_terms(title, query)
            if query else title
        )
        display_abstract = (
            SearchEngine.highlight_terms(str(abstract), query)
            if query else str(abstract)
        )

        # Card
        with st.container():
            col_main, col_badge = st.columns([5, 1])

            with col_main:
                st.markdown(f"#### {display_title}", unsafe_allow_html=True)
                st.markdown(
                    f"**{org}** · {year} · "
                    f"{quality_badge_html(q_level)} · "
                    f"Trust: {trust_score_bar(trust)}",
                    unsafe_allow_html=True,
                )
                if score > 0:
                    st.caption(f"Relevance: {score:.2f}")

            with col_badge:
                has_md = row.get("has_microdata", False)
                if has_md:
                    st.markdown("🔬 **Microdata**")
                if url:
                    st.markdown(f"[🔗 Source]({url})")

            with st.expander("View details"):
                st.markdown(display_abstract, unsafe_allow_html=True)

                # Resources
                rc = row.get("resource_count_computed", 0)
                rt = row.get("resource_types", [])
                st.markdown(
                    f"**Resources**: {rc} · **Types**: {', '.join(rt) if rt else 'N/A'}"
                )

                # Quality flags
                flags = row.get("quality_flags_list", [])
                if flags:
                    st.markdown(f"**Quality flags**: {', '.join(flags)}")
                else:
                    st.markdown("**Quality flags**: None ✅")

            st.markdown("---")
