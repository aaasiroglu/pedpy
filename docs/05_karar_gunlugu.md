# 05: Karar Günlüğü (ADR)

Her karar şu biçimde kaydedilir: **bağlam → karar → gerekçe → sonuçlar → durum**.
Durumlar: `Önerildi` · `Kabul` · `Reddedildi` · `Değiştirildi (K-xxx)`.

---

### K-001: Çekirdek kütüphane yalnızca numpy ve pandas'a bağımlı olacak
- **Bağlam:** Geliştirme ortamında PyPI'a erişim yok; `scipy`, `shapely` ve `pytest` kurulamıyor. Kullanıcı tarafında da az bağımlılık tekrarlanabilirliği artırıyor.
- **Karar:** `energy`, `weighting`, `mcdm`, `prescribe` ve `expansion` çekirdeği yalnızca numpy ve pandas kullanacak. BWM için küçük bir yerleşik LP çözücü yazılacak. Rank korelasyonları için `_stats` modülü yazılacak. `shapely`, `h3`, `requests`, `duckdb` ve `torch` **isteğe bağlı ek paketler** (`pedpy[geo]`, `pedpy[ml]`) olacak.
- **Sonuç:** scipy erişilebilir olduğunda çapraz kontrol testleri eklenecek.
- **Durum:** Önerildi

### K-002: Dokümantasyon ve planlama repo içinde `docs/` altında tutulacak
- **Bağlam:** Kullanıcı tüm adımların yazılı ve not alınarak ilerlemesini istedi.
- **Karar:** Markdown dosyaları + `references.bib`; sürüm kontrolü git ile.
- **Durum:** Kabul

### K-003: SSR, SCR ve PAR tanımları ve NaN politikası
- **Karar:**
  - SSR = ΣE_sc/ΣD (talep yoksa NaN)
  - SCR = ΣE_sc/ΣG (üretim yoksa NaN; T1)
  - PAR = tepe şebeke çekiş gücü / ortalama talep gücü (PV her saati karşılıyorsa 0)
- **Gerekçe:** Salom vd. (2014) ve Luthander vd. (2015) ile uyumlu, boyutsuz bir maliyet kriteri. "Tepe/ortalama" tanımı aynı yıllık talepteki iki adayı adil biçimde karşılaştırıyor (T2).
- **Açık nokta:** Alternatif olarak tepe çekişin tepe talebe oranı (∈ [0,1]) de düşünülebilir. Danışmanla netleştirilecek.
- **Durum:** Önerildi

### K-004: MARCOS'ta sıfır ve negatif değer politikası
- **Bağlam:** Maliyet kriterinde AI_j/x_ij, x = 0 için tanımsız (R2).
- **Seçenekler:**
  - (a) Her sütuna x + ε·aralık ötelemesi uygulamak (basit ama ötelemeye duyarlı)
  - (b) Maliyet kriterlerini önceden fayda kriterine çevirmek: x' = max − x + ε
  - (c) Tanımsızsa hata vermek, kullanıcı karar versin
- **Öneri:** Varsayılan (c). (a) ve (b) parametreyle seçilebilsin ve tezde duyarlılık olarak raporlansın.
- **Durum:** Önerildi

### K-005: MARCOS ≡ κ·WSM eşdeğerliği açıkça raporlanacak
- **Bağlam:** f(K_i) = κ·S_i (Xie & Zou, 2025). Bu repoda rastgele 12×6 matrisle sayısal olarak doğrulandı: `np.allclose` True; f(K⁻) aralığı 0, f(K⁺) aralığı ~1e-16.
- **Karar:**
  - README'deki T4 ("Smooth-MARCOS yakınsaması") yeniden tanımlanacak: T4' = özdeşlik testi + Stević 2020 örneğinin yeniden üretimi.
  - Smooth-MARCOS tezde katkı olarak sunulmayacak; yalnızca ideal değer yumuşatmasının etkin ağırlığa etkisi olarak tartışılacak.
  - Eşdeğerlik **XAI-1'in (kesin Shapley) dayanağı** olarak kullanılacak.
- **Durum:** Önerildi

### K-006: Geo-AI modülleri (FT-Transformer, MaskCLIP + FeatUp, nnPU) kapsam dışında
- **Bağlam:** Kapsam riski (R8). Her biri ayrı bir tez konusu büyüklüğünde. Etiketli veri ve GPU gerektiriyor.
- **Karar:** Gelecek çalışma olarak yazılacak. Yerine 🟩 Graf-2 (GNN ile yükseklik ve yaş tamamlama) ve bir GBM karşılaştırması yapılacak.
- **Durum:** Önerildi

