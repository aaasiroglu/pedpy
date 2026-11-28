# 22 · Kapsam: pedx — açık veriyle kentsel yapay zekâ (K-059)

> Tek cümle: **pedx, dünyanın her yerinde aynı H3 altıgen ızgarası üzerinde yalnız açık ve küresel verilerle çalışan, her kararını gerçek örneklerle doğrulanmış bir kentsel yapay zekâ karar destek sistemidir. Çekirdek karar problemi pozitif enerji bölgesi (PED) planlamasıdır.**

Bu belge projenin sınırını çizer. Bir sistem mühendisi gözüyle yazıldı: bir çekirdek, bu çekirdeğe takılan sayılı karar modülleri ve bir modülün kapsama girip giremeyeceğini belirleyen tek bir kural. Amaç dallanıp budaklanmak değil. Amaç, elimizdeki veri ve şehirlerle doğrulanabilir olan her kararı aynı altyapıdan üretmek.

## 1. Adlandırma

| Katman | Ad | Ne |
|---|---|---|
| Sistem | **pedx · Açık Kentsel Zekâ** (Urban AI) | Bütün sistem: veri katmanı, modeller, ajan, arayüz |
| Yazılım kütüphanesi | `pedx` | Python paketi; değişmiyor |
| Ajan | `pedx-agent` | Soruyu araç çağrılarına çeviren planlayıcı (docs/21) |

"PED" adı kütüphanede kalıyor, çünkü çekirdek karar ve tezin iddiası PED. "Kentsel yapay zekâ" ise sistemin kapsamını anlatıyor: aynı veri katmanı ve aynı doğrulama yöntemi başka kentsel kararlara da hizmet edebiliyor.

## 2. Mimari: bir çekirdek, takılabilir karar modülleri

```
                ┌──────────────────────── pedx-agent (soru → araç planı → kaynaklı yanıt) ────────────────────────┐
                │                                                                                                  │
   Karar modülleri:  M1 PED uygunluğu (çekirdek) · M2 Kentsel dönüşüm baskısı · M3 Konum değeri · M4 Kırılganlık
                │   her modül = hedef değişken + doğrulama etiketi + ağırlıklar + açıklama + tersine analiz          │
                └──────────────────────────────────────────────┬───────────────────────────────────────────────────┘
                                                               │ aynı özellik tablosu
   Küresel H3 özellik deposu:  hücre_id × özellik × kaynak × sürüm   (r9 / r10 / r11; bina ve yapı adası aşağı ölçek)
                                                               │ bağlayıcılar (yalnız istenen pencereyi okur)
   Açık küresel veri:  Overture (OSM tabanlı küre) · GHSL · HRSL · WorldCover · Sentinel-2 · Landsat · DEM · PVGIS · UNSD · Wikidata
```

**Arayüz sözleşmesi** (modüller arasında tek ortak nokta):
- Özellik deposu satırı: `(h3_cell, resolution, feature, value, source_id, release, license)`.
- Modül çıktısı: `(h3_cell, module, score_0_100, contributions{feature: logit}, applicable: bool, inverse(target))`.

Yeni bir modül bu iki sözleşmeye uyuyorsa haritaya, rapora ve ajana kod yazılmadan bağlanır. Bu kural PED skorunun (`pedx.score.PEDScore`) bugün nasıl çalıştığını genelleştiriyor. Yeni bir sınıf yazılmıyor; aynı sınıf başka bir hedef ve başka bir etiketle yeniden kullanılıyor.

## 3. "Küresel ölçekte hexagonlar" ne demek?

Dünyanın bütün karası r10'da yaklaşık 10 milyar hücre ediyor (r10 hücresi ~0,015 km², kara ~149 milyon km²). Hepsini önceden hesaplamak gereksiz ve imkânsız. Bunun yerine üç katman var:

