# 23 · Benzer araçlar: neyi doğru söylüyoruz, bize ne katarlar? (K-060)

Kullanıcının paylaştığı karşılaştırma metni üç kategoriyi tartışıyordu: kentsel bina enerji modelleme (UBEM), çatı ve güneş simülasyonu, MCDM kütüphaneleri. Her iddia paketlerin kendisine bakılarak sınandı; PyPI'den indirilen dağıtımların meta verisi ve modül listesi incelendi. Ardından en somut katkı, MCDM kıyaslaması, gerçekten çalıştırıldı.

## 1. İddiaların sınanması

| Metindeki iddia | Bulgu | Kaynak |
|---|---|---|
| CEA'nın MCDM ya da optimizasyon modülü yok | **Yanlış.** CEA'da `cea/optimization` (dağıtık enerji arz sistemi, `deap` ile evrimsel çok amaçlı optimizasyon: maliyet, CO₂, birincil enerji) ve `cea/analysis/multicriteria` var. Doğru ayrım: CEA **verilen bir bölgenin** enerji arz sistemini optimize ediyor. Bir kent içinde saha **seçmiyor** ve gerçek PED'lerden öğrenmiyor. | cityenergyanalyst 3.11.0 (PyPI, MIT); güncel CEA 4 GitHub/conda üzerinden dağıtılıyor, incelenmedi |
| CEA dünyanın her yerinde çalışır | Kısmen. Hazır arketip veritabanları CH ve SG için; başka bir ülke için arketip girilmesi gerekiyor. OSM'den bina ve sokak çekiyor (`zone_helper`, `streets_helper`, `osmnx`). | aynı |
| Ladybug Tools tamamen grafik arayüz (Grasshopper) tabanlı | **Yanlış.** `ladybug-core`, `honeybee-core`, `honeybee-radiance`, `dragonfly-core` Rhino'suz çalışan Python SDK'ları ve komut satırı araçlarıdır. Asıl kısıt **lisans**: hepsi **AGPL-3.0**. | PyPI meta verisi |
| MCDM kütüphaneleri yalnız tablosal | Doğru. CBS'den, geometriden, enerji fiziğinden habersizler. | pymcdm 1.4.0 (MIT), pyDecision 5.1.8 (GPL-3.0), scikit-criteria 0.10 (BSD-3) |
| pedpy PU-Learning ve Mekânsal-MARCOS tabanlı sınır genişletme yapıyor | **Kısmen.** `pedx.mcdm` MARCOS, TOPSIS, CRITIC, entropi ve BWM içeriyor; `pedx.graph.grow_ped_boundary` sınır büyütme yapıyor. **PU-learning yok.** Gerçek PED'ler ve kontroller vaka–kontrol tasarımıyla kullanılıyor. | kod tabanı |
| pedpy Nash/CRITIC ağırlık füzyonu kuruyor | **Hayır.** Füzyon doğrusal: `w = λ·BWM + (1−λ)(α·CRITIC + (1−α)·entropi)`. Nash yok. | `pedx/mcdm/weighting.py` |
| pedpy bütçe kısıtlı tersine reçete üretiyor | **Hayır, henüz değil.** Tersine analiz kapalı biçimli: hedef skor için çatı kullanımı, modül verimi ve talep azaltımı hesaplanıyor. Maliyet verisi olmadığı için bütçe kısıtı yok (Mimari A9: "maliyet verisi bekleniyor"). | `PEDScore.inverse` |

**Sonuç:** Metindeki konumlandırma özünde doğru, ama iki yönde abartılı. Rakiplerin eksikleri olduğundan büyük gösteriliyor, pedx'in yetenekleri de olduğundan fazla sayılıyor. Tezde yalnız sınanmış ayrımlar kullanılmalı.

**Savunulabilir konumlandırma:** pedx, saha seçimini **gerçek PED'lerden öğrenen**, bunu **kentler arası dışarıda bırakarak** doğrulayan, **uygulanabilirlik alanını** bilen ve **dünyanın her yerinde yalnız açık veriyle** çalışan bir karar destek sistemi. Ayrıntılı fizik (CEA, URBANopt, Ladybug) pedx'in rakibi değil; pedx'in seçtiği sahada sonraki adım.

## 2. MCDM kıyaslaması: çalıştırıldı (`scripts/mcdm_benchmark.py`)

**Soru (yöneylem araştırması):** Klasik MCDM yöntemleri, gerçek PED sahasını kendi kentinin yerleşik kontrolleri arasında PED skoru kadar iyi sıralayabiliyor mu?

