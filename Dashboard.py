"""
Dashboard.py — Streamlit Cloud entry point.
Minimal: page config + CSS, veri yükleme, sidebar, filtreler, tab çağrıları.
İş mantığı src/core/, veri src/services/, UI src/ui/ içindedir.
"""

import warnings
import pandas as pd
import streamlit as st

warnings.filterwarnings('ignore')

# ── Sayfa Ayarları ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Flight Revenue Intelligence",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
from src.config.settings import APP_CSS
st.markdown(f"<style>{APP_CSS}</style>", unsafe_allow_html=True)

# ── Veri Yükleme ──────────────────────────────────────────────────────────────
from src.services.data_loader import load_data
df = load_data()
all_months   = sorted(df['Ay_str'].dropna().unique().tolist())
month_labels = {m: pd.to_datetime(m).strftime('%b %Y') for m in all_months}

# ── Sidebar Filtreleri ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ✈️ Flight Revenue")
    st.markdown("**Intelligence Dashboard v2.0**")
    st.markdown("---")
    st.markdown("### 📅 Dönem")
    c1s, c2s = st.columns(2)
    with c1s:
        start_month = st.selectbox("Başlangıç", all_months, index=0,
                                   format_func=lambda x: month_labels[x])
    with c2s:
        end_month = st.selectbox("Bitiş", all_months, index=len(all_months)-1,
                                 format_func=lambda x: month_labels[x])
    st.markdown("---")
    st.markdown("### 🏢 Kurumsal Firma")
    sel_firma = st.multiselect("(boş = hepsi)",
                               sorted(df['Kurumsal Firma'].dropna().unique()),
                               default=[], key="firma_filter")
    st.markdown("---")
    st.markdown("### ✈️ Havayolu")
    sel_airlines = st.multiselect("(boş = hepsi)",
                                  sorted(df['Havayolu'].dropna().unique()), default=[])
    st.markdown("---")
    st.markdown("### 🛫 Uçuş Tipi")
    sel_flight = st.multiselect("(boş = hepsi)",
                                sorted(df['Uçuş Tipi'].dropna().unique()), default=[])
    st.markdown("---")
    st.markdown("### 🔢 Gösterim")
    top_n = st.slider("Top N", 5, 30, 15)
    st.markdown("---")
    st.caption(f"📊 {len(df):,} kayıt | {month_labels[all_months[0]]} – {month_labels[all_months[-1]]}")

# ── Filtrele ──────────────────────────────────────────────────────────────────
fdf = df[(df['Ay_str'] >= start_month) & (df['Ay_str'] <= end_month)].copy()
if sel_airlines: fdf = fdf[fdf['Havayolu'].isin(sel_airlines)]
if sel_flight:   fdf = fdf[fdf['Uçuş Tipi'].isin(sel_flight)]
if sel_firma:    fdf = fdf[fdf['Kurumsal Firma'].isin(sel_firma)]

# ── Core Hesaplamalar (global state yok — her şey fonksiyon çıktısı) ──────────
from src.core.engine import (
    compute_kpis, compute_prev_year, compute_yoy, shift_year,
)
from src.config.settings import TUFE_DB

kpis   = compute_kpis(fdf)
py_s   = shift_year(start_month)
py_e   = shift_year(end_month)
_py, py_kpis = compute_prev_year(
    df, py_s, py_e, sel_airlines, sel_flight, sel_firma, all_months
)
tufe_end = TUFE_DB.get(end_month, 30.0)
yoy      = compute_yoy(kpis, py_kpis, tufe_end)

# ── Başlık ────────────────────────────────────────────────────────────────────
st.markdown("## ✈️ Flight Revenue Intelligence Dashboard v2.0")
st.markdown(
    f"**Dönem:** {month_labels[start_month]} – {month_labels[end_month]}  |  "
    f"**Kayıt:** {len(fdf):,}  |  "
    f"**Filtreler:** {'Havayolu:' + ','.join(sel_airlines[:2]) if sel_airlines else 'Tüm Havayolları'}"
    f"{' | Firma:' + ','.join([f[:12] for f in sel_firma[:2]]) if sel_firma else ''}"
)

# ── Sekmeler ──────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Özet",
    "💰 Gelir Kalitesi",
    "🔎 Segment & Rota",
    "📐 Reel Büyüme",
    "🔄 Müşteri Dinamiği",
    "✈️ Havayolu Stratejisi",
    "📦 Marj Kalitesi",
])

from src.ui.tab1_ozet    import render_tab1
from src.ui.tab2_gelir   import render_tab2
from src.ui.tab3_segment import render_tab3
from src.ui.tab4_reel    import render_tab4
from src.ui.tab5_musteri import render_tab5
from src.ui.tab6_havayolu import render_tab6
from src.ui.tab7_marj    import render_tab7

with tab1:
    render_tab1(fdf, df, _py, kpis, py_kpis, yoy,
                sel_airlines, sel_flight, sel_firma,
                month_labels, all_months, py_s, py_e)
with tab2:
    render_tab2(fdf, df, _py, kpis, py_kpis, yoy,
                sel_airlines, sel_flight, sel_firma, top_n)
with tab3:
    render_tab3(fdf, _py, yoy, top_n)
with tab4:
    render_tab4(df, sel_airlines, sel_flight, sel_firma, all_months, month_labels)
with tab5:
    render_tab5(fdf, df, _py, yoy, start_month, month_labels)
with tab6:
    render_tab6(fdf, _py, yoy, top_n)
with tab7:
    render_tab7(fdf, top_n)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "✈️ Flight Revenue Intelligence Dashboard v2.0 | "
    "Gerçek Gelir = Hizmet Tutarı + Ek-Servis | "
    "Net Gelir (Op.Brüt) = Hizmet+Ek-Servis, gider dahil değil | "
    "Reel Büyüme: ((1+Nominal)/TÜFE Katsayısı)−1"
)