| Katman | Ne zaman hesaplanır | Kapsam | Veri |
|---|---|---|---|
| **K0 · Küresel tarama** | Bir kez, toplu | GHSL SMOD'daki kentsel kümelerin tamamı, r7–r8 | Yalnız raster katmanlar: GHS-POP, GHS-BUILT, WorldCover, PVGIS ızgarası, ülke enerji tablosu |
| **K1 · Kent penceresi** | İstendiğinde, sonuç önbelleğe yazılır | Herhangi bir kent, 16×16 km (İstanbul 60×60 km), r9/r10 | Bütün katmanlar (bugünkü 19 alan böyle hesaplandı) |
| **K2 · Saha** | Tıklandığında | Tek hücre ve komşuları, r11, bina, yapı adası | Bina ölçeğine dasimetrik dağıtım (docs/19 V6) |

- K0'ın büyüklüğü SMOD'dan hesaplanacak; ilk iş bu (Bölüm 7, adım 1).
- K1 bugün çalışıyor: `pedx.citygrid.city_grid(lat, lon)` her koordinat için aynı kodu çalıştırıyor.
- K2 de bugün çalışıyor: `pedx.service.assess_point` ve çok ölçekli Caferağa çalışması.

### "OSM küresi"

Gezegen ölçeğinde OSM'yi (planet.osm, onlarca GB PBF) indirip işlemiyoruz. Küresel OSM katmanı olarak **Overture Maps GeoParquet** kullanılıyor:
- OSM'den türetilmiş, ODbL lisanslı, aylık sürümlü ve sürümü sabitlenebiliyor (`overture.RELEASE`).
- Bulutta duruyor. Satır grubu dizini sayesinde yalnız istenen pencere okunuyor: Kadıköy için 256 satır grubundan 1'i.
- Temalar: binalar, mekânlar, ulaşım, arazi kullanımı, su, altyapı, idari bölümler.

Overpass yalnız Overture'da eksik kalan katmanlar için kullanılıyor: toplu taşıma durakları, özel arazi. Overpass kırılgan bir kaynak; bu oturumda da bağlantıyı reddetti. O yüzden her Overpass katmanının bir Overture ya da Wikidata yedeği var (K-052, K-058).

## 4. Elimizdeki veri

Katalog (`pedx.datalake.catalog`) 55 veri seti içeriyor:

| Durum | Sayı |
|---|---|
| Sisteme alınmış (ingested) | 31 |
| Bağlayıcısı hazır | 5 |
| Planlanan | 15 |
| Lisans gerekçesiyle reddedilen | 4 |

Kapsam açısından önemli olan, her veri setinin hangi modüle hizmet ettiği:

| Tema | Veri (küresel, açık) | M1 PED | M2 Dönüşüm | M3 Konum değeri | M4 Kırılganlık |
|---|---|:-:|:-:|:-:|:-:|
| Nüfus | GHS-POP, Meta HRSL (yaş grupları) | ● | ● | ● | ● |
| Yapı stoku | GHS-BUILT S/V/H, NRES; Overture binaları (kat, yükseklik) | ● | ● | ● | ● |
| Yapı stoku değişimi | GHS-BUILT-S 1975/1990/2000/2020 dönemleri | | ● (etiket) | | ● |
| Enerji | PVGIS, UNSD ve OWID ülke tüketimi, Overture altyapısı | ● | | | |
| Mekân ve işlev | Overture mekânları (taksonomi), Overture arazi kullanımı, OSM özel arazi | ● | ● | ● | ● |
| Erişim | OSM durakları, Overture ulaşım ağı | ● | ● | ● | ● |
| Çevre | WorldCover, Sentinel-2 NDVI, Landsat yüzey sıcaklığı, Copernicus DEM | ● | | ● | ● |
| Mekânın ruhu | Wikidata (miras, P18 fotoğraf), Commons, CLIP | ● | ● | ● | |
| Yer adları | Overture divisions, Wikidata yerleri (ajan sözlüğü) | ajan | ajan | ajan | ajan |

## 5. Şehirler ve her birinin neyi doğrulayabildiği

