# 17 · Gerçek PED'lerle dış doğrulama (vaka–kontrol)

*Karar: K-041 · Kod: `scripts/validate_ped_sites.py` · Veri: `data/validation/` · Tarih: 2026-11-08*

## 1. Soru

Model, gerçek Pozitif Enerji Bölgelerini (PED) ve Akıllı Şehir öncü (lighthouse) sahalarını, **aynı kentteki sıradan konumlardan daha yüksek** puanlıyor mu?

Bu, modelin tek dış referansıdır. Model, kendi tanımladığı bir idealle değil, gerçekte seçilmiş ve yatırım yapılmış sahalarla sınanır.

## 2. Tasarım (sonuçlar görülmeden sabitlendi)

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

## 3. Sonuçlar

*(Betik çalıştırıldıktan sonra `data/validation/ped_validation.csv` ve `ped_validation_summary.json` dosyalarından doldurulur; bkz. §5.)*

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
