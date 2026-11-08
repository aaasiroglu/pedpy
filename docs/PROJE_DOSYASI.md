# pedx: Proje Dosyası

**Tez:** Pozitif Enerji Bölgesi Projeleri için Açıklanabilir ve Fizik Kenetli Elverişlilik Analizi: Küresel Açık Veri, Referans Sınıf Tahmini ve İstanbul Doğrulaması
**Hazırlayan:** Abdurrahim Arif Aşıroğlu · **Danışman:** Prof. Dr. Hande Demirel · İTÜ Geomatik Mühendisliği
**Sürüm:** v0.5 · 2026-11-08 · **Repo:** `aaasiroglu/pedpy` (dal `claude/dreamy-allen-fvtsux`) · **Uygulama:** `web/pedx_app.html`

> Bu belge projenin tek giriş noktasıdır. Sırasıyla **amaç → sistem mimarisi → kullanılan veriler → işlem adımları → sonuçlar → proje yönetimi** bölümlerinden oluşur. Ayrıntılı belgeler sonda listelenmiştir.

---

## 1. Amaç ve kapsam

Herhangi bir yerde önerilen bir PED projesi için dört soruyu yanıtlamak:
- **Yapılabilir mi?** Fiziksel enerji dengesi.
- **Neden olmaz?** Açıklama.
- **Ne yapılırsa olur?** Tersine analiz.
- **Değer mi?** ROI.

Bu yanıtlar yalnızca **küresel açık veriyle (G1)** üretilir ve **İstanbul'un resmî verisiyle (G2)** doğrulanır.

**Analiz birimi:** proje adayı = sınır (H3 altıgen kümesi) + müdahale paketi + bağlam + finansman.

| Araştırma sorusu | Ölçüt |
| --- | --- |
| **AS1:** Küresel açık veri yerel gerçekliği ne kadar temsil eder? | G1 ile G2 arasındaki farklar, sıra korelasyonu |
| **AS2:** Saatlik tamamlayıcılık proje sınırını nasıl değiştirir? Her altıgenin katkısı nedir? | Küme öz-yeterliliği, Shapley değeri |
| **AS3:** En küçük fiziksel müdahale ve getirisi nedir? | Maliyet, NPV, fiziksel denetim |

---

