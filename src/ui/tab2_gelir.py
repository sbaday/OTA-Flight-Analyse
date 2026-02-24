"""Tab 2 — Gelir Kalitesi: Servis Bedeli Trendi, Havayolu Marj, İç/Dış Hat, Firma Tablo."""

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.config.settings import ACCENT, GRID_COL, PAPER_BG, PLOT_BG, FONT_COL
from src.core.engine import fmt_mil, fmt_pct, pct_delta
from src.ui.components import section_title, chart_info, apply_layout, base_layout


def render_tab2(fdf, df, _py, kpis, py_kpis, yoy,
                sel_airlines, sel_flight, sel_firma, top_n):
    enf_k = yoy['enf_k']

    section_title("💰 Servis Bedeli & Marj Trendi")

    svc = df.copy()
    if sel_airlines: svc = svc[svc['Havayolu'].isin(sel_airlines)]
    if sel_flight:   svc = svc[svc['Uçuş Tipi'].isin(sel_flight)]
    if sel_firma:    svc = svc[svc['Kurumsal Firma'].isin(sel_firma)]
    svc = svc.groupby('Ay_str').agg(
        Hizmet=('Hizmet Tutarı',  lambda x: x.fillna(0).sum()),
        EkSvc=('Ek-Servis',       lambda x: x.fillna(0).sum()),
        Brut=('Brüt Toplam','sum'),
        PNR=('PNR','nunique')
    ).reset_index().sort_values('Ay_str')
    svc['Hizmet%'] = svc['Hizmet'] / svc['Brut'].replace(0,np.nan) * 100
    svc['GerGel']  = svc['Hizmet'] + svc['EkSvc']
    svc['GPnr']    = svc['GerGel'] / svc['PNR'].replace(0,np.nan)

    fig_svc = make_subplots(rows=1, cols=3,
        subplot_titles=["Servis Bedeli Geliri (₺)", "Hizmet/Servis % Trendi",
                        "Net Gelir/PNR Trendi ← KRİTİK"])
    fig_svc.add_trace(go.Bar(x=svc['Ay_str'], y=svc['Hizmet'],
        name='Hizmet Tutarı', marker_color=ACCENT[0], opacity=0.85), row=1, col=1)
    fig_svc.add_trace(go.Bar(x=svc['Ay_str'], y=svc['EkSvc'],
        name='Ek-Servis', marker_color=ACCENT[2], opacity=0.85), row=1, col=1)
    fig_svc.add_trace(go.Scatter(x=svc['Ay_str'], y=svc['Hizmet%'],
        mode='lines+markers', name='Hizmet %',
        line=dict(color=ACCENT[3],width=2), marker=dict(size=6)), row=1, col=2)
    fig_svc.add_trace(go.Scatter(x=svc['Ay_str'], y=svc['GPnr'],
        mode='lines+markers', name='Net Gelir/PNR',
        line=dict(color=ACCENT[4],width=2.5),
        marker=dict(size=7, color=[ACCENT[2] if v>=(svc['GPnr'].mean()) else ACCENT[4]
                                   for v in svc['GPnr']])), row=1, col=3)
    fig_svc.update_layout(paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
        font=dict(color=FONT_COL,family="Inter"), height=300, barmode='stack',
        legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(size=11)),
        margin=dict(l=10,r=10,t=50,b=10),
        hoverlabel=dict(bgcolor="#1e293b",font=dict(color="white",size=12)))
    for j in range(1,4):
        fig_svc.update_xaxes(gridcolor=GRID_COL, tickangle=-30, row=1, col=j)
        fig_svc.update_yaxes(gridcolor=GRID_COL, row=1, col=j)
    st.plotly_chart(fig_svc, use_container_width=True)
    st.caption("↑ Net Gelir/PNR düşüyorsa: komisyon oranı düşmüş, pazarlık gücü azalmış ya da havayolu override bitmiş olabilir.")
    chart_info("Net Gelir/PNR Trendi", [
        "Her bilet işleminden ortalama ne kadar kazanıldığını gösterir.",
        "Düşen trend → pazarlık gücü veya komisyon eriyor.",
        "Yükselen trend → daha karlı segmentlere girilmiş veya fiyat politikası güçlenmiş.",
        "**Aksiyon:** Sürekli düşüş varsa havayolu ile override görüşmesi başlatılabilir.",
    ])

    st.markdown("---")
    col_ha, col_ut = st.columns(2)

    with col_ha:
        section_title("✈️ Havayolu Bazlı Marj (Hizmet %)")
        hv = fdf.groupby('Havayolu').agg(
            PNR=('PNR','nunique'), Brut=('Brüt Toplam','sum'),
            Gelir=('Gerçek Gelir','sum'),
            Hizmet=('Hizmet Tutarı',lambda x: x.fillna(0).sum())
        ).reset_index()
        hv['Svc%']      = hv['Hizmet'] / hv['Brut'].replace(0,np.nan) * 100
        hv['Gelir/PNR'] = hv['Gelir']  / hv['PNR'].replace(0,np.nan)
        hv_top = hv.sort_values('Svc%', ascending=True).head(top_n)  # ascending for horizontal
        # .values kullan — [::-1] sonrası index uyumsuzluğunu önler
        y_vals   = hv_top['Havayolu'].str[:22].values
        x_vals   = hv_top['Svc%'].values
        txt_vals = [f"{v:.2f}%" for v in x_vals]
        cmax     = float(hv['Svc%'].quantile(0.9)) if len(hv) > 1 else 20.0
        fig_hv = go.Figure(go.Bar(
            y=y_vals, x=x_vals, orientation='h',
            marker=dict(color=x_vals, colorscale='RdYlGn', cmin=0, cmax=cmax),
            text=txt_vals, textposition='inside', textfont=dict(size=10)))
        apply_layout(fig_hv, f"Top {top_n} Havayolu — Hizmet %",
                     height=max(320, top_n*27), showlegend=False)
        st.plotly_chart(fig_hv, use_container_width=True)

    with col_ut:
        section_title("🛫 İç Hat vs Dış Hat Karşılaştırması")
        ut = fdf.groupby('Uçuş Tipi').agg(
            PNR=('PNR','nunique'), Brut=('Brüt Toplam','sum'),
            Gelir=('Gerçek Gelir','sum'),
            Hizmet=('Hizmet Tutarı',lambda x: x.fillna(0).sum()),
            Bilet=('Bilet Tutarı',  lambda x: x.fillna(0).mean())
        ).reset_index()
        ut['Svc%']      = ut['Hizmet'] / ut['Brut'].replace(0,np.nan) * 100
        ut['Gelir/PNR'] = ut['Gelir']  / ut['PNR'].replace(0,np.nan)

        # 3 ayrı subplot — farklı ölçekler aynı eksende görüntülenemez
        from plotly.subplots import make_subplots
        fig_ut = make_subplots(rows=1, cols=3,
            subplot_titles=["Gelir/PNR (₺)", "Hizmet %", "Ort. Bilet (₺)"])
        colors = [ACCENT[i % len(ACCENT)] for i in range(len(ut))]
        for i, row in ut.iterrows():
            tip = str(row['Uçuş Tipi'])[:16]
            c   = colors[i % len(colors)]
            fig_ut.add_trace(go.Bar(name=tip, x=[tip], y=[row['Gelir/PNR']],
                marker_color=c, showlegend=(i==0)), row=1, col=1)
            fig_ut.add_trace(go.Bar(name=tip, x=[tip], y=[row['Svc%']],
                marker_color=c, showlegend=False), row=1, col=2)
            fig_ut.add_trace(go.Bar(name=tip, x=[tip], y=[row['Bilet']],
                marker_color=c, showlegend=False), row=1, col=3)
        fig_ut.update_layout(paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
            font=dict(color=FONT_COL, family="Inter"), height=320,
            margin=dict(l=10,r=10,t=50,b=10), barmode='group',
            legend=dict(bgcolor="rgba(0,0,0,0)"))
        for j in range(1, 4):
            fig_ut.update_xaxes(gridcolor=GRID_COL, row=1, col=j)
            fig_ut.update_yaxes(gridcolor=GRID_COL, row=1, col=j)
        st.plotly_chart(fig_ut, use_container_width=True)


    st.markdown("---")
    section_title("🏢 Firma Bazlı Karlılık Tablosu")
    frm2 = fdf.groupby('Kurumsal Firma').agg(
        PNR=('PNR','nunique'), Brut=('Brüt Toplam','sum'),
        Gelir=('Gerçek Gelir','sum'),
        Hizmet=('Hizmet Tutarı',lambda x: x.fillna(0).sum())
    ).reset_index()
    frm2['Svc%']      = frm2['Hizmet'] / frm2['Brut'].replace(0,np.nan) * 100
    frm2['Gelir/PNR'] = frm2['Gelir']  / frm2['PNR'].replace(0,np.nan)
    frm2['Gelir%']    = frm2['Gelir']  / frm2['Gelir'].sum() * 100
    if not _py.empty:
        py_f2 = _py.groupby('Kurumsal Firma')['Gerçek Gelir'].sum().rename('Gelir_PY')
        frm2  = frm2.join(py_f2, on='Kurumsal Firma', how='left')
        frm2['Gelir_PY'] = frm2['Gelir_PY'].fillna(0)
        frm2['Reel%'] = frm2.apply(
            lambda r: ((1+(r['Gelir']-r['Gelir_PY'])/r['Gelir_PY'])/enf_k-1)*100
                      if r['Gelir_PY']>0 else None, axis=1)
    else:
        frm2['Reel%'] = None
    frm2_s = frm2.sort_values('Gelir', ascending=False).head(top_n)
    d2 = frm2_s[['Kurumsal Firma','PNR','Gelir','Svc%','Gelir/PNR','Gelir%','Reel%']].copy()
    d2.columns = ['Firma','PNR','Gerçek Gelir (₺)','Svc%','Gel/PNR','Pay%','Reel YoY']
    d2['Gerçek Gelir (₺)'] = d2['Gerçek Gelir (₺)'].apply(lambda v: f"{v:,.0f}")
    d2['Gel/PNR']          = d2['Gel/PNR'].apply(lambda v: f"{v:,.0f}")
    d2['Svc%']             = d2['Svc%'].apply(lambda v: f"{v:.2f}%")
    d2['Pay%']             = d2['Pay%'].apply(lambda v: f"{v:.1f}%")
    d2['Reel YoY']         = d2['Reel YoY'].apply(
        lambda v: f"{v:+.1f}%" if pd.notna(v) and v is not None else "—")
    st.dataframe(d2, use_container_width=True, hide_index=True)
