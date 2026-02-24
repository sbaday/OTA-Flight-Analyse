"""
Paylaşılan Streamlit / Plotly UI yardımcı fonksiyonları.
Yalnızca render eder; iş mantığı veya veri işleme içermez.
"""

import streamlit as st
import plotly.graph_objects as go

from src.config.settings import (
    PLOT_BG, PAPER_BG, FONT_COL, GRID_COL,
)


# ── KPI Kartı ─────────────────────────────────────────────────────────────────

def kpi_card(col, label: str, val: str, sub: str, color: str = "#e2e8f0") -> None:
    """Koyu arka planlı KPI metric kartı render eder."""
    with col:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="label">{label}</div>'
            f'<div class="value" style="color:{color}">{val}</div>'
            f'<div class="sub">{sub}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ── Grafik Bilgi Expander ──────────────────────────────────────────────────────

def chart_info(title: str, lines: list[str]) -> None:
    """Grafik altına 'nasıl okunur' açıklama expander'ı ekler."""
    with st.expander(f"ℹ️ {title} — nasıl okunur?", expanded=False):
        for ln in lines:
            st.markdown(f"- {ln}")


# ── Plotly Layout Sabitleri ───────────────────────────────────────────────────

def base_layout(title: str = "") -> dict:
    """Tüm grafikler için ortak Plotly layout dict'i döndürür."""
    return dict(
        title=dict(text=title, font=dict(color=FONT_COL, size=14)),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(color=FONT_COL, family="Inter"),
        xaxis=dict(gridcolor=GRID_COL, linecolor=GRID_COL, tickfont=dict(size=11)),
        yaxis=dict(gridcolor=GRID_COL, linecolor=GRID_COL, tickfont=dict(size=11)),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
        margin=dict(l=10, r=10, t=45, b=10),
        hoverlabel=dict(bgcolor="#1e293b", font=dict(color="white", size=12)),
    )


def apply_layout(fig: go.Figure, title: str = "", **extra) -> None:
    """base_layout + extra parametreleri birleştirerek fig'e uygular."""
    lo = base_layout(title)
    lo.update(extra)
    fig.update_layout(**lo)


# ── Section Başlığı ───────────────────────────────────────────────────────────

def section_title(text: str) -> None:
    """Stillendirilmiş bölüm başlığı render eder."""
    st.markdown(
        f'<div class="section-title">{text}</div>',
        unsafe_allow_html=True,
    )
