# ✈️ Flight Revenue Intelligence Dashboard

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://drmflight.streamlit.app)

Havayolu satış verilerini analiz eden, **7 sekmeli** interaktif Streamlit dashboard'u.  
Gerçek geliri (Hizmet + Ek-Servis), enflasyondan arındırılmış büyümeyi ve müşteri dinamiklerini ölçer.

---

## 📊 Sekmeler

| Sekme | İçerik |
|---|---|
| 📊 Özet | YoY KPI'lar, HHI Konsantrasyon, Büyüme Kaynağı (Hacim vs Marj) |
| 💰 Gelir Kalitesi | Servis bedeli trendi, Havayolu marjı, Firma karlılığı |
| 🔎 Segment & Rota | Karlı/hacimli rotalar, Risk Tablosu (2-of-3 kriter), Scatter haritası |
| 📐 Reel Büyüme | TÜFE'den arındırılmış büyüme analizi |
| 🔄 Müşteri Dinamiği | Cohort analizi, Retention, Churn |
| ✈️ Havayolu Stratejisi | Tedarikçi karlılığı, HHI, Reel YoY, Stratejik uyarılar |
| 📦 Marj Kalitesi | Firma Svc% dağılımı, Boxplot, Operasyon risk tablosu |

---

## 🏗️ Mimari

```
flight/
├── Dashboard.py              # Streamlit Cloud entry point (80 satır)
│
├── src/
│   ├── config/settings.py    # Renkler, TÜFE DB, CSS, CSV path
│   ├── core/engine.py        # Saf hesaplama — Streamlit/IO bağımsız
│   ├── services/data_loader.py # @st.cache_data ile CSV yükleme
│   └── ui/
│       ├── components.py     # kpi_card, chart_info, layout helpers
│       └── tab1_ozet.py … tab7_marj.py  # Her sekme ayrı modül
│
├── tests/
│   └── test_engine.py        # 20 birim testi (pytest)
│
├── analyze.py                # Konsol tabanlı veri kalite analizi
└── requirements.txt
```

> **Temel formül:**  
> Net Gelir (Op.Brüt) = Hizmet Tutarı + Ek-Servis  
> Reel Büyüme = ((1 + Nominal) / (1 + TÜFE)) − 1

---

## 🚀 Kurulum ve Çalıştırma

### Gereksinimler
```bash
pip install -r requirements.txt
```

### Lokal çalıştırma
```bash
streamlit run Dashboard.py
```

### Testleri çalıştırma
```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

---

## 📁 Veri Dosyası

`Flight Sale Report.csv` — repo kökünde bulunmalıdır.  
Zorunlu sütunlar: `Satış Tarihi`, `PNR`, `Havayolu`, `Uçuş Tipi`, `Kurumsal Firma`,  
`Brüt Toplam`, `Hizmet Tutarı`, `Bilet Tutarı`, `Ek-Servis`, `Ceza`, `Rota1`, `Rota2`

---

## 🧪 Testler

```
pytest tests/test_engine.py -v
→ 20 tests passed [100%]
```

Core katmanı (`fmt_mil`, `compute_kpis`, `compute_yoy` vb.) Streamlit olmadan test edilir.
