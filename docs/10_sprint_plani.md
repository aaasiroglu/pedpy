# 10: Sprint Planı (Kasım 2026 – Haziran 2027)

*İki haftalık sprintler; her sprint sonunda Hande Hoca ile görüşme yapılır ve bu dosyadaki "Görüşme notu" satırı doldurulur. Bu plan, `04_yol_haritasi.md` içindeki göreli A1–A12 takviminin yerini alır.*

**Hedef çıktılar (Haziran 2027 başı):**

| Kod | Çıktı | Çekirdek katkı | Aday yayın yeri (danışmanla netleşecek; son tarihler teyit edilmeli) |
| --- | --- | --- | --- |
| **B1** | Konferans bildirisi | pedx çerçevesi ve Caferağa v1 sonuçları (açık veri, mutlak indeks, graf-XAI) | ISPRS Archives veya Annals, ulusal CBS ve Uzaktan Algılama kongreleri, AESOP |
| **M-A** | Makale A: *Açık veri sadakati* | G1 (OSM, PVGIS) ile G2 (İBB) karşılaştırması; OSM tamlığının PEB kararlarına etkisi; sıra kararlılığı ve MAUP | ISPRS IJGI, CEUS, Sustainable Cities and Society |
| **M-B** | Makale B: *Yöntem* | Fizik kenetli türevlenebilir tersine analiz, toplamsal olmayan graf bölgeselleştirmesi ve Shapley ile graf-XAI | Applied Energy, Energy and Buildings, SCS |
| **T** | Tez | Hepsi | İTÜ Fen Bilimleri Enstitüsü |

**Kural:** Her sprintte (1) çalışan kod ve testler, (2) bir belge veya notebook, (3) danışman görüşme notu üretilir.

---

| Sprint | Tarih | Hedef | Teslim | Yayın bağlantısı |
| --- | --- | --- | --- | --- |
| **S1** | 9–22 Kas 2026 | v0 sunumu (**web demo MVP**: OSM haritası ve bilimsel arayüz, K-024); İBB veri talebi; PED veritabanı çalışması başlıyor | Web demo; `pedx.export`; veri talep listesi; PED DB'den alanlar çıkarılmış tablo | B1 kapsamı |
| **S2** | 23 Kas – 6 Ara | Gerçek ya da yarı-gerçek tüketim profilleri (Hande Hoca projeleri, İBB); talep modülü v1 | `pedx.demand` (arketip × profil × ERA5 sıcaklığı); varsayım tablosunun güncellenmesi | B1 ve M-A |
| **S3** | 7–20 Ara | Tepe rahatlamasının yeniden tanımı (mevsimsel ve depolamalı); 3B çatı ve gölge girdisi (SEBE veya Demirel vd. 2025 çıktıları) | Gösterge v1; "kendi ışınım verini getir" arayüzü | **B1 özetinin gönderimi** (son tarihe göre) |
| **S4** | 21 Ara – 3 Oca | İBB katmanlarının içe aktarılması (G2): kat, yaş, kullanım | `ingest/ibb.py`; bina eşleşme oranı | M-A |
| **S5** | 4–17 Oca | G1/G2 karşılaştırması: ρ, τ, ilk-k örtüşmesi, RMSE, MAPE, bootstrap güven aralığı; ısı pompası senaryosu | `validation` modülü; ilk tablolar | M-A çekirdeği |
| **S6** | 18–31 Oca | Ağırlık ve sıra kararlılığı; H3 çözünürlüğü 8/9/10 (MAUP) | Duyarlılık raporu | M-A |
| **S7** | 1–14 Şub | **Makale A taslağı**; küme düzeyinde tersine analiz tasarımı | M-A v1 → danışman | **M-A** |
| **S8** | 15–28 Şub | Küme düzeyinde birlikte optimizasyon (paylaşımlı); EV ve esnek yük | `inverse.cluster` | M-B |
| **S9** | 1–14 Mar | Graf karşılaştırmaları (max-p, rastgele, kesin) ve optimallik açığı; benchmark için şehir seçimi | Karşılaştırma tablosu | M-B |
| **S10** | 15–28 Mar | Çok şehirli mini benchmark (Caferağa + 1–2 açık veri şehri); PED DB analog karşılaştırması | `benchmarks/` | M-B ve tez |
| **S11** | 29 Mar – 11 Nis | **Makale B taslağı**; **M-A gönderimi** | M-B v1; M-A gönderildi | **M-B, M-A** |
| **S12** | 12–25 Nis | Tez bölüm 1–3 (giriş, literatür, yöntem) | Tez taslağı v1 | T |
| **S13** | 26 Nis – 9 May | Tez bölüm 4–6 (bulgular, tartışma, sonuç); **M-B gönderimi** | Tez taslağı v2 | **M-B** |
| **S14** | 10–23 May | Danışman düzeltmeleri; kod ve veri sürümü (Zenodo DOI); B1 tam metni (kabul edildiyse) | pedx v1.0 | B1 |
| **S15** | 24 May – 6 Haz | **Tez teslimi**; savunma hazırlığı | Tez | T |

## Kritik yol ve riskler

| Risk | Etkisi | Önlem |
| --- | --- | --- |
| Gerçek tüketim profili bulunamaz | C1 döngüselliği nedeniyle M-B'deki graf bulguları zayıflar | S2'de kesinleştirmek; bulunamazsa iki bağımsız profil kütüphanesiyle duyarlılık analizi ve sınırlılığın açıkça yazılması |
| İBB verisi gecikir | M-A gecikir | S1'de resmî talep; ara çözüm olarak Demirel vd. (2025) 3B çıktıları |
| Dergi süreçleri uzun | Haziran'a kadar kabul gelmeyebilir | "Gönderilmiş" ya da "değerlendirmede" durumu hedeflenir; bildiri daha hızlı bir yol |
| Kapsam genişler | Teslim gecikir | Zorunlu, Güçlü, Bonus katmanları; NLP Bonus katmanda kalır |

## Görüşme notları

| Sprint | Tarih | Hande Hoca'nın yönlendirmeleri | Alınan kararlar (05'e bağlantı) |
| --- | --- | --- | --- |
| S1 | | | |
