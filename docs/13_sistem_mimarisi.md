# 13: Sistem Mimarisi (pedx platformu)

*Tarih: 2026-11-08 · Sürüm: mimari v1 · Sahibi: tez ekibi · İlgili kararlar: K-025 (yalnızca küresel açık veri), K-028 (tek eksen), K-029 (özellik sözleşmesi), K-030 (karar motoru)*

## 1. Amaç ve sistem bağlamı

**Görev tanımı:** Dünyanın herhangi bir A noktası (ya da bölgesi) için şu dört soruyu açık veriyle, açıklanabilir ve tekrar üretilebilir biçimde yanıtlamak:

1. **Olur mu?** Burada bir PED veya kentsel dönüşüm projesi fiziksel olarak mümkün mü, bağlam bu tür projelere benziyor mu?
2. **Neden olmaz?** Engelleyen etkenler hangileri (fiziksel, yapısal, sosyo-ekonomik)?
3. **Ne yapılırsa olur?** En küçük ve uygulanabilir müdahale paketi nedir?
4. **Değer mi?** Paketin yatırım getirisi nedir (NPV, IRR, geri dönüş süresi, CO₂)?

**Paydaşlar:** tez ekibi (danışman ve öğrenci), belediye planlamacıları (İBB), araştırmacılar, yatırımcı veya kooperatifler.

## 2. Gereksinimler

| Kod | Gereksinim | Tür | Doğrulama |
| --- | --- | --- | --- |
| R1 | Girdiler yalnızca küresel açık veri; yerel veri yalnızca doğrulamada | Kısıt | Kaynak kütüğü (11), katalog lisans alanı |
| R2 | Sentetik veya yer tutucu değer hiçbir çıktıya girmez | Kısıt | Kod incelemesi; `synthetic` yalnızca testlerde |
| R3 | Her özellik kayıtlı (ad, aile, birim, kaynak, lisans, durum) | İşlevsel | `validate_columns` dışa aktarımı engeller |
| R4 | Mekânsal birim H3 (r8, r9, r10), çok çözünürlüklü | İşlevsel | T5 testleri |
| R5 | Enerji göstergeleri saatlik fizikten türetilir | İşlevsel | T1, T2; enerji korunumu denetimi |
| R6 | Her skorun açıklaması var (kesin katkı, Shapley, SHAP) | İşlevsel | Verimlilik aksiyomu testleri |
| R7 | Tersine analiz fiziksel ve uygulanabilir değişkenlerde; sonuç kesin modelle denetlenir | İşlevsel | 7 denetim; ızgara ve ikiye bölme testleri |
| R8 | ROI, kaynaklı maliyet ve fiyatlarla; kaynaksız değer yoksa ROI gösterilmez | İşlevsel | Parametre kütüğü |
| R9 | Tek komutla yerelde kurulum ve çalıştırma | İşletim | `make` hedefleri, Docker |
| R10 | Her şehir için aynı hat (yalnızca sınır ve koordinat değişir) | Ölçeklenebilirlik | İkinci şehir koşusu (S10) |

