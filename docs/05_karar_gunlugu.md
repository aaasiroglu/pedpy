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

### K-009: Geliştirme, plan onaylanana kadar durduruldu
- **Bağlam:** Kullanıcı "geliştirme yapmadan önce planlama" istedi.
- **Karar:** Plan sohbetinden önce yazılan taslak kod dosyaları (`src/pedpy/_stats.py`, `energy/load_match.py`, `energy/records.py`, `mcdm/criteria.py`) kaybolmasın diye **"taslak" etiketiyle** commit edildi. Henüz paket hâline gelmediler (`__init__.py` ve `pyproject.toml` yok) ve test edilmediler. Plan onayından sonra Faz 2'de gözden geçirilip kullanılacaklar.
- **Durum:** Kabul
