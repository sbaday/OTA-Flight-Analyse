import pandas as pd
import numpy as np
import warnings
import re
import io

warnings.filterwarnings('ignore')

CSV_PATH = r'c:\Users\doguk\OneDrive\Belgeler\Dream Incentive\flight\Flight Sale Report.csv'
OUT_PATH = r'c:\Users\doguk\OneDrive\Belgeler\Dream Incentive\flight\analiz_sonuc.txt'

out = io.StringIO()

def p(*args, **kwargs):
    print(*args, file=out, **kwargs)

SEP = '-'*65

# 1. VERI YUKLEME
df = pd.read_csv(CSV_PATH, encoding='utf-8-sig', sep=None, engine='python')

def to_num(s):
    if pd.isnull(s): return np.nan
    s = str(s).strip().replace('.', '').replace(',', '.')
    try: return float(s)
    except: return np.nan

for c in ['Brut Toplam', 'Hizmet Tutari', 'Bilet Tutari', 'Havaalani Vergisi', 'Yakit', 'Diger', 'Ceza', 'Ek-Servis']:
    pass  # placeholder

# Use actual column names
NUM_COLS = [c for c in df.columns if any(k in c for k in ['Toplam', 'Tutari', 'Tutarı', 'Vergisi', 'Yakıt', 'Yakit', 'Diger', 'Diğer', 'Ceza', 'Servis'])]
for c in NUM_COLS:
    df[c] = df[c].apply(to_num)

def parse_date(s):
    s = str(s).strip()
    m = re.match(r'^(\d{1,2})\.(\d{1,2})\.(\d{4})$', s)
    if m:
        return pd.Timestamp(f'{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}')
    return pd.NaT

df['Satis Tarihi'] = df['Satış Tarihi'].apply(parse_date)
df['Ay'] = df['Satis Tarihi'].dt.to_period('M')

# Gelir hesabi
hiz_col = [c for c in df.columns if 'Hizmet' in c][0]
ek_col = [c for c in df.columns if 'Ek' in c][0]
brut_col = [c for c in df.columns if 'Brüt' in c or 'Brut' in c][0]
ceza_col = [c for c in df.columns if 'Ceza' in c][0]

df['Gercek_Gelir'] = df[hiz_col].fillna(0) + df[ek_col].fillna(0)

# =============================================
# PROMPT 0 - DOSYA TANITIMI
# =============================================
p(SEP)
p('PROMPT 0 - DOSYA TANITIMI')
p(SEP)
p(f'Toplam Satir  : {len(df):,}')
p(f'Toplam Sutun  : {df.shape[1]}')
p(f'Tarih Araligi : {df["Satis Tarihi"].min().date()} -> {df["Satis Tarihi"].max().date()}')
p()
p(f'{"SUTUN":<25} {"DOLULUK%":>9}  ORNEK DEGER')
p('-'*65)
for c in df.columns:
    dol = df[c].notna().mean()*100
    orn = str(df[c].dropna().iloc[0])[:40] if df[c].notna().any() else '-'
    p(f'{c:<25} {dol:>8.1f}%  {orn}')

p()
p('VERI KALITE SKORU')
p('-'*45)
dup_n = df['PNR'].duplicated().sum()
dup_pct = dup_n / len(df) * 100
neg_n = (df[brut_col] < 0).sum()
neg_pct = neg_n / len(df) * 100
tarih_null = df['Satis Tarihi'].isnull().mean() * 100
hiz0 = ((df[hiz_col].isna()) | (df[hiz_col] == 0)).sum()
hiz0_pct = hiz0 / len(df) * 100

skor_dup    = max(0, 100 - dup_pct * 5)
skor_neg    = max(0, 100 - neg_pct * 10)
skor_tarih  = max(0, 100 - tarih_null * 10)
skor_hiz    = max(0, 100 - hiz0_pct)
toplam_skor = (skor_dup + skor_neg + skor_tarih + skor_hiz) / 4

