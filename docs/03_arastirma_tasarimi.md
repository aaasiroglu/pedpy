# 03: Araştırma Tasarımı

*Tarih: 2026-11-08 · Durum: taslak, danışman onayı bekliyor*

## 1. Çalışma başlığı (öneri)

> **Pozitif Enerji Bölgeleri için Açıklanabilir ve Graf Tabanlı Mekânsal Karar Destek: Açık Küresel Veri ile Saatlik Enerji Dengesi, Çok Kriterli Sıralama ve Karşı-Olgusal Dönüşüm Reçeteleri. İstanbul Caferağa Doğrulaması**

İngilizce: *Explainable, Graph-Based Spatial Decision Support for Positive Energy Districts: Hourly Energy Balance, Multi-Criteria Ranking and Counterfactual Transformation Prescriptions from Open Global Data, Validated in Caferağa, Istanbul*

## 2. Ana fikir

Sistem üç soruyu tek bir **doğrulanabilir** iş akışında yanıtlıyor:

1. **Nerede?** Hangi yapı adası veya H3 hücresi PEB'e en uygun? *(saatlik enerji + ÇKKDS)*
2. **Neden?** Bu sıralama neden böyle, hangi kriterler ne kadar katkı verdi ve sıralama ne kadar güvenilir? *(XAI)*
3. **Ne yapılmalı?** Sınır nereye genişletilmeli, düşük skorlu ada için en ucuz uygulanabilir müdahale ne? *(graf + karşı-olgusal reçete)*

Bunlara bir de **dil katmanı** ekleniyor. Uzman ve paydaş görüşleri ağırlıklara dönüştürülüyor (NLP-1). Sonuçlar planlamacılar için Türkçe, sayılara sadık açıklamalara çevriliyor (NLP-2).

```
 Açık veri (OSM/Overture, PVGIS, ERA5, POI)      İBB yerel veri (LiDAR/DSM, envanter)
            │  G1                                          │  G2
            ▼                                              ▼
   Bina saatlik enerji (G_b,t , D_b,t) ──► Ada/H3 toplulaştırma (SSR, SCR, PAR; enerji korunumu)
                                                │
                     C1…C6 karar matrisi X ◄────┘
                                │
   Ağırlıklar: CRITIC + Entropi + BWM ◄── NLP-1: LLM destekli uzman görüşü (BWM tutarlılık denetimi)
                                │
             ÇKKDS: MARCOS (≡ κ·WSM), TOPSIS, PROMETHEE II (yöntem duyarlılığı)
                                │
      ┌─────────────── XAI ───────────────┬───────────── Graf ─────────────┐
      │ XAI-1 kesin Shapley katkıları      │ Graf-1 PEB sınır genişletme     │
      │ XAI-1b sıra düzeyi açıklama        │   (saatlik tamamlayıcılık;      │
      │ XAI-2 fiziksel kısıtlı reçete      │    max-p ve SKATER ile kıyas)   │
      │ XAI-3 belirsizlik ve sıra aralığı  │ Graf-2 (Bonus) GNN ile eksik    │
      └─────────────────┬──────────────────┴─ veri tamamlama ──────────────┘
                        ▼
          NLP-2: Türkçe, sayılara sadık açıklama ve reçete metinleri
                        ▼
          G3: açık veri ve İBB karşılaştırması (ρ, τ, ilk-k, RMSE, MAPE, bootstrap güven aralığı)
```

## 3. Araştırma soruları (AS) ve hipotezler (H)

