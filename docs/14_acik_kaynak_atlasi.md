# 14: Açık Kaynak Atlası (insan, bina, sokak, kent, enerji ve ötesi)

*Tarih: 2026-11-08 · Kural K-025: girdi olabilmesi için kaynağın küresel kapsamlı ve açık lisanslı olması gerekir. Durum: ✅ pedx'te etkin · 🟡 planlı (katalogda) · 🔍 değerlendirilecek · ⛔ kullanılmayacak (gerekçeli). Lisanslar "teyit" işaretliyse kaynağın kendi sayfasında doğrulanmadan girdi yapılmaz.*

## 1. İnsan (nüfus, demografi, aktivite)

| Kaynak | Ne verir | Çözünürlük ve kapsam | Lisans | Durum | pedx katmanı |
| --- | --- | --- | --- | --- | --- |
| JRC GHS-POP R2023A | Nüfus | ~90 m, küresel, 1975–2030 | CC BY 4.0 ✓ | ✅ | `demo_*` |
| WorldPop (yaş ve cinsiyet) | Yaş yapısı, 65+ | 100 m, küresel | CC BY 4.0 | 🟡 | `demo_age_65plus_share` |
| Meta HRSL / Data for Good | Nüfus ve demografi | 30 m | CC BY 4.0 (teyit) | 🔍 | GHS-POP ile çapraz kontrol |
| GHS-SMOD | Kentsel–kırsal derece | 1 km | CC BY 4.0 | 🔍 | Bağlam (kentsel tipoloji) |
| UN WPP, Our World in Data | Ülke nüfusu | ülke | CC BY 4.0 ✓ | ✅ | Kişi başı türetimler |

## 2. Bina (geometri, yükseklik, kullanım, yaş)

| Kaynak | Ne verir | Lisans | Durum | Not |
| --- | --- | --- | --- | --- |
| OpenStreetMap binaları | Taban alanı, kat (%17), kullanım etiketi | ODbL ✓ | ✅ | Tamlık göstergesi tutuluyor |
| **Overture Maps Buildings** | OSM, Microsoft ve Google birleşik; yükseklik alanı | ODbL / CDLA (katmana göre, teyit) | 🔍 Öncelikli | OSM'deki kat ve yükseklik boşluğunu doldurabilir |
| Microsoft Global ML Building Footprints | Taban alanı, bazı bölgelerde yükseklik | ODbL | 🔍 | — |
| Google Open Buildings 2.5D Temporal | Yükseklik (Güney yarıküre ve Asya ağırlıklı) | CC BY 4.0 / ODbL (teyit) | 🔍 | Türkiye kapsamı teyit edilecek |
| JRC GHS-BUILT-S/H/V/C R2023A | Yapı alanı, **konut dışı yapı alanı**, yükseklik, hacim, morfolojik bölgeler | AB yeniden kullanımı (teyit) | 🟡 | `built_nres_surface_m2`, `built_height_m`, `built_volume_m3` |
| EUBUCCO | Avrupa'da bina yaşı, yükseklik ve tipi (resmî kaynaklardan derlenmiş) | ODbL / değişken | 🔍 | Avrupa'daki PED vakaları için eğitim verisi |
| Mapillary | Sokak görüntüsü → kat sayısı, pencere/duvar oranı | CC BY-SA 4.0; erişim anahtarı gerekli | 🟡 | `img_svi_levels_est`, `img_svi_wwr_est` |

## 3. Sokak ve hareketlilik (yürünebilirlik, erişim)

| Kaynak ya da araç | Ne verir | Lisans | Durum | pedx katmanı |
| --- | --- | --- | --- | --- |
| OSM yaya ağı + Dijkstra (pedx) | 10 dakikalık yürüme erişimi, günlük ihtiyaç tamlığı, durak, sokak ve kavşak yoğunluğu | ODbL ✓ | ✅ | `mob_*` (7 özellik) |
| OSMnx (Boeing 2017) | Ağ ölçütleri (dairesellik, bağlantılılık, merkezilik) | MIT | 🔍 | Ağ tipolojisi |
| cityseer (Simons 2022) | Yaya ölçeğinde merkezilik, karışık kullanım ve erişilebilirlik | AGPL-3.0 (lisans uyumu teyit) | 🔍 | Merkezilik katmanı |
| pandana, r5py | Hızlı ağ erişimi, toplu taşımalı yolculuk süresi | BSD / GPL (teyit) | 🔍 | — |
| Mobility Database (GTFS) | Toplu taşıma tarifeleri | Kaynağa göre açık lisans | 🔍 | Sefer sıklığı |
| OSM `amenity=charging_station` | EV şarj noktaları | ODbL | 🟡 | `mob_ev_chargers` |
| PedPy (Jülich) | **Deneysel yaya yörüngelerinin** analizi | MIT | ⛔ Kapsam dışı | Kent ölçeğinde erişilebilirlik aracı değil; adı benzer |
| Walk Score | Yürünebilirlik puanı | Ticari | ⛔ | Açık değil |

## 4. Kent ve morfoloji

| Kaynak ya da araç | Ne verir | Lisans | Durum |
| --- | --- | --- | --- |
| momepy (Fleischmann 2019) | Bina ve sokak morfometrisi | BSD-3 ✓ | ✅ `morph_*` (7 özellik) |
| srai (Spatial Representations for AI) | H3 için OSM tabanlı gömme vektörleri (Hex2Vec, GeoVex) | Apache-2.0 (teyit) | 🔍 Öncelikli: POI ve sokak gömmeleri |
| GHS Urban Centre Database | Kent merkezi sınırları ve göstergeleri | CC BY 4.0 (teyit) | 🔍 Küresel benchmark şehirlerini seçmek için |
| OSM idari sınırlar | Mahalle, ilçe | ODbL ✓ | ✅ |

