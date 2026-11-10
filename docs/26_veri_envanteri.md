# 26 — Veri envanteri: tezde kullanılan bütün veriler ve kaynakları

Tek doğru kaynak `src/pedx/datalake/catalog.py` (55 kayıt: 31 sisteme alındı, 5 bağlayıcı hazır, 15 planlı,
4 reddedildi). Bu belge onu tezin çekirdeğine göre süzer. Kural (K-025): modele yalnız **küresel ve açık
lisanslı** veri girer; yerel veri yalnız doğrulamada kullanılır. Ayrıntı ve araştırma günlüğü: `docs/11`.

## 1. Tezin çekirdeğine giren veriler

| # | Veri | Sağlayıcı, sürüm | Çözünürlük | Lisans | Tezde ne için |
|---|---|---|---|---|---|
| 1 | Bina taban alanları, kat bilgisi | Overture Maps buildings (OSM + Microsoft/Google ML + Esri) | poligon | ODbL 1.0 | Çatı alanı → FV üretimi; bina sayısı, taban alanı, kat kapsamı, OSM dışı pay |
| 2 | Nüfus ve yaş grupları | Meta Data for Good HRSL (genel, 60+, 0–5) | 1″ (~30 m) | CC BY 4.0 | Talep (kişi sayısı); yoğunluk, yaşlı ve çocuk payı |
| 3 | FV üretimi | EU JRC PVGIS 5.3 (SARAH-3 + ERA5), 1 kWp, kayıp %14 | saatlik, nokta | AB yeniden kullanım | Enerji dengesinin payı |
| 4 | Konut elektrik tüketimi | UN Statistics Division, Energy Statistics (UNdata) | ülke, yıllık | atıfla serbest | Enerji dengesinin paydası (kişi başı) |
| 5 | Ülke nüfusu | UN WPP, Our World in Data üzerinden | ülke, yıllık | CC BY 4.0 | 4'ü kişi başına çevirmek |
| 6 | Arazi örtüsü | ESA WorldCover 2021 v200 | 10 m | CC BY 4.0 | Yeşil, yapılı, su, tarım payı; çıplak alan (dönüşüm sınaması) |
| 7 | Yansıtım indisleri | Copernicus Sentinel-2 L2A | 10 m | Copernicus açık | NDVI, NDBI |
| 8 | Yüzey sıcaklığı | USGS Landsat 8/9 Collection 2 Level 2 | 30 m (ısıl 100 m) | kamu malı | LST ortalaması ve kent içi sapması |
| 9 | Yükseklik modeli | Copernicus DEM GLO-30 | 30 m | Copernicus DEM lisansı | Yükseklik, eğim, rölyef |
| 10 | Mekânlar (POI) | Overture Maps places (Meta, Foursquare OS Places, Microsoft) | nokta | CDLA-Permissive-2.0 | Mekân sayısı, kategori çeşitliliği, kişi başı mekân |
| 11 | Altyapı | Overture Maps base/infrastructure | nokta | ODbL 1.0 | Şebeke varlıkları, toplu taşıma durakları |
| 12 | Arazi kullanımı | Overture Maps base/land_use | poligon | ODbL 1.0 | Arazi kullanımı koruması; inşaat ve konut alanı (dönüşüm sınaması) |
| 13 | Yapılı yüzey, konut dışı pay | JRC GHS-BUILT-S ve NRES R2023A | 3″ (~90 m) | CC BY 4.0 | Konut dışı yapı payı (dönüşüm sınaması); bina tamlığı çapraz kontrolü |
| 14 | Mekânsal birim | Uber H3 (r9, r10, r11) | ızgara | Apache 2.0 | Bütün toplulaştırma; ~28 ha aday saha |

Parametreler (veri değil, literatür değeri): çatı kullanım katsayısı 0,26–0,50 (Gagnon vd. 2016, NREL);
modül verimi 0,20 (Fraunhofer ISE Photovoltaics Report).

### Hangi veri hangi ölçütü üretiyor (31 ölçüt)

| Aile | Ölçüt sayısı | Kaynak |
|---|---|---|
| Enerji dengesi | 1 | 1 + 2 + 3 + 4 + 5 |
| Bina | 6 | 1 (+ 2: kişi başı çatı) |
| Nüfus ve kırılganlık | 6 | 2 |
| Uydu | 4 | 7, 8 |
| Arazi örtüsü | 4 | 6 |
| Arazi | 3 | 9 |
| Kentsel işlev | 3 | 10 (+ 2) |
| Altyapı | 4 | 11 |

