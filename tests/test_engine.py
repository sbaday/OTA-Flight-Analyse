"""
Core katmanı birim testleri.
Streamlit veya IO bağımlılığı olmadan çalışır.
Çalıştırma: pytest tests/
"""

import pandas as pd
import numpy as np
import pytest

from src.core.engine import (
    fmt_mil,
    pct_delta,
    fmt_pct,
    yoy_color,
    shift_year,
    compute_kpis,
    compute_yoy,
)


# ── fmt_mil ───────────────────────────────────────────────────────────────────

def test_fmt_mil_million():
    assert fmt_mil(1_500_000) == "1.50M ₺"

def test_fmt_mil_thousand():
    assert fmt_mil(25_000) == "25.0K ₺"

def test_fmt_mil_small():
    assert fmt_mil(500) == "500 ₺"

def test_fmt_mil_zero():
    assert fmt_mil(0) == "0 ₺"

def test_fmt_mil_negative():
    result = fmt_mil(-2_000_000)
    assert "M ₺" in result


# ── pct_delta ─────────────────────────────────────────────────────────────────

def test_pct_delta_positive():
    assert pct_delta(110, 100) == pytest.approx(10.0)

def test_pct_delta_negative():
    assert pct_delta(90, 100) == pytest.approx(-10.0)

def test_pct_delta_zero_old():
    assert pct_delta(100, 0) is None


# ── fmt_pct ───────────────────────────────────────────────────────────────────

def test_fmt_pct_none():
    assert fmt_pct(None) == "—"

def test_fmt_pct_plus():
    assert fmt_pct(12.5, plus=True) == "+12.5%"

def test_fmt_pct_negative():
    assert fmt_pct(-5.0, plus=True) == "-5.0%"


# ── yoy_color ─────────────────────────────────────────────────────────────────

def test_yoy_color_positive():
    assert yoy_color(10) == "#10b981"

def test_yoy_color_negative():
    assert yoy_color(-10) == "#ef4444"

def test_yoy_color_neutral():
    assert yoy_color(1) == "#f59e0b"

def test_yoy_color_none():
    assert yoy_color(None) == "#8892a4"


# ── shift_year ────────────────────────────────────────────────────────────────

def test_shift_year_backward():
    assert shift_year("2025-03") == "2024-03"

def test_shift_year_forward():
    assert shift_year("2024-06", delta=1) == "2025-06"

def test_shift_year_invalid():
    assert shift_year("not-a-date") is None


# ── compute_kpis ──────────────────────────────────────────────────────────────

@pytest.fixture
def sample_df():
    """Minimal test dataframe."""
    return pd.DataFrame({
        'Brüt Toplam':   [1000.0, 2000.0, 1500.0],
        'Gerçek Gelir':  [100.0,  200.0,  150.0],
        'PNR':           ['A001', 'A002', 'A003'],
        'Hizmet Tutarı': [80.0,   150.0,  120.0],
        'Bilet Tutarı':  [900.0,  1800.0, 1350.0],
    })

def test_compute_kpis_totals(sample_df):
    result = compute_kpis(sample_df)
    assert result['total_brut']   == pytest.approx(4500.0)
    assert result['total_gercek'] == pytest.approx(450.0)
    assert result['total_pnr']    == 3

def test_compute_kpis_hizmet_pct(sample_df):
    result = compute_kpis(sample_df)
    # 350 / 4500 * 100
    assert result['hizmet_pct'] == pytest.approx(350/4500*100, rel=1e-3)

def test_compute_kpis_per_pnr(sample_df):
    result = compute_kpis(sample_df)
    assert result['per_pnr'] == pytest.approx(150.0)


# ── compute_yoy ───────────────────────────────────────────────────────────────

def test_compute_yoy_real_growth():
    kpis   = {'total_gercek': 110}
    py_kpis = {'py_gercek': 100}
    result = compute_yoy(kpis, py_kpis, tufe_end=5.0)
    assert result['nominal_yoy'] == pytest.approx(10.0)
    # reel = (1.10 / 1.05 - 1) * 100
    expected_reel = (1.10 / 1.05 - 1) * 100
    assert result['reel_yoy'] == pytest.approx(expected_reel, rel=1e-3)

def test_compute_yoy_no_prev():
    kpis   = {'total_gercek': 110}
    py_kpis = {'py_gercek': 0}
    result = compute_yoy(kpis, py_kpis, tufe_end=30.0)
    assert result['nominal_yoy'] is None
    assert result['reel_yoy'] is None
