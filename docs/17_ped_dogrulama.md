# 17 · Gerçek PED'lerle dış doğrulama (vaka–kontrol)

*Karar: K-041 · Kod: `scripts/validate_ped_sites.py` · Veri: `data/validation/` · Tarih: 2026-11-08*

## 1. Soru

Model, gerçek Pozitif Enerji Bölgelerini (PED) ve Akıllı Şehir öncü (lighthouse) sahalarını, **aynı kentteki sıradan konumlardan daha yüksek** puanlıyor mu?

Bu, modelin tek dış referansıdır. Model, kendi tanımladığı bir idealle değil, gerçekte seçilmiş ve yatırım yapılmış sahalarla sınanır.

## 2. Tasarım v1 (K-041; v2 için bkz. §2b)

| Öğe | Seçim | Gerekçe |
|---|---|---|
| Vakalar | PED Booklet 2020 (Gollner vd. 2020) ve H2020 SCC öncü projelerinde (ATELIER, SPARCS, MAKING-CITY, RESPONSE, SmartEnCity, mySMARTLife, syn.ikia, +CityxChange) adı geçen 16 saha | Yayımlanmış, adı ve yeri belli sahalar |
| Saha geometrisi | OSM nesnesi, adla Overpass'tan; OSM kimliği `ped_sites.json` dosyasında | Yeniden üretilebilir; elle koordinat girilmedi |
| Kontroller | Her saha için sahadan 1,5–8 km uzaklıkta 10 rastgele nokta (sabit tohum 20261108); en az 50 kişilik nüfus | Aynı kent: iklim (Y), ülke talebi (d) ve nüfus kaynağı aynı → kıyas adil |
| Model | `pedx.service.assess_point`, k = 2 (19 altıgen, ~0,3 km²) | Tıkla→hesapla kodunun aynısı |
| Ölçü | Saha dengesinin kontrol dağılımındaki yüzdelik sırası; havuzlanmış ortalama = tabakalı AUC; tek yönlü işaret testi | Mann–Whitney ile eşdeğer, dağılım varsayımı yok |
| Tabakalar | Gelişim tipi: kahverengi alan ve yeni yapım / mevcut stokun yenilenmesi | Aşağıdaki yanlılık bu tabakalarda ayrı raporlanır |

**Bilinen yanlılık:** kahverengi alanlar (eski liman ya da sanayi alanları) bugünkü durumlarıyla ölçülür. Az nüfus ve büyük çatılar dengeyi yükseltir. Bu yüksek skor kısmen "henüz insan yok" anlamına gelir. Bu yüzden sonuçlar tabakalara ayrılarak verilir ve gizlenmez.

**Yasak olanlar:** sonucu gördükten sonra parametre, saha listesi ya da kontrol yarıçapı değiştirilmez. Değiştirilirse yeni karar kaydı açılır ve iki sonuç da raporlanır.

## 2b. Tasarım v2 (K-043, geçerli olan)

