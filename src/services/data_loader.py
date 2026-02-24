"""
Veri yükleme servisi.
Streamlit @st.cache_data ile sarmalanmıştır; data IO bu katmanda kalır.

İki giriş noktası:
  - load_data_from_upload(file_bytes)  → st.file_uploader ile
  - load_data()                        → local dev / fallback
"""

import io
import re
import pandas as pd
import numpy as np
import streamlit as st

from src.config.settings import get_csv_path

_NUMERIC_COLS = [
    'Brüt Toplam', 'Hizmet Tutarı', 'Bilet Tutarı',
    'Havaalanı Vergisi', 'Yakıt', 'Diğer', 'Ceza', 'Ek-Servis',
]


def _to_num(s):
    """Türkçe biçimli sayı string'ini float'a çevirir."""
    if pd.isnull(s):
        return np.nan
    s = str(s).strip().replace('.', '').replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return np.nan


def _parse_date(s) -> pd.Timestamp:
    """'dd.MM.yyyy' formatındaki string'i Timestamp'e çevirir."""
    s = str(s).strip()
    m = re.match(r'^(\d{1,2})\.(\d{1,2})\.(\d{4})$', s)
    if m:
        return pd.Timestamp(f'{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}')
    return pd.NaT


def _build_df(source) -> pd.DataFrame:
    """
    CSV kaynağını (path str veya BytesIO) parse edip temiz DataFrame döndürür.
    Tüm temizleme mantığı burada — iki loader aynı kodu kullanır.
    """
    df = pd.read_csv(source, encoding='utf-8-sig', sep=None, engine='python')

    for col in _NUMERIC_COLS:
        if col in df.columns:
            df[col] = df[col].apply(_to_num)

    df['Satış Tarihi'] = df['Satış Tarihi'].apply(_parse_date)
    df['Ay_str'] = df['Satış Tarihi'].dt.strftime('%Y-%m')
    df['Yıl']    = df['Satış Tarihi'].dt.year
    df['Ay_No']  = df['Satış Tarihi'].dt.month

    df['Gerçek Gelir'] = df['Hizmet Tutarı'].fillna(0) + df['Ek-Servis'].fillna(0)
    return df


@st.cache_data(show_spinner="📂 Veri yükleniyor…")
def load_data_from_upload(file_bytes: bytes) -> pd.DataFrame:
    """
    st.file_uploader'dan gelen ham byte'ları parse eder.
    file_bytes hashable olduğu için cache düzgün çalışır —
    aynı dosya tekrar yüklenmez.
    """
    return _build_df(io.BytesIO(file_bytes))


@st.cache_data
def load_data() -> pd.DataFrame:
    """Local dev / CI fallback: disk yolundan yükler."""
    return _build_df(get_csv_path())