### K-007: Paket dizin yapısı
- **Bağlam:** README ile mimari metni farklı dizinler öneriyor.
- **Karar:** README'deki işlevsel yapı korunacak (`ingest`, `energy`, `weighting`, `mcdm`, `expansion`, `prescribe`, `validation`). Üstüne `xai`, `graph` ve `nlp` alt paketleri ile `pipelines` eklenecek. `core/building.py` gibi ayrı veri sınıfları yerine `energy.records` kullanılacak (tek doğruluk kaynağı).
- **Durum:** Önerildi

### K-008: Entropi ağırlığı yön düzeltilmiş normalize veride hesaplanacak
- **Gerekçe:** R3; Zhu vd. (2020).
- **Durum:** Önerildi

### K-010: Danışman Hande Demirel
- **Kaynak:** Kullanıcının beyanı (2026-11-08). Tez, Demirel vd. (2025) ve Alpagut vd. (2021) hattının devamı olarak konumlanacak.
- **Durum:** Kabul

### K-011: Öncelik XAI ve graf; NLP Bonus katmana iniyor
- **Kaynak:** Kullanıcı kararı (2026-11-08).
- **Sonuç:** Graf-1 (sınır genişletme ve graf-XAI) ile XAI-2 (eylem uzayında karşı-olgusal yollar) Güçlü katmandan **Zorunlu** katmana çıkıyor. NLP-1 ve NLP-2 Bonus katmanda kalıyor. Yol haritası (04) güncellendi.
- **Durum:** Kabul

### K-012: Kaynaksız sabit kuralı
- **Karar:** Koddaki her sayısal varsayımın (katsayı, eşik, azalma mesafesi) ya bir kaynağı olacak ya da duyarlılık analizine girecek. Sabitler tek bir `assumptions` tablosunda, kaynak sütunuyla tutulacak.
- **Gerekçe:** 07, D5.
- **Durum:** Önerildi

### K-013: Paket adı değişmeli
- **Bağlam:** `pedpy` adı PyPI'da Jülich'in yaya dinamiği kütüphanesine ait (07, A1).
- **Seçenekler:** `pedscape`, `pedkit`, `posidistrict`, `plusdistrict`, `pedx` (müsaitlik kontrol edilecek). Repo adı `pedpy` olarak kalabilir; PyPI ve `import` adı değişir.
- **Durum:** Kabul (kullanıcı onayı 2026-11-08)

### K-014: Mutlak, fiziksel hedefe bağlı PEB Hazırlık İndeksi
- **Karar:** Ana çıktı, sabit referanslarla [0,1]'e eşlenen değer fonksiyonlarından oluşan, şehirler arası karşılaştırılabilir bir indeks olacak. Kümeye göreli ÇKKDS (MARCOS, TOPSIS, PROMETHEE) "şehir içi önceliklendirme" görünümü olarak kalacak.
- **Gerekçe:** 07, B1 (sıra tersinmesi; küresel karşılaştırılamazlık).
- **Durum:** Kabul (kullanıcı onayı 2026-11-08)

### K-015: Kriter seti iki eksende yeniden yapılanacak
- **Karar:** Enerji ekseni: G/D yıllık denge, SSR, şebeke stresi (yüzdelik). Dönüşüm ekseni: ısıl iyileştirme ihtiyacı, işlev karması, altyapı. C1 (kWh/m²) ana kriterden çıkarılıp tanısal göstergeye dönüşecek. C6 isteğe bağlı olacak.
- **Gerekçe:** 07, B2, C2, D3.
- **Durum:** Kabul (kullanıcı onayı 2026-11-08)

### K-016: Reçete kriter uzayında değil, eylem uzayında kurulacak
- **Karar:** Karar değişkenleri müdahale seviyeleri (PV m², batarya kWh, yalıtım, EV) olacak. Hedef fiziksel olacak (G/D ≥ 1, SSR ≥ s*). Her aday çözüm için saatlik simülasyon yeniden çalıştırılacak. K-005'teki "kesin knapsack çözücü" fikri bu kararla geçersiz kalıyor.
- **Gerekçe:** 07, E1.
- **Durum:** Kabul (kullanıcı onayı 2026-11-08)