Not: "kişi başı çatı alanı" ile "enerji dengesi" kent içinde özdeştir (K-065); bağımsız ölçüt sayısı 30.

## 2. Etiket: gerçek PED'ler

| Veri | Kaynak | Not |
|---|---|---|
| 16 PED sahasının adı ve kenti | PED Booklet (Gollner vd. 2020) ve H2020 SCC öncü projeleri: ATELIER, SPARCS, MAKING-CITY, RESPONSE, SmartEnCity, mySMARTLife, syn.ikia, +CityxChange | Liste sonuç görülmeden donduruldu (`docs/17`) |
| Sahaların konumu | OpenStreetMap nesne kimlikleri (`data/validation/ped_sites.json`) | ODbL 1.0 |
| Kontroller | Aynı kentin 16×16 km penceresinden 30 yerleşik saha | Veriden türetilir |
| PED türü (yeni gelişim / mevcut mahalle) | Proje tanımlarından elle etiket (K-064) | **Kaynakla doğrulanacak** |

Sahalar: Buiksloterham (Amsterdam), Zorrotzaurre (Bilbao), Kera ve Leppävaara (Espoo), Fornebu (Bærum),
Kaukovainio (Oulu), Paddepoel (Groningen), Fontaine d'Ouche (Dijon), Linnakaupunki (Turku), Confluence (Lyon),
Seestadt Aspern (Viyana), Brunnshög (Lund), Coronación (Vitoria-Gasteiz), Rosendal (Uppsala),
Kalasatama (Helsinki), Île de Nantes (Nantes).

## 3. Yerel doğrulama verileri (modele girmez)

| Veri | Kaynak | Ne için |
|---|---|---|
| İstanbul kişi başı net tüketim, 2022 | TEDAŞ 2023 Sektör Raporu, Tablo 7 | Ulusal ortalamanın İstanbul'daki sapması |
| Caferağa nüfusu, 2020 | TÜİK ADNKS (Kadıköy Belediyesi üzerinden) | Nüfus rasterinin doğrulanması |
| İstanbul çatı FV potansiyeli | Yıldırım (2021) | Açık veriyle hesaplanan potansiyelin karşılaştırılması |
| Bina sayısı ve 3B çatı ışınımı | Demirel vd. (2025), Open Research Europe 5:81 | OSM ve GHSL bina tamlığı |
| Saatlik konut profili | EPİAŞ profil katsayıları | Planlı (Faz 2) |
| Bina envanteri, LiDAR | İBB | Planlı; erişim gerekiyor |

## 4. Sisteme alınmış ama tez çekirdeğinde kullanılmayan veriler

Ek modüller ve ajan için: OpenStreetMap (binalar, POI, yaya ağı, duraklar, idari sınır, dayanıklılık tesisleri),
JRC GHS-POP, GHS-BUILT-V, GHS-BUILT-H ve yapı dönemleri, Overture places taksonomisi, Foursquare OS Places,
Wikidata, Wikimedia Commons, ERA5 (Open-Meteo), Overture divisions (yer adı sözlüğü).

## 5. Planlı ve reddedilen

- **Planlı (15):** Microsoft ve Google bina izleri, Global Solar Atlas, GHS-SMOD, WorldPop, GloFAS taşkın,
  GEM deprem, Kummu GSYH/İGE, Chen elektrik, AlphaEarth, Mapillary, GTFS, GDELT, PED Database, İBB toplanma alanları.
- **Reddedilen (4):** Google Environmental Insights Explorer (açık değil), Google Popular Times ve yorumlar
  (kullanım koşulları, KVKK/GDPR), Yandex Haritalar (açık lisans yok), Uber Movement (kapatıldı).

## 6. Bilinen veri eksikleri

1. Konut dışı elektrik talebi mekâna dağıtılmıyor (UNSD'de ülke toplamı var).
2. Isıtma talebi yok.
3. Kişi başı talep ülke ortalaması; kent içi farklılaşma yok.
4. Gerçek PED'lerin ölçülmüş yıllık enerji dengesi yok.
5. Maliyet ve mülkiyet verisi yok.