## 3. Katmanlı mimari

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ L6  Sunum: web demo (Leaflet + OSM), raporlar, ileride REST API (FastAPI)    │
├──────────────────────────────────────────────────────────────────────────────┤
│ L5  KARAR MOTORU (K-030)                                                     │
│     ① Fiziksel fizibilite   ② Benimseme ve bağlam benzerliği   ③ ROI         │
│     → "olur mu / neden / ne yapılırsa / değer mi" yorumu                     │
├──────────────────────────────────────────────────────────────────────────────┤
│ L4  Açıklama ve tersine analiz (XAI)                                         │
│     kesin katkılar · sıra aralıkları · Shapley (graf) · SHAP (öğrenen model) │
│     · fiziksel tersine analiz (JAX) · eyleme dönük karşı-olgusal analiz      │
├──────────────────────────────────────────────────────────────────────────────┤
│ L3  Motorlar                                                                 │
│     Fizik: saatlik G/D, batarya, denge  │ Graf: paylaşım oyunu, sınır büyütme │
│     Öğrenen: PED benzerlik modeli (PU öğrenme, gruplu mekânsal çapraz dogr.) │
├──────────────────────────────────────────────────────────────────────────────┤
│ L2  H3 ÖZELLİK DEPOSU (altıgen veri küpü)                                    │
│     enerji · yapılı çevre · demografi · POI · ekonomi · ulaşım · çevre ·     │
│     iklim · sosyal   (katalog = veri sözleşmesi, K-029)                      │
├──────────────────────────────────────────────────────────────────────────────┤
│ L1  Ayrıştırma, köken bilgisi, lisans, kalite (tamlık) ölçümleri             │
├──────────────────────────────────────────────────────────────────────────────┤
│ L0  Bağlayıcılar: OSM/Overpass · GHSL · UNdata · OWID/Ember · PVGIS ·        │
│     WorldPop · ESA WorldCover · Copernicus DEM · ERA5 · PED Veritabanı ·     │
│     GDELT/açık metin (sosyal) · …   (önbellek: data/raw)                     │
└──────────────────────────────────────────────────────────────────────────────┘
          ▲ G2 doğrulama veri yolu (yalnızca okuma): İBB · TEDAŞ · EPİAŞ · TÜİK · Demirel vd. 2025