### K-017: Mekânsal gecikme ve Smooth-MARCOS bırakılıyor
- **Gerekçe:** 07, B5 ve B6.
- **Durum:** Kabul (kullanıcı onayı 2026-11-08)

### K-018: Graf katkısı "toplamsal olmayan bölgeselleştirme" ve "Shapley ile graf-XAI" olarak çerçevelenecek
- **Karar:** Küme öz-yeterliliği işbirlikçi bir oyun olarak tanımlanacak. Her adanın Shapley katkısı kesin olarak hesaplanacak (küme ≤ 12 ada). Karşılaştırma yöntemleri: max-p, rastgele bitişik büyütme, küçük n için tam sayım.
- **Gerekçe:** 07, E3.
- **Durum:** Kabul (kullanıcı onayı 2026-11-08)

### K-019: Ana mekânsal birim H3 altıgenleri; yapı adası kaldırıldı
- **Kaynak:** Kullanıcı kararı (2026-11-08).
- **Gerekçe:** Yapı adası sınırları ülkeden ülkeye değişiyor ve keyfi. H3, küresel ölçekte tek tip 6 komşulu bir graf sağlıyor; bu da graf yöntemlerini ve çok çözünürlüklü (MAUP) analizi kolaylaştırıyor. PEB sınırı, altıgenlerin graf üzerinde kümelenmesiyle **ortaya çıkan** bir çıktı oluyor.
- **Bilinen sınırlılıklar:** Binalar ağırlık merkezine göre hücreye atanıyor; boş hücrelerin (park, deniz) bağlantısı ayrıca ele alınmalı; H3 komşuluğu elektrik şebekesi topolojisiyle aynı değil (sanal PEB çerçevesi).
- **Durum:** Kabul

### K-020: Türevlenebilirlik MARCOS'ta değil, fiziksel modelde
- **Karar:** Gradyan, müdahale → saatlik akışlar → göstergeler → mutlak indeks zinciri üzerinden alınıyor (JAX). Yumuşatma yalnızca aramada kullanılıyor; raporlanan her sonuç kesin modelle yeniden hesaplanıp denetleniyor. Sadakat, ρ > 0,999 yerine **kanıtlanabilir hata sınırıyla** gösteriliyor.
- **Gerekçe:** docs/08, bölüm 2.
- **Durum:** Kabul

### K-021: Ana veri kaynağı OSM ve diğer ücretsiz açık veriler; şebeke stresi CVaR ile ölçülüyor
- **Karar:** Binalar OSM'den (Overpass), ışınım PVGIS'ten alınıyor. İBB verisi doğrulama katmanı (G2) olarak kullanılıyor. Şebeke stresi, tek bir maksimum saat yerine en yüksek %1'lik saatlerin ortalamasıyla (CVaR_0.99) hesaplanıyor. Tepe rahatlaması = 1 − CVaR(I)/CVaR(D); keyfi bir referans değer gerektirmiyor.
- **Durum:** Kabul

### K-022: Bulut ortamı
- **Karar:** Yalnızca bu repo için kişisel `pedpy` ortamı oluşturuldu: PyPI erişimi açık; izin verilen sunucular `overpass-api.de` ve `re.jrc.ec.europa.eu`.
- **Durum:** Kabul

### K-023: Takvim
- **Karar:** 2 haftalık sprintler; Haziran 2027 başında tez teslimi, 2 makale ve 1 bildiri (`10_sprint_plani.md`).
- **Durum:** Kabul

### K-024: Danışman sunumu web tabanlı bir demo (MVP) olarak yapılacak
- **Kaynak:** Kullanıcı kararı (2026-11-08). Sunum daha sonraki bir oturumda hazırlanacak.
- **Biçim:** OSM altlık haritası üzerinde H3 hücre katmanı ve bilimsel bir arayüz: skorlar, sıra aralıkları, katkılar, PEB sınırı ve Shapley katkıları, bütçe–skor Pareto eğrisi. `docs/09_v0_sunum.md` içeriğin metin kaynağı olarak kalıyor.
- **Teknik öneri (henüz uygulanmadı):** pedx çıktılarını GeoJSON ve JSON olarak dışa aktaran bir `pedx.export` modülü ve sunucusuz bir statik web sayfası (Leaflet ile OSM karoları, H3 altıgenleri, grafikler). Böylece demo tekrarlanabilir olur ve paylaşılabilir bir bağlantıyla açılabilir.
- **Durum:** Kabul (uygulama sonraya)

