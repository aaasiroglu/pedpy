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

### K-009: Geliştirme, plan onaylanana kadar durduruldu
- **Bağlam:** Kullanıcı "geliştirme yapmadan önce planlama" istedi.
- **Durum:** Taslak kod dosyaları (`src/pedpy/_stats.py`, `energy/load_match.py`, `energy/records.py`, `mcdm/criteria.py`) **commit edilmedi**. Plan onayından sonra Faz 2'de gözden geçirilip kullanılacak.
- **Durum:** Kabul
