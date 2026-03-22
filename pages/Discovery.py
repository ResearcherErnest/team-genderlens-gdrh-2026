"""
Discovery — Smart search & discovery page.
"""

from pathlib import Path

import streamlit as st

from src.filters import apply_filters
from src.pipeline.ingestion import load_all
from src.pipeline.quality import compute_quality_scores
from src.pipeline.transform import transform
from src.quality_badges import quality_badge_html, quality_emoji, trust_score_bar
from src.search_engine import SearchEngine

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Discovery — GenderLens RW",
    page_icon="🔍",
    layout="wide",
)

css_path = Path(__file__).resolve().parents[1] / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading data …")
def get_data():
    studies, resources, quality = load_all()
    df = transform(studies, resources, quality)
    return compute_quality_scores(df)


df = get_data()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("# 🔍 Smart Discovery")
st.caption("AI-powered semantic search across all studies and abstracts in the NISR catalog")
st.markdown("---")

# ---------------------------------------------------------------------------
# Search bar (prominent, full-width)
# ---------------------------------------------------------------------------
query = st.text_input(
    "Search studies",
    placeholder="e.g. female-headed households, agricultural labour, population census …",
    key="discovery_search",
    label_visibility="collapsed",
)

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🔧 Filters")

    # Year range
    if "year" in df.columns and df["year"].notna().any():
        min_yr = int(df["year"].min())
        max_yr = int(df["year"].max())
        year_range = st.slider("Year range", min_yr, max_yr, (min_yr, max_yr))
    else:
        year_range = None

    # Organisation
    orgs = sorted(df["organization"].dropna().unique().tolist())
    selected_orgs = st.multiselect("Organisation", orgs)

    # Quality level
    selected_quality = st.multiselect(
        "Quality level",
        ["good", "warning", "critical"],
        format_func=lambda x: f"{quality_emoji(x)} {x.title()}",
    )

    # Microdata
    microdata_filter = st.radio(
        "Microdata availability",
        ["All", "With microdata", "Without microdata"],
    )
    has_microdata = (
        True  if microdata_filter == "With microdata" else
        False if microdata_filter == "Without microdata" else
        None
    )

# ---------------------------------------------------------------------------
# Search + filter pipeline
# ---------------------------------------------------------------------------
engine = SearchEngine(df)
results = engine.search(query)
results = apply_filters(
    results,
    year_range=year_range if year_range else None,
    organizations=selected_orgs or None,
    quality_levels=selected_quality or None,
    has_microdata=has_microdata,
)

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
st.markdown(f"### Results &nbsp;·&nbsp; {len(results)} {'study' if len(results)==1 else 'studies'}", unsafe_allow_html=True)

if len(results) == 0:
    st.info("No studies match your criteria. Try broadening your search or clearing filters.")
else:
    for _, row in results.iterrows():
        title    = row.get("title", "Untitled")
        org      = row.get("organization", "Unknown")
        year     = row.get("year", "N/A")
        abstract = str(row.get("abstract", "No abstract available."))
        url      = row.get("url", "")
        q_level  = row.get("quality_level", "unknown")
        trust    = row.get("trust_score", 0)
        score    = row.get("relevance_score", 0)
        has_md   = row.get("has_microdata", False)

        display_title    = SearchEngine.highlight_terms(title,    query) if query else title
        display_abstract = SearchEngine.highlight_terms(abstract, query) if query else abstract

        with st.container():
            st.markdown(
                f"""
                <div class="glass-card" style="padding:1.25rem 1.5rem;margin-bottom:0.75rem;">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;">
                        <div style="flex:1;">
                            <h4 style="margin:0 0 0.4rem;font-size:1.05rem;color:#E2E8F0;">
                                {display_title}
                            </h4>
                            <div style="display:flex;flex-wrap:wrap;gap:0.5rem;align-items:center;font-size:0.85rem;color:#94A3B8;">
                                <span>🏛️ {org}</span>
                                <span>·</span>
                                <span>📅 {year}</span>
                                <span>·</span>
                                {quality_badge_html(q_level)}
                                {"<span>·</span><span style='color:#3498DB;font-weight:600;'>📦 Microdata</span>" if has_md else ""}
                                {f'<span>·</span><span style="color:#64A7E5;">Relevance: {score:.2f}</span>' if score > 0 else ""}
                            </div>
                        </div>
                        <div style="flex:0 0 auto;">
                            {f'<a href="{url}" target="_blank" style="color:#3498DB;font-size:0.8rem;">🔗 Catalog</a>' if url else ""}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.expander("View details & abstract"):
                col_abs, col_meta = st.columns([3, 1], gap="large")

                with col_abs:
                    st.markdown("**Abstract**")
                    st.markdown(display_abstract, unsafe_allow_html=True)

                with col_meta:
                    st.markdown("**Trust Score**")
                    st.markdown(trust_score_bar(trust))

                    rc  = row.get("resource_count_computed", 0)
                    rts = row.get("resource_types", [])
                    st.markdown("**Resources**")
                    st.markdown(f"{int(rc)} · {', '.join(rts) if rts else 'N/A'}")

                    flags = row.get("quality_flags_list", [])
                    st.markdown("**Quality Flags**")
                    st.markdown(", ".join(flags) if flags else "None ✅")
