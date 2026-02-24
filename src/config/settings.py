"""
Uygulama genelinde kullanılan sabitler ve konfigürasyon değerleri.
Streamlit veya IO bağımlılığı yoktur.
"""

import os

# ── CSV Yolları ────────────────────────────────────────────────────────────────
CSV_LOCAL    = 'Flight Sale Report.csv'
CSV_FALLBACK = r'c:\Users\doguk\OneDrive\Belgeler\Dream Incentive\flight\Flight Sale Report.csv'

def get_csv_path() -> str:
    """Streamlit Cloud'da CSV_LOCAL, local dev'de fallback kullanır."""
    return CSV_LOCAL if os.path.exists(CSV_LOCAL) else CSV_FALLBACK

# ── TÜFE Veritabanı (TÜİK Yıllık Enflasyon %) ─────────────────────────────────
TUFE_DB: dict[str, float] = {
    "2024-01": 64.86, "2024-02": 67.07, "2024-03": 68.50, "2024-04": 69.80,
    "2024-05": 75.45, "2024-06": 71.60, "2024-07": 61.78, "2024-08": 51.97,
    "2024-09": 49.38, "2024-10": 48.58, "2024-11": 47.09, "2024-12": 44.38,
    "2025-01": 42.12, "2025-02": 39.05, "2025-03": 38.10, "2025-04": 37.86,
    "2025-05": 35.05, "2025-06": 35.18, "2025-07": 33.60, "2025-08": 31.68,
    "2025-09": 27.17, "2025-10": 28.06, "2025-11": 27.95, "2025-12": 25.24,
    "2026-01": 30.65, "2026-02": 30.50,
}

# ── Grafik Renk Sabitleri ──────────────────────────────────────────────────────
PLOT_BG   = "#0f1117"
PAPER_BG  = "#0f1117"
FONT_COL  = "#c9d1d9"
GRID_COL  = "#21262d"

ACCENT = [
    "#3b82f6", "#6366f1", "#10b981", "#f59e0b",
    "#ef4444", "#8b5cf6", "#06b6d4", "#f97316",
    "#84cc16", "#ec4899",
]

# ── CSS Stilleri ───────────────────────────────────────────────────────────────
APP_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.main{background:#0f1117;}
.metric-card{background:linear-gradient(135deg,#1a1d2e,#16213e);border:1px solid #2a2d3e;border-radius:12px;padding:18px;text-align:center;box-shadow:0 4px 20px rgba(0,0,0,.3);margin-bottom:8px;}
.metric-card .label{font-size:10px;color:#8892a4;text-transform:uppercase;letter-spacing:1px;font-weight:600;margin-bottom:6px;}
.metric-card .value{font-size:22px;font-weight:700;color:#e2e8f0;margin-bottom:4px;}
.metric-card .sub{color:#8892a4;font-size:11px;}
.delta-pos{color:#10b981;font-size:13px;font-weight:600;}
.delta-neg{color:#ef4444;font-size:13px;font-weight:600;}
.delta-neu{color:#8892a4;font-size:12px;}
.section-title{font-size:13px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin:16px 0 10px 0;padding-bottom:6px;border-bottom:1px solid #2a2d3e;}
.stTabs [data-baseweb="tab-list"]{gap:8px;}
.stTabs [data-baseweb="tab"]{background:#1a1d2e;border-radius:8px;border:1px solid #2a2d3e;color:#8892a4;padding:8px 20px;font-weight:600;font-size:13px;}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,#3b82f6,#6366f1)!important;color:white!important;border:none!important;}
div[data-testid="stSidebar"]{background:#0d1117;border-right:1px solid #1f2937;}
"""