## 5. Enerji

| Kaynak | Ne verir | Lisans | Durum |
| --- | --- | --- | --- |
| EU JRC PVGIS 5.3 | Saatlik PV, ışınım, sıcaklık | AB ✓ | ✅ |
| UNSD Energy Statistics (UNdata) | Sektörel elektrik tüketimi | Atıfla serbest ✓ | ✅ |
| Ember (Our World in Data) | Ülke talebi, karbon yoğunluğu | CC BY 4.0 ✓ | ✅ ve ROI için 🟡 |
| Chen vd. 2022 (1 km GSYH ve elektrik) | Izgara elektrik tüketimi | Teyit | 🟡 Talep modelinin bağımsız sınaması |
| Demand.ninja | Saatlik ısıtma ve soğutma talebi | Açık kaynak (teyit) | 🔍 Saatlik talep kararı |
| Awesome Electricity Demand kataloğu | Ülkelerin açık saatlik talep verileri | Kaynağa göre | 🔍 Saatlik talep kararı |
| Global Solar Atlas | PV potansiyeli (ikinci kaynak) | CC BY 4.0 | 🔍 PVGIS ile tutarlılık kontrolü |
| OpenInfraMap / OSM `power=*` | Trafo, hat | ODbL | 🟡 |
| Global Energy Monitor | Santraller | CC BY 4.0 | 🔍 |
| IRENA maliyet raporları | PV ve depolama maliyetleri | Atıfla (teyit) | 🟡 ROI |

## 6. Çevre, iklim ve görüntü

| Kaynak | Ne verir | Lisans | Durum |
| --- | --- | --- | --- |
| Copernicus Sentinel-2 L2A | 10 m görüntü → NDVI, NDBI, albedo | Copernicus açık ✓ | 🟡 |
| Landsat 8/9 (USGS) | 30 m görüntü, yüzey sıcaklığı (kentsel ısı adası) | Kamu malı | 🟡 |
| **AlphaEarth Satellite Embedding** | 10 m, 64 boyutlu yıllık gömmeler | Earth Engine; lisans teyit | 🟡 Lisans ve erişim teyidi |
| Açık temel modeller (Clay, Prithvi, SatCLIP) | Kendi gömmelerimizi üretmek için | Apache-2.0 / MIT (teyit) | 🔍 AlphaEarth'e açık alternatif |
| ESA WorldCover / Dynamic World | Arazi örtüsü 10 m | CC BY 4.0 | 🟡 |
| Copernicus DEM GLO-30 | Yükseklik, eğim | Copernicus lisansı | 🟡 |
| ERA5 (PVGIS ve Open-Meteo üzerinden) | Saatlik sıcaklık → HDD/CDD | Copernicus lisansı | 🟡 |

## 7. Ekonomi ve sosyal

| Kaynak | Ne verir | Lisans | Durum |
| --- | --- | --- | --- |
| Kummu vd. 2018 | Izgara GSYH (SGP), İGE | CC0 (2018 sürümü) | 🟡 |
| Chen vd. 2022 | 1 km GSYH | Teyit | 🟡 |
| Meta Relative Wealth Index | Göreli refah (düşük ve orta gelirli ülkeler) | CC BY-NC (teyit) | 🔍 Ticari olmayan kullanım kısıtı |
| GDELT | Haber tonu ve yoğunluğu | Açık | 🟡 |
| World / European Values Survey | Çevre tutumları (ülke ve bölge) | Araştırma lisansı (kayıt) | 🔍 |
| Wikipedia / Wikivoyage | Yer metinleri → konu ve duygu | CC BY-SA | 🔍 |
| Google yorumları | — | Hizmet şartları kazımayı yasaklıyor; açık değil | ⛔ (K-031) |

## 8. PED etiketleri (öğrenen model için)

| Kaynak | Ne verir | Durum |
| --- | --- | --- |
| PED Veritabanı (COST PED-EU-NET, JPI UE, IEA Annex 83) | Proje konumu, ölçek, teknolojiler | 🔍 S4: dışa aktarım ve lisans teyidi |
| JPI UE PED kitapçığı (2020) | 60–61 proje | ✅ Önceki çalışmada kullanıldı |
| Zhang vd. 2021; Gollner/Bossi vd. 2020 | Proje özellik tabloları | 🔍 |

## 9. Önceliklendirme (sistem mühendisliği bakışıyla)

**Ölçüt:** (a) tezin kritik yolundaki bir boşluğu kapatıyor mu? (b) Küresel ve açık mı? (c) Maliyeti ne?

1. **Saatlik talep:** Demand.ninja ve ulusal açık veri. Kritik yol.
2. **Overture Buildings, GHS-BUILT-H ve GHS-BUILT-C:** OSM'nin %83'lük kat boşluğunu ve konut/konut dışı ayrımını kapatır, doğrudan talep ve kat alanını etkiler.
3. **Tamponlu POI ve GTFS:** Erişim katmanındaki sınır etkisini giderir.
4. **srai (Hex2Vec) ve Sentinel-2 gömmeleri:** "OSM'de olmayan bilgi". PED benzerlik modeli için güçlü, ama yorumlanması zor. PCA ve sondalama (probing) ile açıklanacak.
5. **Ekonomi:** Kummu (CC0) ve Chen (teyit).
6. **Sosyal:** GDELT (deneysel).
7. **Mapillary:** Erişim anahtarı ve bilgisayarlı görü modeli gerektiriyor; en yüksek maliyet, S8 sonrası.
