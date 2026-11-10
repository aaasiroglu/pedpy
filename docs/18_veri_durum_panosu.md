# 18 · Veri durum panosu (otomatik üretilir: `pedx.datalake.catalog`)

*55 veri seti · sistemde 31 · bağlayıcı 5 · planlı 15 · reddedildi 4*

Kural: yalnızca açık lisanslı, küresel veri model girdisidir. Yerel veri (İBB, EPİAŞ, TÜİK) yalnızca Faz 2 doğrulamasıdır. Reddedilenler kullanım koşulları ya da kişisel veri nedeniyle dışarıdadır.

| Durum | Tema | Veri | Çözünürlük | Lisans | Erişim / engel | Kullanım |
|---|---|---|---|---|---|---|
| ✅ sistemde | bina | OpenStreetMap | poligon | ODbL 1.0 | Overpass API | built_*, morph_* |
| ✅ sistemde | bina | JRC GHS-BUILT-S R2023A (toplam) | 3″ | CC BY 4.0 | jeodpp tiles | ghsl_built_surface_m2 |
| ✅ sistemde | bina | JRC GHS-BUILT-S NRES R2023A | 3″ | CC BY 4.0 | jeodpp tiles | ghsl_nres_surface_m2 |
| ✅ sistemde | bina | JRC GHS-BUILT-V R2023A (toplam) | 3″ | CC BY 4.0 | jeodpp tiles | ghsl_volume_m3 |
| ✅ sistemde | bina | JRC GHS-BUILT-V NRES R2023A | 3″ | CC BY 4.0 | jeodpp tiles | ghsl_nres_volume_m3 |
| ✅ sistemde | bina | JRC GHS-BUILT-H AGBH R2023A | 3″ | CC BY 4.0 | jeodpp tiles | ghsl_height_m |
| ✅ sistemde | bina | Overture Maps buildings (OSM + Microsoft/Google ML + Esri) | poligon + yükseklik/kat | ODbL 1.0 | S3 GeoParquet (satır grubu indeksi) | ov_bld_*, ov_nonosm_share; tıkla→hesapla taban alanı |
| ✅ sistemde | cevre | ESA WorldCover 2021 v200 | 10 m | CC BY 4.0 | AWS COG (esa-worldcover) | env_wc_* (yeşil, yapılı, su payı) |
| ✅ sistemde | cevre | Copernicus DEM GLO-30 | 30 m | Copernicus DEM lisansı | AWS open data (COG) | yükseklik, eğim, rölyef |
| ✅ sistemde | enerji | EU JRC PVGIS 5.3 | saatlik, nokta | AB yeniden kullanım | re.jrc.ec.europa.eu API | energy_pv_* |
| ✅ sistemde | enerji | UN Statistics Division (UNdata) | ülke, yıllık | atıfla serbest | data.un.org | konut elektriği/kişi |
| ✅ sistemde | enerji | Our World in Data (Ember, UN WPP) | ülke, yıllık | CC BY 4.0 | GitHub CSV | nüfus, talep/kişi |
| ✅ sistemde | enerji | Overture Maps base/infrastructure (trafo, jeneratör, EV şarj, toplu taşıma, bisiklet) | nokta | ODbL 1.0 | S3 GeoParquet | şebeke varlığı, EV şarj, toplu taşıma yoğunluğu |
| ✅ sistemde | goruntu | Copernicus Sentinel-2 L2A | 10 m | Copernicus açık | Earth Search STAC (COG) | NDVI, NDBI |
| ✅ sistemde | goruntu | USGS Landsat 8/9 C2 L2 (ST) | 30 m (ısıl 100 m) | kamu malı | Planetary Computer STAC (COG) | yüzey sıcaklığı (LST) |
| ✅ sistemde | goruntu | Wikimedia Commons coğrafi etiketli fotoğraflar | nokta | CC BY-SA ve özgür lisanslar | commons.wikimedia.org API (≤1 istek/s) | cm_photos_n (fotoğrafik dikkat) |
| ✅ sistemde | iklim | ECMWF ERA5 (Open-Meteo) | saatlik, ~25 km | CC BY 4.0 | archive-api.open-meteo.com | Demand.ninja girdisi |
| ✅ sistemde | insan | JRC GHS-POP R2023A | 3″ (~90 m), 1975–2030 | CC BY 4.0 | jeodpp.jrc.ec.europa.eu tiles | demo_population |
| ✅ sistemde | kent | OpenStreetMap | nokta | ODbL 1.0 | Overpass API | poi_* |
| ✅ sistemde | kent | Overture Maps places (Meta, Foursquare OS Places, Microsoft, AllThePlaces) | nokta | CDLA-Permissive-2.0 | S3 GeoParquet | ov_places_* (Caferağa: OSM'nin 1,7 katı) |
| ✅ sistemde | kent | Foursquare OS Places (Swarm/Foursquare tabanı, 100M+) | nokta | Apache 2.0 | Overture places içinde (kaynak: Foursquare) | Overture places içinde zaten var |
| ✅ sistemde | kent | OpenStreetMap boundary | poligon | ODbL 1.0 | Overpass API | AOI sınırı |
| ✅ sistemde | kent | Overture Maps base/land_use (meydan, yaya, park, inşaat, konut, ticaret) | poligon | ODbL 1.0 | S3 GeoParquet | lu_* (meydan, yeşil, inşaat payı) |
| ✅ sistemde | kent | Overture places taksonomisi (sosyal, finans, eğitim, kültür, miras, inanç, gece …) | nokta | CDLA-Permissive-2.0 | S3 GeoParquet | pl_* (işlev profili, karışım) |
| ✅ sistemde | kirilganlik | Meta Data for Good HRSL (genel, 60+, 0–5, 15–24, kadın 15–49) | 1″ (~30 m) | CC BY 4.0 | AWS COG (dataforgood-fb-data/hrsl-cogs) | vul_* (yaşlı, çocuk, genç) |
| ✅ sistemde | kirilganlik | JRC GHS-BUILT-S R2023A E1975/E1990/E2000 | 3″ | CC BY 4.0 | jeodpp tiles | vul_built_pre*_share (doku yaşı) |
| ✅ sistemde | kirilganlik | OpenStreetMap (hastane, itfaiye, okul, bakım, toplanma alanı) | nokta | ODbL 1.0 | Overpass API | res_* |
| ✅ sistemde | sokak | OpenStreetMap highway | çizgi | ODbL 1.0 | Overpass API | mob_* |
| ✅ sistemde | sokak | OpenStreetMap | nokta | ODbL 1.0 | Overpass API | mob_walk800_transit_stops |
| ✅ sistemde | sokak | Uber H3 (açık kaynak altıgen ızgara) | ızgara | Apache 2.0 | pip h3 | tüm mekânsal birim |
| ✅ sistemde | sosyal | Wikidata (önemli yerler, miras P1435, meydan Q174782, sitelink) | nokta | CC0 1.0 | query.wikidata.org SPARQL | wd_* (kolektif dikkat, miras) |
| 🔌 bağlayıcı hazır | enerji | EPİAŞ Şeffaflık (TR ulusal yük) — yalnız Faz 2 yerel doğrulama | saatlik, ülke | atıfla kullanım; hesap gerekli | seffaflik.epias.com.tr API (TGT) | Faz 2: saatlik profil doğrulaması |
| 🔌 bağlayıcı hazır | goruntu | OpenAI CLIP ViT-B/32 (açık ağırlık) — sıfır-atış mekân algısı | görüntü başına | MIT | huggingface.co | Faz 3: fotoğraflardan canlı/güvenli/tarihî/yeşil algısı |
| 🔌 bağlayıcı hazır | kent | Overture Maps divisions (ülke…mahalle) | poligon | ODbL 1.0 | S3 GeoParquet | ülke/bölge eşlemesi |
| 🔌 bağlayıcı hazır | sokak | Overture Maps transportation (segment, connector) | çizgi | ODbL 1.0 | S3 GeoParquet | OSM yaya ağına küresel yedek |
| 🔌 bağlayıcı hazır | sosyal | Wikipedia ve Wikivoyage yer metinleri | metin | CC BY-SA 4.0 | API (geosearch) | Faz 3: NLP ile mekân anlatısı (yorum yerine açık metin) |
| ⏳ planlı | bina | Microsoft Global ML Building Footprints | poligon | ODbL | GitHub / Planetary Computer | taban alanı tamlığı |
| ⏳ planlı | bina | Google Open Buildings (2.5D Temporal) | poligon / 4 m | CC BY 4.0 / ODbL | GCS | yükseklik (kapsam teyit) |
| ⏳ planlı | ekonomi | Kummu vd. 2018 (Dryad) | 5′ / 30″ | CC0 1.0 | datadryad.org (ağ açık; 30″ NetCDF büyük → COG dönüşümü) | GSYH, İGE |
| ⏳ planlı | enerji | Chen vd. 2022 (figshare) | 1 km, 1992–2019 | teyit | figshare | bağımsız talep sınaması |
| ⏳ planlı | enerji | World Bank / Solargis Global Solar Atlas | 250 m | CC BY 4.0 | globalsolaratlas.info | PVGIS çapraz kontrol |
| ⏳ planlı | goruntu | Google AlphaEarth Satellite Embedding | 10 m, 64-B | teyit | Earth Engine | gömme vektörleri |
| ⏳ planlı | goruntu | Mapillary | sokak görüntüsü | CC BY-SA 4.0; anahtar | graph.mapillary.com (kullanıcı erişim anahtarı gerekli) | kat ve cephe tahmini |
| ⏳ planlı | insan | WorldPop | 100 m | CC BY 4.0 | data.worldpop.org (ülke dosyası, COG değil) | yaş yapısı (HRSL'ye alternatif) |
| ⏳ planlı | kent | JRC GHS-SMOD R2023A | 1 km | CC BY 4.0 | jeodpp (Mollweide döşeme; bağlayıcı S2) | kentsel/kırsal derece |
| ⏳ planlı | kirilganlik | JRC GloFAS/CEMS taşkın tehlike haritaları (10–500 yıl) | 3″ (~90 m) | kısıtsız (JRC) | data.jrc.ec.europa.eu | taşkın derinliği |
| ⏳ planlı | kirilganlik | GEM Global Seismic Hazard Map (PGA, 475 yıl) | ~1 km | CC BY-NC-SA 4.0 (ticari kullanım anlaşmayla) | globalquakemodel.org | deprem tehlikesi (akademik) |
| ⏳ planlı | kirilganlik | İBB Açık Veri: afet toplanma alanları | nokta | İBB Açık Veri Lisansı | data.ibb.gov.tr | yalnız G2 doğrulama (OSM'de yok) |
| ⏳ planlı | ped | PED Database (COST PED-EU-NET, JPI UE, IEA Annex 83) | proje | teyit | pedeu.net / Annex 83 | referans sınıfı |
| ⏳ planlı | sokak | MobilityData | tarife | kaynağa göre açık | mobilitydatabase.org | sefer sıklığı |
| ⏳ planlı | sosyal | GDELT Project | olay, şehir | açık (teyit) | gdeltproject.org | haber tonu |
| ⛔ reddedildi | enerji | Google Environmental Insights Explorer | kent | lisanslı paylaşım, açık değil | - | yalnız literatür karşılaştırması |
| ⛔ reddedildi | kent | Yandex Haritalar / panorama | - | açık lisans yok | - | kullanılamaz |
| ⛔ reddedildi | sokak | Uber Movement seyahat süreleri | bölge çifti | kapatıldı / kullanım koşulları | - | erişilemez |
| ⛔ reddedildi | sosyal | Google Maps Popular Times / yorumlar | mekân | Google ToS (açık değil), KVKK/GDPR | - | kazıma yasak |

## Planlı olanların yolu

| Veri | Engel | Çözüm | Sprint |
|---|---|---|---|
| Mapillary | kullanıcı erişim anahtarı | ortam sırrı olarak eklenir (request_credential) → sokak görüntüsü + CLIP | S3 |
| CLIP (görüntü algısı) | torch kurulumu (~700 MB) | Commons/Mapillary fotoğraflarında sıfır-atış algı puanları | S3 |
| Wikipedia/Wikivoyage NLP | — | açık metinle mekân anlatısı; LLM yalnız özetler, sayı üretmez | S3 |
| GHS-SMOD | Mollweide döşeme | raster motoru CRS dönüşümünü destekliyor; döşeme indirici eklenecek | S2 |
| Kummu GSYH/İGE | büyük NetCDF | bir kez indirip COG'a çevirme | S2 |
| GloFAS taşkın | büyük döşemeler | COG pencere okuma | S3 |
| GEM sismik | NC lisansı | yalnız akademik; ayrı katman | S3 |
| WorldPop | ülke dosyaları | HRSL ile karşılaştırma için seçili ülkeler | S4 |
| Google Open Buildings / MS Buildings | Overture içinde kısmen var | Overture ML payı (ov_nonosm_share) yeterli; ek gerekirse | — |
| GTFS (MobilityData) | API anahtarı | sefer sıklığı | S4 |
| GDELT | büyük akış | kent düzeyi haber tonu | S5 |
| AlphaEarth | Earth Engine hesabı | açık alternatif: Clay/Prithvi gömmeleri | S5 |
| PED Veritabanı | lisans teyidi | vaka setini büyütmek için en kritik kaynak | Faz 2 |
| İBB toplanma alanları | yerel veri | yalnızca G2 doğrulaması | Faz 2 |
