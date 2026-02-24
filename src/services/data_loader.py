"""
Veri yükleme servisi.
Streamlit @st.cache_data ile sarmalanmıştır; data IO bu katmanda kalır.
"""

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


@st.cache_data
def load_data() -> pd.DataFrame:
    """
    CSV'yi yükler, sayısal sütunları temizler, tarih ve türetilmiş alanları ekler.
    Streamlit Cloud'da 'Flight Sale Report.csv' (repo kökü) kullanılır;
    local dev'de fallback path devreye girer.
    """
    path = get_csv_path()
    df = pd.read_csv(path, encoding='utf-8-sig', sep=None, engine='python')

    # Sayısal sütunlar
    for col in _NUMERIC_COLS:
        if col in df.columns:
            df[col] = df[col].apply(_to_num)

    # Tarih
    df['Satış Tarihi'] = df['Satış Tarihi'].apply(_parse_date)
    df['Ay_str'] = df['Satış Tarihi'].dt.strftime('%Y-%m')
    df['Yıl']    = df['Satış Tarihi'].dt.year
    df['Ay_No']  = df['Satış Tarihi'].dt.month

    # Türetilmiş gelir sütunu
    df['Gerçek Gelir'] = df['Hizmet Tutarı'].fillna(0) + df['Ek-Servis'].fillna(0)

    return df
