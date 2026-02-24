"""Tab 1 — Stratejik Özet: KPI'lar, HHI, Aylık Trend, Dönem Karşılaştırması, Büyüme Kaynağı."""

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.config.settings import ACCENT, GRID_COL, PAPER_BG, PLOT_BG, FONT_COL
from src.core.engine import fmt_mil, fmt_pct, pct_delta, yoy_color
from src.ui.components import kpi_card, chart_info, apply_layout, section_title


def render_tab1(fdf, df, _py, kpis, py_kpis, yoy, sel_airlines, sel_flight,
                sel_firma, month_labels, all_months, py_s, py_e,
                start_month, end_month):
    k  = kpis
    pk = py_kpis
    y  = yoy

    total_brut   = k['total_brut']
    total_gercek = k['total_gercek']
    total_pnr    = k['total_pnr']
    total_hizmet = k['total_hizmet']
    avg_bilet    = k['avg_bilet']
    hizmet_pct   = k['hizmet_pct']
    per_pnr      = k['per_pnr']
    gelir_oran   = k['gelir_oran']

    py_gercek    = pk['py_gercek']
    py_pnr       = pk['py_pnr']
    py_brut      = pk['py_brut']
    py_hizmet    = pk['py_hizmet']
    py_hizmet_pct= pk['py_hizmet_pct']
    nominal_yoy  = y['nominal_yoy']
    reel_yoy     = y['reel_yoy']
    enf_k        = y['enf_k']

    from src.config.settings import TUFE_DB
    tufe_end = TUFE_DB.get(end_month, 30.0)

    section_title("📊 Temel KPI'lar")

    c1,c2,c3,c4,c5x = st.columns(5)
    kpi_card(c1,"💰 Brüt Ciro", fmt_mil(total_brut), f"Net Gelir oranı: {gelir_oran:.1f}%")
    kpi_card(c2,"✅ Net Gelir (Op.Brüt)", fmt_mil(total_gercek),
             "Hizmet + Ek-Servis (gider hariç)", "#10b981")
    kpi_card(c3,"📋 Toplam PNR", f"{total_pnr:,}", f"Toplam işlem: {len(fdf):,}")
    kpi_card(c4,"🎫 Ort. Bilet Tutarı",
             f"{avg_bilet:,.0f} ₺" if avg_bilet and not np.isnan(avg_bilet) else "—",
             "Uçuş başı ortalama bilet")
    py_per_pnr = py_gercek / py_pnr if py_pnr else 0
    kpi_card(c5x,"📌 Net Gelir / PNR", fmt_mil(per_pnr),
             f"Önceki yıl: {fmt_mil(py_per_pnr)}" if py_gercek else "Marj kalitesi göstergesi",
             yoy_color(pct_delta(per_pnr, py_per_pnr)))

    st.markdown("")
    c5,c6,c7,c8 = st.columns(4)
    kpi_card(c5,"📈 Hizmet/Servis %", f"{hizmet_pct:.2f}%",
             f"Önceki yıl: {py_hizmet_pct:.2f}%" if py_gercek else "Önceki yıl verisi yok",
             "#10b981" if not py_gercek or hizmet_pct>=py_hizmet_pct else "#ef4444")
    kpi_card(c6,"📊 Nominal Büyüme YoY", fmt_pct(nominal_yoy, plus=True),
             f"{month_labels.get(py_s,'—')} – {month_labels.get(py_e,'—')}", yoy_color(nominal_yoy))
    kpi_card(c7,"💎 Reel Büyüme YoY", fmt_pct(reel_yoy, plus=True),
             f"((1+Nom)/(1+TÜFE%{tufe_end:.1f}))−1", yoy_color(reel_yoy))
    kpi_card(c8,"🔥 TÜFE (Yıllık)", f"{tufe_end:.2f}%", f"{month_labels.get(end_month,'?')} dönemi")

    st.markdown(""); st.markdown("---")

    col_risk, col_trend = st.columns([1,2])

    with col_risk:
        section_title("⚠️ Konsantrasyon Riski + HHI")
        frm_risk = fdf.groupby('Kurumsal Firma')['Gerçek Gelir'].sum().sort_values(ascending=False)
        tgs = frm_risk.sum()
        t3  = frm_risk.head(3).sum()/tgs*100 if tgs else 0
        t5  = frm_risk.head(5).sum()/tgs*100 if tgs else 0
        t10 = frm_risk.head(10).sum()/tgs*100 if tgs else 0
        shares = frm_risk/tgs if tgs else frm_risk
        hhi = float((shares**2).sum())
        hhi_level = "⛔ Yüksek" if hhi>0.25 else ("⚠️ Orta" if hhi>0.15 else "✅ Düşük")
        hhi_color = "#ef4444" if hhi>0.25 else ("#f59e0b" if hhi>0.15 else "#10b981")
        rc  = "#ef4444" if t3>=60 else ("#f59e0b" if t3>=40 else "#10b981")
        rl  = ("⛔ YÜKSEK RİSK — Top 3 cironun %60+" if t3>=60
               else ("⚠️ ORTA RİSK — Konsantre müşteri" if t3>=40
               else "✅ DÜŞÜK RİSK — Çeşitlendirilmiş"))
        st.markdown(f"""<div style="background:linear-gradient(135deg,#1a1d2e,#16213e);
            border-left:4px solid {rc};border-radius:8px;padding:14px 18px">
            <div style="color:{rc};font-weight:700;font-size:13px;margin-bottom:8px">{rl}</div>
            <table style="width:100%;font-size:12px;color:#8892a4">
            <tr><td>Top 3 firma</td><td style="text-align:right;color:{rc};font-weight:700">{t3:.1f}%</td></tr>
            <tr><td>Top 5 firma</td><td style="text-align:right;color:#f59e0b">{t5:.1f}%</td></tr>
            <tr><td>Top 10 firma</td><td style="text-align:right">{t10:.1f}%</td></tr>
            <tr><td>Toplam firma</td><td style="text-align:right">{len(frm_risk):,}</td></tr>
            <tr><td colspan=2 style="padding-top:8px;border-top:1px solid #2a2d3e"></td></tr>
            <tr><td><b>HHI Endeksi</b></td><td style="text-align:right;color:{hhi_color};font-weight:700">{hhi:.4f}</td></tr>
            <tr><td>HHI Seviyesi</td><td style="text-align:right;color:{hhi_color}">{hhi_level}</td></tr>
            <tr><td colspan=2 style="color:#475569;font-size:10px">0.15&lt;orta&lt;0.25&lt;yüksek</td></tr>
            </table></div>""", unsafe_allow_html=True)

    with col_trend:
        section_title("📈 Aylık Gerçek Gelir Trendi")
        trend_all = df.copy()
        if sel_airlines: trend_all = trend_all[trend_all['Havayolu'].isin(sel_airlines)]
        if sel_flight:   trend_all = trend_all[trend_all['Uçuş Tipi'].isin(sel_flight)]
        if sel_firma:    trend_all = trend_all[trend_all['Kurumsal Firma'].isin(sel_firma)]
        ayl = trend_all.groupby('Ay_str').agg(
            Gelir=('Gerçek Gelir','sum'),
            Hizmet=('Hizmet Tutarı', lambda x: x.fillna(0).sum()),
            Brut=('Brüt Toplam','sum')
        ).reset_index().sort_values('Ay_str')
        ayl['Hizmet%'] = ayl['Hizmet'] / ayl['Brut'].replace(0,np.nan) * 100
        fig_ayl = make_subplots(specs=[[{"secondary_y":True}]])
        fig_ayl.add_trace(go.Bar(x=ayl['Ay_str'], y=ayl['Gelir'], name='Gerçek Gelir',
            marker_color=ACCENT[0], opacity=0.8), secondary_y=False)
        fig_ayl.add_trace(go.Scatter(x=ayl['Ay_str'], y=ayl['Hizmet%'], name='Hizmet %',
            mode='lines+markers', line=dict(color=ACCENT[2],width=2), marker=dict(size=5)),
            secondary_y=True)
        apply_layout(fig_ayl, "Gerçek Gelir + Hizmet %", height=280, showlegend=True,
                     legend=dict(orientation='h',y=1.08,bgcolor="rgba(0,0,0,0)"))
        fig_ayl.update_yaxes(gridcolor=GRID_COL, secondary_y=False)
        fig_ayl.update_yaxes(gridcolor=GRID_COL, secondary_y=True,
                              title_text="Hizmet %", tickformat=".1f")
        st.plotly_chart(fig_ayl, use_container_width=True)
        chart_info("Aylık Net Gelir Trendi", [
            "Çubuklar aylık kazancı, çizgi hizmet ücretlerinin oranını gösterir.",
            "Çizgi yükselde → hizmet kalitesi veya eklenti satışı artıyor.",
            "Çubuk düşüp çizgi düşüyorsa iki taraflı baskı var: hem ciro hem marj eriyor.",
            "**Aksiyon:** Çizgi düşerse hizmet fiyatlandırması gözden geçirilmeli.",
        ])

    st.markdown("---")
    section_title("📋 Dönem Karşılaştırma Tablosu")
    rows_yoy = []
    lbl_cur = f"{month_labels.get(start_month,'?')}–{month_labels.get(end_month,'?')}"
    lbl_py  = f"{month_labels.get(py_s,'—')}–{month_labels.get(py_e,'—')}"
    for lbl, cur, prev, fn in [
        ("Net Gelir (Op.Brüt)", total_gercek, py_gercek, lambda v: fmt_mil(v)),
        ("Brüt Ciro",           total_brut,   py_brut,   lambda v: fmt_mil(v)),
        ("Hizmet Tutarı",       total_hizmet, py_hizmet, lambda v: fmt_mil(v)),
        ("Hizmet %",            hizmet_pct,   py_hizmet_pct, lambda v: f"{v:.2f}%"),
        ("Toplam PNR",          total_pnr,    py_pnr,    lambda v: f"{v:,.0f}"),
        ("Net Gelir/PNR",       per_pnr,      py_per_pnr,lambda v: fmt_mil(v)),
    ]:
        d = pct_delta(cur, prev)
        rows_yoy.append({"Metrik": lbl, lbl_cur: fn(cur),
                          lbl_py: fn(prev) if prev else "—",
                          "Fark (%)": fmt_pct(d, plus=True),
                          "📊": "🟢" if d and d>2 else ("🔴" if d and d<-2 else "🟡") if d else "—"})
    st.dataframe(pd.DataFrame(rows_yoy), use_container_width=True, hide_index=True)

    if nominal_yoy is not None and py_pnr and py_per_pnr:
        st.markdown("---")
        section_title("🔬 Büyüme Kaynağı: Hacim vs Fiyat/Marj Etkisi")
        pnr_effect  = pct_delta(total_pnr, py_pnr) or 0
        gpnr_effect = pct_delta(per_pnr, py_per_pnr) or 0
        _bg1, _bg2  = st.columns([2,1])
        with _bg1:
            _items = ["Hacim Etkisi (ΔPnr %)", "Fiyat/Marj Etkisi (ΔGelir/PNR %)", "Toplam Nominal YoY %"]
            _vals  = [pnr_effect, gpnr_effect, nominal_yoy or 0]
            _cols  = [ACCENT[0] if pnr_effect>=0 else "#ef4444",
                      ACCENT[2] if gpnr_effect>=0 else "#ef4444",
                      ACCENT[1] if (nominal_yoy or 0)>=0 else "#ef4444"]
            fig_bg = go.Figure(go.Bar(x=_items, y=_vals, marker_color=_cols,
                text=[f"{v:+.1f}%" for v in _vals], textposition='outside',
                textfont=dict(size=13, color=FONT_COL)))
            apply_layout(fig_bg, "Büyüme Kaynağı Analizi", height=280, showlegend=False,
                         yaxis=dict(tickformat="+.1f", gridcolor=GRID_COL,
                                    zeroline=True, zerolinecolor="#475569"))
            st.plotly_chart(fig_bg, use_container_width=True)
            chart_info("Büyüme Kaynağı", [
                "Büyüme neden oldu? Daha fazla müşteri mi vardı, yoksa her müşteriden mi daha fazla kazanıldı?",
                "Hacim Etkisi: PNR (işlem) sayısının değişimi — büyüme hacimden mi geliyor?",
                "Fiyat/Marj Etkisi: İşlem başına kazancın değişimi — daha mı karlı satış yapılıyor?",
                "**Risk:** Hacim artarken marj düşüyorsa büyüme sürdürülemez.",
            ])
        with _bg2:
            _dom = "Hacim" if abs(pnr_effect) > abs(gpnr_effect) else "Fiyat/Marj"
            st.markdown(
                f"**Büyümenin kaynağı: {_dom} Etkisi**\n\n"
                f"• PNR artışı: **{pnr_effect:+.1f}%**\n"
                f"• Gelir/PNR değişimi: **{gpnr_effect:+.1f}%**\n\n"
                f"{'✅ Hem hacim hem marj artıyorsa ideal büyüme.' if pnr_effect>0 and gpnr_effect>0 else '⚠️ Ciro artarken marj düşüyorsa büyüme zararlı olabilir.' if pnr_effect>0 and gpnr_effect<0 else ''}"
            )
