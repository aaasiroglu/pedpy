> ⚠️ **ARŞİV: bu belge artık güncel değil.** Neden: takvim 10_sprint_plani.md ile, kapsam 00_TEZ_PUSULASI.md ile değişti. Güncel tez tanımı için **[00_TEZ_PUSULASI.md](../00_TEZ_PUSULASI.md)** dosyasına bakın.

# 04: Yol Haritası (Adım Adım Plan)

*Tarih: 2026-11-08 · Süreler göreli ay olarak verildi (A1 = başlangıç ayı). Tez teslim tarihi netleşince takvime oturtulacak (bkz. [06](06_acik_sorular.md)).*

## Önceliklendirme

| Katman | Anlamı | İçerik |
| --- | --- | --- |
| 🟥 **Zorunlu** | Tez bu olmadan savunulamaz | Enerji çekirdeği, mutlak PEB Hazırlık İndeksi (K-014), ağırlık belirsizliği, T1–T5, G1/G2 veri sadakati ve model geçerliliği, XAI-3 (sıra aralıkları), **Graf-1 ve Shapley ile graf-XAI (K-018)**, **XAI-2 eylem uzayında yollar (K-016)** |
| 🟧 **Güçlü** | Tezi "çok iyi" yapar, makale çekirdeği | XAI-1b sıra düzeyi açıklama, H3 ve MAUP, çok-şehirli benchmark (07, D1), tek satırlık `assess()` API'si |
| 🟩 **Bonus** | Etkileyici, ama zaman kalırsa | NLP-1, NLP-2, Graf-2 GNN, JOSS makalesi |

> **2026-11-08 güncellemesi:** Kullanıcı önceliği XAI ve graf olarak belirledi (K-011). Kırılganlık analizi (07) sonucunda K-013 ile K-018 arası kararlar önerildi. Faz 2 ile Faz 6'nın içeriği bu kararlar kabul edilince yeniden yazılacak.

**Kural:** Bir üst katmandaki işler kabul ölçütlerini karşılamadan alt katmana geçilmez.

---

## Faz 0: Kapsam ve izinler (A1) 🟥