| Kod | Araştırma sorusu | Hipotez ve ölçüt | Katman |
| --- | --- | --- | --- |
| **AS1** | Yalnızca açık küresel veriyle elde edilen PEB uygunluk sıralaması, İBB yerel verisiyle elde edilen sıralamayı ne ölçüde temsil ediyor? | **H1:** Spearman ρ ≥ ρ* ve %95 bootstrap güven aralığının alt sınırı > 0,7. (ρ* önceden kayda geçirilecek; öneri 0,80.) İkincil ölçütler: Kendall τ, ilk-10 örtüşmesi, yükseklik RMSE'si, yıllık üretim MAPE'si | Zorunlu |
| **AS2** | Saatlik yük eşleşmesi kriterleri (SSR, PAR) sıralamaya yıllık denge göstergelerinin ötesinde ayırt edici bilgi katıyor mu? | **H2:** C2 ve C3 çıkarıldığında (ablasyon) sıralama anlamlı biçimde değişiyor (ρ < 0,9). T2 testi aynı yıllık toplamda ayrışmayı sentetik olarak kanıtlıyor | Zorunlu |
| **AS3** | Sıralama, ağırlıklandırma ve yöntem seçimine ne kadar duyarlı ve bu belirsizlik karar vericiye nasıl açıklanabilir? | **H3:** Ağırlık ve veri belirsizliği altında üst sıradaki adaların sıra aralıkları (XAI-3) dar kalıyor. Kararlı ve kararsız adalar ayrışıyor | Zorunlu |
| **AS4** | Saatlik tamamlayıcılığı gözeten graf tabanlı sınır genişletme, yalnızca yıllık dengeye dayalı bölgeselleştirmeye göre daha iyi PEB kümeleri üretiyor mu? | **H4:** Aynı hücre sayısında küme SSR'si daha yüksek, PAR'ı daha düşük. Karşılaştırma: max-p, rastgele bitişik büyütme ve küçük örneklerde tam sayım | Güçlü |
| **AS5** | Fiziksel ve bütçe kısıtlı karşı-olgusal reçeteler uygulanabilir, kararlı ve en düşük maliyetli mi? | **H5:** Kesin çözücü, SLSQP ve gradyan temelli çözücüden eşit veya daha düşük maliyet buluyor. Reçeteler küçük veri pertürbasyonlarında kararlı | Güçlü |
| **AS6** | LLM destekli uzman görüşü çıkarımı, insan uzman BWM ağırlıklarına ne kadar yakın ve ne kadar tutarlı? | **H6:** LLM tabanlı BWM tutarlılık oranı (ξ) kabul eşiğinde. İnsan uzman ağırlıklarıyla Kendall τ > 0,5. İstem (prompt) varyansı raporlanacak | Bonus |
| **AS7** | Sayılara sadık doğal dil açıklamaları planlamacıların sonucu anlamasını iyileştiriyor mu? | **H7:** Küçük kullanıcı çalışmasında (n ≈ 8–15 planlamacı) kavrama görevinde doğruluk artıyor. Açıklamadaki sayıların %100'ü otomatik olarak doğrulanabiliyor | Bonus |

## 4. Bileşenlerin bilimsel tasarımı

### 4.1 Enerji çekirdeği (Zorunlu)

- Bina düzeyinde: G_b,t = I_t · A_çatı · f_kullanım · η · PR · s_b,t · Δt. Burada I_t PVGIS ışınımı, s_b,t ise 2,5B ufuk gölgeleme katsayısı.
- Talep: arketip (yaş bandı ve kullanım türü) × günlük ve haftalık profil × ERA5 sıcaklık duyarlılığı (HDD/CDD). Gerçek veri varsa onunla değiştirilecek.
- Ada düzeyinde iki paylaşım modu var: `block_shared` (ada içinde enerji paylaşımı) ve `independent` (her bina kendi başına).
- Göstergeler (Salom vd., 2014; Luthander vd., 2015):
  - SSR = ΣE_sc / ΣD
  - SCR = ΣE_sc / ΣG
  - PAR = max_t(I_t/Δt) / (ΣD / TΔt)
  - Tanımsız durumlar için açık NaN politikası (K-003)
- Doğrulama: T1, T2 ve T5 testleri. Enerji korunumu her saatte kontrol edilecek (G = E_sc + X, D = E_sc + I).

### 4.2 Ağırlıklandırma ve ÇKKDS (Zorunlu)

- CRITIC (Diakoulaki vd., 1995): yön düzeltilmiş min-max normalizasyon, σ (ddof=0), Pearson R. Sabit sütunlar dışlanıp ağırlıkları 0 yapılacak.
- Entropi: **yön düzeltilmiş normalize veri** üzerinde hesaplanacak (R3). Ham veri sürümü duyarlılık analizinde raporlanacak.
- BWM: doğrusal model (Rezaei, 2016) ve ξ tutarlılık göstergesi.
- Füzyon: w* = λ·w_BWM + (1−λ)·[α·w_CRITIC + (1−α)·w_Entropi]. Alt sınır ve sabit sütun koruması için kısıtlı izdüşüm (projeksiyon) kullanılacak. (α, λ) ızgarasında duyarlılık incelenecek.
- MARCOS, Stević vd. (2020) formülasyonuyla uygulanacak. **Eşdeğerlik teoremi** (f(K_i) = κ·S_i) tezde kanıtıyla verilecek.
- Yöntem duyarlılığı için TOPSIS ve PROMETHEE II (telafi etmeyen yöntem) kullanılacak.
- Mekânsal gecikme seçeneği: X̃ = (1−ρ)X + ρWX. W satır-standartlaştırılmış komşuluk matrisi. Etkisi ablasyonla ölçülecek.

### 4.3 XAI katmanı *(tezin "etkileyici" çekirdeği)*