**19 alan:** 16 gerçek PED projesi ve 3 Türkiye pilotu (Caferağa → Kadıköy → İstanbul). Bir modülün doğrulanabilmesi için o alanda açık bir doğrulama etiketi bulunmalı:

| Alanlar | M1 PED | M2 Dönüşüm | M3 Konum değeri (açık fiyat ya da değer verisi) | M4 |
|---|---|---|---|---|
| Lyon, Nantes, Dijon (FR) | gerçek PED | GHSL değişimi | **DVF tapu satışları** (data.gouv.fr, Licence Ouverte 2.0) | ● |
| Helsinki, Espoo ×2, Turku, Oulu (FI) | gerçek PED | GHSL değişimi | **İstatistik Finlandiya: posta kodu düzeyinde konut fiyatları** (CC BY 4.0) | ● |
| Amsterdam, Groningen (NL) | gerçek PED | GHSL değişimi | **CBS mahalle düzeyinde ortalama WOZ değeri** (CC BY 4.0) | ● |
| Bilbao, Vitoria-Gasteiz (ES), Viyana (AT), Lund, Uppsala (SE), Oslo/Bærum (NO) | gerçek PED | GHSL değişimi | açık işlem fiyatı yok; yalnız tahmin, doğrulama yok | ● |
| Caferağa, Kadıköy, İstanbul (TR) | aday (G2: Yıldırım 2021, Demirel 2025) | GHSL değişimi + Faz 2'de yerel dönüşüm alanları | açık fiyat yok; Faz 2'de yalnız yerel doğrulama | ● |

- M3 sütunundaki üç kaynağın erişimi ve lisansı henüz denenmedi. Planlanan durumda; ilgili alan adları ağ izin listesine eklenince teyit edilecek.
- Türkiye'de açık, işlem düzeyinde konut fiyatı yok. Bu kural (yerel veri yalnız G2 doğrulamasında) M3 için de geçerli.

## 6. Modüller: neye girer, neye girmez

**Kapsama girme kuralı.** Bir karar modülü ancak üç koşulun üçünü de sağlarsa kapsama girer:
1. Girdileri açık ve küresel.
2. En az bir ülkede açık ve gerçek bir **doğrulama etiketi** var. Sentetik etiket kabul edilmez.
3. Aynı H3 özellik deposunu ve aynı modül sözleşmesini kullanıyor.

Bir koşul eksikse modül "keşif" olarak kalır ve tezde bulgu olarak sunulmaz.

| Modül | Karar sorusu | Hedef ve etiket | Doğrulama | Durum |
|---|---|---|---|---|
| **M1 PED uygunluğu** (çekirdek) | Bu saha PED olabilir mi, ne gerekir? | Gerçek PED sahası ve kontroller | 16 PED, kentler arası dışarıda bırakma: AUC 0,80 | **Çalışıyor** (K-047…K-053) |
| **M2 Kentsel dönüşüm baskısı** | Bu sahada yapı stoku dönüşüyor mu, dönüşecek mi? | GHSL yapı yüzeyi değişimi (2000→2020) ve Overture inşaat payı | Zamansal ayırma: 2000 özellikleri → 2000–2020 değişimi; 19 alan | **Sıradaki**; veri elde |
| **M3 Konum değeri** | Bu konumun açık verilerle açıklanan değeri ne, hangi kaldıraçlar etkiler? | Hedonik model; etiket DVF, Finlandiya ve WOZ değerleri | FR, FI ve NL'de ülkeler arası dışarıda bırakma; 10 alan | Planlı; erişim teyidi gerekiyor |
| **M4 Kırılganlık** | Yaşlı, çocuk, ısı ve hizmet erişimi açısından kim risk altında? | Tanımlayıcı gösterge; tahmin değil | Ölçülen katmanlar: HRSL, Landsat; G2'de İBB toplanma alanları | Katmanlar var; skor yok |