### K-025: Girdiler yalnızca küresel ölçekte açık veriden alınacak
- **Kaynak:** Kullanıcı kuralları (2026-11-08): "global olarak open olmayan verileri kullanmamalıyız"; "hiçbir veri dummy olmamalı"; "İstanbul ölçeğinde özel verilerle yalnızca validasyon yapılacak".
- **Karar:** G1 girdileri OSM, JRC GHS-POP, UNSD/UNdata, UN WPP ve Ember (OWID üzerinden), PVGIS ile literatür parametreleri (aralıklarıyla). TEDAŞ, EPİAŞ, İBB ve TÜİK yalnızca G2 doğrulaması. Sentetik profil ve yer tutucu değerler hiçbir çıktıya girmiyor; eksik veri "eksik" olarak gösteriliyor. Ayrıntı: `11_veri_kaynaklari.md`.
- **Sonuç:** `pedx.synthetic` yalnızca testlerde kalıyor; v0 iş akışındaki varsayım tablosu (K-012) yerini kaynaklı parametrelere bırakıyor.
- **Durum:** Kabul

### K-026: Web demo v0.1 yalnızca yıllık göstergeleri içeriyor
- **Gerekçe:** Küresel ve açık bir saatlik konut talep kaynağı henüz seçilmedi (11, §3).
- **Karar:** Demo yıllık denge, PV potansiyeli, gereken çatı payı, belirsizlik aralığı ve G2 doğrulama panelini içeriyor. Saatlik göstergeler kaynak seçilince eklenecek.
- **Durum:** Kabul

### K-027: Önceki çalışma (2024) "Aşama 1: sosyo-kurumsal hazırlık" katmanı olarak yeniden kurulacak
- **Karar:** RF tabanlı PED benimseme modeli şu düzeltmelerle B1 bildirisine aday: PED Veritabanı koordinatları, H3 özellikleri, gruplu mekânsal çapraz doğrulama, OSM tamlık kontrolü, SHAP. pedx'in fiziksel skoruyla çakıştırılacak (12, §3).
- **Durum:** Önerildi

### K-028: Proje tek eksende toplandı
- **Kaynak:** Kullanıcı isteği (2026-11-08): bütün bilgi birikimi birleşsin; proje derli toplu ve sade olsun.
- **Karar:**
  - `00_TEZ_PUSULASI.md` tek doğruluk kaynağı oldu: 3 soru, 3 katkı, 3 yayın.
  - Sentetik ve yer tutucu değerli v0 hattı kaldırıldı (`pipeline.py`, `assumptions.py`, `examples/v0_caferaga.py`, `results/v0`).
  - 01, 03, 04 ve 09 arşiv olarak işaretlendi.
  - NLP, GNN, Geo-AI ve Smooth-MARCOS kapsam dışı.
- **Durum:** Kabul

### K-029: H3 özellik deposu ve veri sözleşmesi
- **Karar:** Altıgen başına bütün açık veri katmanları kayıtlı özellikler olarak tutuluyor (`pedx.features`). Kayıtsız ya da planlanan sütun dışa aktarılamıyor. Aileler: enerji, yapılı çevre, demografi, POI, ekonomi, ulaşım, çevre, iklim, sosyal. "En az alakalı veri bile" katalogda yer alabilir; ancak modelleme gruplu doğrulama ve çoklu test kontrolüyle yapılır (docs/13 §6).
- **Durum:** Kabul

### K-030: Karar motoru: "olur mu, neden olmaz, ne yapılırsa olur, değer mi"
- **Kaynak:** Kullanıcı hedefi (2026-11-08): bir A noktasında PED projesi olup olmayacağını yorumlamak, olmuyorsa nedenini ve ne yapılırsa olacağını küresel ölçekte çıkarmak, kentsel dönüşüm ROI hesaplayıcısı gibi çalışmak.
- **Karar:** ① fiziksel fizibilite, ② PED benzerliği (PU öğrenme, PED Veritabanı), ③ ROI. Bunlar dört bölgeli bir yorum matrisinde birleşiyor. Karşı-olgusal analiz yalnızca eyleme dönük özelliklerde yapılıyor (docs/13 §5, §8).
- **Durum:** Kabul (S4–S8 uygulama)

