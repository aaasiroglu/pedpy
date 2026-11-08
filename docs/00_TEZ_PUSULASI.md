# 00: Tez Pusulası (tek sayfa, tek doğruluk kaynağı)

*Güncelleme: 2026-11-08 · Bu belge diğer bütün belgelerin önündedir. Çelişki olursa bu belge geçerlidir.*

## Tek cümle

> **Dünyanın herhangi bir mahallesi için, yalnızca küresel açık veriyle, saatlik fiziğe dayanan, açıklanabilir ve "ne yapmalı?" sorusuna yanıt veren bir Pozitif Enerji Bölgesi (PEB) analizi; İstanbul'un resmî verileriyle doğrulanmış.**

**Başlık önerisi:** *Küresel Açık Veriyle Açıklanabilir ve Fizik Kenetli Pozitif Enerji Bölgesi Analizi: H3 Tabanlı Bir Çerçeve ve İstanbul Doğrulaması*

## Üç soru, üç katkı, üç yayın

| | Araştırma sorusu | Katkı | Ölçüt | Yayın |
| --- | --- | --- | --- | --- |
| **1** | Yalnızca küresel açık veriyle hesaplanan PEB potansiyeli, İstanbul'un resmî verisini ne kadar doğru temsil eder? | Küresel açık veri hattı (OSM, GHS-POP, UNSD, PVGIS) ve H3 üzerinde mutlak PEB indeksi; **G1/G2 doğrulama protokolü** | Nüfus, talep, PV ve saatlik profil için hata (%), sıra korelasyonu (ρ, τ) ve bootstrap güven aralığı | **B1 bildirisi** (Aralık), sonra **Makale A** |
| **2** | Saatlik tamamlayıcılık, PEB sınırını nasıl değiştirir ve her altıgenin buna katkısı nedir? | **Toplamsal olmayan enerji paylaşımı oyunu** ve kesin Shapley ile graf-XAI; sınır büyütme algoritması | Küme öz-yeterliliği; max-p ve rastgele büyütmeye göre kazanç; optimallik açığı | **Makale B** |
| **3** | Bir altıgeni PEB yapmanın en küçük fiziksel müdahalesi nedir? | **Fizik kenetli tersine analiz** (PV, depolama, kabuk, yük dönüşümü) ve bütçe–skor Pareto eğrisi; kesin modelle denetim | Fiziksel tutarlılık (7 denetim), kesin çözüme karşı sapma | **Makale B** |

**Yan bulgular (tezde tartışma ve ek):**
- MARCOS ≡ κ·WSM özdeşliği.
- OSM tamlığının PEB kararlarına etkisi.
- Önceki çalışma (2024): PEB benimseme modeli. Bunun eleştirisi ve fiziksel modelle birleştirilmesi.

## Kapsam

| İÇİNDE (çekirdek) | DIŞINDA (gelecek çalışma) |
| --- | --- |
| H3 altıgenleri, saatlik denge, mutlak indeks | Yapı adası birimi (K-019) |
| G1 küresel açık girdiler + G2 İstanbul doğrulaması | Yerel veriyi girdi olarak kullanmak (K-025) |
| Sıra belirsizliği, kesin katkılar, Shapley ile graf-XAI | NLP ve LLM modülleri, GNN, Geo-AI (FT-Transformer, VLM, nnPU) |
| Fiziksel müdahale uzayında tersine analiz | MARCOS'u yumuşatmak (Smooth-MARCOS), mekânsal gecikme |
| Web demo | Ağırlık füzyonunu ana katkı yapmak (yalnızca duyarlılık analizinde) |

## Tek hat (mimari)

```
OSM sınır + binalar ─┐
JRC GHS-POP nüfus ───┤                    ┌─► mutlak PEB indeksi + sıra aralığı ─┐
UNSD hane elektriği ─┼─► bina → H3 r10 ───┤                                      ├─► web demo
PVGIS saatlik PV ────┤   saatlik G, D     ├─► graf: paylaşım oyunu, Shapley ─────┤   (harita + paneller)
[saatlik talep şekli]┘                    └─► tersine: müdahale → Pareto ────────┘
                         İstanbul resmî verisi (TEDAŞ, EPİAŞ, İBB, Demirel 2025) ──► G2 doğrulama paneli
```