**M1'le bağlantı.** M2, M3 ve M4 ayrı ürünler değil. M1'in kararını zenginleştiriyorlar: "Bu aday saha PED olabilir; dönüşüm baskısı yüksek (yenileme fırsatı); konum değeri şu kaldıraçlarla artar; yaşlı nüfus payı yüksek (önce enerji yoksulluğu)." Ajan bu soruların hepsini aynı araç çağrısıyla yanıtlıyor: `find_sites(objective=…)` ve `assess_site`.

**Kapsam dışı.** Bunları bilinçli olarak dışarıda bırakıyoruz:

| Konu | Neden dışarıda |
|---|---|
| Trafik tahmini, suç, sağlık sonucu | Küresel açık etiket yok |
| Google yorumları, popüler saatler | Kullanım koşulları; KVKK/GDPR (K-031) |
| Gerçek zamanlı akış verisi, dijital ikiz simülasyonu | Çekirdek karar sorusuna katkısı yok |
| Bina ölçeğinde enerji simülasyonu (EnergyPlus vb.) | Tez kapsamı yıllık denge; saatlik eşleşme Faz 2 |
| Emlak **fiyat tahmini** ürünü | M3 bir *açıklama* modülüdür, değerleme raporu değildir. Açık fiyat yalnız 3 ülkede var; Türkiye'de yok. |

## 7. Yol haritası

Sıralama çekirdeği bozmadan ilerleyecek şekilde yapıldı.

| Adım | İş | Çıktı | Doğrulama |
|---|---|---|---|
| 1 | K0 küresel tarama: SMOD kentsel kümeleri × r8 × raster katmanlar | Küresel PED ön-uygunluk haritası; K0 hücre sayısı | Gerçek 16 PED'in K0 yüzdeliği |
| 2 | M2 dönüşüm baskısı: GHSL dönemlerinden etiket, aynı `PEDScore` sınıfı | `find_sites(objective="transformation")` | Zamansal ayırma AUC; 19 alan |
| 3 | Ajan sözlüğü tamamlama (K-058): yer adları ve hedef sözcükleri, yeni bağımsız set | Planlayıcı doğruluğu | Bağımsız set-2 |
| 4 | M3 erişim teyidi (DVF, Finlandiya, CBS) → hedonik model | Konum değeri katkıları | FR/FI/NL ülkeler arası |
| 5 | M4 kırılganlık skoru (tanımlayıcı) | Raporda kırılganlık bölümü | Ölçülen katmanlarla tutarlılık |
| — | Tez yazımı: çekirdek iddialar (docs/00 pusula) | — | — |

**Tezin iddiaları değişmiyor.** M1 tezin kendisi. M2 tezde bir bölüm olabilir: aynı yöntemin ikinci bir karar problemine aktarılabildiğini gösteren genelleme kanıtı. M3 ve M4 ileri çalışma olarak kalıyor ve yalnız doğrulandıkları ölçüde yazılıyor.

## 8. Gereksinimler (sistem mühendisliği)

| No | Gereksinim | Ölçüt | Bugün |
|---|---|---|---|
| R1 | Her koordinatta aynı kod çalışır | 19 alanın hepsi tek fonksiyonla | ✔ |
| R2 | Her sayı bir kaynaktan gelir | Ajan yanıtındaki her sayı gözlemde var (topraklama testi) | ✔ |
| R3 | Her modül gerçek etiketle doğrulanır | Kentler ya da ülkeler arası dışarıda bırakma | M1 ✔, M2–M4 bekliyor |
| R4 | Model sınırını bilir | Uygulanabilirlik alanı (AoA) ve arazi kullanımı koruması | ✔ |
| R5 | Karar tersine çözülebilir | Kapalı biçimli tersine analiz | M1 ✔ |
| R6 | Yeniden üretilebilirlik | Sürümü sabitlenmiş Overture, önbellek, `make build` | ✔ |
| R7 | Lisans temiz | Katalogda her verinin lisansı; reddedilenler görünür | ✔ |
