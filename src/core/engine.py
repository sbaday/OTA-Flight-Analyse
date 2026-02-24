"""
Core hesaplama motoru.
Streamlit, IO veya global state bağımlılığı yoktur.
Tüm fonksiyonlar saf Python / Pandas / NumPy'dır.
"""

import numpy as np
import pandas as pd
from src.config.settings import TUFE_DB


# ── Formatlama Yardımcıları ────────────────────────────────────────────────────

def fmt_mil(v) -> str:
    """Sayıyı ₺ ile birlikte K/M formatında döndürür."""
    v = float(v or 0)
    if abs(v) >= 1e6:
        return f"{v/1e6:.2f}M ₺"
    if abs(v) >= 1e3:
        return f"{v/1e3:.1f}K ₺"
    return f"{v:,.0f} ₺"


def pct_delta(new_val, old_val):
    """İki değer arasındaki yüzde değişimini döndürür; bölme hatasında None."""
    return (new_val - old_val) / abs(old_val) * 100 if old_val else None


def fmt_pct(v, plus: bool = False) -> str:
    """Yüzde değerini biçimli string'e çevirir."""
    if v is None:
        return "—"
    return f"{'+'if plus and v > 0 else ''}{v:.1f}%"


def yoy_color(v) -> str:
    """YoY büyüme değerine göre renk kodu döndürür."""
    if v is None:
        return "#8892a4"
    return "#10b981" if v > 2 else ("#ef4444" if v < -2 else "#f59e0b")


def shift_year(month_str: str, delta: int = -1):
    """'YYYY-MM' formatındaki ayı delta yıl öteler; hata durumunda None."""
    try:
        dt = pd.to_datetime(month_str + '-01')
        return dt.replace(year=dt.year + delta).strftime('%Y-%m')
    except Exception:
        return None


# ── KPI Hesaplama ─────────────────────────────────────────────────────────────

def compute_kpis(fdf: pd.DataFrame) -> dict:
    """
    Filtrelenmiş dataframe üzerinden temel KPI'ları hesaplar.
    Dönen dict her zaman aynı anahtarları içerir.
    """
    total_brut   = fdf['Brüt Toplam'].sum()
    total_gercek = fdf['Gerçek Gelir'].sum()
    total_pnr    = fdf['PNR'].nunique()
    total_hizmet = fdf['Hizmet Tutarı'].fillna(0).sum()
    avg_bilet    = fdf['Bilet Tutarı'].fillna(0).replace(0, np.nan).mean()
    hizmet_pct   = total_hizmet / total_brut * 100 if total_brut else 0
    gelir_oran   = total_gercek / total_brut * 100 if total_brut else 0
    per_pnr      = total_gercek / total_pnr if total_pnr else 0

    return dict(
        total_brut=total_brut,
        total_gercek=total_gercek,
        total_pnr=total_pnr,
        total_hizmet=total_hizmet,
        avg_bilet=avg_bilet,
        hizmet_pct=hizmet_pct,
        gelir_oran=gelir_oran,
        per_pnr=per_pnr,
    )


def compute_prev_year(df: pd.DataFrame, py_s, py_e,
                      sel_airlines, sel_flight, sel_firma,
                      all_months) -> tuple[pd.DataFrame, dict]:
    """
    Önceki yıl verisini filtreler ve KPI'larını hesaplar.
    Döner: (_py_df, py_kpis_dict)
    """
    if not (py_s and py_e and py_s in all_months):
        empty = pd.DataFrame()
        zeros = dict(py_gercek=0, py_pnr=0, py_brut=0,
                     py_hizmet=0, py_hizmet_pct=0)
        return empty, zeros

    _py = df[(df['Ay_str'] >= py_s) & (df['Ay_str'] <= py_e)].copy()
    if sel_airlines:
        _py = _py[_py['Havayolu'].isin(sel_airlines)]
    if sel_flight:
        _py = _py[_py['Uçuş Tipi'].isin(sel_flight)]
    if sel_firma:
        _py = _py[_py['Kurumsal Firma'].isin(sel_firma)]

    py_brut   = _py['Brüt Toplam'].sum()
    py_hizmet = _py['Hizmet Tutarı'].fillna(0).sum()

    return _py, dict(
        py_gercek=_py['Gerçek Gelir'].sum(),
        py_pnr=_py['PNR'].nunique(),
        py_brut=py_brut,
        py_hizmet=py_hizmet,
        py_hizmet_pct=py_hizmet / py_brut * 100 if py_brut else 0,
    )


def compute_yoy(kpis: dict, py_kpis: dict, tufe_end: float) -> dict:
    """
    Nominal ve reel YoY büyüme hesaplar.
    Döner: {nominal_yoy, reel_yoy, enf_k}
    """
    enf_k       = 1 + tufe_end / 100
    nominal_yoy = pct_delta(kpis['total_gercek'], py_kpis['py_gercek']) \
                  if py_kpis['py_gercek'] else None
    reel_yoy    = ((1 + (nominal_yoy or 0) / 100) / enf_k - 1) * 100 \
                  if nominal_yoy is not None else None
    return dict(nominal_yoy=nominal_yoy, reel_yoy=reel_yoy, enf_k=enf_k)