**Protokol:**
- `build_atlas.py` ile aynı veri: 16 gerçek PED, 31 temiz kriter, kent içi z-puanları, kentler arası dışarıda bırakma (LOCO).
- Kriterlerin yönü (fayda ya da maliyet) yalnız eğitim kentlerinden geliyor.
- Nesnel ağırlıklar (eşit, CRITIC, entropi) dışarıda bırakılan kentin kendi karar matrisinde, etiket görmeden hesaplanıyor.
- Ölçüt: vakanın kontroller arasındaki yüzdeliği; ortalaması AUC.

| Yöntem × ağırlık (seçme) | AUC | İlk %10'da |
|---|---|---|
| MARCOS · eşit / CRITIC | **0,88** | 10/16 |
| WSM · eşit | 0,88 | 11/16 |
| TOPSIS · eşit | 0,85 | 9/16 |
| WSM · kanıt ağırlıkları | 0,83 | 7/16 |
| **PED skoru** (kanıt ağırlıkları, lojistik) | **0,80** | 7/16 |
| PROMETHEE II · eşit | 0,81 | 7/16 |
| VIKOR · eşit | 0,32 | 3/16 |

Tablo `data/validation/mcdm_benchmark.json`'daki 25 sonuçtan seçmedir.

**Okuma:**
1. **Eşit ağırlıklı toplam, öğrenilmiş seyrek ağırlıklardan kötü değil; ortalamada daha iyi.** Ama fark anlamlı değil:
   - WSM-eşit, PED skoruna göre 10 kentte daha iyi, 5 kentte daha kötü; eşleştirilmiş Wilcoxon p = 0,31, n = 16.
   - Farkın büyük kısmı tek bir kentten geliyor: Coronación'da PED skoru 0,03, eşit ağırlık 0,93.

   Bu, "uygunsuz doğrusal modeller" bulgusunun kentsel PED'deki karşılığı (Dawes 1979; Einhorn ve Hogarth 1975): az örnekle ağırlık öğrenmek, yönleri doğru eşit ağırlıklardan daha iyi olmayabilir.
2. **25 kombinasyonun en iyisini seçmek iyimser bir tahmindir** (seçim yanlılığı). 0,88 bir üst sınır olarak okunmalı. Adil bir karşılaştırma için kombinasyon da LOCO içinde seçilmeli; bu yapılmadı.
3. **VIKOR eşit ağırlıkla çöküyor (0,32).** VIKOR'un "en kötü kriterdeki pişmanlık" terimi tek bir zayıf kriteri cezalandırıyor. Gerçek PED'ler telafi edici profiller: bir kriterde zayıf, diğerlerinde güçlü. Telafi etmeyen yöntemler bu karar problemine uygun değil. Bu, yöntem seçimi için kendi başına bir bulgu.
4. **PED skorunun üstünlüğü sıralamada değil, başka yerde:**
   - kalibre edilmiş olasılık (0–100);
   - kesin katkılar;
   - kapalı biçimli tersine analiz;
   - kümeye göreli olmayan mutlak puan: yeni bir aday eklendiğinde mevcut sıralama değişmez. TOPSIS ve MARCOS ise kümeye göreli yöntemler; sıra tersine dönmesine açıklar.

**Uygulama doğrulaması:** pedx.mcdm, pymcdm ile her kent matrisinde karşılaştırıldı.

| Yöntem | Sonuç |
|---|---|
| TOPSIS | Birebir aynı (en büyük fark 0; Kendall τ = 1) |
| CRITIC | En çok 0,027 farklı. pymcdm kriter yönünü dikkate almıyor; pedx yöne duyarlı (K-008). |
| Entropi | En çok 0,26 farklı. Tanımlar farklı: pymcdm ham matrisi toplama göre normalize ediyor; pedx önce yöne duyarlı min-max uyguluyor (Zhu vd. 2020). |

**Karar önerisi (kullanıcıya bırakıldı):** Çekirdek PED skoru şimdilik değişmiyor.
- Tezde "eşit ağırlık + öğrenilmiş yön" modeli **güçlü bir temel karşılaştırma** olarak raporlanmalı.
- Sonraki adım, ağırlık şemasını LOCO içinde seçen iç içe doğrulama (nested LOCO). Ancak o seçimle kazanan model çekirdek olabilir.
- Pratikte bir ara yol var: eşit ağırlıklı toplamın da kalibrasyonu, katkıları ve tersine analizi aynı `PEDScore.from_weights` ile yapılabiliyor. Yani eşit ağırlığa geçmek, sistemin hiçbir özelliğini kaybettirmiyor.