p(f'  Duplicate PNR          : {dup_n:,} ({dup_pct:.1f}%)  -> Puan: {skor_dup:.0f}')
p(f'  Negatif Brut           : {neg_n:,} ({neg_pct:.1f}%)  -> Puan: {skor_neg:.0f}')
p(f'  Tarih Null             : {tarih_null:.1f}%          -> Puan: {skor_tarih:.0f}')
p(f'  Hizmet Bos/Sifir       : {hiz0:,} ({hiz0_pct:.1f}%)  -> Puan: {skor_hiz:.0f}')
p(f'  TOPLAM SKOR            : {toplam_skor:.1f}/100')
p()
p('GELIR KONTROLU')
p('-'*45)
p(f'  Brut Toplam = 0        : {(df[brut_col]==0).sum():,}')
p(f'  Hizmet Tutari bos      : {df[hiz_col].isna().sum():,}')
p(f'  Hizmet Tutari sifir    : {(df[hiz_col]==0).sum():,}')
p(f'  Ek-Servis dolu         : {(df[ek_col]>0).sum():,} ({(df[ek_col]>0).mean()*100:.1f}%)')

# =============================================
# PROMPT 0.5 - FINANSAL GUVENILIRLIK
# =============================================
p()
p(SEP)
p('PROMPT 0.5 - FINANSAL GUVENILIRLIK')
p(SEP)
ceza_brut_pct = df[ceza_col].fillna(0).sum() / df[brut_col].fillna(0).sum() * 100
p(f'  Duplicate PNR orani    : {dup_pct:.1f}%  -> Risk: {"YUKSEK" if dup_pct>10 else ("ORTA" if dup_pct>3 else "DUSUK")}')
p(f'  Hizmet 0 orani         : {hiz0_pct:.1f}%  -> Risk: {"YUKSEK" if hiz0_pct>20 else ("ORTA" if hiz0_pct>5 else "DUSUK")}')
p(f'  Ek-Servis dolu orani   : {(df[ek_col]>0).mean()*100:.1f}%')
p(f'  Ceza/Brut orani        : {ceza_brut_pct:.2f}%  -> {"RISKLI (>%5)" if ceza_brut_pct>5 else "Kabul edilebilir"}')
p(f'  Havayolu cesit sayisi  : {df["Havayolu"].nunique()} farkli isim')
p()
p('  Havayolu Paylari (Top 10):')
for k, v in df['Havayolu'].value_counts(normalize=True).head(10).items():
    p(f'    {str(k):<35} {v*100:.1f}%')
p()
p('  En Guvenilir 3 Analiz:')
p('    1. Havayolu bazli gelir performansi (veri tam)')
p('    2. Kurumsal firma service fee analizi (firma veri tam)')
p('    3. Aylik trend analizi (tarih veri tam)')

# =============================================
# PROMPT 1A - GENEL PERFORMANS
# =============================================
p()
p(SEP)
p('PROMPT 1 - BLOK A: GENEL PERFORMANS')
p(SEP)
tbrut = df[brut_col].sum()
thiz  = df[hiz_col].fillna(0).sum()
tek   = df[ek_col].fillna(0).sum()
tger  = thiz + tek
upnr  = df['PNR'].nunique()
ger_oran = tger / tbrut * 100
per_pnr  = tger / upnr
p(f'  Toplam Brut Ciro      : {tbrut:>18,.2f} TL')
p(f'  Toplam Hizmet Tutari  : {thiz:>18,.2f} TL')
p(f'  Toplam Ek-Servis      : {tek:>18,.2f} TL')
p(f'  Toplam Gercek Gelir   : {tger:>18,.2f} TL')
p(f'  Gercek Gelir / Brut   : {ger_oran:>17.2f}%')
p(f'  Ortalama Gelir/PNR    : {per_pnr:>18,.2f} TL')
p(f'  Unique PNR            : {upnr:>18,}')
p(f'  Toplam Kayit (Satir)  : {len(df):>18,}')

