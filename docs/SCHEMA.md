# CSV Veri Şeması — Flight Revenue Intelligence Dashboard

Farklı bir CSV yüklenecekse aşağıdaki sütunların **birebir** mevcut olması gerekir.

---

## 🔑 Kimlik / Boyut Sütunları

| Sütun | Tip | Açıklama |
|---|---|---|
| `PNR` | string | İşlem kimliği — unique sayısı alınır |
| `Satış Tarihi` | string | **`dd.MM.yyyy`** formatında (örn. `15.03.2024`) |
| `Havayolu` | string | Havayolu adı |
| `Uçuş Tipi` | string | Yurt içi / Yurt dışı vb. |
| `Kurumsal Firma` | string | Müşteri firma adı |
| `Rota1` | string | Kalkış noktası |
| `Rota2` | string | Varış noktası |

---

## 💰 Sayısal Sütunlar

> **Sayı formatı:** Türkçe — nokta binlik ayraç, virgül ondalık.  
> Örnek: `1.234,56` → 1234.56

| Sütun | Açıklama | Boş olabilir mi? |
|---|---|---|
| `Brüt Toplam` | Toplam ciro | Hayır |
| `Hizmet Tutarı` | Servis bedeli (gelirin ana kaynağı) | Evet (`fillna(0)`) |
| `Bilet Tutarı` | Uçuş bileti bedeli | Evet |
| `Ek-Servis` | Ek hizmet geliri | Evet (`fillna(0)`) |
| `Ceza` | Ceza/iptal tutarı | Evet |
| `Havaalanı Vergisi` | Havaalanı vergisi | Evet |
| `Yakıt` | Yakıt bedeli | Evet |
| `Diğer` | Diğer masraflar | Evet |

---

## 🔄 Otomatik Türetilen Sütunlar

Bunları CSV'ye eklemeye gerek yok; dashboard kendi hesaplar:

| Sütun | Formül |
|---|---|
| `Gerçek Gelir` | `Hizmet Tutarı + Ek-Servis` |
| `Ay_str` | `Satış Tarihi` → `YYYY-MM` (örn. `2024-03`) |
| `Yıl` | `Satış Tarihi` → yıl |
| `Ay_No` | `Satış Tarihi` → ay numarası |

---

## ⚠️ Kritik Uyarılar

1. **Sütun adları birebir eşleşmeli** — büyük/küçük harf ve Türkçe karakterler dahil (`ü`, `ı`, `ş`, `ğ`, `ö`, `ç`)
2. **Tarih formatı:** yalnızca `dd.MM.yyyy` desteklenir
3. **Encoding:** UTF-8 veya UTF-8-BOM (`utf-8-sig`) — Excel'den kaydedilmiş CSV'ler genellikle BOM içerir, desteklenmektedir
4. **Ayraç:** virgül (`,`) veya noktalı virgül (`;`) otomatik algılanır