| Adım | İş | Çıktı | Kabul ölçütü |
| --- | --- | --- | --- |
| 0.1 | Danışmanla kapsam toplantısı: bu klasördeki 01, 03 ve 04 dosyaları gözden geçirilecek | Onaylı kapsam notu (05'e K-0xx olarak) | AS1–AS7 içinden seçilenler yazılı |
| 0.2 | İBB veri talebi: LiDAR/DSM, bina envanteri (yaş, kullanım, kat), Caferağa yapı adası sınırları | Resmî talep yazısı | Talep gönderildi; veri lisans koşulları kayıtlı |
| 0.3 | Tüketim verisi talebi (dağıtım şirketi veya İBB, toplulaştırılmış ve anonim) | Talep yazısı | Gönderildi. Yoksa "sentetik talep" sınırlılığı yazılı |
| 0.4 | Etik kurul (yalnızca NLP-1 ve NLP-2 kullanıcı çalışması ile uzman görüşmeleri için) | Başvuru | Bonus katman seçilirse zorunlu |
| 0.5 | ρ* eşiğinin ve birincil ölçütlerin **önceden kaydı** | 05'e karar kaydı | Veri görülmeden önce yazıldı |

## Faz 1: Literatür (A1–A2) 🟥 → Tez Bölüm 2

| Adım | İş | Çıktı | Kabul ölçütü |
| --- | --- | --- | --- |
| 1.1 | 02'deki ❓ ve ⚠️ işaretli kaynakları doğrulama | `references.bib` tamam | ❓ kalmadı |
| 1.2 | Sistematik tarama (Scopus, WoS) ve PRISMA diyagramı | `docs/lit/prisma.md` | Dahil etme ve dışlama ölçütleri yazılı |
| 1.3 | Temel makalelerin okuma notları (Alpagut 2021, Demirel 2025, Salom 2014, Stević 2020, Xie & Zou 2025, ShaRP, Wachter) | `docs/lit/notlar/*.md` | Her not: yöntem, veri, sonuç, sınırlılık, bizimle ilişkisi |
| 1.4 | Boşluk analizi tablosu (mevcut PEB ÇKKDS çalışmaları × özellik) | Bölüm 2 tablosu | Katkı 1–5'in her biri için "yok" veya "kısmen" kanıtı |

## Faz 2: Çekirdek kütüphane (A2–A3) 🟥 → Bölüm 3.1–3.3

| Adım | İş | Literatür | Kabul ölçütü |
| --- | --- | --- | --- |
| 2.1 | Paket iskeleti (`pyproject.toml`, `src/pedpy`), kodlama standartları, CI (GitHub Actions) | — | `pip install -e .` çalışıyor, CI yeşil |
| 2.2 | `energy`: `BuildingEnergyRecord`, yük eşleşme göstergeleri, ada toplulaştırma (iki paylaşım modu) | Salom 2014, Luthander 2015 | T1, T2 ve T5 geçiyor; her saatte enerji korunumu sağlanıyor |
| 2.3 | `weighting`: CRITIC, Entropi (yön düzeltilmiş), doğrusal BWM (yerleşik LP çözücü), füzyon ve izdüşüm | Diakoulaki 1995, Rezaei 2016, Zhu 2020 | T3 geçiyor; BWM sonucu yayımlanmış bir örnekle eşleşiyor |
| 2.4 | `mcdm`: MARCOS (kesin), WSM, TOPSIS, PROMETHEE II, mekânsal gecikme, sıfır ve negatif değer politikası | Stević 2020, Xie & Zou 2025 | T4' (yeniden tanımlandı): MARCOS = κ·WSM özdeşliği 1e-12 hassasiyetle; Stević 2020'deki sayısal örnek yeniden üretiliyor |
| 2.5 | `_stats`: Spearman, Kendall τ-b, RMSE, MAPE (yalnızca numpy) | — | scipy ile aynı sonuçlar (scipy erişilebilir olduğunda karşılaştırılacak) |

## Faz 3: Açık veri hattı, G1 (A3–A5) 🟥 → Bölüm 3.4, 4.1

| Adım | İş | Kabul ölçütü |
| --- | --- | --- |
| 3.1 | `ingest`: OSM/Overture binalar ve POI, PVGIS saatlik ışınım, Open-Meteo ERA5 sıcaklık. Önbellek ve sürüm bilgisi | Çağrılar çevrimdışı test edilebilir (ayrıştırıcılar ayrı); veri tarihi ve lisansı kaydediliyor |
| 3.2 | 2,5B ufuk gölgelemesi (güneş konumu ve komşu yükseklikleri) | Basit geometride analitik sonuçla eşleşiyor |
| 3.3 | Sentetik talep: arketip × profil × HDD/CDD | Yıllık toplam korunuyor; profil şekilleri kaynaklı |
| 3.4 | C4, C5 ve C6 yardımcıları (Shannon, termal vekil, erişilebilirlik) | Birim testleri |
| 3.5 | Caferağa G1 koşusu | `results/G1/` + veri sözlüğü |

## Faz 4: İBB verisi ve çapraz doğrulama, G2/G3 (A5–A7) 🟥 → Bölüm 4.2

| Adım | İş | Kabul ölçütü |
| --- | --- | --- |
| 4.1 | İBB verisinin içe aktarılması (`ingest/ibb.py`), koordinat sistemi dönüşümü, eşleme | Bina eşleşme oranı raporlanıyor |
| 4.2 | G2 koşusu | `results/G2/` |
| 4.3 | G3: ρ, τ, ilk-k, RMSE, MAPE, bootstrap güven aralığı | H1 sonucu (olumlu veya olumsuz) raporlanıyor |
| 4.4 | Demirel vd. (2025)'teki %22,29 platform farkı ile kıyas | Tartışma bölümü notu |

## Faz 5: XAI katmanı (A6–A8) 🟥 / 🟧 → Bölüm 3.5, 4.3

| Adım | İş | Katman | Kabul ölçütü |
| --- | --- | --- | --- |
| 5.1 | XAI-1 kesin katkılar ve ikili açıklama | 🟥 | Σ_j φ_ij = f_i − f̄ (verimlilik aksiyomu) her ada için sağlanıyor |
| 5.2 | XAI-3 belirsizlik (Dirichlet ağırlık örneklemesi, veri bootstrap) ve sıra aralıkları | 🟥 | Kararlı ve kararsız ada sınıflaması çıkıyor |
| 5.3 | XAI-1b sıra düzeyi Shapley (ShaRP benzeri, örneklemeli) | 🟧 | Skor ve sıra açıklamalarının uyumsuz olduğu örnekler tartışılıyor |
| 5.4 | XAI-2 kesin reçete çözücüsü, çeşitli reçeteler, SLSQP ile kıyas | 🟧 | Kesin çözüm, SLSQP sonucundan daha pahalı değil (H5) |
| 5.5 | Ölçüt ve müdahale kolu eşlemesi; birim maliyet kaynakları | 🟧 | Her maliyetin kaynağı var |

## Faz 6: Graf katmanı (A7–A9) 🟧 → Bölüm 3.6, 4.4

| Adım | İş | Kabul ölçütü |
| --- | --- | --- |
| 6.1 | Komşuluk grafı (ada poligonları, H3 `grid_disk`) | Graf bağlantılı, istatistikleri raporlanıyor |
| 6.2 | Graf-1 sınır genişletme (tamamlayıcılık ve PEB kısıtı) | Sentetik gündüz/gece testinde tamamlayıcı ada önce seçiliyor |
| 6.3 | Karşılaştırma yöntemleri: max-p (PySAL/spopt, erişim varsa), rastgele bitişik büyütme, küçük n için tam sayım | Optimallik açığı raporlanıyor (H4) |
| 6.4 | H3 çözünürlüğü 8, 9 ve 10 ile MAUP analizi | Çapraz ölçek ρ tablosu |
| 6.5 | 🟩 Graf-2 GNN tamamlama (PyTorch Geometric, erişim varsa) ve GBM karşılaştırması | Çapraz doğrulamada RMSE |

## Faz 7: NLP katmanı (A8–A10) 🟩 → Bölüm 3.7, 4.5

| Adım | İş | Kabul ölçütü |
| --- | --- | --- |
| 7.1 | 3–5 insan uzmanla BWM anketi (Türkçe form) | ξ değerleri raporlanıyor |
| 7.2 | NLP-1: yapılandırılmış istem, alıntı zorunluluğu, çoklu model ve istem varyansı | H6 testi |
| 7.3 | NLP-2: JSON'dan Türkçe metin üretimi ve sayı sadakati denetleyicisi | Sadakat %100; uydurma sayı içeren metin reddediliyor |
| 7.4 | Kullanıcı çalışması (planlamacılar) | H7 testi |

## Faz 8: Duyarlılık, aktarım, yayın (A9–A11) 🟧

| Adım | İş | Çıktı |
| --- | --- | --- |
| 8.1 | E4 ablasyonlarının tamamı | Bölüm 4 tabloları |
| 8.2 | 🟩 E9: ikinci şehir aktarımı | Ek |
| 8.3 | Makale taslağı (hedef dergi: Applied Energy, Sustainable Cities and Society, Energy and Buildings veya CEUS) | Taslak |
| 8.4 | Zenodo: kod ve açık veri sürümü (DOI) | Yeniden üretilebilirlik paketi |

## Faz 9: Tez yazımı ve savunma (A10–A12) 🟥

| Tez bölümü | Kaynak faz |
| --- | --- |
| 1. Giriş (problem, AS, katkılar) | 01, 03 |
| 2. Literatür | Faz 1 |
| 3. Yöntem (enerji, ÇKKDS, XAI, graf, NLP) | Faz 2, 5, 6, 7 |
| 4. Uygulama ve bulgular (Caferağa G1/G2/G3, ablasyon) | Faz 3, 4, 8 |
| 5. Tartışma (MARCOS ≡ WSM, sınırlılıklar, PEB kapsamı) | 01 |
| 6. Sonuç ve gelecek çalışmalar (Geo-AI modülleri, küresel aktarım) | K-006 |

---

## İlerleme günlüğü

| Tarih | Faz | Not |
| --- | --- | --- |
| 2026-11-08 | — | Planlama klasörü oluşturuldu; literatür ön taraması yapıldı; MARCOS ≡ κ·WSM sayısal olarak doğrulandı; geliştirme danışman onayına kadar durduruldu |
| 2026-11-08 | — | Danışman Hande Demirel; öncelik XAI ve graf. Kırılganlık analizi (07) yazıldı: 7 ölümcül, 12 ciddi, 7 orta bulgu. Paket adı çakışması (PyPI'da Jülich PedPy) tespit edildi |
| 2026-11-08 | Faz 2–3 (v0) | `pedx` v0: H3, mutlak indeks, graf-XAI, fizik kenetli tersine analiz, OSM ve PVGIS hattı; 44 test; Caferağa'da ilk koşu (2876 OSM binası). **Takvim artık `10_sprint_plani.md` dosyasında** |