# =============================================
# PROMPT 1B - HAVAYOLU PERFORMANSI
# =============================================
p()
p(SEP)
p('PROMPT 1 - BLOK B: HAVAYOLU PERFORMANSI (Top 15)')
p(SEP)
hv = df.groupby('Havayolu').agg(
    PNR=('PNR', 'count'),
    Brut=(brut_col, 'sum'),
    GGelir=('Gercek_Gelir', 'sum')
).reset_index()
hv['Gel_PNR'] = hv['GGelir'] / hv['PNR']
hv['Gel_pct'] = hv['GGelir'] / hv['GGelir'].sum() * 100
hv = hv.sort_values('GGelir', ascending=False)

p(f'  {"Havayolu":<30} {"PNR":>7} {"Brut":>14} {"GGelir":>12} {"Gel/PNR":>10} {"Gel%":>6}')
p('  ' + '-'*82)
for _, r in hv.head(15).iterrows():
    ha = str(r['Havayolu'])[:30]
    p(f'  {ha:<30} {r["PNR"]:>7,} {r["Brut"]:>14,.0f} {r["GGelir"]:>12,.0f} {r["Gel_PNR"]:>10,.0f} {r["Gel_pct"]:>5.1f}%')

best_vol = hv.sort_values('PNR', ascending=False).iloc[0]
best_pnr = hv.sort_values('Gel_PNR', ascending=False).iloc[0]
p()
p(f'  En Yuksek Hacim    : {best_vol["Havayolu"]}  ({best_vol["PNR"]:,} PNR, {best_vol["Gel_pct"]:.1f}% gelir)')
p(f'  En Yuksek Gel/PNR  : {best_pnr["Havayolu"]}  ({best_pnr["Gel_PNR"]:,.0f} TL/PNR)')

# =============================================
# PROMPT 1C - KURUMSAL FIRMA
# =============================================
p()
p(SEP)
p('PROMPT 1 - BLOK C: KURUMSAL FIRMA (Top 15)')
p(SEP)
frm = df.groupby('Kurumsal Firma').agg(
    PNR=('PNR', 'count'),
    Brut=(brut_col, 'sum'),
    GGelir=('Gercek_Gelir', 'sum'),
    Hiz=(hiz_col, lambda x: x.fillna(0).sum())
).reset_index()
frm['Gel_pct'] = frm['GGelir'] / frm['GGelir'].sum() * 100
frm['SvcOran'] = frm['Hiz'] / frm['Brut'].replace(0, np.nan) * 100
frm = frm.sort_values('GGelir', ascending=False)

p(f'  {"Firma":<38} {"PNR":>6} {"Brut":>14} {"GGelir":>11} {"Gel%":>6} {"Svc%":>7}')
p('  ' + '-'*87)
for _, r in frm.head(15).iterrows():
    fn = str(r['Kurumsal Firma'])[:37]
    p(f'  {fn:<38} {r["PNR"]:>6,} {r["Brut"]:>14,.0f} {r["GGelir"]:>11,.0f} {r["Gel_pct"]:>5.1f}% {r["SvcOran"]:>6.1f}%')

dusuk = frm[(frm['SvcOran'] < 2) & (frm['PNR'] > 5)].head(5)
p()
p('  Servis Orani < %2 (Risk - en az 5 PNR sartı):')
if len(dusuk) > 0:
    for _, r in dusuk.iterrows():
        p(f'    {str(r["Kurumsal Firma"])[:50]}  ->  {r["SvcOran"]:.2f}%')
else:
    p('    Risk netlesmedi, daha derin inceleme gerekiyor.')

