"""Tab 7 — Marj Kalitesi: Firma Svc% dağılımı, boxplot, scatter strateji haritası, uyarılar."""

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from src.config.settings import ACCENT, GRID_COL, FONT_COL
from src.core.engine import fmt_mil
from src.ui.components import kpi_card, chart_info, section_title, apply_layout


def render_tab7(fdf, top_n):
    section_title("📦 Firma Marj Kalitesi — Operasyon Disiplin Analizi")

    fdf_m = fdf.copy()
    fdf_m['Row_Svc%'] = (fdf_m['Hizmet Tutarı'].fillna(0) /
                          fdf_m['Brüt Toplam'].replace(0, np.nan) * 100)

    def iqr_range(x):
        return x.quantile(0.75) - x.quantile(0.25)

    frm_m = fdf_m.groupby('Kurumsal Firma').agg(
        PNR=('PNR','nunique'), Gelir=('Gerçek Gelir','sum'),
        Brut=('Brüt Toplam','sum'), AvgSvc=('Row_Svc%','mean'),
        MedSvc=('Row_Svc%','median'), StdSvc=('Row_Svc%','std'),
        MinSvc=('Row_Svc%','min'), MaxSvc=('Row_Svc%','max'),
        IQR=('Row_Svc%', iqr_range), N=('Row_Svc%','count')
    ).reset_index()
    frm_m['Pay%']    = frm_m['Gelir'] / frm_m['Gelir'].sum() * 100
    frm_m['StdSvc']  = frm_m['StdSvc'].fillna(0)

    genel_avg = frm_m['AvgSvc'].mean()
    genel_med = frm_m['MedSvc'].median()
    genel_std = frm_m['StdSvc'].mean()
    dusuk_pct = (frm_m['AvgSvc'] < genel_avg).sum() / len(frm_m) * 100 if len(frm_m) else 0

    frm_m['_o1'] = (frm_m['AvgSvc'] < genel_avg).astype(int)
    frm_m['_o2'] = (frm_m['Pay%'] > 15).astype(int)
    frm_m['_o3'] = (frm_m['StdSvc'] > genel_std * 1.5).astype(int)
    frm_m['OpsRisk'] = frm_m['_o1'] + frm_m['_o2'] + frm_m['_o3']

    section_title("📊 Operasyon KPI'ları")
    ok1,ok2,ok3,ok4,ok5 = st.columns(5)
    kpi_card(ok1,'💰 Ortalama Marj', f"{genel_avg:.2f}%", "Genel operasyon seviyesi")
    kpi_card(ok2,'⚖️ Medyan Marj', f"{genel_med:.2f}%", "Aykırılardan arındırılmış",
             "#10b981" if genel_med >= genel_avg else "#f59e0b")
    kpi_card(ok3,'📉 Düşük Marj %', f"{dusuk_pct:.1f}%",
             f"Ort altı firma oranı ({(frm_m['AvgSvc']<genel_avg).sum()} firma)",
             "#ef4444" if dusuk_pct>50 else "#f59e0b")
    top3_avg = frm_m.nlargest(3,'AvgSvc')['AvgSvc'].mean()
    kpi_card(ok4,'🔥 Top 3 Ortalama Marj', f"{top3_avg:.2f}%" if len(frm_m) else "—",
             "En karlı 3 firmanın marj ort.", "#10b981")
    kpi_card(ok5,'🎯 Marj Varyansı (σ)', f"{genel_std:.2f}%",
             "Yüksek = fiyat disiplinsizliği",
             "#ef4444" if genel_std>5 else ("#f59e0b" if genel_std>2 else "#10b981"))

    st.markdown(""); st.markdown("---")
    section_title("📦 Firma Svc% Dağılımı — Boxplot")
    top_frm_names = (frm_m[frm_m['N']>=5]
                     .sort_values('Gelir', ascending=False)
                     .head(top_n)['Kurumsal Firma'].tolist())
    if top_frm_names:
        box_data  = fdf_m[fdf_m['Kurumsal Firma'].isin(top_frm_names)].copy()
        med_order = (box_data.groupby('Kurumsal Firma')['Row_Svc%']
                     .median().sort_values(ascending=False).index.tolist())
        fig_box = go.Figure()
        for firma in med_order:
            if firma not in top_frm_names: continue
            fd = box_data[box_data['Kurumsal Firma']==firma]['Row_Svc%'].dropna()
            risk_vals = frm_m.loc[frm_m['Kurumsal Firma']==firma,'OpsRisk'].values
            r_val = int(risk_vals[0]) if len(risk_vals) else 0
            box_color = "#ef4444" if r_val>=2 else ("#f59e0b" if r_val==1 else "#3b82f6")
            fig_box.add_trace(go.Box(
                y=fd, name=firma[:26], boxmean='sd', marker_color=box_color,
                line=dict(color=box_color, width=1.5),
                fillcolor=('rgba(239,68,68,0.18)' if r_val>=2
                           else 'rgba(245,158,11,0.18)' if r_val==1
                           else 'rgba(59,130,246,0.18)'),
                showlegend=False,
                hovertemplate=f"<b>{firma[:26]}</b><br>Svc%%: %%{{y:.2f}}%%<extra></extra>"))
        apply_layout(fig_box, f"Top {top_n} Firma — Svc% Dağılımı (kırmızı=risk≥2)",
                     height=max(380,top_n*28),
                     yaxis=dict(title="Svc%", gridcolor=GRID_COL, zeroline=False),
                     showlegend=False)
        fig_box.add_hline(y=genel_avg, line_dash="dot", line_color="#f59e0b", opacity=0.7,
                          annotation_text=f"ort {genel_avg:.1f}%",
                          annotation_font=dict(color="#f59e0b",size=11))
        st.plotly_chart(fig_box, use_container_width=True)
        chart_info("Firma Svc% Boxplot", [
            "Her kutucuk, o firmadan yapılan tüm işlemlerin hizmet ücreti dağılımını gösterir.",
            "**İnce kutu** → tutarlı fiyat politikası.",
            "**Geniş kutu** → fiyatlar rastgele değişiyor, standart yok.",
            "**Aşağı çıkıntı** → o firmaya çok düşük/sıfır hizmet ücreti uygulanmış işlem var.",
            "**Aksiyon:** Geniş kutulu büyük firmalar için minimum hizmet ücreti limiti belirlenmeli.",
        ])
    else:
        st.info("Yeterli veri yok (min 5 işlem/firma).")

    st.markdown("---")
    col_sc1, col_sc2 = st.columns([3,2])
    with col_sc1:
        section_title("📊 Gelir vs Marj Scatter (Strateji Haritası)")
        sc = frm_m[frm_m['N']>=3].copy()
        sc['FirmaK']  = sc['Kurumsal Firma'].str[:22]
        sc['RiskLbl'] = sc['OpsRisk'].apply(
            lambda v: "⛔ Yüksek Risk" if v>=2 else ("⚠️ Orta" if v==1 else "✅ Sağlıklı"))
        color_map = {"✅ Sağlıklı":"#10b981","⚠️ Orta":"#f59e0b","⛔ Yüksek Risk":"#ef4444"}
        fig_sc = px.scatter(sc, x='Gelir', y='AvgSvc', size='PNR', color='RiskLbl',
                             hover_name='FirmaK', color_discrete_map=color_map, size_max=50,
                             labels={'Gelir':'Net Gelir (₺)','AvgSvc':'Ort. Svc%','RiskLbl':'Risk'},
                             custom_data=['FirmaK','PNR','Pay%','StdSvc'])
        fig_sc.update_traces(
            hovertemplate="<b>%{customdata[0]}</b><br>"
                          "Gelir: %{x:,.0f}₺<br>"
                          "Svc%: %{y:.2f}%<br>"
                          "PNR: %{customdata[1]}<br>"
                          "Pay%: %{customdata[2]:.1f}%<br>"
                          "σ: %{customdata[3]:.2f}%<extra></extra>")
        fig_sc.add_hline(y=genel_avg, line_dash="dot", line_color="#f59e0b", opacity=0.6)
        fig_sc.update_layout(paper_bgcolor='#0f1117', plot_bgcolor='#0f1117',
                             font=dict(color=FONT_COL,family="Inter"),
                             hoverlabel=dict(bgcolor="#1e293b",font=dict(color="white",size=12)),
                             legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(size=11)),
                             height=400, margin=dict(l=10,r=10,t=30,b=10))
        fig_sc.update_xaxes(gridcolor=GRID_COL, tickformat=",.0f")
        fig_sc.update_yaxes(gridcolor=GRID_COL, tickformat=".1f")
        st.plotly_chart(fig_sc, use_container_width=True)
        chart_info("Gelir vs Marj Haritası", [
            "Her nokta bir firma: yatay eksen ciroyu, dikey eksen hizmet ücretini gösterir.",
            "**Sağ-üst köşe** → büyük ve karlı: ilişki derinleştirilmeli.",
            "**Sağ-alt köşe** → büyük ama düşük marjlı: acil hizmet ücreti revizyonu.",
            "**Sol-üst köşe** → küçük ama karlı: büyütülebilecek altın segment.",
        ])

    with col_sc2:
        section_title("🚨 Operasyon Risk Tablosu")
        risk_ops = frm_m[frm_m['OpsRisk']>=2].sort_values('OpsRisk', ascending=False).head(top_n)
        if len(risk_ops):
            dr_ops = risk_ops[['Kurumsal Firma','PNR','AvgSvc','StdSvc','Pay%','OpsRisk']].copy()
            dr_ops.columns = ['Firma','PNR','Avg Svc%','σ Svc%','Pay%','Risk(/3)']
            dr_ops['Avg Svc%'] = dr_ops['Avg Svc%'].apply(lambda v: f"{v:.2f}%")
            dr_ops['σ Svc%']   = dr_ops['σ Svc%'].apply(lambda v: f"{v:.2f}%")
            dr_ops['Pay%']     = dr_ops['Pay%'].apply(lambda v: f"{v:.1f}%")
            dr_ops['Risk(/3)'] = dr_ops['Risk(/3)'].apply(
                lambda v: "🔴🔴🔴" if v==3 else "🔴🔴" if v==2 else "🟡")
            st.dataframe(dr_ops, use_container_width=True, hide_index=True)
            st.caption(f"Kriter(2-of-3): AvgSvc<{genel_avg:.1f}% | Pay%>15% | σ>ort×1.5")
        else:
            st.success("✅ 2-of-3 operasyon riskini karşılayan firma yok.")

    st.markdown("---")
    section_title("🎯 Operasyon Stratejik Uyarıları")
    ops_alerts = []
    for _, r in frm_m[(frm_m['Pay%']>15)&(frm_m['AvgSvc']<genel_avg)].iterrows():
        ops_alerts.append(("⚠️","#f59e0b",
            f"**{r['Kurumsal Firma'][:30]}** — %{r['Pay%']:.0f} pay, "
            f"ancak avg marj **{r['AvgSvc']:.2f}%** (ort {genel_avg:.2f}%). Servis fee revizyonu gerekiyor."))
    for _, r in frm_m[(frm_m['StdSvc']>genel_std*2)&(frm_m['Pay%']>10)].iterrows():
        ops_alerts.append(("⛔","#ef4444",
            f"**{r['Kurumsal Firma'][:30]}** — σ={r['StdSvc']:.2f}% (ort {genel_std:.2f}%). "
            "Fiyat disiplini düşük. Minimum marj politikası uygulanmalı."))
    for _, r in frm_m[(frm_m['Pay%']<10)&(frm_m['AvgSvc']>genel_avg*1.5)&(frm_m['N']>=5)].iterrows():
        ops_alerts.append(("🚀","#10b981",
            f"**{r['Kurumsal Firma'][:30]}** — Küçük pay (%{r['Pay%']:.0f}) ama yüksek marj "
            f"**{r['AvgSvc']:.2f}%**. Büyütülebilecek kaliteli segment."))
    if ops_alerts:
        for icon, color, msg in ops_alerts[:8]:
            st.markdown(f"""<div style="background:linear-gradient(135deg,#1a1d2e,#16213e);
                border-left:4px solid {color};border-radius:8px;padding:11px 16px;margin:5px 0">
                <span style="font-size:15px">{icon}</span>&nbsp;
                <span style="color:#c9d1d9;font-size:13px">{msg}</span>
                </div>""", unsafe_allow_html=True)
    else:
        st.success("✅ Kritik operasyon uyarısı yok. Marj dağılımı dengeli.")

    st.markdown("---")
    section_title("🏆 En Karlı Firmalar (Avg Svc% Sıralaması)")
    col_tbl1, col_tbl2 = st.columns(2)
    top_karli_n = min(10, len(frm_m))
    for col, label, ascending in [(col_tbl1,"🥇 En Yüksek Marjlı Firmalar",False),
                                   (col_tbl2,"🔻 En Düşük Marjlı Firmalar (min 3 işlem)",True)]:
        with col:
            st.markdown(f"**{label}**")
            subset = frm_m[frm_m['N']>=3]
            tbl = (subset.nsmallest(top_karli_n,'AvgSvc') if ascending
                   else subset.nlargest(top_karli_n,'AvgSvc'))
            tbl = tbl[['Kurumsal Firma','PNR','AvgSvc','StdSvc','Pay%','Gelir']].copy()
            tbl.columns = ['Firma','PNR','Avg Svc%','σ','Pay%','Gelir (₺)']
            tbl['Avg Svc%'] = tbl['Avg Svc%'].apply(lambda v: f"{v:.2f}%")
            tbl['σ']        = tbl['σ'].apply(lambda v: f"{v:.2f}%")
            tbl['Pay%']     = tbl['Pay%'].apply(lambda v: f"{v:.1f}%")
            tbl['Gelir (₺)']= tbl['Gelir (₺)'].apply(lambda v: f"{v:,.0f}")
            st.dataframe(tbl, use_container_width=True, hide_index=True)
    st.caption("σ = Standart sapma. Yüksek σ → fiyat tutarsızlığı. Min 3 işlem filtresi uygulandı.")

    st.markdown("---")
    section_title("📊 Svc% Genel Dağılımı (tüm işlemler)")
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Histogram(
        x=fdf_m['Row_Svc%'].dropna(), nbinsx=50, name='İşlem Dağılımı',
        marker_color=ACCENT[0], opacity=0.8,
        hovertemplate="Svc%%: %{x:.1f}%%<br>Adet: %{y}<extra></extra>"))
    fig_hist.add_vline(x=genel_avg, line_dash="solid", line_color="#f59e0b",
                       annotation_text=f"ort {genel_avg:.1f}%",
                       annotation_font=dict(color="#f59e0b",size=11))
    fig_hist.add_vline(x=genel_med, line_dash="dot", line_color="#10b981",
                       annotation_text=f"med {genel_med:.1f}%",
                       annotation_font=dict(color="#10b981",size=11))
    apply_layout(fig_hist,"Tüm İşlemler Svc% Frekans Dağılımı", height=260, showlegend=False,
                 xaxis=dict(title="Svc%",gridcolor=GRID_COL),
                 yaxis=dict(title="İşlem Sayısı",gridcolor=GRID_COL))
    st.plotly_chart(fig_hist, use_container_width=True)
    st.caption("Sağ kuyruk = yüksek marjlı nadir işlemler. Sol kuyruk = zararına veya çok düşük marjlı işlemler.")
