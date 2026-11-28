# 27 — Danışman görüşmesi (Prof. Dr. Hande Demirel) ve yeni yol haritası

## 1. Görüşmeden çıkanlar

1. Önce tezin **araştırma soruları** belirlenecek.
2. Birinci sorun: **PED sınırlarını tanımlamak zor.** Bunun nasıl çözüleceği tezin ilk sorusu.
3. Örnek: Sony CSL'in 15 dakikalık şehir çalışması (Bruno vd. 2024, *Nature Cities*; açık platform).
4. Hedef: dünyadaki **bütün PED proje sahalarını** bulmak (60'tan fazla) ve sınırlarını belirlemek; özellikle
   ekonomiyi kaldıraç olarak kullanan PED'ler.
5. Altıgen mantığı iyi, ama sınır **organik yapı adası** üzerinde tanımlanmalı.
6. 60 saha, makine öğrenmesiyle model eğitmek için **yeterli değil**; ne yapılacağı açık.
7. Şimdiye kadarki çalışma değerli; adım adım ilerleyip Q1 hedeflenecek.

## 2. Değerlendirme

- **Sınır sorunu elimizdeki en zayıf halkayı hedefliyor.** Şu an her PED'i tek bir nokta ve onun çevresindeki
  ~28 ha'lık diskle temsil ediyoruz. Caferağa'da saha 250 m kayınca puan 41'den 67'ye çıktı; dengedeki nüfus
  payı yapı adasında %93, r10'da %77. Yani sonuçlarımız sınıra duyarlı ve sınırı biz varsaydık.
- **Literatür sınırı kavramsal olarak tanımlıyor, mekânsal olarak değil.** Üç sınır türü var: coğrafi,
  işlevsel, sanal (JPI Urban Europe; Annex 83). Tekrar üretilebilir bir sınır çizme yöntemi yok; PED
  veritabanı (PED-EU-NET, Annex 83, JPI UE) sahaları nokta ve öznitelik olarak tutuyor. Boşluk burada.
- **Yapı adası altyapımız hazır.** `pedx.scales.blocks_from_streets` sokak ağından yapı adası üretiyor;
  bina → yapı adası → altıgen toplulaştırması kesin yapılıyor (Caferağa çok ölçekli çalışması).
- **Altıgen ile yapı adası rakip değil.** Altıgen küresel tarama ve indeks birimi olarak kalır (Sony CSL de
  altıgen kullanıyor); karar ve sınır birimi yapı adası olur.
- **60 saha sorunu, soruyu değiştirerek çözülür.** Model eğitmiyoruz; fiziksel bir ölçütü ve bir sınır
  yöntemini gerçek sahalara karşı **sınıyoruz**. Bunun için 60 saha yeterlidir (bkz. §5).

## 3. Önerilen araştırma soruları

| | Soru | Yöntem | Çıktı |
|---|---|---|---|
| **AS1** | Bir PED'in mekânsal sınırı açık veriyle, tekrar üretilebilir biçimde nasıl tanımlanır? | Yapı adalarını atomik birim al; sınırı "enerji dengesini sağlayan en küçük bitişik yapı adası kümesi" olarak çiz (bölgeleme problemi). Proje belgelerindeki sınırlarla örtüşme (IoU) ile sına | Sınır çizme yöntemi + doğruluğu |
| **AS2** | Dünyadaki PED sahaları nerede, sınırları ne ve hangi türdeler? | PED veritabanı, PED Booklet, Annex 83 ve H2020/Horizon projelerinden envanter; sınırların sayısallaştırılması; tür ve ekonomi öznitelikleri | Açık küresel PED coğrafi veri tabanı (60+) |
| **AS3** | Bu sınırlar içinde açık veriyle hesaplanan enerji dengesi, PED'leri kendi kentlerindeki benzer yapı adası kümelerinden ayırıyor mu; sonuç sınır tanımına ne kadar duyarlı? | Vaka–kontrol (mevcut tasarım), ama birim artık gerçek sınır; nokta-disk, altıgen ve yapı adası sınırlarının karşılaştırması | Doğrulama + ölçek/sınır duyarlılığı |
| **AS4** | Ekonomiyi kaldıraç olarak kullanan PED'ler mekânsal ve enerji açısından diğerlerinden farklı mı? | AS2'deki tür özniteliğiyle katmanlı karşılaştırma | PED tipolojisi |

AS1 ve AS2 yeni; AS3 mevcut çalışmanın sınır üzerine oturtulmuş hâli (16/16, AUC 0,82, MAUP, dönüşüm alanı
sınaması buraya taşınır). AS4, AS2 bitmeden başlamaz.

## 4. Sınır sorunu için önerilen çözüm (AS1)

1. **Atomik birim:** sokak ağının çevrelediği yapı adaları (OSM/Overture ulaşım katmanı → `polygonize`).
2. **Referans sınır:** her PED için proje belgesindeki sınırı yapı adası kümesi olarak sayısallaştır
   (kaynak belge ve güven düzeyi kaydedilir).
3. **Üç sınır türü, üç işlem:**
   - Coğrafi: bitişik yapı adası kümesi.
   - İşlevsel: aynı enerji altyapısına (bölgesel ısıtma, trafo bölgesi) bağlı yapı adaları; açık veride
     ancak kısmen görülebilir.
   - Sanal: sınır dışı üretim; mekânsal olarak çizilemez, öznitelik olarak kaydedilir.
4. **Algoritmik sınır:** bir çekirdek yapı adasından başlayıp komşuları ekleyerek yıllık dengeyi ≥ 1 yapan
   en küçük bitişik kümeyi bul (bölge büyütme; max-p bölgeleme ailesi). Çıktı: "kendine yeten en küçük komşuluk".
5. **Sınama:** algoritmik sınır ile referans sınırın örtüşmesi (IoU, alan oranı); nokta-disk ve altıgen
   yaklaşımlarının aynı ölçüyle karşılaştırılması.

Sony CSL örneğinden alınacaklar: küresel kapsam, tek ve basit bir ölçüt, açık platform, "her kente uygulanabilir
mi?" sorusunun kendisinin bulgu olması. Almayacağımız: altıgeni karar birimi yapmak.

## 5. "60 saha yetmez" sorununa cevap

| Seçenek | Ne yapar | Öneri |
|---|---|---|
| Model eğitme, sına | Fiziksel ölçüt ve sınır yöntemi önceden sabitlenir; 60 saha yalnız test kümesidir | **Ana yol** |
| Az parametreli istatistik | Eşleştirilmiş vaka–kontrol, işaret/permütasyon testleri, bootstrap aralıkları | Zaten kurulu |
| Birimi küçült | 60 PED içinde binlerce yapı adası; PED düzeyinde kümelenmiş analiz | AS1 ve AS3'te kullanılır |
| Etiket kümesini genişlet | Planlama aşamasındaki PED'ler, PED laboratuvarları, benzer sınıflar (net sıfır mahalleler) | Ayrı katman olarak; karıştırılmaz |
| Derin öğrenme, temel model | Çok parametre, az etiket | **Yapılmaz** |

## 6. Adım adım yol haritası

| Adım | İş | Bitti sayılır |
|---|---|---|
| 1 | Araştırma sorularını danışmanla kesinleştir | AS1–AS4 onaylı |
| 2 | PED envanteri: kaynakları tara, saha listesini çıkar (ad, kent, proje, durum, tür, kaynak) | 60+ satırlık tablo |
| 3 | Pilot: mevcut 16 sahanın sınırını belgelerden yapı adası kümesi olarak sayısallaştır | 16 referans sınır |
| 4 | Sınır algoritmasını 16 sahada kur ve sına | IoU tablosu |
| 5 | Envanterin geri kalanına yay | 60+ sınır |
| 6 | AS3: dengeyi gerçek sınırlarda yeniden hesapla; sınır duyarlılığı | Güncel doğrulama |
| 7 | AS4: ekonomi ve tür katmanları | Tipoloji |

Makale adayları: (a) açık küresel PED coğrafi veri tabanı ve sınır çizme yöntemi (AS1 + AS2);
(b) açık veriyle PED enerji dengesinin doğrulanması ve sınır duyarlılığı (AS3 + AS4).

## 7. Danışmana sorulacaklar

1. Referans sınır olarak neyi kabul edelim: proje belgesindeki harita mı, proje ekibinden teyit mi?
2. "Ekonomiyi kaldıraç olarak kullanan PED" için ölçüt ne: iş modeli, finansman türü, mülkiyet?
3. PED laboratuvarları ve planlama aşamasındaki sahalar envantere girsin mi?
4. İlk makale veri + yöntem (AS1 + AS2) olsun mu?

## Kaynaklar

- Bruno, Melo, Campanelli, Loreto (2024). A universal framework for inclusive 15-minute cities. *Nature Cities*. Platform: whatif.sonycsl.it/15mincity
- Civiero vd. (2024). Operational insights and future potential of the database for positive energy districts. *Energies* 17(4):899. Harita: pedeu.net/map
- Albert-Seifried vd. (2022). Definitions of positive energy districts: a review of the status quo and challenges. SEB 2021, Springer.