```

**Kod eşlemesi:**

| Katman | Modül |
| --- | --- |
| L0, L1 | `pedx.ingest` (osm, pvgis, global_data) |
| L2 | `pedx.features` (registry, layers) |
| L3 | `pedx.energy`, `pedx.graph`; öğrenen motor S5–S7'de |
| L4 | `pedx.index`, `pedx.xai`, `pedx.inverse` |
| L5 | `pedx.decision` (S6–S9) |
| L6 | `web/`, `examples/build_demo_caferaga.py` |

## 4. Veri sözleşmesi (L2)

- **Anahtar:** `cell` (H3 kimliği, çözünürlük meta veride).
- **Sütun adı:** `<aile>_<ad>`. Her sütunun `FeatureSpec` kaydı var: `family, label_tr, unit, source, license, status, role, note`.
- **Kurallar:**
  - Kayıtsız ya da `planned` durumundaki sütun dışa aktarılamaz.
  - Sayımlar hücre içine toplanır, oranlar hücre içinde hesaplanır, yoğunluklar gerçek H3 alanına bölünür.
  - Tamlık göstergeleri de özellik olarak tutulur (ör. `built_levels_known_share`), çünkü OSM tamlığı başlı başına bir yanlılık kaynağı.
- **Çıktılar:**
  - `data/processed/<alan>_h3r<k>_features.csv`
  - `feature_catalog.csv`
  - `web/data/*`

**Şu an:** 41 etkin özellik (enerji, yapılı çevre, demografi, POI ve iki XAI ayrıştırma katmanı), 17 planlanan özellik (ekonomi, ulaşım, çevre, iklim, GHSL yapı katmanları).

## 5. Karar motoru (L5)

| Bileşen | Soru | Yöntem | Veri |
| --- | --- | --- | --- |
| ① Fiziksel fizibilite | Enerji dengesi ve öz-yeterlilik tutar mı? | Saatlik fizik, mutlak indeks | L2 enerji ve yapılı çevre özellikleri |
| ② Bağlam benzerliği | Bu bağlam gerçek PED projelerine benziyor mu? | **PU öğrenme**: PED Veritabanı projeleri pozitif, rastgele arka plan etiketsiz. Kalibre edilmiş olasılık; ülke ve bölge gruplu çapraz doğrulama | L2'nin tamamı |
| ③ ROI | Müdahale paketi kendini öder mi? | NPV, IRR, geri dönüş süresi, CO₂ (Ember karbon yoğunluğu) | Kaynaklı maliyet ve tarifeler |
| Yorum | Olur mu, neden olmaz, ne yapılırsa olur? | ① ve ②'nin dört bölgeli matrisi; ① için fiziksel tersine analiz, ② için **yalnızca eyleme dönük özelliklerde** karşı-olgusal analiz; ③ ile sıralama | — |

**Dört bölgeli yorum matrisi:**

| | Bağlam PED projelerine benziyor | Benzemiyor |
| --- | --- | --- |
| **Fiziksel olarak mümkün** | "Hazır aday": ROI'ye göre önceliklendir | "Fiziksel potansiyel var, bağlam hazır değil": kurumsal ve sosyal engeller |
| **Mümkün değil** | "Bağlam hazır, enerji yetmiyor": tersine fiziksel reçete | "Uzun vadeli dönüşüm": ROI ile gerçekçilik testi |

**Eyleme dönük ve değişmez özellikler:**
- **Değişmez:** iklim, eğim, ülke GSYH'si.
- **Eyleme dönük:** PV alanı, depolama, yük dönüşümü, POI karması ve kullanım dönüşümü (kentsel dönüşüm senaryosu), EV şarj, yalıtım.

Karşı-olgusal arama yalnızca eyleme dönük özelliklerde ve fiziksel sınırlar içinde yapılır.

**Bilimsel uyarılar (tezde açıkça yazılacak):**
1. ② bir **benzerlik ve benimseme** modelidir, nedensel değildir. "PED projeleri bugüne kadar nerede yapıldı?" sorusunu öğrenir; seçim yanlılığı (AB fonlu, Kuzey ve Batı Avrupa) içerir.
2. Bölgeler arası aktarım (Avrupa'dan İstanbul'a) **bölge dışarıda bırakılarak** sınanır; düşük güven açıkça raporlanır.
3. Karşı-olgusal analiz "ne değişirse model farklı söyler" sorusunu yanıtlar. Fiziksel tersine analiz ise "ne yapılırsa enerji dengesi tutar" sorusunu yanıtlar. Yalnızca ikincisi nedenseldir.

## 6. "Her veriyi kat" ilkesi ve istatistiksel disiplin

Geniş özellik deposu (yüzlerce sütun) aşırı öğrenme ve sahte ilişki üretir. Önlemler:
- (a) Özellikler ailelere göre gruplanır; önem **aile düzeyinde** de raporlanır (gruplu SHAP veya permütasyon).
- (b) Mekânsal blok ve ülke gruplu çapraz doğrulama yapılır; rastgele bölme kullanılmaz.
- (c) Çoklu karşılaştırma için FDR kontrolü ve permütasyon testleri uygulanır.
- (d) Tanımsal bileşenler hedeften dışlanır (ör. denge ∝ taban alanı / nüfus).
- (e) Tamlık göstergeleri kontrol değişkeni olarak eklenir (OSM'nin iyi haritalandığı yer ≠ PED).
- (f) Sade bir referans model (lojistik veya GAM) her zaman karmaşık modelle birlikte raporlanır.

## 7. Sosyal katman: insanların yorumları, eğilimleri ve ilgisi

**Google yorumları kullanılamaz.**
- Google Maps Platform hizmet şartları içeriğin kazınmasını ve kalıcı depolanmasını yasaklıyor. Veri açık lisanslı da değil, dolayısıyla R1 kuralını karşılamıyor.
- Ayrıca kişisel veri riski taşıyor (KVKK ve GDPR).

**Açık alternatifler (her birinin lisansı ve kapsamı S3'te teyit edilecek):**

| Kaynak | Ölçek | Ne verir | Not |
| --- | --- | --- | --- |
| **GDELT** (haber olay ve ton veritabanı) | Şehir ve konum | Enerji, iklim ve kentsel dönüşüm haberlerinin tonu ve yoğunluğu | Açık; küresel |
| **World Values Survey / European Values Study** | Ülke ve bölge | Çevre ve iklim tutumları, güven, katılım | Araştırma için serbest (kayıtla) |
| **Mangrove Reviews** | Nokta | Açık lisanslı kullanıcı yorumları | Kapsamı dar; deneysel |
| **Wikipedia ve Wikivoyage metinleri** | Yer | Mahalle karakteri (dil modeliyle konu çıkarımı) | CC BY-SA |
| **OSM etiketleri** | Hücre | Kooperatif, topluluk merkezi, geri dönüşüm noktası, bisiklet altyapısı | ODbL; "çevreci altyapı" vekilleri |

**Yöntem:** Metinlerden konu ve duygu çıkarılır (çok dilli, açık bir dil modeliyle). Hücre ya da şehir düzeyinde "sosyal hazırlık" özellikleri üretilir. Bunlar ② numaralı modele aday özellik olarak eklenir; katkıları gruplu SHAP ile ölçülür.

**Sonuç beklentisi açıkça yazılacak:** Etki bulunmazsa bu da bir bulgu.

## 8. ROI hesaplayıcı (L5-③)

**Girdi:** tersine analizin müdahale paketi u (m² PV, kWh depolama, kabuk iyileştirme, yük dönüşümü). Fizik motoru bu paketten yıllık enerji akışlarını üretir.

**Formüller:**
- Fayda_t = (önlenen şebeke alımı × tarife) + (satılan fazla enerji × satış fiyatı) + (önlenen CO₂ × karbon fiyatı)
- NPV = −CAPEX(u) + Σ_t (Fayda_t − O&M_t) / (1+r)^t
- Ayrıca IRR, geri dönüş süresi ve seviyelendirilmiş maliyet (LCOE) hesaplanır.

**Parametre kaynakları:**

| Parametre | Kaynak | Not |
| --- | --- | --- |
| PV ve batarya kurulum maliyeti | IRENA *Renewable Power Generation Costs* (ülke ya da bölge) | — |
| Şebeke emisyon yoğunluğu | Ember (CC BY 4.0) | — |
| Karbon fiyatı | Senaryo (ör. AB ETS) | — |
| İskonto oranı ve ömür | IRENA veya NREL ATB varsayımları | — |
| Elektrik tarifesi | **Küresel açık bir kaynak yok** | Kullanıcı senaryo girdisi; kaynağı her koşuda zorunlu olarak kaydedilir (Türkiye için EPDK tarifesi) |

Duyarlılık için tornado grafiği ve Monte Carlo kullanılacak. Kaynaksız parametre olduğunda ROI hesaplanmıyor ve "parametre eksik" uyarısı gösteriliyor (R8).

## 9. Kalite ve doğrulama

| Düzey | Ne | Araç |
| --- | --- | --- |
| Birim | Fizik, katalog, ayrıştırıcılar | `pytest` (53 test) |
| Bütünleşik | Uçtan uca demo yapımı | `make build` |
| Bilimsel (G2) | Nüfus, talep, PV, saatlik profil | Doğrulama paneli ve Makale A |
| Model | PU modelinin aktarım performansı | Bölge dışarıda bırakılarak çapraz doğrulama, kalibrasyon eğrileri |

## 10. Dağıtım ve çalıştırma

- **Yerel kurulum:** `docs/LOCAL_SETUP.md`. `make serve` hazır demoyu açar; `make data && make build` her şeyi sıfırdan üretir.
- **Docker:** `docker build -t pedx .`, ardından `docker run -p 8765:8765 pedx`.
- **İleride:** FastAPI ile `/assess?lat=..&lon=..` uç noktası (A noktası sorgusu), zamanlanmış veri güncellemesi.

## 11. Teslim planı (sprintlerle)

| Sprint | Mimari teslim |
| --- | --- |
| S1 | ✅ L0–L2 omurgası, POI katmanı, katalog, web v0.2, yerel kurulum |
| S2 | Saatlik talep (karar) → saatlik L3; dasimetrik nüfus |
| S3 | Ekonomi katmanı (Kummu, Chen); GHSL yapı katmanları; sosyal katman lisans araştırması |
| S4–S5 | PED Veritabanından pozitif örnekler; PU modeli; gruplu SHAP |
| S6–S7 | Karar motoru: dört bölgeli matris; eyleme dönük karşı-olgusal analiz |
| S8 | ROI hesaplayıcı (kaynaklı parametrelerle) |
| S9–S10 | İkinci ve üçüncü şehir; A noktası API'si |