# =============================================
# PROMPT 1D - UCUS TIPI
# =============================================
p()
p(SEP)
p('PROMPT 1 - BLOK D: UCUS TIPI')
p(SEP)
ut = df.groupby('Uçuş Tipi').agg(
    PNR=('PNR', 'count'),
    Brut=(brut_col, 'sum'),
    GGelir=('Gercek_Gelir', 'sum')
).reset_index()
ut['Gel_PNR'] = ut['GGelir'] / ut['PNR']
ut['Gel_pct'] = ut['GGelir'] / ut['GGelir'].sum() * 100

p(f'  {"Ucus Tipi":<15} {"PNR":>8} {"Brut":>15} {"GGelir":>13} {"Gel/PNR":>10} {"Gel%":>6}')
p('  ' + '-'*72)
for _, r in ut.sort_values('GGelir', ascending=False).iterrows():
    p(f'  {str(r["Uçuş Tipi"]):<15} {r["PNR"]:>8,} {r["Brut"]:>15,.0f} {r["GGelir"]:>13,.0f} {r["Gel_PNR"]:>10,.0f} {r["Gel_pct"]:>5.1f}%')

# =============================================
# PROMPT 1E - AYLIK TREND
# =============================================
p()
p(SEP)
p('PROMPT 1 - BLOK E: AYLIK TREND')
p(SEP)
trend = df.groupby('Ay').agg(
    PNR=('PNR', 'count'),
    Brut=(brut_col, 'sum'),
    GGelir=('Gercek_Gelir', 'sum')
).reset_index()
trend['Gel_PNR'] = trend['GGelir'] / trend['PNR']

p(f'  {"Ay":<10} {"PNR":>7} {"Brut":>17} {"Gercek Gelir":>14} {"Gel/PNR":>10}')
p('  ' + '-'*62)
for _, r in trend.iterrows():
    p(f'  {str(r["Ay"]):<10} {r["PNR"]:>7,} {r["Brut"]:>17,.0f} {r["GGelir"]:>14,.0f} {r["Gel_PNR"]:>10,.0f}')

if len(trend) > 1:
    f1, s1 = trend.iloc[0], trend.iloc[-1]
    pg = (s1['PNR'] - f1['PNR']) / f1['PNR'] * 100
    gg = (s1['Gel_PNR'] - f1['Gel_PNR']) / f1['Gel_PNR'] * 100
    p()
    p(f'  PNR Degisimi (ilk->son ay) : {pg:+.1f}%')
    p(f'  Gelir/PNR Degisimi         : {gg:+.1f}%')
    if gg < -5:
        p('  !!! UYARI: Gelir/PNR dusüyor - marj eriyor!')
    elif gg > 5:
        p('  Gelir/PNR artiyor - pozitif marj trendı!')

# =============================================
# PROMPT 1.5 - HACIM vs FIYAT
# =============================================
p()
p(SEP)
p('PROMPT 1.5 - HACIM vs FIYAT ETKISI')
p(SEP)
if len(trend) >= 2:
    a1, a2 = trend.iloc[0], trend.iloc[-1]
    he = (a2['PNR'] - a1['PNR']) * a1['Gel_PNR']
    fe = (a2['Gel_PNR'] - a1['Gel_PNR']) * a2['PNR']
    total = he + fe
    p(f'  Baz Ay         : {a1["Ay"]}  (PNR={a1["PNR"]:,}, Gel/PNR={a1["Gel_PNR"]:,.0f} TL)')
    p(f'  Son Ay         : {a2["Ay"]}  (PNR={a2["PNR"]:,}, Gel/PNR={a2["Gel_PNR"]:,.0f} TL)')
    p(f'  Hacim Etkisi   : {he:>+15,.0f} TL')
    p(f'  Fiyat Etkisi   : {fe:>+15,.0f} TL')
    p(f'  Toplam Degisim : {total:>+15,.0f} TL')
    if fe < 0 and he > 0:
        p('  SONUC: Hacim artıyor ama fiyat/PNR dusiyor -> Hacim sismesi riski!')
    elif fe > 0:
        p('  SONUC: Hem hacim hem fiyat/PNR artiyor -> Saglikli buyume!')

