# 11: Veri Kaynağı Kütüğü ve Araştırma Günlüğü

*Başlangıç: 2026-11-08 · Kural seti K-025 (bkz. 05): Her girdi **küresel ölçekte mevcut ve açık lisanslı** olmalı. Yerel veriler (İBB, TEDAŞ, EPİAŞ, TÜİK) **yalnızca doğrulamada (G2)** kullanılır. Hiçbir çıktıya sentetik veya yer tutucu değer girmez; eksik veri açıkça "eksik" olarak gösterilir.*

## 1. Kullanılan katmanlar (demo v0.1)

| # | Katman | Kaynak | Sürüm, yıl | Çözünürlük | Lisans | Rol | Gerekçe |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Mahalle sınırı | OpenStreetMap, relation 9441032 "Caferağa Mahallesi" (admin_level 8, Wikidata Q6040926) | Overpass, 2026-11-08 | poligon | ODbL 1.0 | G1 | Her ülkede idari sınır OSM'de mevcut; resmî sınırla karşılaştırma G2'de yapılacak |
| 2 | Bina taban alanları | OSM `way["building"]`, Overpass | 2026-11-08 | poligon | ODbL 1.0 | G1 | Küresel, açık; tamlık raporlanıyor (kat bilgisi yalnızca %17'sinde var) |
| 3 | Nüfus | **JRC GHS-POP R2023A**, E2020, 3″ (~90 m), WGS84 karosu R5_C21 | R2023A | ~90 m | **CC BY 4.0** (resmî `copyright.txt` dosyasından doğrulandı) | G1 | Dünyanın tamamını kapsayan, nüfus sayımına kalibre edilmiş ızgara (Schiavina vd., 2023) |
| 4 | Konut elektriği (ulusal) | **UNSD Energy Statistics Database** (UNdata, EDATA): "Electricity – Consumption by households", Türkiye, 2023 = **65.541 milyon kWh** | 2023 | ülke | UNdata kullanım koşulları: atıfla serbest kullanım | G1 | BM'nin tüm ülkeler için tuttuğu tek tutarlı açık sektör serisi |
| 5 | Ülke nüfusu | UN WPP, Our World in Data `energy-data` üzerinden: Türkiye 2023 = 87.270.502 | 2023 | ülke | CC BY 4.0 | G1 | 4 numaralı katmanı kişi başına çevirmek için |
| 6 | Kişi başı toplam talep | Ember, OWID üzerinden: Türkiye 2022 = 3.713 kWh/kişi | 2022 | ülke | CC BY 4.0 | G1 (yalnızca doğrulama karşılaştırması) | — |
| 7 | PV üretimi | **EU JRC PVGIS 5.3** `seriescalc`, 1 kWp, crystSi, kayıp %14 (PVGIS varsayılanı), `mountingplace=building`, optimum açı (34°, azimut 9°) | 2023, SARAH-3 + ERA5 | saatlik, nokta | AB yeniden kullanım politikası | G1 | Avrupa, Afrika, Asya ve Amerika'yı kapsar. Yıllık verim **1.267,7 kWh/kWp** |
| 8 | Çatı kullanım katsayısı | Gagnon vd. (2016), NREL/TP-6A20-65298: küçük binalarda çatı alanının %26'sı uygun | — | — | kamu raporu | G1 parametre | Küresel bir değer yok. Lidar tabanlı en kapsamlı çalışma alt sınır olarak alındı; üst sınır 0,50. Demirel vd. (2025) ile G2'de kalibre edilecek |
| 9 | Modül verimi | Fraunhofer ISE, *Photovoltaics Report*: ticari Si modül verimi son on yılda ~%17'den %25'in biraz altına çıktı | — | — | kamu raporu | G1 parametre | Ana değer 0,20; aralık 0,17–0,25 |

**Türetilen değer:** kişi başı konut elektriği = 65.541 × 10⁶ kWh ÷ 87.270.502 = **751,0 kWh/kişi·yıl** (Türkiye, 2023).

## 2. Doğrulama (G2) katmanları: girdi olarak kullanılmıyor

| Katman | Kaynak | Ne için |
| --- | --- | --- |
| İstanbul kişi başı net tüketim, 2022 = 2.678 kWh | TEDAŞ 2023 Sektör Raporu, Tablo 7 (www.tedas.gov.tr) | Ulusal ortalama (Ember) ile İstanbul farkı: G1 değeri %38,7 daha yüksek; sanayi yükü etkisi |
| Caferağa nüfusu 2020 = 21.421 | Kadıköy Belediyesi "Anlat Kadıköy" (TÜİK ADNKS 2020 kaynaklı; İngilizce Vikipedi'den aktarım) | GHS-POP toplamı 22.005 → **fark +%2,7** |
| Saatlik konut profili | EPİAŞ 2023 profil katsayıları: mesken ve ticarethane; AYEDAŞ kalemi (`2023_Profil_Katsayilari__v2.rar`) | Küresel talep şeklinin doğrulanması (sıradaki adım) |
| Bina envanteri, LiDAR | İBB | Kat, yaş ve yükseklik doğrulaması |
| 3B çatı ışınımı | Demirel vd. (2025), Open Research Europe 5:81 | Çatı kullanım katsayısı ve PV potansiyelinin doğrulanması |

## 3. Bilinen eksikler (bu sürümde gösterilmiyor)

1. **Saatlik konut talep şekli:** Küresel ve açık lisanslı bir kaynak henüz seçilmedi. Adaylar:
   - (a) Open Energy Transition'ın *Awesome Electricity Demand* kataloğundaki ulusal açık saatlik talep verileri. Türkiye için EPİAŞ kayıtlı; kullanım atıfla serbest ama kayıt gerekiyor.
   - (b) Demand.ninja (Staffell, Pfenninger, Johnson 2023, Nature Energy): ısıtma ve soğutma için küresel saatlik model; açık kaynak.
   - (c) GlobalEnergyGIS / PLEXOS-World 2015 profilleri (lisansı netleşmedi).

   Seçilene kadar SSR, tepe rahatlaması, Shapley ve batarya demoda gösterilmiyor.
2. **Hizmet sektörü talebi:** UNSD'de "commercial and public services" Türkiye 2023 = 78.524 milyon kWh. Bunu mekâna dağıtma yöntemi (POI, konut dışı taban alanı) henüz kurulmadı.
3. **Gölgeleme ve çatı geometrisi:** Çatı kullanım katsayısı aralığıyla temsil ediliyor.
4. **Ölçek uyumsuzluğu:** GHS-POP pikselleri (~90 m) ile H3 r10 hücreleri (~1,5 ha) arasında. Kıyı hücrelerinde nüfus bina olmayan alana düşüyor. Çözüm adayı: OSM konut taban alanıyla dasimetrik yeniden dağıtım, ya da r9 çözünürlüğü.

## 4. Araştırma günlüğü (2026-11-08)

| Adım | Sorgu ya da işlem | Bulgu | Karar |
| --- | --- | --- | --- |
| 1 | EPİAŞ profil katsayıları | Yıllık mesken ve ticarethane profilleri yayımlanıyor, AYEDAŞ'a özel kalem var | Önce girdi düşünüldü; K-025 sonrasında **G2** |
| 2 | TEDAŞ 2023 sektör raporu (PDF indirildi) | Tablo 7: illere göre kişi başı net tüketim; İstanbul 2.678 kWh | G2 |
| 3 | Caferağa nüfusu | TÜİK 2023 mahalle değeri arama sonuçlarında yok; 2020 için 21.421 bulundu | G2; İBB'den resmî tablo istenecek |
| 4 | Kullanıcı kuralı: "global olarak açık olmayan veri girdi olmayacak" | — | K-025 |
| 5 | GHS-POP R2023A | 3″ WGS84 karoları açık; lisans `copyright.txt` dosyasında CC BY 4.0 | G1 |
| 6 | UNdata EDATA | trID 1231 = hane, 1235 = ticari ve kamu hizmetleri; Türkiye 2023 değerleri alındı | G1 |
| 7 | Saatlik talep için küresel kaynak | Awesome Electricity Demand kataloğu, Demand.ninja, GlobalEnergyGIS bulundu; tek ve açık bir küresel konut profili yok | **Eksik olarak işaretlendi**, karar kullanıcıda |
| 8 | Modül verimi | ITRPV ortalaması bulunamadı; Fraunhofer ISE aralığı bulundu | Aralıkla kullanıldı |
| 9 | Çatı kullanım katsayısı | Gagnon 2016 (%26, küçük binalar); Bódis 2019 (AB, katsayı tam metinde) | 0,26–0,50 aralığı |
| 10 | Demirel vd. (2025) tam metni | PMC sayfası reCAPTCHA döndürdü; ORE, ore.eu'ya yönleniyor ve bu sunucu izinli değil | PDF'nin kullanıcıdan alınması önerilecek |
| 11 | OSM sınırı | "Caferağa" adıyla eşleşme yok; doğru ad "Caferağa Mahallesi" (relation 9441032) | G1 |
| 12 | Bina sorgusu | Overpass bağlantısı aralıklı kopuyor; yeniden denemeyle 3.645 bina geldi, 2.061'i sınır içinde | G1 |

## 5. Yeniden üretim

```bash
python scripts/build_features.py
```

```bash
python -m http.server 8765 -d web
```

Ham indirmeler `data/raw/` altında; git'e eklenmiyor. Demo verisi `web/data/` altında.