## Bilgi birikiminin tezdeki yeri

| Bilgi birikimi | Tezdeki yeri |
| --- | --- |
| Hande Hoca: Caferağa 3B güneş analizi (Demirel vd. 2025), PEB'de CBS çalışmaları, erişilebilirlik | Çalışma alanı; **PV ve çatı kalibrasyonu için G2**; Bölüm 2'nin omurgası |
| Alpagut vd. (2021): CBS ile ÇKKDS ile PEB sınırı | **Karşılaştırma yöntemi** (statik ve yıllık katmanlar ile saatlik ve açıklanabilir yaklaşım) |
| Kullanıcının 2024 tasarım projesi (60 + 60 şehir, RF) | Aşama 1 ve motivasyon: "benimseme" ile "fiziksel potansiyel" ayrımı; düzeltilmiş hâli isteğe bağlı |
| Kullanıcının İBB'deki konumu | G2 verisine erişim: bina envanteri, mahalle nüfusu, çatı |
| Bruck vd. (2022) açık kaynak PV-PEB yer seçimi | **En yakın çalışma**; farkımız: saatlik, H3, XAI, tersine analiz, G1/G2 |
| Schneider vd. (2023) bağlamsal hedefler | Mutlak indeksin referans değerleri |
| Salom (2014), Luthander (2015) | SSR ve denge göstergeleri |
| Wachter (2018), Shapley ve oyun kuramı | Tersine analiz ve graf-XAI kuramı |

## Durum

| Bileşen | Durum |
| --- | --- |
| Küresel veri hattı (OSM, GHS-POP, UNSD, PVGIS) | ✅ Caferağa'da çalışıyor |
| Web demo v0.2: 41 özellikli H3 deposu (enerji, yapı, demografi, POI), katalog, ilişkiler | ✅ |
| Sistem mimarisi ve karar motoru tasarımı (docs/13) | ✅ tasarım; uygulama S4–S8 |
| Yerel kurulum (`make`, Docker) | ✅ |
| G2: nüfus (+%2,7), kişi başı tüketim | ✅ ilk iki karşılaştırma |
| Graf-XAI ve tersine motor (kod ve testler) | ✅ kod hazır, **gerçek veride saatlik talep bekliyor** |
| **Saatlik konut talep şekli (küresel ve açık)** | ❌ **kritik eksik**: karar S1'de |
| Nüfusun binalara göre dasimetrik dağıtımı (kıyı hücreleri) | ⏳ S2 |
| Kaynaklı müdahale maliyetleri | ⏳; o zamana kadar tersine analiz fiziksel birimlerle (m², kWh) |

## Kritik yol (sırayla)

1. **Saatlik talep şekli kararı (S1).**
2. Saatlik göstergeleri gerçek veriyle açmak; EPİAŞ mesken profiliyle G2.
3. Dasimetrik nüfus düzeltmesi.
4. B1 bildirisi (katkı 1, Caferağa).
5. Graf ve tersine analiz sonuçları (Makale B).
6. Makale A (tam G1/G2, birkaç mahalle).
7. Tez yazımı.

## Platform hedefi (docs/13)

Tezin üç katkısı, "A noktasında PED olur mu, neden olmaz, ne yapılırsa olur, değer mi?" sorularını yanıtlayan **karar motorunun** çekirdeğidir. Benzerlik modeli (PU) ve ROI, platformun ürün katmanıdır. Tezde katkı 1'in uzantısı ve uygulama örneği olarak yer alır.

## Belge haritası

| Geçerli | Arşiv (yalnızca tarihçe) |
| --- | --- |
| 00 (bu belge), 02 literatür, 05 kararlar, 06 sorular, 07 kırılganlık analizi, 08 tersine analiz, 10 sprint planı, 11 veri kütüğü, 12 önceki çalışmalar | 01 ilk değerlendirme, 03 eski araştırma tasarımı, 04 eski yol haritası, 09 eski v0 sunumu |