p()
p('  CEZA RISK OZETI (Ceza/Brut > %5):')
cf = df.groupby('Kurumsal Firma').agg(
    Ceza=(ceza_col, lambda x: x.fillna(0).sum()),
    Brut=(brut_col, lambda x: x.fillna(0).sum())
).reset_index()
cf['CB_pct'] = cf['Ceza'] / cf['Brut'].replace(0, np.nan) * 100
risk = cf[cf['CB_pct'] > 5].sort_values('CB_pct', ascending=False)
if len(risk) > 0:
    p(f'  {"Firma":<40} {"Ceza TL":>12} {"CB%":>8}')
    p('  ' + '-'*63)
    for _, r in risk.head(10).iterrows():
        fn = str(r['Kurumsal Firma'])[:39]
        p(f'  {fn:<40} {r["Ceza"]:>12,.0f} {r["CB_pct"]:>7.1f}%')
else:
    p('  Ceza/Brut > %5 olan firma bulunamadi - TEMIZ')

# =============================================
# PROMPT 3 - YONETICI OZETI
# =============================================
p()
p(SEP)
p('PROMPT 3 - YONETICI OZETI (FORMAT A - Yonetim)')
p(SEP)
best_hv2 = hv.sort_values('Gel_PNR', ascending=False).iloc[0]
top3_gelir = frm.head(3)

p(f'  Toplam Brut Ciro     : {tbrut:>18,.0f} TL')
p(f'  Toplam Gercek Gelir  : {tger:>18,.0f} TL  (Brut un {ger_oran:.1f}%si)')
p(f'  Ortalama Gelir/PNR   : {per_pnr:>18,.0f} TL')
p()
p('  KRITIK RISKLER:')
p(f'    Risk 1 - Hizmet Bos/Sifir Orani: {hiz0_pct:.1f}%')
p(f'             Bu oran dusurulmeden gercek gelir buyumesi saglanamaz.')
if dup_pct > 3:
    p(f'    Risk 2 - Duplicate PNR: {dup_pct:.1f}%')
    p(f'             RT biletin analiz oncesi duplicate temizligi yapilmali.')
p()
p('  AKSIYON ONERILERI:')
p(f'    Aksiyon 1: {best_hv2["Havayolu"]} ile hacim artisi  ({best_hv2["Gel_PNR"]:,.0f} TL/PNR - en yuksek)')
p(f'    Aksiyon 2: Servis orani dusuk firmalarla fee revizyonu')
p(f'    Aksiyon 3: Ek-Servis satisini artir (simdi sadece {(df[ek_col]>0).mean()*100:.1f}% dolu)')
p()
p('  YONETİCİ 3 CUMLESI:')
p(f'    Toplam {tbrut:,.0f} TL brut ciro uretilmis ancak gercek service geliri bunun yalnizca {ger_oran:.1f}%i.')
p(f'    {best_vol["Havayolu"]} en yuksek hacimli havayolu olmakla birlikte')
p(f'    {best_hv2["Havayolu"]} en yuksek bilet basina gelir uretiyor; bu ikilem strateji kararini zorunlu kiliyor.')
p(f'    Hizmet bos/sifir oraninin {hiz0_pct:.1f}% olmasi kritik gelir kaybi riski olusturmakta,')
p(f'    bu alanin sistematik takibi ve ek-servis penetrasyonunun arttirilmasi once gelen aksiyonlardir.')

p()
p(SEP)
p('Analiz Tamamlandi - Revenue Intelligence Framework v1.1')
p(SEP)

# DOSYAYA YAZ
with open(OUT_PATH, 'w', encoding='utf-8') as f:
    f.write(out.getvalue())

print(f'BASARILI - Sonuc yazildi: {OUT_PATH}')
