"""Tab 6 — Havayolu Stratejik Performans: Reel YoY, scatter, tablo, uyarılar, trend."""

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from src.config.settings import ACCENT, GRID_COL, FONT_COL
from src.core.engine import fmt_mil, fmt_pct, pct_delta
from src.ui.components import kpi_card, chart_info, section_title, apply_layout, base_layout


def render_tab6(fdf, _py, yoy, top_n):
    enf_k = yoy['enf_k']

    section_title("✈️ Havayolu Stratejik Performans — Tedarikçi Karlılığı")

    hva = fdf.groupby('Havayolu').agg(
        PNR=('PNR','nunique'), Brut=('Brüt Toplam','sum'),
        Gelir=('Gerçek Gelir','sum'),
        Hizmet=('Hizmet Tutarı', lambda x: x.fillna(0).sum())
    ).reset_index()
    hva['Svc%']    = hva['Hizmet'] / hva['Brut'].replace(0,np.nan) * 100
    hva['Gel/PNR'] = hva['Gelir']  / hva['PNR'].replace(0,np.nan)
    hva['Pay%']    = hva['Gelir']  / hva['Gelir'].sum() * 100
    avg_gpnr_hv    = hva['Gel/PNR'].mean()

    if not _py.empty:
        hva_py = _py.groupby('Havayolu').agg(
            Gelir_PY=('Gerçek Gelir','sum'), PNR_PY=('PNR','nunique'),
            Hizmet_PY=('Hizmet Tutarı', lambda x: x.fillna(0).sum()),
            Brut_PY=('Brüt Toplam','sum')
        ).reset_index()
        hva = hva.merge(hva_py, on='Havayolu', how='left')
        hva['Gelir_PY'] = hva['Gelir_PY'].fillna(0)
        hva['PNR_PY']   = hva['PNR_PY'].fillna(0)
        hva['GPnr_PY']  = hva['Gelir_PY'] / hva['PNR_PY'].replace(0,np.nan)
        hva['Svc_PY%']  = (hva['Hizmet_PY'].fillna(0) /
                           hva['Brut_PY'].replace(0,np.nan).fillna(np.nan) * 100)
        hva['Nom_YoY']  = hva.apply(
            lambda r: pct_delta(r['Gelir'], r['Gelir_PY']) if r['Gelir_PY']>0 else None, axis=1)
        hva['Reel_YoY'] = hva['Nom_YoY'].apply(
            lambda n: ((1+n/100)/enf_k-1)*100 if pd.notna(n) else None)
    else:
        hva['Gelir_PY'] = 0; hva['Nom_YoY'] = None
        hva['Reel_YoY'] = None; hva['GPnr_PY'] = None

    hva['_r1'] = (hva['Pay%'] > 25).astype(int)
    hva['_r2'] = hva['Reel_YoY'].apply(lambda v: 1 if pd.notna(v) and v<0 else 0)
    hva['_r3'] = (hva['Gel/PNR'] < avg_gpnr_hv).astype(int)
    hva['RiskPuan'] = hva['_r1'] + hva['_r2'] + hva['_r3']

    hv_shares = hva['Pay%'] / 100
    hhi_hv    = float((hv_shares**2).sum())
    hhi_hv_lv = "⛔ Yüksek" if hhi_hv>0.25 else ("⚠️ Orta" if hhi_hv>0.15 else "✅ Düşük")
    hhi_hv_c  = "#ef4444" if hhi_hv>0.25 else ("#f59e0b" if hhi_hv>0.15 else "#10b981")
    t3_hv     = hva.nlargest(3,'Gelir')['Pay%'].sum()
    hva_reel  = hva.dropna(subset=['Reel_YoY'])
    best_hv   = hva_reel.loc[hva_reel['Reel_YoY'].idxmax()] if len(hva_reel) else None
    worst_hv  = hva_reel.loc[hva_reel['Reel_YoY'].idxmin()] if len(hva_reel) else None

    section_title("📊 Havayolu KPI'ları")
    hk1,hk2,hk3,hk4,hk5 = st.columns(5)
    kpi_card(hk1,'🏆 En İyi Reel YoY',
             best_hv['Havayolu'][:18] if best_hv is not None else "—",
             f"Reel: {fmt_pct(best_hv['Reel_YoY'] if best_hv is not None else None, plus=True)}",
             "#10b981")
    worst_color = ("#ef4444" if worst_hv is not None and worst_hv['Pay%']>25
                   and (worst_hv['Reel_YoY'] or 0)<0 else "#f59e0b")
    kpi_card(hk2,'⚠️ Riskli Havayolu',
             worst_hv['Havayolu'][:18] if worst_hv is not None else "—",
             (f"Pay%{worst_hv['Pay%']:.0f} | Reel:{fmt_pct(worst_hv['Reel_YoY'] if worst_hv is not None else None)}"
              if worst_hv is not None else "Veri yok"),
             worst_color)
    kpi_card(hk3,'📌 Ort. Gel/PNR', fmt_mil(avg_gpnr_hv), "Havayolu ortalaması")
    kpi_card(hk4,'🔗 HHI (Havayolu)', f"{hhi_hv:.4f}", f"{hhi_hv_lv} tedarikçi riski", hhi_hv_c)
    kpi_card(hk5,'🎯 Top 3 HV Payı', f"{t3_hv:.1f}%", "İlk 3 havayolunun gelir payı",
             "#ef4444" if t3_hv>70 else ("#f59e0b" if t3_hv>50 else "#10b981"))

    st.markdown(""); st.markdown("---")
    col_rg1, col_rg2 = st.columns(2)
    with col_rg1:
        section_title("💎 Havayolu Reel Büyüme (YoY)")
        hva_plot = hva[hva['Reel_YoY'].notna()].sort_values('Reel_YoY', ascending=True)
        if len(hva_plot):
            colors_r = ["#10b981" if v>=0 else "#ef4444" for v in hva_plot['Reel_YoY']]
            fig_reel = go.Figure(go.Bar(
                y=hva_plot['Havayolu'].str[:20], x=hva_plot['Reel_YoY'],
                orientation='h', marker_color=colors_r,
                text=[f"{v:+.1f}%" for v in hva_plot['Reel_YoY']],
                textposition='outside', textfont=dict(size=10,color=FONT_COL)))
            fig_reel.add_vline(x=0, line_color="#475569", line_width=1)
            apply_layout(fig_reel,"Havayolu Reel YoY Büyüme",
                         height=max(300,len(hva_plot)*32), showlegend=False)
            st.plotly_chart(fig_reel, use_container_width=True)
            chart_info("Havayolu Reel Büyüme", [
                "Enflasyon çıkarıldıktan sonra her havayolunun gerçekte ne kadar büyüdüğünü gösterir.",
                "Yeşil çubuk → enflasyonun üzerinde büyüme.",
                "Kırmızı çubuk → enflasyonun altında: nominal büyüse de satın alma gücü eridi.",
                "**Aksiyon:** Kırmızı + büyük pay = en acil tedarikçi pazarlık önceliği.",
            ])
        else:
            st.info("Önceki yıl verisi olmadan reel büyüme hesaplanamıyor.")

    with col_rg2:
        section_title("📊 Gelir Payı vs Svc%")
        fig_pay = px.scatter(hva[hva['PNR']>=3], x='Pay%', y='Svc%', size='PNR',
                              color='Reel_YoY', hover_name='Havayolu',
                              color_continuous_scale='RdYlGn', color_continuous_midpoint=0,
                              size_max=55, title="Pay% vs Svc% (boyut=PNR, renk=Reel YoY)")
        fig_pay.update_layout(**base_layout())
        st.plotly_chart(fig_pay, use_container_width=True)

    st.markdown("---")
    section_title("📋 Havayolu Stratejik Performans Tablosu")
    hva_tbl = hva.sort_values('Gelir', ascending=False).head(top_n)
    disp_hv = hva_tbl[['Havayolu','PNR','Gelir','Pay%','Svc%','Gel/PNR',
                         'Nom_YoY','Reel_YoY','RiskPuan']].copy()
    disp_hv.columns = ['Havayolu','PNR','Gelir (₺)','Pay%','Svc%','Gel/PNR','Nom YoY','Reel YoY','Risk(/3)']
    disp_hv['Gelir (₺)'] = disp_hv['Gelir (₺)'].apply(lambda v: f"{v:,.0f}")
    disp_hv['Pay%']      = disp_hv['Pay%'].apply(lambda v: f"{v:.1f}%")
    disp_hv['Svc%']      = disp_hv['Svc%'].apply(lambda v: f"{v:.2f}%")
    disp_hv['Gel/PNR']   = disp_hv['Gel/PNR'].apply(lambda v: f"{v:,.0f}")
    disp_hv['Nom YoY']   = disp_hv['Nom YoY'].apply(
        lambda v: f"{v:+.1f}%" if pd.notna(v) and v is not None else "—")
    disp_hv['Reel YoY']  = disp_hv['Reel YoY'].apply(
        lambda v: f"{v:+.1f}%" if pd.notna(v) and v is not None else "—")
    disp_hv['Risk(/3)']  = disp_hv['Risk(/3)'].apply(
        lambda v: "🔴🔴🔴" if v==3 else "🔴🔴" if v==2 else ("🟡" if v==1 else "✅"))
    st.dataframe(disp_hv, use_container_width=True, hide_index=True)
    st.caption(f"⚠️ Risk (2-of-3): Pay%>25% | Reel YoY<0% | Gel/PNR<ort({avg_gpnr_hv:,.0f}₺)")

    st.markdown("---")
    section_title("🎯 Stratejik Uyarılar & Aksiyon Noktaları")
    alerts = []
    for _, r in hva[(hva['Pay%']>25)&(hva['Reel_YoY'].notna())&(hva['Reel_YoY']<0)].iterrows():
        alerts.append(("⛔","#ef4444",
            f"**{r['Havayolu']}** — %{r['Pay%']:.0f} paya sahip ancak reel büyüme **{r['Reel_YoY']:+.1f}%**. "
            "Pahallanan bir tedarikçiye bağımlılık var. Alternatif değerlendirilmeli."))
    for _, r in hva[(hva['Pay%']<15)&(hva['Reel_YoY'].notna())&(hva['Reel_YoY']>10)].iterrows():
        alerts.append(("🚀","#10b981",
            f"**{r['Havayolu']}** — Küçük pay (%{r['Pay%']:.0f}) ama reel büyüme **{r['Reel_YoY']:+.1f}%**. "
            "Büyütülmesi gereken kârlı tedarikçi."))
    for _, r in hva[(hva['Pay%']>15)&(hva['Gel/PNR']<avg_gpnr_hv*0.7)].iterrows():
        alerts.append(("⚠️","#f59e0b",
            f"**{r['Havayolu']}** — Fazla gelir payı (%{r['Pay%']:.0f}) ancak Gel/PNR "
            f"**{r['Gel/PNR']:,.0f}₺** ortalama altında ({avg_gpnr_hv:,.0f}₺). Düşük marjlı yoğunluk."))
    if hhi_hv > 0.25:
        alerts.append(("⛔","#ef4444",
            f"**Tedarikçi HHI {hhi_hv:.4f}** — Yüksek konsantrasyon. Tek havayolu riski porföyü tehdit edebilir."))
    if alerts:
        for icon, color, msg in alerts:
            st.markdown(f"""<div style="background:linear-gradient(135deg,#1a1d2e,#16213e);
                border-left:4px solid {color};border-radius:8px;padding:12px 18px;margin:6px 0">
                <span style="font-size:16px">{icon}</span>&nbsp;
                <span style="color:#c9d1d9;font-size:13px">{msg}</span>
                </div>""", unsafe_allow_html=True)
    else:
        st.success("✅ Kritik uyarı yok. Havayolu portföyü dengeli görünüyor.")

    st.markdown("---")
    section_title("📈 Top Havayolu Aylık Gelir Trendi")
    top5_hv = hva.nlargest(5,'Gelir')['Havayolu'].tolist()
    trend_hv = (fdf[fdf['Havayolu'].isin(top5_hv)]
                .groupby(['Ay_str','Havayolu'])['Gerçek Gelir'].sum().reset_index())
    fig_trend_hv = px.line(trend_hv, x='Ay_str', y='Gerçek Gelir', color='Havayolu',
                            markers=True, color_discrete_sequence=ACCENT,
                            labels={'Ay_str':'Ay','Gerçek Gelir':'Gelir (₺)'})
    fig_trend_hv.update_traces(line=dict(width=2), marker=dict(size=6))
    apply_layout(fig_trend_hv, f"Top {len(top5_hv)} Havayolu Aylık Gelir",
                 height=300, legend=dict(orientation='h',y=1.05,bgcolor='rgba(0,0,0,0)'))
    st.plotly_chart(fig_trend_hv, use_container_width=True)