**XAI-1: Kesin katkı ayrıştırması.** MARCOS normalize uzayda doğrusal olduğu için:

$$f(K_i) = \kappa \sum_j w_j n_{ij} \;\Rightarrow\; \phi_{ij} = \kappa\, w_j\,(n_{ij} - \bar n_j)$$

φ_ij, ortalama ada referansına göre **kesin Shapley değeri**. Örnekleme ya da yaklaşıklık gerekmiyor (Lundberg & Lee, 2017; Labreuche & Fossier, 2018).
- *İkili açıklama:* "A adası B'den neden üstte?" sorusunun yanıtı Δ_AB = κ Σ_j w_j (n_Aj − n_Bj) ve bunun kriter kriter dökümü.
- *Mekânsal açıklama:* her kriter için φ haritası. "Bu bölgede skoru PAR aşağı çekiyor" gibi okumalar.

**XAI-1b: Sıra düzeyinde açıklama.** Sıra (rank) doğrusal değil. Bu yüzden ShaRP (Pliatsika vd.) yaklaşımıyla "ilk-k'da olma" ve "sıra" için Shapley değerleri hesaplanıp skor katkılarıyla karşılaştırılacak. Literatürde gösterildiği gibi ikisi farklı şeyleri açıklıyor. Bu fark tezde tartışma malzemesi.

**XAI-2: Fiziksel kısıtlı karşı-olgusal reçete (WOW-2).**

