"""Tab 5 — Müşteri Dinamiği: Cohort analizi, retention, aylık yeni vs mevcut."""

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

from src.config.settings import ACCENT
from src.core.engine import fmt_mil, fmt_pct, pct_delta, yoy_color
from src.ui.components import kpi_card, chart_info, section_title, apply_layout


def render_tab5(fdf, df, _py, yoy, start_month, month_labels):
    enf_k = yoy['enf_k']

    section_title("🔄 Müşteri Dinamiği — Cohort Analizi")

    ilk_islem = df.groupby('Kurumsal Firma')['Satış Tarihi'].min().reset_index()
    ilk_islem.columns = ['Kurumsal Firma','IlkIslem']
    ilk_islem['IlkAy'] = ilk_islem['IlkIslem'].dt.strftime('%Y-%m')

    fdf_c = fdf.merge(ilk_islem[['Kurumsal Firma','IlkAy']], on='Kurumsal Firma', how='left')
    fdf_c['Cohort'] = fdf_c['IlkAy'].apply(
        lambda x: 'Yeni Müşteri' if pd.notna(x) and x >= start_month else 'Mevcut Müşteri')

    yeni_df   = fdf_c[fdf_c['Cohort'] == 'Yeni Müşteri']
    mevcut_df = fdf_c[fdf_c['Cohort'] == 'Mevcut Müşteri']
    yeni_gelir   = yeni_df['Gerçek Gelir'].sum()
    mevcut_gelir = mevcut_df['Gerçek Gelir'].sum()
    toplam_c     = yeni_gelir + mevcut_gelir
    yeni_pnr   = yeni_df['PNR'].nunique()
    mevcut_pnr = mevcut_df['PNR'].nunique()
    yeni_frm   = yeni_df['Kurumsal Firma'].nunique()
    mevcut_frm = mevcut_df['Kurumsal Firma'].nunique()
    yeni_gpnr   = yeni_gelir   / yeni_pnr   if yeni_pnr   else 0
    mevcut_gpnr = mevcut_gelir / mevcut_pnr if mevcut_pnr else 0

    py_firms  = set(_py['Kurumsal Firma'].dropna().unique()) if not _py.empty else set()
    cur_firms = set(fdf['Kurumsal Firma'].dropna().unique())
    retained  = py_firms & cur_firms
    churned   = py_firms - cur_firms
    retention_rate = len(retained) / len(py_firms) * 100 if py_firms else None

    mevcut_py_gelir = 0
    if not _py.empty:
        mevcut_py_gelir = _py[_py['Kurumsal Firma'].isin(
            mevcut_df['Kurumsal Firma'])]['Gerçek Gelir'].sum()
    mevcut_reel = None
    if mevcut_py_gelir:
        _m_nom = pct_delta(mevcut_gelir, mevcut_py_gelir)
        if _m_nom is not None:
            mevcut_reel = ((1 + _m_nom/100) / enf_k - 1) * 100

    section_title("📊 Cohort KPI'ları")
    ka, kb, kc, kd, ke = st.columns(5)
    yeni_pay = yeni_gelir / toplam_c * 100 if toplam_c else 0
    kpi_card(ka,'🆕 Yeni Gelir', fmt_mil(yeni_gelir),
             f"%{yeni_pay:.1f} pay | {yeni_frm} firma", ACCENT[2])
    kpi_card(kb,'🏛️ Mevcut Gelir', fmt_mil(mevcut_gelir),
             f"%{100-yeni_pay:.1f} pay | {mevcut_frm} firma", ACCENT[0])
    kpi_card(kc,'🆕 Yeni Gel/PNR', fmt_mil(yeni_gpnr),
             f"Mevcut: {fmt_mil(mevcut_gpnr)}",
             "#10b981" if yeni_gpnr >= mevcut_gpnr else "#f59e0b")
    ret_color = ("#10b981" if retention_rate and retention_rate >= 70
                 else "#ef4444" if retention_rate and retention_rate < 50 else "#f59e0b")
    kpi_card(kd,'🔄 Retention',
             f"{retention_rate:.1f}%" if retention_rate is not None else "—",
             f"{len(retained):,} aktif / {len(churned)} kaybedildi", ret_color)
    kpi_card(ke,'📉 Mevcut Reel YoY',
             fmt_pct(mevcut_reel, plus=True) if mevcut_reel is not None else "—",
             "Mevcut portföy reel büyümesi", yoy_color(mevcut_reel))

    st.markdown(""); st.markdown("---")
    col_c1, col_c2 = st.columns([3,2])
    with col_c1:
        section_title("📊 Aylık Gelir: Yeni vs Mevcut")
        ayl_coh = fdf_c.groupby(['Ay_str','Cohort'])['Gerçek Gelir'].sum().reset_index()
        fig_coh = px.bar(ayl_coh, x='Ay_str', y='Gerçek Gelir', color='Cohort',
                          barmode='stack',
                          color_discrete_map={'Yeni Müşteri':ACCENT[2], 'Mevcut Müşteri':ACCENT[0]},
                          labels={'Ay_str':'Ay','Gerçek Gelir':'Gelir (₺)'})
        apply_layout(fig_coh,'Aylık Cohort Gelir', height=300,
                     legend=dict(orientation='h',y=1.05,bgcolor='rgba(0,0,0,0)'))
        st.plotly_chart(fig_coh, use_container_width=True)
        chart_info("Yeni vs Mevcut Müşteri Geliri", [
            "Her ay kazanılan gelirin yeni ve eski müşterilerden gelen payını gösterir.",
            "Mavi dilim büyüyorsa mevcut müşteri sadık ve büyüyor.",
            "Yeşil (yeni) dilim baskın olursa büyüme yeni müşteriye bağımlı — riskli.",
            "**Aksiyon:** Yeni müşteri payı %50+ ise mevcut müşteri koruma programı devreye alınmalı.",
        ])

    with col_c2:
        section_title("🔄 Retention Durumu")
        if py_firms:
            st.markdown(f"""<div style="background:linear-gradient(135deg,#1a1d2e,#16213e);
border-left:4px solid {ret_color};border-radius:8px;padding:14px 18px">
<div style="color:{ret_color};font-weight:700;font-size:13px;margin-bottom:8px">
{'✅ Güçlü Retention' if (retention_rate or 0)>=70 else '⚠️ Orta' if (retention_rate or 0)>=50 else '⛔ Zayıf Retention'}
</div>
<table style="width:100%;font-size:12px;color:#8892a4">
<tr><td>Geçen yıl aktif</td><td style="text-align:right">{len(py_firms):,}</td></tr>
<tr><td>Bu yıl devam</td><td style="text-align:right;color:#10b981;font-weight:600">{len(retained):,}</td></tr>
<tr><td>Churn (kaybedilen)</td><td style="text-align:right;color:#ef4444;font-weight:600">{len(churned):,}</td></tr>
<tr><td>Retention</td><td style="text-align:right;color:{ret_color};font-weight:700">{retention_rate:.1f}%</td></tr>
<tr><td>Yeni müşteri</td><td style="text-align:right;color:{ACCENT[2]}">{yeni_frm:,}</td></tr>
</table>
<div style="color:#475569;font-size:10px;margin-top:8px">
{'✅ Yeni kazanım churnu karşılıyor' if yeni_frm >= len(churned) else '⚠️ Churn > Yeni kazanım'}
</div></div>""", unsafe_allow_html=True)
        else:
            st.info("Önceki yıl verisi olmadan retention hesaplanamıyor.")

    st.markdown("---")
    section_title("📈 Cohort Bazında Net Gelir/PNR Trendi")
    gpnr_t = fdf_c.groupby(['Ay_str','Cohort']).agg(
        Gelir=('Gerçek Gelir','sum'), PNR=('PNR','nunique')).reset_index()
    gpnr_t['GPnr'] = gpnr_t['Gelir'] / gpnr_t['PNR'].replace(0,np.nan)
    import plotly.express as px2
    fig_gp = px.line(gpnr_t, x='Ay_str', y='GPnr', color='Cohort', markers=True,
                      color_discrete_map={'Yeni Müşteri':ACCENT[2],'Mevcut Müşteri':ACCENT[0]},
                      labels={'Ay_str':'Ay','GPnr':'Net Gelir/PNR (₺)'})
    fig_gp.update_traces(line=dict(width=2.5), marker=dict(size=8))
    apply_layout(fig_gp,'Cohort Bazında Net Gelir/PNR', height=280,
                 legend=dict(orientation='h',y=1.05,bgcolor='rgba(0,0,0,0)'))
    st.plotly_chart(fig_gp, use_container_width=True)
    st.caption("Mevcut müşteri Gelir/PNR düşüyorsa: pazarlık gücü erozyonu. "
               "Yeni müşteri düşüyorsa: prim müşteri çekişi yok.")

    st.markdown("---")
    section_title("🏢 Firma Cohort Tablosu (Top N)")
    frm_coh = fdf_c.groupby(['Kurumsal Firma','Cohort','IlkAy']).agg(
        PNR=('PNR','nunique'), Gelir=('Gerçek Gelir','sum'),
        Hizmet=('Hizmet Tutarı', lambda x: x.fillna(0).sum())
    ).reset_index()
    brut_map = fdf_c.groupby('Kurumsal Firma')['Brüt Toplam'].sum().rename('Brut')
    frm_coh  = frm_coh.join(brut_map, on='Kurumsal Firma')
    frm_coh['Svc%']    = frm_coh['Hizmet'] / frm_coh['Brut'].replace(0,np.nan) * 100
    frm_coh['Gel/PNR'] = frm_coh['Gelir']  / frm_coh['PNR'].replace(0,np.nan)
    frm_s = frm_coh.sort_values('Gelir', ascending=False).head(20)
    dfc = frm_s[['Kurumsal Firma','Cohort','IlkAy','PNR','Gelir','Svc%','Gel/PNR']].copy()
    dfc.columns = ['Firma','Segment','İlk Ay','PNR','Gelir (₺)','Svc%','Gel/PNR']
    dfc['Gelir (₺)'] = dfc['Gelir (₺)'].apply(lambda v: f"{v:,.0f}")
    dfc['Svc%']      = dfc['Svc%'].apply(lambda v: f"{v:.2f}%")
    dfc['Gel/PNR']   = dfc['Gel/PNR'].apply(lambda v: f"{v:,.0f}")
    st.dataframe(dfc, use_container_width=True, hide_index=True)

    st.markdown("---")
    if retention_rate is not None:
        _yc = ret_color
        if retention_rate >= 70 and yeni_pay < 40:
            _bt = "✅ Sürdürülebilir Büyüme"
            _oz = (f"• Retention {retention_rate:.0f}% — mevcut müşteri sağlam.\n"
                   f"• Yeni müşteri payı %{yeni_pay:.0f} — portföy genişliyor.\n"
                   "• Aksiyon: Mevcut müşteride derinleş, yeni kazanımı koru.")
        elif yeni_pay >= 50:
            _bt = "⚠️ Büyüme Yeni Müşteriye Bağlı"
            _oz = (f"• Gelirin %{yeni_pay:.0f}'i yeni müşteriden geliyor.\n"
                   f"• Mevcut müşteri reel büyüme: {fmt_pct(mevcut_reel, plus=True)}\n"
                   "• Aksiyon: Mevcut müşteri koruma programları devreye al.")
        elif retention_rate < 50:
            _bt = "⛔ Kritik: Yüksek Churn"
            _oz = (f"• Geçen yıl aktif firmaların %{100-retention_rate:.0f}'i kaybedildi.\n"
                   "• Acil müşteri iletişim ve nedensel analiz gerekiyor.\n"
                   "• Aksiyon: Churned firmalar aranmalı, geri kazanım planlanmalı.")
        else:
            _bt = "🟡 Karma Durum"
            _oz = f"• Retention {retention_rate:.0f}%, Yeni pay %{yeni_pay:.0f} — denge izlenmeli."
        st.markdown(f"""<div style="background:linear-gradient(135deg,#1a1d2e,#16213e);
            border-left:4px solid {_yc};border-radius:8px;padding:16px 20px">
            <div style="color:{_yc};font-weight:700;font-size:15px;margin-bottom:8px">{_bt}</div>
            <div style="color:#c9d1d9;font-size:13px;line-height:1.9">{_oz.replace(chr(10),'<br>')}</div>
            </div>""", unsafe_allow_html=True)
