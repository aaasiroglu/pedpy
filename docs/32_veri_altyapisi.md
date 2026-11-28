# 32 — Tezin veri altyapısı: kompakt ve denetlenebilir (K-071)

## 1. İlke

Her veri üç katmandan birindedir ve her katmanın tek bir kuralı vardır:

| Katman | Yer | Kural |
|---|---|---|
| Ham ve önbellek | `data/raw/`, `data/cache/` | İndirildiği gibi durur, elle değiştirilmez, git'e girmez |
| Ürünler | `data/inventory/`, `data/lake/<alan>/` | Yazılı bir şeması vardır (`pedx.store.schema`) |
| Manifest | `data/manifest.json` | Her ürün satır sayısı, SHA-256, girdiler, lisanslar, parametreler ve kod sürümüyle kaydedilir |

Denetim tek komuttur: `make check-data`. Bir ürün eksikse, elle değiştirilmişse ya da sözleşmesini
(sütun, tür, aralık, izinli değerler, tekillik, kapsama oranı) sağlamıyorsa hata verir.

## 2. Ürünler

| Ürün | Dosya | Satır | İçerik |
|---|---|---|---|
| Küresel PED envanteri | `data/inventory/ped_sites.csv` | 155 | Tekil saha; kaynak kayıtları, konum kaynağı, sınıf, aşama, yapı türü, alan, sınır türü, finansman |
| Bina katmanı | `data/lake/<alan>/buildings.parquet` | Caferağa 2.070, Kalasatama 207 | Taban alanı, yükseklik ve kaynağı, kat, kat alanı, kullanım sınıfı ve kaynağı, veri kaynağı, yapı adası, H3 r9/r10/r11 |
| Yapı adası katmanı | `data/lake/<alan>/blocks.parquet` | Caferağa 155, Kalasatama 132 | Sokaklar ve alan sınırıyla çevrili poligonlar; bina sayısı ve taban alanı |
| Çalışma alanları | `data/areas.json` | 2 | Alan kimliği → OSM sınırı |

Göl (`data/lake/`) git'e girmez; `make lake AREA=<alan>` ile yeniden üretilir. Manifest ve envanter git'tedir.

## 3. Küresel PED envanteri

Dört kaynak tek tabloda birleşti:

| Kaynak | Kayıt | Kimlik |
|---|---|---|
| PED veritabanı (2026) | 114 | `PEDDB-<id>` (ana kayıt) |
| PED Booklet (2020) | 61 proje; 39'u veritabanındaki bir sahayla birleşti | birleşmeyenler `BKL-<no>` |
| Doğrulama seti (16 saha, docs/17) | 16; 8'i veritabanında, 1'i booklet'te | eşleşmeyenler `SCC-<n>` |
| Avrupa dışı / PED demeyen adaylar | 12 | `C-<n>` |

- **Sonuç:** 155 tekil saha, 30 ülke. Sınıflar: 57 PED (A), 68 PED ile ilgili ya da PED'e doğru (B), 18 PED laboratuvarı, 12 aday (C).
- **Konum:** 133 sahada var. 65'i kaynakta enlem/boylamı ters girilmiş, düzeltildi (`coord_src = database_corrected`).
- **Alan:** 80 sahada var. **Sınır türü:** 79 sahada var.
- **Eşleştirme kuralı:** aynı ülke ve ortak ayırt edici ad (kent adı ve genel sözcükler hariç) ya da 1,5 km'den yakın.
- **Elle kararlar** `ped_merge_overrides.csv` dosyasında, her biri gerekçesiyle (11 karar: 2 yanlış otomatik eşleşme düzeltildi, 9 kaçan eşleşme eklendi).
- **Her birleştirme** `ped_merge_log.csv` dosyasında izlenebilir.

## 4. Bina katmanı

| Alan | Kaynak sırası | Kaynak sütunu |
|---|---|---|
| Taban alanı | Overture binaları (OSM + makine öğrenmesi izleri), UTM'de alan | `data_src` |
| Yükseklik | Overture yüksekliği (≥ 2 m) → Overture kat sayısı × 3 m → GHSL BUILT-H (100 m piksel ortalaması, ≥ 2,5 m) → eksik | `height_src` |
| Kat ve kat alanı | Kat sayısı; yoksa yükseklik ÷ 3 m; kat alanı = taban × kat | — |
| Kullanım sınıfı (13) | Overture sınıfı → Overture alt türü → binanın altındaki Overture arazi kullanımı poligonu → `unknown` | `use_src` |
| Birim | Temsil noktasının düştüğü yapı adası; H3 r9, r10, r11 | — |

Kullanım sınıfları tüketim modelinin girdisidir: konut, eğitim, spor, kamu, sağlık, dini, ticaret, ofis,
sanayi/depo, tarım, ulaşım, diğer, bilinmiyor.

### İlk iki alanda veri kalitesi

| | Caferağa | Kalasatama |
|---|---|---|
| Bina / yapı adası | 2.070 / 155 | 207 / 132 |
| Yükseklik: Overture ölçümü | %0,2 | %35 |
| Yükseklik: Overture kat sayısı | %16 | %27 |
| Yükseklik: GHSL piksel ortalaması | %81 | %23 |
| Yükseklik yok | %2 | %16 |
| Kullanım: Overture sınıf/alt türü | %29 | — |
| Kullanım: arazi kullanımından | %69 | — |
| Binası yapı adasına düşen | %100 | %99,5 |

**En önemli veri açığı yükseklik.** Caferağa'da binaların %81'inin yüksekliği bina değil 100 m piksel
ortalamasından geliyor. Kat alanı, dolayısıyla tüketim, buna bağlı. Çözüm adayı TUM GlobalBuildingAtlas
(bina başına yükseklik, %97 kapsama): lisansı (CC BY 4.0 mı, CC BY-NC 4.0 mı) teyit edilince
`height_src = gba` olarak zincire GHSL'nin önüne eklenecek. Sözleşme yükseklik kapsamını %80'in altına düşürmez.

## 5. Kural: neyi yapmıyoruz

- Ham veriyi değiştirmiyoruz; düzeltme ürün katmanında ve kaynak sütunuyla yapılıyor (ör. ters koordinatlar).
- Kaynağı belirsiz değer üretmiyoruz: her türetilmiş değerin yanında nereden geldiği yazıyor.
- Sentetik veri yok. Kişisel veri yok (PED veritabanındaki iletişim bilgileri alınmadı).
- Yerel veri (İBB, TEDAŞ, EPİAŞ) yalnız doğrulama ürünlerine girer; bina katmanına girmez.

## 6. Sıradaki ürünler

| Ürün | Şema | İçerik |
|---|---|---|
| `energy.parquet` (alan başına) | `energy` | Bina başına FV üretimi (çatı × kullanılabilirlik × verim × PVGIS) ve tüketim (kat alanı × kullanım yoğunluğu, ülke toplamına kapanan), alt/orta/üst değerlerle; fazla |
| `regions.parquet` (alan başına) | `regions` | Çapa binalar ve bulanık PED bölgeleri (docs/29 §4) |
| `ped_boundaries.parquet` | `ped_boundaries` | Proje belgelerinden sayısallaştırılmış referans sınırlar |

## 7. Komutlar

```bash
make inventory
```

```bash
make lake AREA=caferaga
```

```bash
make check-data
```

Yeni bir çalışma alanı eklemek için `data/areas.json` dosyasına OSM ilişki kimliğiyle bir satır eklenir.