| Öğe | v2 |
|---|---|
| Kent ızgarası | `pedx.citygrid.city_grid`: 16 × 16 km pencere, H3 r10 (~17 bin hücre/kent). Katmanlar: HRSL (nüfus, 60+, 0–5), Overture (taban alanı, mekân), Sentinel-2 (NDVI, NDBI), Landsat (en az bulutlu 4 sahnenin LST'si, kent medyanına göre anomali), Copernicus DEM (eğim, rölyef; çok döşemeli), PVGIS ve UNSD/OWID (enerji). Kent başına ~35 s. |
| Saha | Saha hücresi çevresinde k = 2 disk (19 hücre ≈ 0,28 km²) |
| Kontroller | Saha başına 30; disk merkezi yerleşik ve dolu (HRSL ≥ 20 kişi, taban alanı > 0), sahadan ≥ 1,5 km; tohum 20261108 |
| Model (a) | Yıllık konut elektriği dengesi (fiziksel çekirdek) |
| Model (b) | 20 yoğun (intensive) özelliğin (WorldCover yeşil ve su payı, toplu taşıma, şebeke varlığı ve EV şarj yoğunluğu dahil) kent içi z-puanı, L2 lojistik regresyon (C = 0,5, dengeli sınıf ağırlığı). Her seferinde bir kent dışarıda bırakılıyor: o kentin puanını o kentin verisi hiç görmüyor |
| Ölçü | Vakanın kendi kontrolleri içindeki yüzdeliği; ortalaması tabakalı AUC; tek yönlü işaret testi |
| Ek | Caferağa İstanbul içinde, tüm PED kentleriyle eğitilmiş modelle puanlanıyor (Caferağa gerçek bir PED değil, aday) |

**Sınırlılıklar:**
- 16 vaka küçük bir örneklem.
- Nüfus her yerde HRSL; düzey yanlılığı vaka ve kontrolde ortak.
- Copernicus DEM bir yüzey modeli (DSM), bu yüzden eğime binalar da karışıyor.
- Kahverengi alanlar 2023 durumuyla ölçülüyor.
- Overture'da yükseklik ve kat bilgisi seyrek.

## 3. Sonuçlar

*Tasarım v2 · 16 saha × 30 yerleşik kontrol · tohum 20261108 · 2026-11-08 · veri: `data/validation/`*

| Model | AUC | Medyanın üstündeki saha | İşaret testi (tek yönlü) |
|---|---|---|---|
| (a) Yalnız enerji dengesi | **0,82** | 16/16 | p = 0,00002 |
| (b) Tüm katmanlar (20 özellik, bir kent dışarıda) | **0,82** | 14/16 | p = 0,002 |
| (a) yoğunluk eşlemeli kontrollerle (13 saha) | 0,79 | — | — |
| (b) yoğunluk eşlemeli kontrollerle (13 saha) | 0,81 | — | p = 0,002 |

**Gelişim tipine göre (a / b):** kahverengi alan 0,82 / 0,85 · yeni yapım 0,86 / 0,89 · mevcut stok 0,81 / 0,73.

**Gerçek PED'leri ayıran özellikler** (tüm veriyle, kent içi z-puanı, lojistik katsayı):
- Daha düşük yapı örtüsü (−1,61)
- Daha az yeşil alan (−1,57)
- Kişi başı daha fazla çatı (+0,97)
- Daha yüksek enerji dengesi (+0,97)
- Daha yüksek nüfus yoğunluğu (+0,72)
- Daha düşük yaşlı payı (−0,66)
- Daha fazla su yüzeyi (+0,62)

Okuması: tipik bir gerçek PED, kıyıya yakın, seyrek yapılaşmış, büyük çatılı ve dönüşüm geçiren bir kentsel alandır. Liman ve sanayi alanlarının dönüşümü bu tanıma uyar.

**Veri ölçekleme eğrisi** (`data/validation/data_scaling.json`, %90 bootstrap aralığı):

| Adım | Özellik | AUC | %90 aralık |
|---|---|---|---|
| Fizik: enerji dengesi | 1 | 0,82 | 0,77–0,88 |
| + Yapılı çevre | 5 | 0,84 | 0,77–0,90 |
| + Demografi ve kırılganlık | 8 | 0,84 | 0,77–0,90 |
| + Uydu (S2, Landsat, WorldCover) | 13 | 0,83 | 0,75–0,90 |
| + Arazi (DEM) | 15 | 0,84 | 0,78–0,90 |
| + Kentsel işlev (mekânlar) | 17 | 0,88 | 0,83–0,92 |
| + Altyapı | 20 | 0,82 | 0,74–0,90 |

**Caferağa (İstanbul içinde, gerçek bir PED değil):**
- Enerji dengesine göre İstanbul'daki yerleşik alanların %73'ünden yüksek (denge 1,30, HRSL nüfusuyla).
- Gerçek PED imzasına göre %43'lük dilimde, yani İstanbul ortalamasında.
- Okuması: Caferağa fiziksel olarak elverişli, ama bugünkü gerçek PED'lerin tipik sahasına (kıyıda dönüşen, seyrek yapılı alan) benzemiyor. Yoğun ve tarihî bir dokuda PED, mevcut referans sınıfının dışında yeni bir proje türü olur. Bu, tezin Caferağa vakası için en önemli bulgusu.

## 3b. Yorum

1. **İddia B doğrulandı (sınırlı örneklemle):** fizik çekirdeği tek başına gerçek PED'leri kendi kentlerindeki yerleşik alanlardan ayırıyor (AUC 0,82; 16/16 saha medyanın üstünde). Yoğunluk eşlemesinden sonra da etki sürüyor (0,79), yani sonuç yalnızca "seyrek nüfus" etkisi değil.
2. **Büyük soruya ampirik yanıt:** veri ailesi eklemek AUC'yi istatistiksel olarak anlamlı artırmıyor; bütün aralıklar örtüşüyor. Kentsel işlev ailesi en iyi değeri veriyor (0,88). Altyapı eklenince AUC düşüyor: 16 vakayla 20 özellik aşırı öğrenmeye başlıyor. Daha fazla veri, daha fazla vaka olmadan kesinlik getirmiyor. Belirsizliği daraltan şey veri katmanı değil, öğrenilecek gerçek örnek sayısı. Faz 2'nin önceliği bu yüzden PED Veritabanı ile vaka setini büyütmek.
3. **Sınırlılıklar:**
   - 16 vaka var.
   - Sahalar adla bulundu; OSM ağırlık merkezi proje sınırı değil.
   - Kahverengi alanlar 2023 durumuyla ölçülüyor.
   - HRSL düzey yanlılığı taşıyor.
   - DEM bir yüzey modeli (DSM).

## 4. Caferağa çalışmalarının doğrulanması (G2)

| Karşılaştırma | pedx (küresel açık veri) | Yerel ya da önceki çalışma | Durum |
|---|---|---|---|
| Nüfus | GHS-POP 22.005 (+%2,7) · HRSL 35.375 (+%65) | TÜİK ADNKS 2020: 21.421 | ✅ |
| Kişi başı elektrik | Ember 3.713 kWh | TEDAŞ 2023 İstanbul: 2.678 kWh | ✅ (fark açıklandı) |
| Çatı güneş potansiyeli | 26,44 GWh/yıl (u = 0,26, η = 0,20, PVGIS 1.268 kWh/kWp) | Demirel vd. (2025), *Open Research Europe* 5:81, 3B CBS analizi | ⏳ Makale bu ortamdan erişilemedi (ore.eu engelli). Tablo değerleri tam metinden alınacak; platformlar arası %22,29 fark belirsizlik bandı olarak kullanılacak |
| Saatlik konut profili | Demand.ninja + EPİAŞ ayrıştırması | EPİAŞ mesken (AYEDAŞ) profili | ⏳ EPİAŞ hesabı |
| Toplanma alanına erişim | OSM'de yok | İBB afet toplanma alanları | ⏳ G2 |

## 5. Yorumlama kuralı (önceden yazıldı)

- **AUC > 0,5 ve işaret testi p < 0,05:** fiziksel denge, gerçek PED seçimini kısmen açıklıyor. Tabakalar ayrı ayrı okunur.
- **AUC ≈ 0,5:** yıllık denge tek başına PED seçimini açıklamıyor. Eksik ölçütler (yönetişim, kamu arazisi, yeni yapım, bölgesel ısı ağı) referans sınıf modeline (A10) ve altıgen transformer'ına (docs/16) eklenir. Bu da tezin bulgusudur.
- **Yeniden yapım tabakası yüksek, mevcut stok düşük çıkarsa:** yoğun mevcut dokuda PED ancak sanal ya da bölgesel enerjiyle mümkündür. Bu, Caferağa için doğrudan çıkarımdır.
