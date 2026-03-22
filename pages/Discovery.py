"""
Discovery — Smart search & discovery page.
"""

import textwrap
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
st.markdown("# Smart Discovery")
st.caption("AI-powered semantic search across all studies and abstracts in the NISR catalog")
st.markdown("---")

# ---------------------------------------------------------------------------
# Search bar
# ---------------------------------------------------------------------------
query = st.text_input(
    "Search studies",
    placeholder="e.g. female-headed households, agricultural labour, population census …",
    key="discovery_search",
)

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Filters")

    # Year range
    if "year" in df.columns and df["year"].notna().any():
        min_yr = int(df["year"].min())
        max_yr = int(df["year"].max())
        year_range = st.slider("Year range", min_yr, max_yr, (min_yr, max_yr))
    else:
        year_range = None

    st.markdown("---")

    # Organisation
    orgs = sorted(df["organization"].dropna().unique().tolist())
    selected_orgs = st.multiselect("Organisation", orgs)

    st.markdown("---")

    # Quality level
    selected_quality = st.multiselect(
        "Quality level",
        ["good", "warning", "critical"],
        format_func=lambda x: f"{quality_emoji(x)} {x.title()}",
    )

    st.markdown("---")

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
# Results header with count
# ---------------------------------------------------------------------------
st.markdown("---")

result_count = len(results)
count_label = "study" if result_count == 1 else "studies"
st.markdown(f"### Results ({result_count} {count_label})")

# ---------------------------------------------------------------------------
# Result cards
# ---------------------------------------------------------------------------
if result_count == 0:
    st.info("No studies match your criteria. Try broadening your search or clearing filters.")
else:
    for _, row in results.iterrows():
        title    = row.get("title", "Untitled")
        org      = row.get("organization", "Unknown")
        year     = row.get("year", "N/A")
        abstract = str(row.get("abstract", ""))
        url      = row.get("url", "")
        q_level  = row.get("quality_level", "unknown")
        trust    = row.get("trust_score", 0)
        score    = row.get("relevance_score", 0)
        has_md   = row.get("has_microdata", False)

        display_title    = SearchEngine.highlight_terms(title,    query) if query else title
        display_abstract = SearchEngine.highlight_terms(abstract, query) if query else abstract

        # Short preview of abstract (first 180 chars)
        raw_abstract = abstract.strip()
        if raw_abstract and raw_abstract.lower() != "nan":
            preview = raw_abstract[:180] + ("…" if len(raw_abstract) > 180 else "")
        else:
            preview = ""

        # Build catalog link
        catalog_html = ""
        if url:
            catalog_html = (
                f'<a href="{url}" target="_blank" '
                f'style="color:#60a5fa; font-size:0.8rem; '
                f'text-decoration:none; font-weight:500;">'
                f'View in Catalog &rarr;</a>'
            )

        # Build microdata pill
        microdata_html = ""
        if has_md:
            microdata_html = (
                '<span style="background:rgba(59,130,246,0.12); border:1px solid rgba(59,130,246,0.2); '
                'border-radius:100px; padding:0.15rem 0.6rem; font-size:0.75rem; font-weight:500; '
                'color:#60a5fa; margin-left:0.25rem;">Microdata</span>'
            )

        # Relevance indicator
        relevance_html = ""
        if score > 0:
            pct = min(int(score * 100), 100)
            relevance_html = (
                f'<div style="display:flex; align-items:center; gap:0.5rem; margin-top:0.6rem;">'
                f'<span style="font-size:0.75rem; color:#64748b; min-width:62px;">Relevance</span>'
                f'<div style="flex:1; height:4px; background:rgba(148,163,184,0.12); border-radius:100px; overflow:hidden;">'
                f'<div style="width:{pct}%; height:100%; background:#3b82f6; border-radius:100px;"></div>'
                f'</div>'
                f'<span style="font-size:0.75rem; color:#60a5fa; font-weight:600;">{score:.0%}</span>'
                f'</div>'
            )

        with st.container():
            html_content = f"""<div style="background: rgba(22,32,64,0.75); border: 1px solid rgba(91,147,223,0.15); border-radius: 12px; padding: 1.25rem 1.5rem; margin-bottom: 0.6rem; transition: all 0.2s ease;">
<div style="display:flex; justify-content:space-between; align-items:flex-start; gap:1rem; margin-bottom:0.6rem;">
<div style="margin:0; font-size:1rem; font-weight:600; color:#f1f5f9; line-height:1.4;">{display_title}</div>
<div style="flex-shrink:0;">{catalog_html}</div>
</div>
<div style="display:flex; flex-wrap:wrap; gap:0.6rem; align-items:center; font-size:0.875rem; color:#cbd5e1; margin-bottom:0.6rem;">
<span style="font-weight:500;">{org}</span><span style="color:#94a3b8;">&middot;</span><span>{year}</span><span style="color:#94a3b8;">&middot;</span>
{quality_badge_html(q_level)}
{microdata_html}
</div>
{"<p style='margin:0; font-size:0.875rem; color:#cbd5e1; line-height:1.65;'>" + preview + "</p>" if preview else ""}
{relevance_html}
</div>"""
            if hasattr(st, "html"):
                st.html(html_content)
            else:
                st.markdown(html_content, unsafe_allow_html=True)

            with st.expander("View full details"):
                detail_col, meta_col = st.columns([3, 1], gap="large")

                with detail_col:
                    st.markdown("**Abstract**")
                    if raw_abstract and raw_abstract.lower() != "nan":
                        st.markdown(display_abstract, unsafe_allow_html=True)
                    else:
                        st.markdown("*No abstract available.*")

                with meta_col:
                    st.markdown("**Trust Score**")
                    st.markdown(trust_score_bar(trust))

                    rc  = row.get("resource_count_computed", 0)
                    rts = row.get("resource_types", [])
                    st.markdown("**Resources**")
                    type_str = ", ".join(rts) if rts else "N/A"
                    st.markdown(f"{int(rc)} &middot; {type_str}", unsafe_allow_html=True)

                    flags = row.get("quality_flags_list", [])
                    st.markdown("**Quality Flags**")
                    st.markdown(", ".join(flags) if flags else "None")