### K-031: Google yorumları kullanılmayacak; açık sosyal kaynaklar araştırılacak
- **Gerekçe:** Google Maps Platform şartları içeriğin kazınmasını ve kalıcı depolanmasını yasaklıyor; veri açık lisanslı değil; kişisel veri riski var (KVKK/GDPR).
- **Karar:** GDELT, WVS/EVS, Mangrove, Wikipedia/Wikivoyage ve OSM etiketleri lisanslarıyla birlikte S3'te araştırılacak (docs/13 §7).
- **Durum:** Önerildi

### K-032: Görüntü, morfoloji ve erişilebilirlik katmanları
- **Kaynak:** Kullanıcı önerileri (2026-11-08): uydu görüntüsü gömmeleri, Mapillary, kentsel morfoloji kütüphanesi, yaya erişilebilirliği.
- **Karar:**
  - momepy ile 7 morfoloji özelliği etkin (ortak duvar oranı fiziksel olarak ısı kaybına bağlı).
  - OSM yaya ağı ve Dijkstra ile 7 erişilebilirlik özelliği etkin ("10 dakikalık yürüme", günlük ihtiyaç tamlığı).
  - Uydu gömmeleri (AlphaEarth veya açık temel model) ile Mapillary planlı. Gömmeler ayrı bir vektör deposunda tutulacak; tabloya yorumlanabilir PCA bileşenleri girecek.
  - PedPy (Jülich) deneysel yaya yörüngesi analizi için olduğundan kapsam dışı.
  - Atlas: `14_acik_kaynak_atlasi.md`.
- **Durum:** Kabul

### K-033: Analiz birimi "proje adayı"; tez proje elverişliliği olarak çerçevelendi
- **Kaynak:** Kullanıcı (2026-11-08): "amaç mekânsal analiz değil, PED bir proje; projeye elverişlilik analizi".
- **Karar:**
  - Birim P = (sınır, müdahale paketi, bağlam, finansman).
  - Ölçüt aileleri Krangsås vd. (2021)'in 7 alanına eşlendi.
  - Gerçek PED projeleri Flyvbjerg (2014) anlamında bir referans sınıfı olarak kullanılacak ("dış bakış").
  - Önerilen başlık güncellendi (00, 15).
- **Durum:** Kabul (kullanıcı onayı bekleniyor: başlık)

### K-034: Saatlik konut talebi: EPİAŞ ulusal yük ile Demand.ninja
- **Kaynak:** Kullanıcı kararı (2026-11-08).
- **Karar:** D_t = E·[(1−w)b_t + w·m_t].
  - b_t: ulusal saatlik yükten (EPİAŞ, G1; küresel katalog kuralıyla) hava bileşeni çıkarılmış taban şekli.
  - m_t: Demand.ninja ısıtma ve soğutma şekli (ERA5, Open-Meteo).
  - w: ulusal yükün Demand.ninja derece-saatlerine regresyonundan; serbest sabit yok.
  - EPİAŞ mesken (AYEDAŞ) profili yalnızca G2 doğrulaması.
  - Demand.ninja BSD-3 lisansıyla projeye dahil edildi, pandas 2 için iki satır yamalandı.
  - EPİAŞ kimlik bilgileri yalnızca ortam değişkenlerinden okunuyor.
- **Durum:** Kabul (EPİAŞ verisi bekleniyor)

### K-035: Veri gölü: küresel katalog, AOI bağlayıcıları, raster → H3 motoru
- **Kaynak:** Kullanıcı (2026-11-08): "dünyadaki küresel ölçekli raster ve vektör verilerle devasa bir veritabanı".
- **Karar:**
  - Bütün veri kopyalanmıyor. 35 veri setlik katalogda her setin bağlayıcısı var; bir AOI geldiğinde yalnızca gereken parça çekilip önbelleğe alınıyor.
  - `zonal_h3` her rasteri H3 özelliklerine dönüştürüyor.
  - İlk parti: GHSL yapı alanı, hacmi ve yüksekliği (5 katman, CC BY 4.0).
  - Ana belge: `PROJE_DOSYASI.md`.
- **Durum:** Kabul

### K-036: Yer gözlemi katmanları (SUHII mantığıyla): Landsat LST, Sentinel-2, Copernicus DEM
- **Kaynak:** Kullanıcı (2026-11-08): Officina-SCIFT/SUHII_mapping_tool mantığının kullanılması.
- **Karar:**
  - Yöntem, yayımlanmış ürün tanımlarından yeniden kuruldu: Landsat C2 L2 yüzey sıcaklığı bandı, QA ile bulut maskesi, yaz mevsimi ortalaması; DEM; OSM. Referans araç AGPL-3.0 lisanslı olduğu için kodu kopyalanmadı.
  - Kaynaklar anahtarsız: Planetary Computer (Landsat), Earth Search (Sentinel-2; `boa_offset_applied` bayrağına uyuluyor), Copernicus DEM (SRTM yerine; OpenTopography anahtarı gerekmiyor).
  - Kırsal referanslı SUHII kent ölçeğinde yapılacak; mahallede LST anomalisi ortancaya göre hesaplanıyor.
