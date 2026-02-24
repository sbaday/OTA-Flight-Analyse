"""Tab 4 — Reel Büyüme: TÜFE'den arındırılmış dönemsel analiz."""

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from src.config.settings import ACCENT, GRID_COL, FONT_COL, TUFE_DB
from src.core.engine import fmt_mil, fmt_pct
from src.ui.components import kpi_card, apply_layout


def render_tab4(df, sel_airlines, sel_flight, sel_firma, all_months, month_labels):
    st.markdown('<div class="section-title">📐 Enflasyondan Arındırılmış Reel Büyüme Analizi</div>',
                unsafe_allow_html=True)
    st.markdown("---")
    col_rg1, col_rg2 = st.columns(2)
    with col_rg1:
        st.markdown("**📅 Baz Dönem**")
        baz_ay = st.selectbox("Baz Ay", all_months,
                               index=all_months.index("2025-02") if "2025-02" in all_months else 1,
                               format_func=lambda x: month_labels[x], key="rg_baz")
        baz_metric = st.selectbox("Metrik",
                                   ["Gerçek Gelir (Hizmet+Ek)","Brüt Toplam","Hizmet Tutarı"],
                                   key="rg_baz_met")
    with col_rg2:
        st.markdown("**📅 Karşılaştırma Dönemi**")
        kars_ay = st.selectbox("Karşılaştırma Ayı", all_months,
                                index=all_months.index("2026-02") if "2026-02" in all_months else len(all_months)-1,
                                format_func=lambda x: month_labels[x], key="rg_kars")
        st.markdown(f"*Metrik: {baz_metric}*")

    st.markdown("---")
    col_t1, col_t2 = st.columns([2,1])
    with col_t1:
        auto_tufe = st.toggle("TÜİK verisi otomatik kullan", value=True)
    with col_t2:
        tufe_val = TUFE_DB.get(kars_ay, None)
        if auto_tufe:
            if tufe_val:
                st.metric("TÜİK TÜFE", f"%{tufe_val:.2f}")
            else:
                st.warning("Bu ay DB'de yok, otomatik kullanılamıyor.")
                tufe_val = 30.0
        else:
            tufe_val = st.number_input("Manuel TÜFE %", 0.0, 200.0,
                                        value=float(tufe_val or 30.0), step=0.1)

    def get_ay_ciro(ay, metric):
        d = df[df['Ay_str']==ay].copy()
        if sel_airlines: d = d[d['Havayolu'].isin(sel_airlines)]
        if sel_flight:   d = d[d['Uçuş Tipi'].isin(sel_flight)]
        if sel_firma:    d = d[d['Kurumsal Firma'].isin(sel_firma)]
        if metric=="Gerçek Gelir (Hizmet+Ek)": return d['Gerçek Gelir'].sum()
        if metric=="Brüt Toplam":              return d['Brüt Toplam'].sum()
        return d['Hizmet Tutarı'].fillna(0).sum()

    baz_ciro  = get_ay_ciro(baz_ay,  baz_metric)
    kars_ciro = get_ay_ciro(kars_ay, baz_metric)

    if baz_ciro > 0 and tufe_val:
        ek       = 1 + tufe_val/100
        nominal  = (kars_ciro - baz_ciro) / baz_ciro
        reel     = (1+nominal)/ek - 1
        beklenen = baz_ciro * ek
        reel_ciro= kars_ciro / ek

        def reel_renk(r):
            if r > 2:     return "#10b981","▲","Reel Büyüme Var ✅"
            elif r < -2:  return "#ef4444","▼","Reel Daralma Var ⚠️"
            else:         return "#f59e0b","→","Yerinde Sayma 〰️"

        st.markdown("### 📊 Büyüme Göstergeleri")
        n1,n2,n3 = st.columns(3)
        nc = "#10b981" if nominal>=0 else "#ef4444"
        rc,ri,ry = reel_renk(reel*100)
        kpi_card(n1,"📈 Nominal Büyüme", f"{nominal*100:+.2f}%", "Enflasyonsuz ham artış", nc)
        kpi_card(n2,"🔥 Enflasyon (TÜFE)", f"{tufe_val:.2f}%", f"Yıllık — {month_labels[kars_ay]}", "#f59e0b")
        kpi_card(n3,"💎 Reel Büyüme", f"{reel*100:+.2f}%", f"{ri} {ry}", rc)

        st.markdown("")
        st.markdown("### 🧮 Hesaplama Adımları")
        fc1,fc2 = st.columns(2)
        with fc1:
            st.markdown(f"""| Adım | Formül | Sonuç |
|------|--------|-------|
|**1. Nominal**|(Yeni−Eski)/Eski|**{nominal*100:+.2f}%**|
|**2. Enflasyon Katsayısı**|1+({tufe_val:.2f}/100)|**{ek:.4f}**|
|**3. Beklenen Ciro**|Baz×Katsayı|**{beklenen:,.0f} ₺**|
|**4. Reel Büyüme**|(1+Nom)/Kat−1|**{reel*100:+.2f}%**|
|**5. Reel Ciro**|Yeni/Katsayı|**{reel_ciro:,.0f} ₺**|""")
        with fc2:
            st.markdown(f"""| Metrik | Değer |
|--------|-------|
|Baz Dönem|{month_labels[baz_ay]}|
|Karşılaştırma|{month_labels[kars_ay]}|
|Baz Ciro|{baz_ciro:,.0f} ₺|
|Yeni Ciro|{kars_ciro:,.0f} ₺|
|Enflasyon Beklentisi|{beklenen:,.0f} ₺|
|Reel Ciro (Baz fiyat)|{reel_ciro:,.0f} ₺|""")

        st.markdown("### 📊 Ciro Karşılaştırması")
        wf_x = [f"Baz\n{month_labels[baz_ay]}","Enflasyon\nBekl.",
                f"Gerçek\n{month_labels[kars_ay]}","Reel Ciro\n(Baz fiyat)"]
        wf_y = [baz_ciro, beklenen, kars_ciro, reel_ciro]
        wf_c = [ACCENT[0],"#f59e0b",
                "#10b981" if kars_ciro>=beklenen else "#ef4444", rc]
        fig_wf = go.Figure(go.Bar(x=wf_x, y=wf_y, marker_color=wf_c,
            text=[f"{v/1e6:.2f}M ₺" for v in wf_y],
            textposition='outside', textfont=dict(size=12,color=FONT_COL)))
        fig_wf.add_hline(y=beklenen, line_dash="dash", line_color="#f59e0b",
                          line_width=1.5, annotation_text="Enflasyon Eşiği",
                          annotation_font_color="#f59e0b")
        apply_layout(fig_wf, f"{month_labels[baz_ay]} vs {month_labels[kars_ay]}", showlegend=False)
        st.plotly_chart(fig_wf, use_container_width=True)

        st.markdown("### 🎯 Stratejik Yorum")
        if reel > 0.02:
            yc,yb = "#10b981","✅ Reel Büyüme Tespit Edildi"
            yt = (f"• Nominal büyüme (%{nominal*100:.1f}) enflasyonun (%{tufe_val:.1f}) **üzerinde**.\n"
                  f"• Reel ciro baz döneme göre **{reel*100:.1f} puan** büyümüş.\n"
                  "• **Aksiyon:** Mevcut strateji sürdürülebilir.")
        elif reel < -0.02:
            yc,yb = "#ef4444","⚠️ Reel Daralma Tespit Edildi"
            yt = (f"• Nominal büyüme (%{nominal*100:.1f}) enflasyonun (%{tufe_val:.1f}) **altında** kalmış.\n"
                  "• Service fee marjı baskı altında olabilir.\n"
                  "• **Aksiyon:** Fee yapısı ve müşteri segmentleri gözden geçirilmeli.")
        else:
            yc,yb = "#f59e0b","〰️ Yerinde Sayma"
            yt = (f"• Nominal (%{nominal*100:.1f}) ≈ Enflasyon (%{tufe_val:.1f}) — reel büyüme yok.\n"
                  "• **Aksiyon:** Enflasyon üzeri büyüme için fee revizyonu değerlendirilebilir.")
        st.markdown(f"""<div style="background:linear-gradient(135deg,#1a1d2e,#16213e);
            border-left:4px solid {yc};border-radius:8px;padding:16px 20px;margin-top:8px">
            <div style="color:{yc};font-weight:700;font-size:15px;margin-bottom:8px">{yb}</div>
            <div style="color:#c9d1d9;font-size:13px;line-height:1.8">{yt.replace(chr(10),'<br>')}</div>
            <div style="color:#475569;font-size:11px;margin-top:12px">
            ⚙️ Reel Büyüme = ((1+Nominal)/Enflasyon Katsayısı)−1 &nbsp;|&nbsp;
            TÜFE: %{tufe_val:.2f} &nbsp;|&nbsp; Manipülasyona kapalı</div></div>""",
            unsafe_allow_html=True)
    else:
        st.warning("Baz dönem için veri bulunamadı. Farklı ay/filtre seçin.")
