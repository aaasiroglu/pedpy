# 09: pedx v0: Danışman Sunumu (Prof. Dr. Hande Demirel)

*Hazırlayan: Abdurrahim Arif Aşıroğlu · Tarih: Kasım 2026 · Sürüm: v0.1.0.dev0 · Repo: `aaasiroglu/pedpy`, dal `claude/dreamy-allen-fvtsux`*

> **Sunum biçimi (K-024):** Bu belge içeriğin metin kaynağıdır. Sunum, OSM haritası ve bilimsel arayüz içeren web tabanlı bir demo (MVP) üzerinden yapılacak; demo daha sonra hazırlanacak.

> **Tek cümle:** pedx, dünyanın herhangi bir şehrinde **yalnızca ücretsiz ve açık veriyle** (OSM, PVGIS) Pozitif Enerji Bölgesi potansiyelini **saatlik fizikle** hesaplıyor, H3 altıgenlerinde **mutlak bir indeksle** puanlıyor, sonucu **açıklıyor** ve **fiziksel müdahale uzayında en ucuz dönüşüm yollarını** öneriyor.

## 1. Neden bu tez? (Hocamızın çalışma hattının devamı)

- **Demirel vd. (2025, Open Research Europe):** Caferağa'da 3B CBS ile güneş potansiyeli analizi yapıldı. Platformlar arası %22,29 fark bulundu. → *Açık veri ile yüksek çözünürlüklü yerel veri arasındaki farkı ölçmek gerekiyor.*
- **Alpagut vd. (2021, Energies):** PEB sınırı için CBS ve ÇKKDS yöntemi önerildi. → *Bu yöntem statik ve yıllık katmanlarla çalışıyor; saatlik eşleşme, açıklama ve reçete yok.*
- **Koçyiğit, Aksu, Terzi, Karadağ, Demirel (2025, WSEAS)** ve AESOP 2025 posteri: PEB'lerde CBS'nin rolü.
- **Literatürdeki boşluk:** PEB tanımı, sınırı ve KPI'ları hâlâ belirsiz (Brozovsky vd., 2021; 35 farklı terim). Mevcut PEB uygunluk çalışmaları açıklama ve reçete üretmiyor.

## 2. v0'da ne yapıldı?

| Katman | Durum | Not |
| --- | --- | --- |
| Açık veri: OSM binaları (Overpass) | ✅ | Caferağa'dan 2876 bina |
| Açık veri: PVGIS saatlik ışınım (SARAH-3, 2019) | ✅ | 1562 kWh/m²/yıl (yatay düzlem) |
| Saatlik enerji dengesi: SSR, denge, CVaR ile şebeke stresi | ✅ | Paylaşımlı ve bağımsız modlar |
| H3 altıgen toplulaştırma (çözünürlük 8, 9, 10) | ✅ | Enerji korunumu test edildi |
| Mutlak PEB hazırlık indeksi ve sıra belirsizliği | ✅ | Sıra tersinmesi yok (test edildi) |
| ÇKKDS görünümü (CRITIC, Entropi, BWM, MARCOS, TOPSIS) | ✅ | MARCOS ≡ κ·WSM kanıtlandı |
| Graf: PEB sınır büyütme ve Shapley katkısı | ✅ | Kesin Shapley, 14 hücreye kadar |
| Tersine analiz: fiziksel müdahale, bütçe–skor eğrisi | ✅ | Kesin modelle bağımsız denetim |
| Ağırlık (politika) kararlılığı | ✅ | LP + QP |
| İBB verisi (G2) | ⏳ | Sprint 2–4 |
| Gerçek tüketim profilleri | ⏳ | **En kritik eksik** |

44 otomatik test çalışıyor. Ayrıntılar: `README.md`, `docs/08`.

## 3. İlk sonuçlar (Caferağa, H3 çözünürlük 10, 92 hücre)

*Talep profilleri SENTETİK; varsayımlar `results/v0/assumptions.csv` dosyasında.*

| Gösterge | Değer |
| --- | --- |
| Hücre sayısı | 92 |
| Teknik potansiyelde yıllık denge ≥ 1 olan hücre | 2 |
| Yıllık denge (G/D) ortalaması | 0,80 (aralık 0,33–1,06) |
| SSR ortalaması | 0,35 |
| Tepe rahatlaması | Tüm hücrelerde 0 (aşağıda açıklandı) |
| En düşük skorlu 3 hücre, 200k € ile ulaşılan skor | 0,06–0,24 (PV baskın) |

## 4. Dürüst bulgular: hocamızın yönlendirmesini istediğimiz noktalar

1. **OSM öznitelik eksikliği çok büyük.** Binaların %85'inde kat sayısı ve yükseklik yok; yapım yılı ise yalnızca %0,03'ünde var. Açık veriyle ısıl iyileştirme ihtiyacı (C5) hesaplanamıyor. **Bu, G1 (açık veri) ile G2 (İBB) karşılaştırmasını tezin merkezine koyuyor.**
2. **Tepe rahatlaması sıfır.** Zirve saatler kış akşamlarında; PV tek başına bunları karşılayamıyor. Gösterge ya depolamayla birlikte, ya da mevsimsel olarak yeniden tanımlanmalı.
3. **Saatlik tamamlayıcılık yok denecek kadar az.** Sentetik profillerin şekilleri tek tip olduğu için hücreler arası tamamlayıcılık ortaya çıkmıyor. Bu, kırılganlık analizinde öngördüğümüz döngüsellik riskini (docs/07, C1) doğruluyor. **Gerçek tüketim profili şart.**
4. **Varsayımların çoğu yer tutucu.** Tüketim yoğunluğu, çatı kullanım oranı ve maliyetler `varsayim` durumunda; gerçek veriyle değiştirilecek.

## 5. Hocamızdan istediğimiz kararlar ve kaynaklar

1. **Tüketim verisi:** Önceki projelerinizden (ör. Caferağa veya PEB projeleri) toplulaştırılmış, anonim saatlik ya da aylık profil kullanılabilir mi?
2. **İBB katmanları:** Hangi mahalle ölçekli verileri talep edelim? Öneri listesi `docs/06` dosyasında.
3. **Yayın stratejisi:** Aşağıdaki üç çıktının hedef dergileri ve konferansı.
4. **PEB kapsamı:** "Elektrik odaklı PEB potansiyeli" sınırlaması kabul edilebilir mi?
5. **Enerji paylaşımı mevzuatı:** Hücreler ve kümeler arası paylaşım hangi senaryo altında anlamlı?

## 6. Takvim (2 haftalık sprintler, Haziran 2027 başı teslim)

Ayrıntılı plan `docs/10_sprint_plani.md` dosyasında. Özet:

| Dönem | Çıktı |
| --- | --- |
| S1–S3 (Kasım–Aralık) | İBB verisi, gerçek profiller, PED veritabanından çıkarımlar; **bildiri özeti** |
| S4–S7 (Aralık–Şubat) | G1/G2 karşılaştırması, ağırlık ve MAUP duyarlılığı; **Makale A taslağı** (açık veri sadakati) |
| S8–S11 (Şubat–Nisan) | Küme düzeyinde tersine analiz, graf-XAI ve benchmark; **Makale B taslağı** (yöntem) |
| S12–S15 (Nisan–Haziran) | Tez yazımı, gönderimler, savunma hazırlığı |