- **Durum:** Kabul

### K-037: Yol ağı karmaşıklığı ve hücre imzası gömmesi
- **Karar:**
  - Boeing (2019) yönelim entropisi ve düzeni, dolambaçlılık, çıkmaz sokak payı ve düğüm başına sokak eklendi.
  - Bütün G1 özelliklerinden PCA ile 5 bileşenli hücre imzası üretildi. Bileşenler yükleriyle açıklanıyor. Tanımsal bileşen içerdikleri için ilişki tablosunda kullanılmıyor.
  - Görüntü-dil modeli (VLM) gömmeleri sonraki adımda ek sütun olarak eklenecek (model indirme ve GPU maliyeti).
- **Durum:** Kabul

### K-038: Overture Maps bağlayıcısı (satır grubu indeksi)
- **Bağlam:** Kullanıcı Overture'u önerdi; OSM'nin seyrek olduğu yerlerde küresel bina ve mekân verisi gerekiyor.
- **Karar:** Overture S3 GeoParquet sürümü sabitlendi (2026-10-21.0). `bbox.*` istatistiklerinden satır grubu indeksi kuruluyor (binalar 84 bin satır grubu, 8 saniye); yalnız AOI'ye düşen satır grupları okunuyor (Caferağa: 1/84 224). Lisans: binalar ODbL, mekânlar CDLA-Permissive-2.0.
- **Bulgu:** Caferağa'daki binaların %100'ü OSM kaynaklı; yükseklik bilgisi %0,2, kat bilgisi %13 dolu. Overture mekânları 2.303, OSM POI 1.320 (1,7 kat); kaynakları Meta, Foursquare, Microsoft ve AllThePlaces. Foursquare (Swarm) verisi pedx'e Overture üzerinden giriyor.
- **Durum:** Kabul

### K-039: Kırılganlık ve afete direnç katmanları
- **Karar:** Meta HRSL (CC BY 4.0, COG): 60+, 0–5, 15–24, kadın 15–49 kırılımları. Paylar HRSL'den alınıyor, kişi sayıları GHS-POP × pay olarak hesaplanıyor. GHSL BUILT-S 1975/1990/2000 dönemleri kent dokusunun yaşının vekili. OSM'den hastane, itfaiye, okul, bakım tesisi ve toplanma alanı. Isı maruziyeti ayrı bileşenlerle (LST⁺ × 60+ ve 0–5) veriliyor; opak bileşik endeks yok.
- **Bulgular (G2):**
  - HRSL nüfusu TÜİK'e göre +%65, GHS-POP +%2,7 → nüfus tabanı GHS-POP.
  - HRSL yaş payları ilçe içinde sabit (60+ = %21,3) → mahalle içi yaş farkı gösterilemez.
  - OSM'de İstanbul afet toplanma alanı yok → İBB verisi G2'de kullanılacak.
- **Reddedilenler:** Google yorumları ve Popular Times (kullanım koşulları, KVKK); Yandex (açık lisans yok); Uber Movement (kapatıldı). GEM sismik tehlike haritası yalnız akademik kullanım (NC lisansı).
- **Durum:** Kabul

### K-040: Hibrit küresel mimari: "tıkla → hesapla"
- **Karar:** `pedx.service.assess_point` + `pedx.api` (FastAPI, `make api`). Dünya için önceden hesaplanmış altıgen tablosu tutulmuyor. Büyük döşemeler önbellekte (`make prepare`), geri kalan her şey pencere ya da satır grubu okumasıyla tıklama anında hesaplanıyor. Fiziksel çekirdek toplu hatla aynı (`pedx.params`). Kesin açıklama: B ≥ 1 ⇔ A/P ≥ d/(u·η·Y).
- **Doğrulama:** Caferağa'da servis 1,65, toplu hat 1,60 verdi. Berlin'de aynı kod çalıştı (HRSL ile, uyarılı).
- **Durum:** Kabul