$$\min_{x'} \sum_j c_j |x'_j - x_j| \quad \text{s.t.}\quad \kappa\sum_j w_j n_j(x'_j) \ge f^\*,\;\; \ell \le x' \le u,\;\; \sum_j c_j|x'_j-x_j| \le B$$

- Fayda kriterlerinde n_j doğrusal. Maliyet kriterlerinde n_j = AI_j / x_j dışbükey ve azalan.
- Yapısal sonuç: en iyi çözümde **en fazla bir değişken kesirli**, diğerleri ya değişmiyor ya sınırda. Bu, sırt çantası (knapsack) problemine benzer bir yapı. n ≤ 12 kriter için tam sayımla **kesin çözüm** bulunabiliyor.
- Karşılaştırma: SLSQP ve SmoothMax ile gradyan yöntemi (H5).
- Ek olarak, DiCE benzeri **çeşitli reçeteler** üretilecek: farklı müdahale karışımlarıyla birden çok alternatif.
- Ada ölçütleri, müdahale kollarına (PV alanı, POI karması, EV şarj, yalıtım) bir **eşleme tablosuyla** bağlanacak. Birim maliyetler kaynaklı olacak.

**XAI-3: Belirsizlik ve sıra aralıkları.**
- Ağırlık belirsizliği: w* çevresinde Dirichlet örneklemesi.
- Veri belirsizliği: G1 ile G2 arasındaki hata dağılımından yeniden örnekleme.
- Mekânsal blok bootstrap.
- Çıktılar: her ada için sıra dağılımı, %90 sıra aralığı ve "ilk-k olasılığı" (SMAA'ya benzer kabul edilebilirlik).

### 4.4 Graf katmanı

**Graf-1: PEB sınır genişletme (Güçlü).**
- Düğümler ada veya H3 hücresi. Kenarlar komşuluk ilişkisi.
- Düğüm özellikleri: saatlik net yük profili, f(K) skoru, yıllık üretim ve talep.
- Adım adım büyütme. Aday skoru:

$$\text{skor}_j = \beta\,\tilde f(K_j) + (1-\beta)\,\Delta_j,\qquad \Delta_j = \frac{I_C + I_j - I_{C\cup j}}{D_j}$$

  Δ_j, paylaşım sayesinde şebekeden çekilmeyen enerjinin payı, yani saatlik tamamlayıcılık.
- Kısıt: yıllık denge ≥ θ (PEB koşulu). Çıktı: büyüme yolu ve **en büyük uygun PEB kümesi**.
- Karşılaştırma yöntemleri: max-p-regions (eşik = yıllık denge), rastgele bitişik büyütme, küçük örneklerde tam sayım (optimallik açığı).
- Ölçütler: küme SSR'si, PAR'ı, kompaktlığı ve hücre sayısı.

**Graf-2: GNN ile eksik veri tamamlama (Bonus).**
- Bina komşuluk grafı üzerinde GraphSAGE. Hedef: yükseklik ve yapım yılı. Karşılaştırma: Milojevic-Dupont vd. (2020) tarzı gradyan artırma (GBM). Yerel referans: Halaçlı vd. (2023).
- Çıkan tahmin belirsizliği, XAI-3 belirsizlik analizine aktarılacak.
- *Not:* FT-Transformer, MaskCLIP + FeatUp ve nnPU **kapsam dışına alındı**. Gelecek çalışma olarak yazılacak (K-006).

### 4.5 NLP katmanı (Bonus, "etkileyici" ama kontrollü)

**NLP-1: LLM destekli BWM çıkarımı.**
- Girdi: paydaş görüşme dökümleri, İBB iklim ve enerji planı metinleri.
- LLM'den *yapılandırılmış* çıktı istenecek: en iyi ve en kötü kriter, 1–9 ölçeğinde karşılaştırma vektörleri ve her karşılaştırmanın metinden alıntılanan gerekçesi.
- Denetimler:
  - (i) BWM ξ tutarlılık eşiği
  - (ii) farklı istemler, sıcaklık değerleri ve modeller arasında varyans
  - (iii) insan uzman BWM ağırlıklarıyla Kendall τ
  - (iv) merkeze yığılma yanlılığı testi (arXiv:2601.05267 uyarısı)
- LLM bir **"sanal uzman paneli"** olarak kullanılacak. Nihai ağırlık kararını insan uzman veriyor.

**NLP-2: Sayılara sadık Türkçe açıklamalar.**
- LLM, yalnızca XAI-1, XAI-2 ve XAI-3'ün ürettiği **yapılandırılmış JSON**'u Türkçe metne çeviriyor.
- Metindeki her sayı otomatik olarak JSON'la karşılaştırılıyor (sadakat denetimi). Uydurma sayı içeren metin reddediliyor.
- Değerlendirme: küçük bir planlamacı kullanıcı çalışması. Kavrama görevi ve Likert ölçeği (H7).

## 5. Deney tasarımı

| Deney | Girdi | Çıktı ve ölçüt |
| --- | --- | --- |
| **E0: Sentetik doğrulama** | Kontrollü sentetik bloklar | T1–T5 geçme durumu; MARCOS ≡ κ·WSM özdeşliği; reçete çözücüsünün tam sayımla uyumu |
| **E1: G1 açık veri baz modeli** | OSM/Overture, PVGIS, ERA5, POI | S_k^Global, sıralama, φ haritaları |
| **E2: G2 İBB baz modeli** | LiDAR/DSM, İBB envanteri | S_k^İBB |
| **E3: G3 çapraz doğrulama** | E1 ve E2 | ρ, τ, ilk-k, RMSE, MAPE, bootstrap güven aralığı (H1) |
| **E4: Ablasyon** | Kriter çıkarma (C2/C3), ağırlık şeması, yöntem (MARCOS, TOPSIS, PROMETHEE), mekânsal gecikme, paylaşım modu | Sıra değişimi (H2, H3) |
| **E5: Ölçek (MAUP)** | Ada ile H3 çözünürlüğü 8, 9 ve 10 | Çapraz ölçek kararlılığı (R10) |
| **E6: Sınır genişletme** | Graf-1 ve karşılaştırma yöntemleri | SSR, PAR, optimallik açığı (H4) |
| **E7: Reçete** | Eşik altındaki adalar | Maliyet, uygulanabilirlik, kararlılık (H5) |
| **E8: NLP** | Uzman ve LLM ile BWM; açıklama metinleri | τ, ξ, istem varyansı, sadakat oranı, kullanıcı çalışması (H6, H7) |
| **E9: Küresel aktarım (Bonus)** | İkinci şehir (ör. Avrupa'da bir PEB pilot alanı) | Hattın değişiklik yapılmadan çalıştığının gösterilmesi |

## 6. Beklenen özgün katkılar (tez savunması için)

1. **Saatlik yük eşleşmesine dayalı** PEB uygunluk sıralaması: SSR ve PAR'ın ÇKKDS kriteri olarak kullanılması ve ayırt edici güçlerinin kanıtı.
2. **MARCOS ≡ κ·WSM özdeşliğinden türetilen kesin açıklanabilirlik:** skor, ikili karşılaştırma ve mekânsal katkılar. Bunlara sıra düzeyinde açıklama ve belirsizlik farkındalığı ekleniyor.
3. **Kesin çözümlü, fiziksel kısıtlı karşı-olgusal PEB dönüşüm reçetesi.**
4. **Tamamlayıcılık farkındalığına sahip graf tabanlı PEB sınır genişletme** ve bölgeselleştirme yöntemleriyle kıyası.
5. **Açık küresel veri ile yerel yüksek çözünürlüklü veri arasındaki farkın nicel ölçümü** (Caferağa).
6. *(Bonus)* LLM destekli, tutarlılık denetimli BWM çıkarımı ve sayılara sadık Türkçe açıklama üretimi.
