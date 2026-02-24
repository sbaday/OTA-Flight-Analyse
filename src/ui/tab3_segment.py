"""Tab 3 — Segment & Rota: Karlı rotalar, hacimli rotalar, firma tablosu, risk tablosu, scatter."""

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from src.config.settings import ACCENT, GRID_COL, PAPER_BG, PLOT_BG, FONT_COL
from src.core.engine import fmt_mil, fmt_pct, pct_delta
from src.ui.components import section_title, chart_info, apply_layout, base_layout


def render_tab3(fdf, _py, yoy, top_n):
    enf_k = yoy['enf_k']

    section_title("🔎 Stratejik Segment & Rota Analizi")
    rota_df = fdf.dropna(subset=['Rota1','Rota2']).copy()
    rota_df['Rota'] = rota_df['Rota1'].astype(str) + ' → ' + rota_df['Rota2'].astype(str)
    rota_agg = rota_df.groupby('Rota').agg(
        PNR=('PNR','nunique'), Gelir=('Gerçek Gelir','sum'),
        Brut=('Brüt Toplam','sum')
    ).reset_index()
    rota_agg['Gelir/PNR'] = rota_agg['Gelir'] / rota_agg['PNR'].replace(0,np.nan)
    rota_agg['Svc%']      = rota_agg['Gelir'] / rota_agg['Brut'].replace(0,np.nan) * 100

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.markdown("**🏆 En Karlı Rotalar (Gelir/PNR)**")
        top_kar = rota_agg[rota_agg['PNR']>=3].sort_values('Gelir/PNR', ascending=False).head(top_n)
        fig_rk = go.Figure(go.Bar(
            y=top_kar['Rota'][::-1], x=top_kar['Gelir/PNR'][::-1], orientation='h',
            marker=dict(color=top_kar['Svc%'][::-1], colorscale='Viridis',
                        colorbar=dict(title="Svc%", thickness=10)),
            text=[f"{v:,.0f} ₺" for v in top_kar['Gelir/PNR'][::-1]],
            textposition='inside', textfont=dict(size=10)))
        apply_layout(fig_rk, f"En Karlı {top_n} Rota", height=max(320,top_n*27), showlegend=False)
        st.plotly_chart(fig_rk, use_container_width=True)

    with col_r2:
        st.markdown("**📊 En Yüksek Hacimli Rotalar (PNR)**")
        top_vol = rota_agg.sort_values('PNR', ascending=False).head(top_n)
        fig_rv = go.Figure(go.Bar(
            y=top_vol['Rota'][::-1], x=top_vol['PNR'][::-1], orientation='h',
            marker_color=ACCENT[1],
            text=[f"{v:,}" for v in top_vol['PNR'][::-1]],
            textposition='inside', textfont=dict(size=10)))
        apply_layout(fig_rv, f"En Hacimli {top_n} Rota", height=max(320,top_n*27), showlegend=False)
        st.plotly_chart(fig_rv, use_container_width=True)

    st.markdown("---")
    fv = fdf.groupby('Kurumsal Firma').agg(
        PNR=('PNR','nunique'), Brut=('Brüt Toplam','sum'),
        Gelir=('Gerçek Gelir','sum'),
        Hizmet=('Hizmet Tutarı',lambda x: x.fillna(0).sum())
    ).reset_index()
    fv['Svc%']      = fv['Hizmet'] / fv['Brut'].replace(0,np.nan) * 100
    fv['Gelir/PNR'] = fv['Gelir']  / fv['PNR'].replace(0,np.nan)
    fv['Gelir%']    = fv['Gelir']  / fv['Gelir'].sum() * 100
    fv['Kısa']      = fv['Kurumsal Firma'].str[:32]
    if not _py.empty:
        py_fv = _py.groupby('Kurumsal Firma')['Gerçek Gelir'].sum().rename('GPY')
        fv = fv.join(py_fv, on='Kurumsal Firma', how='left')
        fv['GPY']  = fv['GPY'].fillna(0)
        fv['Reel%'] = fv.apply(
            lambda r: ((1+(r['Gelir']-r['GPY'])/r['GPY'])/enf_k-1)*100
                      if r['GPY']>0 else None, axis=1)
    else:
        fv['GPY'] = 0; fv['Reel%'] = None

    col_s3, col_s4 = st.columns(2)
    with col_s3:
        st.markdown("**🏅 En Değerli Müşteriler (Gelir)**")
        top_val = fv.sort_values('Gelir', ascending=False).head(top_n)
        dv = top_val[['Kısa','PNR','Gelir','Svc%','Gelir/PNR','Gelir%','Reel%']].copy()
        dv.columns = ['Firma','PNR','Gerçek Gelir','Svc%','Gel/PNR','Pay%','Reel YoY']
        dv['Gerçek Gelir'] = dv['Gerçek Gelir'].apply(lambda v: f"{v:,.0f} ₺")
        dv['Gel/PNR']      = dv['Gel/PNR'].apply(lambda v: f"{v:,.0f} ₺")
        dv['Svc%']         = dv['Svc%'].apply(lambda v: f"{v:.2f}%")
        dv['Pay%']         = dv['Pay%'].apply(lambda v: f"{v:.1f}%")
        dv['Reel YoY']     = dv['Reel YoY'].apply(
            lambda v: f"{v:+.1f}%" if pd.notna(v) and v is not None else "—")
        st.dataframe(dv, use_container_width=True, hide_index=True)

    with col_s4:
        st.markdown("**⚠️ Risk Tablosu — 2-of-3 Kriter**")
        svc_avg = fv['Svc%'].mean()
        fv['_r1'] = (fv['Gelir%'] > 20).astype(int)
        fv['_r2'] = (fv['Svc%'] < svc_avg).astype(int)
        fv['_r3'] = fv['Reel%'].apply(lambda v: 1 if pd.notna(v) and v < 0 else 0)
        fv['RiskPuan'] = fv['_r1'] + fv['_r2'] + fv['_r3']
        risk_f = fv[fv['RiskPuan'] >= 2].sort_values('RiskPuan', ascending=False).head(top_n)
        if len(risk_f) > 0:
            dr = risk_f[['Kısa','PNR','Gelir','Svc%','Gelir%','Reel%','RiskPuan']].copy()
            dr.columns = ['Firma','PNR','Gelir','Svc%','Pay%','Reel YoY','Risk (/3)']
            dr['Gelir']      = dr['Gelir'].apply(lambda v: f"{v:,.0f} ₺")
            dr['Svc%']       = dr['Svc%'].apply(lambda v: f"{v:.2f}%")
            dr['Pay%']       = dr['Pay%'].apply(lambda v: f"{v:.1f}%")
            dr['Reel YoY']   = dr['Reel YoY'].apply(
                lambda v: f"{v:+.1f}%" if pd.notna(v) and v is not None else "—")
            dr['Risk (/3)']  = dr['Risk (/3)'].apply(
                lambda v: "🔴🔴🔴" if v==3 else "🔴🔴" if v==2 else "🟡")
            st.dataframe(dr, use_container_width=True, hide_index=True)
            st.caption(f"⚠️ Kriter (2-of-3): Pay%>20% | Svc%<ort({svc_avg:.1f}%) | Reel YoY<0%")
        else:
            st.success("✅ 2-of-3 risk kriterini karşılayan firma bulunamadı.")

    st.markdown("---")
    section_title("✈️ Havayolu Marj & Hacim Scatter")
    hv3 = fdf.groupby('Havayolu').agg(
        PNR=('PNR','nunique'), Brut=('Brüt Toplam','sum'),
        Gelir=('Gerçek Gelir','sum'),
        Hizmet=('Hizmet Tutarı',lambda x: x.fillna(0).sum())
    ).reset_index()
    hv3['Svc%']      = hv3['Hizmet'] / hv3['Brut'].replace(0,np.nan) * 100
    hv3['Gelir/PNR'] = hv3['Gelir']  / hv3['PNR'].replace(0,np.nan)
    hv3['Gelir%']    = hv3['Gelir']  / hv3['Gelir'].sum() * 100

    col_sc1, col_sc2 = st.columns(2)
    with col_sc1:
        fig_hvsc = px.scatter(hv3[hv3['PNR']>=5], x='Svc%', y='Gelir/PNR',
                               size='PNR', color='Gelir%', hover_name='Havayolu',
                               color_continuous_scale='RdYlGn', size_max=55,
                               title="Havayolu: Marj % vs Gelir/PNR (boyut=PNR, renk=Pay%)")
        fig_hvsc.update_layout(**base_layout())
        st.plotly_chart(fig_hvsc, use_container_width=True)
    with col_sc2:
        fig_hvtm = px.treemap(hv3[hv3['Gelir']>0], path=['Havayolu'],
                               values='Gelir', color='Svc%',
                               color_continuous_scale='RdYlGn',
                               title="Havayolu Gelir Ağaçharitası (renk=Svc%)")
        fig_hvtm.update_layout(paper_bgcolor=PAPER_BG, margin=dict(l=0,r=0,t=40,b=0),
                                font=dict(color=FONT_COL))
        st.plotly_chart(fig_hvtm, use_container_width=True)