### K-041: Dış doğrulama: gerçek PED'ler (vaka–kontrol)
- **Karar:** Tek referans gerçek PED ve öncü proje sahalarıdır. Her saha, aynı kentteki 1,5–8 km uzaklıkta seçilen rastgele kontrollerle aynı kodla puanlanıyor. Ölçüler: yüzdelik sıra, AUC, işaret testi. Tohum sabit; sonuca göre ayar yapılmaz (`scripts/validate_ped_sites.py`, docs/17).
- **Durum:** Kabul

### K-042: Vizyon: PED karar destek sistemi ve altıgen transformer'ı
- **Karar:** Hedef mimari docs/16'da tanımlandı: altıgen = token, öz-denetimli ön eğitim, gerçek PED'lerle pozitif-etiketsiz (PU) ince ayar, fiziksel XAI. Bunun önünde zorunlu bir taban çizgisi var: PCA imzası ve fiziksel model. Transformer bu taban çizgisini gruplu doğrulamada geçemezse teze girmez.
- **Durum:** Kabul (tasarım)

### K-043: Odak üç iddia; doğrulama v2: kent ızgarası ve tüm katmanlar
- **Bağlam:** Kullanıcıyla değerlendirme sonrası kapsam üç iddiaya indirildi:
  - (A) Küresel açık veriyle mahalle ölçeğinde PED dengesi ne kadar güvenilir? (G1/G2)
  - (B) Gerçek PED'ler hangi açık veri imzasını taşıyor?
  - (C) Tıkla→hesapla karar destek aracı ve Caferağa vaka çalışması.

  Transformer, kentsel dönüşüm senaryosu ve ROI "gelecek çalışma" olarak kalıyor.
- **Doğrulama v1'in sorunları:** Kontrollerin yarısı su ya da boş alana düştü. Saha başına 5–8 kontrol kaldı. Buiksloterham iki koşu arasında 0,60'tan 0,375'e oynadı.
- **Karar (v2):** `pedx.citygrid` ile her kent için 16 × 16 km'lik pencerede bütün katmanlar bir kez H3 r10'a işleniyor: HRSL, Overture, Sentinel-2, Landsat LST, Copernicus DEM (çok döşemeli), PVGIS, UNSD/OWID. Kontroller yalnız yerleşik ve dolu hücrelerden seçiliyor (HRSL ≥ 20 kişi, taban alanı > 0); saha başına 30 kontrol. İki model karşılaştırılıyor: (a) enerji dengesi; (b) kent içi z-puanlarıyla L2 lojistik regresyon, her seferinde bir kent dışarıda bırakılarak. Ek olarak Caferağa, İstanbul içinde puanlanıyor (gerçek bir PED değil).
- **Durum:** Kabul