## 3. Bize ne katarlar? Öncelik sırasıyla

| # | Araç | Katkı | Kapsam kuralı (docs/22) | Çaba | Durum |
|---|---|---|---|---|---|
| 1 | **pymcdm** (MIT) | Klasik MCDM ile karşılaştırma ve kendi kodumuzun bağımsız doğrulaması. Sıra tersine dönmesi testi (`leave_one_out_rr`) ve ağırlık duyarlılığı (`param_sensitivity`). | ✔ aynı veri, aynı etiket | düşük | **Kıyaslama yapıldı (bu belge)**; sıra tersine dönmesi testi sırada |
| 2 | **CEA** (MIT) | (a) **Doğrulama:** Caferağa'da CEA'nın bina yüzeyi radyasyonu ve talebi ile bizim çatı PV ve kişi başı talebimizin karşılaştırılması (V-test). (b) **Arketip fikri:** kişi başı ülke ortalaması yerine bina kullanımı (Overture sınıfı) × yaş (GHSL dönemi) arketipiyle talep. (c) Saha seçildikten sonra arz sistemi optimizasyonu (Faz 2). | (a) ✔ doğrulama · (b) ✔ açık girdi · (c) kapsam dışı (Faz 2) | orta–yüksek (conda, Daysim) | planlı |
| 3 | **URBANopt + REopt** (NREL) | Seçilen sahayı URBANopt GeoJSON'u olarak dışa aktarmak (birlikte çalışabilirlik, ucuz). PV + batarya boyutlandırması ve maliyet için REopt: A9'daki bütçe boşluğunu dolduran tek açık araç. | dışa aktarım ✔; REopt maliyet girdisi gerektiriyor | düşük (dışa aktarım) / orta (REopt) | lisans ve erişim teyit edilecek |
| 4 | **Ladybug / Honeybee-Radiance** (AGPL-3.0) | Overture bina yükseklikleriyle gölgeli çatı ışınımı; PVGIS'in gölge görmeyen yıllık değerini bir örneklemde sınamak. **AGPL yüzünden pedx koduna gömülmez**; ayrı bir doğrulama ortamında, harici araç olarak çalıştırılır (SUHII için alınan karar). | ✔ yalnız doğrulama | orta | planlı |
| 5 | pyDecision (GPL-3.0), scikit-criteria (BSD-3) | pymcdm'in kapsamadığı bir şey yok. GPL bağımlılığından kaçınılıyor. | — | — | alınmıyor |

**Tezdeki yeri:**
- Madde 1, yöneylem araştırması ekseninin somut bir bulgusu: öğrenilmiş ağırlık ile klasik MCDM ağırlıklandırması, gerçek etiketle, LOCO protokolünde karşılaştırıldı.
- Madde 2(a) ve 4, enerji fiziğinin dış doğrulaması.
- Madde 3, karar destekten uygulamaya köprü.

Hiçbiri çekirdeği değiştirmiyor; hepsi aynı H3 deposu ve aynı sözleşme üzerinden bağlanıyor.

## Kaynaklar

- Dawes, R. M. (1979). The robust beauty of improper linear models in decision making. *American Psychologist*, 34(7), 571–582.
- Einhorn, H. J., & Hogarth, R. M. (1975). Unit weighting schemes for decision making. *Organizational Behavior and Human Performance*, 13(2), 171–192.
- Diakoulaki, D., Mavrotas, G., & Papayannakis, L. (1995). Determining objective weights in multiple criteria problems: The CRITIC method. *Computers & Operations Research*, 22(7), 763–770.
- Kizielewicz, B., Shekhovtsov, A., & Sałabun, W. (2023). pymcdm — The universal library for solving multi-criteria decision-making problems. *SoftwareX*, 22, 101368.
- Fonseca, J. A., Nguyen, T.-A., Schlueter, A., & Marechal, F. (2016). City Energy Analyst (CEA): Integrated framework for analysis and optimization of building energy systems in neighborhoods and city districts. *Energy and Buildings*, 113, 202–226.
- Opricovic, S., & Tzeng, G.-H. (2004). Compromise solution by MCDM methods: A comparative analysis of VIKOR and TOPSIS. *European Journal of Operational Research*, 156(2), 445–455.
- Zhu, Y., Tian, D., & Yan, F. (2020). Effectiveness of entropy weight method in decision-making. *Mathematical Problems in Engineering*, 2020, 3564835.