## 2. Sistem mimarisi

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ L6 SUNUM        web/pedx_app.html: sunum · mimari · MVP (proje adayı) · veri · kaynakça  │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│ L5 KARAR        yapılabilir mi · neden · ne yapılırsa · değer mi                         │
│                 (Krangsås vd. 2021'in 7 alanı; Flyvbjerg 2014 referans sınıfı)           │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│ L4 XAI ve TERSİNE  kesin katkılar · sıra aralıkları · Shapley (graf) · fiziksel tersine  │
│                    analiz (JAX) · karşı-olgusal analiz                                   │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│ L3 MOTORLAR     fizik (yıllık + saatlik, batarya) · talep (EPİAŞ + Demand.ninja) ·       │
│                 graf (paylaşım oyunu) · referans sınıf modeli (planlı)                   │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│ L2 H3 ÖZELLİK DEPOSU  82 kayıtlı özellik/hücre · veri sözleşmesi (kayıtsız sütun          │
│                       dışa aktarılamaz)                                                  │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│ L1 VERİ GÖLÜ    35 küresel veri seti kataloğu · AOI bağlayıcıları · raster→H3 motoru ·    │
│                 köken ve lisans                                                          │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│ L0 KAYNAKLAR    OSM · JRC GHSL · UNSD · OWID/Ember · PVGIS · ERA5 · EPİAŞ · …             │
└──────────────────────────────────────────────────────────────────────────────────────────┘
          ▲ G2 doğrulama (yalnızca okunur): İBB · TEDAŞ · EPİAŞ mesken profili · Demirel vd. 2025
```

**Veri gölü ilkesi:** Dünyadaki bütün veri tek bir yere kopyalanmaz. Her küresel veri seti için bir **bağlayıcı** vardır. Bir alan (AOI) seçildiğinde bağlayıcı yalnızca o alanın karosunu veya penceresini indirir ve önbelleğe alır. **Raster → H3 motoru** (`zonal_h3`) bunu kayıtlı özelliklere dönüştürür. Aynı kod her şehirde çalışır.

| Katman | Kod | Test |
| --- | --- | --- |
| L0–L1 | `pedx.ingest`, `pedx.datalake` | ayrıştırıcı, zonal motor, katalog |
| L2 | `pedx.features` (registry, layers, morphology, accessibility) | sözleşme ve katman testleri |
| L3 | `pedx.energy`, `pedx.demand`, `pedx.graph` | T1–T5, Demand.ninja, ayrıştırma |
| L4 | `pedx.index`, `pedx.xai`, `pedx.inverse` | Shapley aksiyomları, ızgara aramasına ve ikiye bölmeye karşı kontroller |
| L6 | `scripts/build_features.py`, `web/build_app.py` | uçtan uca yapım |

Toplam **63 otomatik test** var. Kurulum: `make install data build serve` (`docs/LOCAL_SETUP.md`).

---

## 3. Kullanılan veriler

| Veri | Kaynak | Çözünürlük | Lisans | Rol | Kullanım |
| --- | --- | --- | --- | --- | --- |
| Mahalle sınırı | OSM relation 9441032 | poligon | ODbL | G1 | AOI |
| Binalar | OSM (Overpass) | poligon | ODbL | G1 | taban alanı, morfoloji |
| POI | OSM | nokta | ODbL | G1 | kentsel işlev (14 aile) |
| Yaya ağı, duraklar | OSM | çizgi, nokta | ODbL | G1 | 10 dakikalık erişim |
| Nüfus | JRC GHS-POP R2023A E2020 | 3″ (~90 m) | CC BY 4.0 | G1 | talep |
| Yapı alanı ve hacmi (toplam ve konut dışı), yükseklik | JRC GHS-BUILT-S/V/H R2023A | 3″ | CC BY 4.0 | G1 | yükseklik, kullanım, OSM kontrolü |
| Konut elektriği (ulusal) | UNSD Energy Statistics (UNdata) | ülke, yıllık | atıfla serbest | G1 | kişi başı talep |
| Nüfus ve talep (ülke) | Our World in Data (UN WPP, Ember) | ülke | CC BY 4.0 | G1 | kişi başına çevirme |
| PV üretimi | EU JRC PVGIS 5.3 (SARAH-3) | saatlik, nokta | AB | G1 | çatı PV |
| Hava (ısıtma ve soğutma) | ERA5 (Open-Meteo) + Demand.ninja | saatlik | CC BY 4.0 / BSD-3 | G1 | talebin hava bileşeni |
| Yüzey sıcaklığı (LST) | Landsat 8/9 C2 L2 (Planetary Computer), 16 sahne, Haz–Eyl 2023 | 30 m | kamu malı | G1 | ısı adası, soğutma, PV sıcaklığı |
| NDVI, NDBI | Sentinel-2 L2A (Earth Search), 26.07.2023 | 10–20 m | Copernicus açık | G1 | yeşil alan, yapılaşma |
| Yükseklik, eğim | Copernicus DEM GLO-30 | 30 m | Copernicus | G1 | arazi |
| Ulusal saatlik yük | EPİAŞ şeffaflık platformu | saatlik | atıfla; hesap gerekli | G1 | talebin taban şekli (**bekleniyor**) |
| İstanbul kişi başı tüketim | TEDAŞ 2023, Tablo 7 | il | kamu | **G2** | doğrulama |
| Caferağa nüfusu | Kadıköy Belediyesi / TÜİK | mahalle | kamu | **G2** | doğrulama |
| Konut saatlik profili | EPİAŞ profil katsayıları (mesken, AYEDAŞ) | saatlik | kamu | **G2** | doğrulama |

Tam envanter: 35 veri seti; 15'i sisteme alındı, 1 bağlayıcı hazır, 19 planlı. Ayrıntılar `docs/11` ve `docs/14` dosyalarında ve uygulamanın "Mimari" bölümünde.

---

## 4. İşlem adımları

| # | Adım | Girdi | İşlem | Çıktı | Doğrulama | Durum |
| --- | --- | --- | --- | --- | --- | --- |
| A0 | AOI tanımı | OSM sınırı | Overpass sorgusu, halkaların birleştirilmesi | sınır poligonu | — | ✅ |
| A1 | Veri gölü çekimi | Katalog | Bağlayıcılarla AOI karoları ve pencereleri | `data/raw` önbelleği | lisans kaydı | ✅ (15 set) |
| A2 | Bina ve hücre atama | OSM binaları | Ağırlık merkezi sınır içinde mi, H3 r10 ataması | binalar ve hücreleri | enerji korunumu (T5) | ✅ |
| A3 | Raster → H3 | GHS-POP, GHS-BUILT-* | Piksel merkezi ataması, toplam veya ortalama | nüfus, alan, hacim | GHS-POP ile resmî nüfus (G2) | ✅ |
| A4 | Özellik deposu | A2–A3, POI, ağ, EO | Katman fonksiyonları; morfoloji (momepy); erişim (Dijkstra, 800 m); yol ağı karmaşıklığı (Boeing 2019); Landsat LST, Sentinel-2, DEM; PCA imzası | 82 özellik/hücre | veri sözleşmesi | ✅ |
| A5 | Yıllık enerji | A4, UNSD, PVGIS | Konut talebi = nüfus × kişi başı; PV = taban alanı × u × η × verim | denge, gereken çatı payı | aralık analizi | ✅ |
| A6 | Saatlik talep | EPİAŞ, ERA5, Demand.ninja | Ulusal yükün taban ve hava bileşenlerine ayrıştırılması; D_t = E[(1−w)b_t + w m_t] | saatlik konut talebi | EPİAŞ mesken profili (G2) | ⏳ EPİAŞ verisi |
| A7 | Saatlik göstergeler | A6, PVGIS saatlik | SSR, CVaR ile şebeke stresi, batarya | proje göstergeleri | T1, T2 | kod ✅ / veri ⏳ |
| A8 | Proje adayı | A4–A7, komşuluk | Graf büyütme; paylaşım oyunu; Shapley | sınır ve katkılar | Shapley aksiyomları | yıllık ✅ / saatlik ⏳ |
| A9 | Tersine analiz ve ROI | A8, maliyetler | Fizik kenetli arama (JAX), kesin modelle denetim | reçete, Pareto eğrisi | 7 fiziksel denetim | kod ✅ / maliyet ⏳ |
| A10 | Referans sınıfı | PED Veritabanı | Benzerlik modeli, gruplanmış SHAP | dış bakış | bölge dışarıda bırakılarak çapraz doğrulama | planlı (S4–S7) |
| A11 | Sunum | tümü | `build_app.py` | `pedx_app.html` | uçtan uca yapım | ✅ |

---

## 5. Sonuçlar (v0.4, Caferağa, H3 r10)

**Bütünlük:** 2061 bina · 92 hücre · 1320 POI · 2202 yaya yolu · 82 özellik/hücre.

| Sonuç | Değer | Yorum |
| --- | --- | --- |
| Nüfus (GHS-POP 2020) ve resmî değer (2020) | 22.005 / 21.421 → **+%2,7** | Küresel nüfus ızgarası mahalle ölçeğinde güvenilir (AS1) |
| Kişi başı toplam tüketim: Ember (TR) ve TEDAŞ (İstanbul) | 3713 / 2678 kWh → +%38,7 | Ulusal ortalama sanayi yükü içerir; konut payı için UNSD kullanıldı |
| Konut elektriği talebi | 16,53 GWh/yıl | 751 kWh/kişi (UNSD 2023) |
| Çatı PV potansiyeli (ana senaryo) | 26,44 GWh/yıl | PVGIS 2023: 1268 kWh/kWp |
| **Yıllık konut elektriği dengesi** | **1,60 (aralık 1,36–3,85)** | Konut elektriği için mahalle ölçeğinde PED mümkün; ısıtma ve hizmet sektörü dahil değil |
| Yapı alanı: OSM ve GHSL | 401.140 / 462.255 m² | OSM yaklaşık %13 eksik |
| **OSM tamlığı ile denge ilişkisi** | ρ = 0,86 | **Tahmin, OSM tamlığına duyarlı** → GHSL ile duyarlılık analizi şart (Makale A) |
| Ortalama yapı yüksekliği (GHSL hacim/alan) | 11,9 m | OSM'de kat bilgisi yalnızca binaların %17'sinde var |
| Konut dışı yapı payı (GHSL) | %3,3 | Zemin kat ticaretini eksik sayıyor; POI ile çelişiyor |
| Gündüz işlevli POI ile denge | ρ = 0,45 | Tamamlayıcılık hipotezi için işaret |
| 10 dakikalık yürüme: günlük ihtiyaç tamlığı | ortalama 0,95 | Kadıköy merkezi çok yürünebilir |
| Ortak duvar oranı | ortalama 0,22 | Bitişik nizam → düşük ısı kaybı |
| Yaz yüzey sıcaklığı (Landsat, 16 sahne) | ortalama 39,0 °C (29,3–43,0) | Kıyı hücreleri daha serin; ısı adası katmanı |
| NDVI / NDBI ile denge | NDVI ortalaması 0,25; NDBI ile ρ = 0,50 | Yapılaşma dengeyi artırıyor (taban alanı etkisi) |
| Sokak dolambaçlılığı ile denge | ρ = −0,43; yönelim düzeni φ ortalaması 0,82 | Düzenli ızgara dokusu daha elverişli |
| Hücre imzası (PCA) | 1. bileşen %25 kentsel yoğunluk; 2. bileşen %10 ticari ile yeşil karşıtlığı | Bütün katmanların yorumlanabilir özeti |
| Hava bileşeni (Demand.ninja, ERA5 2023) | ısıtma Kasım–Nisan; soğutma Haziran–Eylül | Saatlik modelin hava girdisi hazır |
| Yöntemsel bulgu | MARCOS ≡ κ·ağırlıklı toplam | Xie ve Zou (2025) ile doğrulandı |

---

## 6. Proje yönetimi

**İş kırılım yapısı (İKY):**
1. Veri gölü
2. Özellik deposu
3. Fizik ve talep
4. Graf ve XAI
5. Tersine analiz ve ROI
6. Referans sınıfı
7. Doğrulama (G2)
8. Uygulama
9. Yayınlar
10. Tez yazımı

**Kilometre taşları** (2 haftalık sprintler; ayrıntı `docs/10`):

| Tarih | Kilometre taşı | Çıktı |
| --- | --- | --- |
| Kasım 2026 (S1) | v0.4 sunumu (bu dosya ve uygulama) | Danışman onayı: başlık ve çerçeve |
| Aralık 2026 (S2–S3) | Saatlik talep (EPİAŞ + Demand.ninja), G2 profil doğrulaması | **B1 bildiri özeti** |
| Şubat 2027 (S6–S7) | G1/G2 tam karşılaştırma, OSM ve GHSL duyarlılığı | **Makale A taslağı** |
| Mart 2027 (S8–S10) | Shapley ile proje sınırı, tersine analiz ve ROI, referans sınıfı | **Makale B taslağı** |
| Nisan–Mayıs 2027 (S11–S14) | Tez bölümleri, gönderimler | Tez taslakları |
| Haziran 2027 (S15) | Teslim | Tez |

**Kalite kapıları** (her sprint sonunda):
1. Bütün testler geçiyor.
2. Kayıtsız veya lisansı belirsiz veri yok.
3. Sentetik veri sonuç üretmiyor.
4. Her yeni sonucun bir G2 karşılaştırması ya da yazılı sınırlılığı var.
5. Karar günlüğü güncel.

**Riskler:**

| Risk | Olasılık | Etki | Önlem |
| --- | --- | --- | --- |
| EPİAŞ verisi gecikir | Orta | Yüksek | Hesap açılınca tek komutla çekilir (`make epias`); yedek: kayıtlı ülkelerin açık verisiyle yöntem gösterimi |
| OSM tamlığı sonuçları saptırır | Yüksek | Yüksek | GHSL ile çift kaynak; tamlık özelliği; G2 ile İBB bina envanteri |
| PED Veritabanı lisansı | Orta | Orta | Erken teyit (S2); yoksa JPI kitapçığı ve Zhang vd. (2021) |
| Kapsam genişlemesi | Yüksek | Yüksek | Pusula (`docs/00`), planlı katmanlar ancak öncelik sırasıyla |

**Açık kararlar (danışmandan):** başlık; EPİAŞ hesabı; İBB veri talebi önceliği; hedef dergiler.

---

## 7. Ayrıntılı belgeler

| Belge | Ne var |
| --- | --- |
| `docs/00_TEZ_PUSULASI.md` | Tek sayfa özet |
| `docs/13_sistem_mimarisi.md` | Gereksinimler, katmanlar, veri sözleşmesi, karar motoru |
| `docs/11_veri_kaynaklari.md`, `docs/14_acik_kaynak_atlasi.md` | Kaynak kütüğü, atlas |
| `docs/15_proje_elverislilik.md` | Proje elverişliliği çerçevesi ve literatür |
| `docs/08_tersine_analiz.md` | Tersine analiz matematiği |
| `docs/07_kirilganlik_analizi.md` | Kırılganlık analizi |
| `docs/10_sprint_plani.md` | Sprint planı |
| `docs/05_karar_gunlugu.md` | Kararlar (K-001 … K-035) |
| `docs/02_literatur_haritasi.md`, `docs/references.bib` | Literatür |
| `docs/LOCAL_SETUP.md` | Kurulum |