### K-044: Büyük soru ve veri ölçekleme eğrisi; EPİAŞ yalnızca Faz 2
- **Bağlam:** Kullanıcının üst sorusu: "Sonsuz veriyle karar destek motoru kesin karar verebilir mi?" Ek istek: sistem tamamen küresel ve açık olsun; yerel veri yalnızca doğrulamada kullanılsın.
- **Karar:**
  - Soru, tezin felsefi çerçevesi (Laplace'ın cini) ve bir bilginin değeri deneyi olarak alındı. Veri aileleri önceden belirlenmiş bir sırayla ekleniyor; her adımda bir kent dışarıda bırakılarak AUC hesaplanıyor ve bootstrap ile %90 aralık veriliyor (`scripts/data_scaling.py`).
  - EPİAŞ model girdisinden çıkarıldı (Faz 2 doğrulaması).
  - WorldCover ve Overture altyapı katmanları kent ızgarasına eklendi.
  - Sunum yeniden kuruldu: büyük soru, iki hedef, üç iddia, mimari, veri, yazılım ve donanım, fazlar, sonuçlar.
- **Durum:** Kabul

### K-045: Tez felsefeyle açılıyor
- **Bağlam:** Kullanıcı tezin Laplace'ın cini ve onun çöküşüyle (Heisenberg, kaos, termodinamiğin ikinci yasası) başlamasını önerdi.
- **Karar:** Giriş bölümü buna göre yeniden kuruldu: cin → çöküşü → kent ölçeğinde karmaşıklık ve öz-göndermelilik → veri çağının "yeni cini" (Anderson 2008) ve eleştirisi → belirsizlik altında karar → tezin ölçülebilir sorusu.
- **Akademik özen:** Kuantum belirsizliği kentsel kararları doğrudan etkilemez; tarihsel çerçeve olarak anılır. Kentteki belirsizliğin asıl kaynakları kaos, karmaşıklık, öz-göndermelilik ve ölçüm hatasıdır.
- **Tartışma bölümü:** Cine geri dönülüyor. Veri ölçekleme eğrisi, "veri neyi bilir, neyi bilemez?" sorusunun ampirik yanıtı olarak sunuluyor.
- **Durum:** Kabul

### K-046: Çerçeve: Laplace'ın cininden AGI'ye, alana sınırlı planlama zekâsı
- **Bağlam:** Kullanıcı tezin felsefeye boğulmasını istemiyor; "cinden AGI'ye giden yolda, sınırlı bir tema için kurulan kentsel planlama PED zekâsı" çerçevesini istiyor.
- **Karar:**
  - Felsefe girişte 2–3 sayfa.
  - Zekâ, ajan bileşenleriyle tanımlanıyor: algı, model, öğrenme, karar, açıklama, sınırını bilme.
  - Zekâ iki ölçüyle sınanıyor: görmediği kentlerde gerçek PED'leri tanıma (Chollet 2019 genellemesi) ve veri ölçekleme eğrisi.
  - Sunum ve tez planındaki giriş buna göre güncellendi.
- **Durum:** Kabul

### K-047: Eksen: otonom CBS / coğrafi karar ajanı (pedx-agent)
- **Bağlam:** "Geospatial AGI" fikri değerlendirildi. AGI'nin üzerinde uzlaşılmış, ölçülebilir bir tanımı yok ve bir YL tezi için savunulamaz.
- **Karar:**
  - Literatürdeki karşılık olan otonom CBS çerçevesi benimsendi (Li ve Ning 2023: kendini oluşturan, düzenleyen, doğrulayan, yürüten ve büyüten CBS). AGI girişte ufuk olarak kalıyor.
  - Faz 3'e `pedx-agent` modülü eklendi. Bir LLM doğal dil soruyu araç çağrılarına çeviriyor: kent ızgarası → PED imzası → ÇKKDS → tersine analiz.
  - **LLM sayı üretmez**; her sayı fizik çekirdeğinden, doğrulanmış modelden ya da kaynaklı veriden gelir.
  - Ajan, gerçek PED'lerden türetilen bir görev setiyle sınanıyor (bulunan sahanın gerçek PED'e uzaklığı).
- **Yayın:** Makale 1, "Otonom CBS'ye doğru: gerçek PED'lerle sınanan coğrafi karar ajanı" (*IJDE* ya da *CEUS*).
- **Durum:** Kabul

### K-048: Analiz birimi: bina (fizik) · H3 (veri birleştirme) · proje sahası (karar)
- **Bağlam:** H3 altıgenleri PED değerlendirmesi için yeterince küçük mü? PED, bir bina kümesidir.
- **Karar:** Üç ölçekli hiyerarşi.
  1. **Bina:** fiziğin ve müdahalenin birimi (çatı, talep, yenileme).
  2. **H3 r10 (~1,5 ha):** küresel veri birleştirme ve karşılaştırma birimi (raster, nüfus, uydu).
  3. **Proje sahası:** karar birimi. Bina kümesi olarak tanımlanır (çizilen poligon, yapı adası ya da hücre kümesi). Göstergeler binaların toplamından tam olarak hesaplanır (denge = toplam PV / toplam talep).

  Altıgen PED'in kendisi değil, onun yapı taşıdır.
- **Doğrulama (MAUP; Openshaw 1984):**
  - Sonuçlar H3 çözünürlüğüne (r9, r10, r11) ve proje sahası boyutuna (k = 1, 2, 3) karşı duyarlılık analiziyle raporlanır.
  - Caferağa'da yapı adası toplamıyla altıgen toplamı karşılaştırılır.
- **Durum:** Kabul

### K-009: Geliştirme, plan onaylanana kadar durduruldu
- **Bağlam:** Kullanıcı "geliştirme yapmadan önce planlama" istedi.
- **Karar:** Plan sohbetinden önce yazılan taslak kod dosyaları (`src/pedpy/_stats.py`, `energy/load_match.py`, `energy/records.py`, `mcdm/criteria.py`) kaybolmasın diye **"taslak" etiketiyle** commit edildi. Henüz paket hâline gelmediler (`__init__.py` ve `pyproject.toml` yok) ve test edilmediler. Plan onayından sonra Faz 2'de gözden geçirilip kullanılacaklar.
- **Durum:** Kabul
