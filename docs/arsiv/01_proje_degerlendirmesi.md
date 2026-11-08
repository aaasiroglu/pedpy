# 01: Proje Değerlendirmesi (Eleştirel İnceleme)

*Tarih: 2026-11-08 · Durum: ilk sürüm*

## 1. Repo'nun mevcut durumu

- `aaasiroglu/pedpy` deposunda yalnızca tek satırlık bir `README.md` ve ilk commit var. Kod, veri ve test yok.
- Elimizdeki tasarım girdileri, sohbette paylaşılan dört metin:
  1. README taslağı (API, C1–C6 kriterleri, T1–T5 testleri, WOW-1/WOW-2),
  2. ÇKKDS denklemleri (CRITIC, Entropi, füzyon, MARCOS),
  3. Küresel ölçekleme mimarisi (açık veri, H3, Geo-AI, SEBE, G1/G2/G3 doğrulaması),
  4. Paket mimarisi (core/ingestion/engine/geoai/mcdm/innovations/pipelines).
- Bu metinler **birbirleriyle tam tutarlı değil**. README'deki dizin yapısı (`energy/`, `weighting/`, `expansion/`...) ile mimari metnindeki yapı (`engine/`, `innovations/`, `geoai/`...) farklı. Mimari metnindeki örnek kod ise yer tutucu: `_evaluate_delta_par` sabit `0.15`, `_calculate_cluster_ssr` sabit `0.85` döndürüyor. Bunlar gerçek bir uygulama değil; tezde "çalışan sistem" diye sunulamaz.
- Ortam notu: Bu bulut oturumunda PyPI'a erişim kapalı. Yalnızca `numpy` ve `pandas` kurulu; `scipy`, `shapely` ve `pytest` yok. Çekirdek kütüphaneyi bağımlılığı az tutarak tasarlamak bu yüzden de mantıklı (bkz. [05_karar_gunlugu.md](05_karar_gunlugu.md), K-001).

## 2. Güçlü yönler

1. **Doğru bir boşluğu hedefliyor.** PEB literatürü sınır tanımı, enerji dengesi hesabı ve KPI'lar konusunda hâlâ belirsiz (Brozovsky vd., 2021; Albert-Seifried vd., 2022). Bina düzeyinde saatlik hesap ile ada ve hücre düzeyinde karar destek arasında köprü kurmak değerli.
2. **Güçlü bir yerel temel var.** Demirel vd. (2025), Caferağa'da 3B CBS ile güneş potansiyeli çalışmasını yayımlamış. Platformlar arasında %22,29 tahmin farkı raporlanmış. Alpagut vd. (2021) ise PEB sınırları için CBS tabanlı çok kriterli bir yöntem önermiş. Tez bu hattın doğal devamı olarak konumlanabilir.
3. **Enerji, uygunluk ve müdahale çıktılarını ayırmak** metodolojik olarak temiz. Klasik "tek indeks" yaklaşımlarının yaygın eleştirisini karşılıyor.
4. **Açık veri ile yerel veri karşılaştırması (G1/G2/G3)**, tezi tekrarlanabilir ve küresel ölçekte anlamlı kılan en güçlü deney fikri.

## 3. Bilimsel riskler ve gerekli düzeltmeler

### R1: MARCOS, ağırlıklı toplam yöntemine (WSM) eşdeğer *(kritik)*

MARCOS'ta f(K⁻) = K⁺/(K⁺+K⁻) = S_aai/(S_ai+S_aai) ifadesi **tüm alternatifler için sabit**. f(K⁺) de öyle. Cebir sonucu:

$$f(K_i) = S_i \cdot \frac{S_{ai}+S_{aai}}{S_{ai}^2 + S_{ai}S_{aai} + S_{aai}^2} = \kappa \cdot S_i,\qquad \kappa>0 .$$

Yani MARCOS sıralaması, normalize matrisin ağırlıklı toplamının (S_i) sıralamasıyla **birebir aynı**. Bunu bağımsız olarak Xie & Zou (2025, IAENG IJAM 55(4):911–917) da kanıtlamış.

Sonuçları:
- README'deki **T4 testi** ("τ→∞ iken Smooth-MARCOS sıralaması klasik MARCOS'a yakınsar") kendi başına bilimsel katkı değil. SmoothMax yalnızca normalizasyondaki ideal değerleri (AI_j) etkiliyor. Bu da etkin ağırlıkları w_j/AI_j biçiminde ölçeklemek demek.
- **"Türevlenebilir Smooth-MARCOS ile gradyan tabanlı reçete"** gereksiz karmaşıklık. Skor normalize uzayda doğrusal olduğu için reçete problemi **kesin olarak** çözülebilir (bkz. R7).
- **Fırsat (XAI):** Skor toplamsal olduğu için her kriterin katkısı **kesin Shapley değeri** olarak kapalı formda hesaplanabilir: φ_ij = κ·w_j·(n_ij − n̄_j). Bu, kara kutu SHAP yaklaşımlarına göre "kesin açıklanabilirlik" iddiasını mümkün kılıyor (bkz. [03](03_arastirma_tasarimi.md)).
- **Yapılması gereken:** Tezde bu eşdeğerlik açıkça yazılmalı. Yöntem duyarlılığı için telafi etmeyen (non-compensatory) bir yöntemle (ör. PROMETHEE II) ve TOPSIS ile karşılaştırma yapılmalı.

### R2: MARCOS normalizasyonu sıfır ve negatif değerlerde tanımsız

Maliyet kriterlerinde n_ij = AI_j / x_ij kullanılıyor. PAR = 0 (tüm saatlerde PV talebi karşılıyor) veya C5 = 0 olursa ifade **sıfıra bölünüyor**. Fayda kriterinde AI_j = 0 olursa da aynı sorun çıkıyor. Ayrıca AI_j/x maliyet dönüşümü hiperbolik (doğrusal değil) ve ölçek ile ötelemeye duyarlı.
→ **Karar gerekli:** pozitif öteleme politikası mı, maliyet kriterleri için alternatif dönüşüm mü? Seçenekler K-004'te tartışılıyor.

### R3: Entropi yönteminin ham veriye uygulanması

Önerilen p_ij = x_ij / Σx_ij formülü ham veriye uygulanıyor. Bu durumda (a) kriter yönünü dikkate almıyor, (b) ötelemeye duyarlı (SSR ∈ [0,1] ile kWh/m² aynı muameleyi görüyor), (c) çok sıfır içeren sütunlarda bozuluyor. Zhu vd. (2020) bu bozulmayı belgelemiş.
→ Entropiyi **yön düzeltilmiş min-max normalize** veride hesaplamayı ve ham veri sürümünü duyarlılık analizinde raporlamayı öneriyorum.

### R4: Ağırlık füzyonunun gerekçesi

w* = λ·w_BWM + (1−λ)·[α·w_CRITIC + (1−α)·w_Entropi] tanımında α ve λ keyfi. README'deki "dışbükey optimizasyon" ise sınırlar aktif değilken bu doğrusal kombinasyona indirgeniyor.
→ (α, λ) ızgarasında **sıralama kararlılığı haritası** çıkarılmalı. Chen vd. (2010)'un tek-seferde-bir-değişken (OAT) mekânsal duyarlılık yaklaşımı ve Monte Carlo yöntemi kullanılabilir.

### R5: Sentetik talep ve döngüsellik

Akıllı sayaç verisi yoksa C2 (SSR) ve C3 (PAR), bina tipolojisinden **sentetik olarak türetilen** talep profillerine dayanıyor. Bu durumda C2 ve C3, C4 ve C5 ile bilgi paylaşabilir (gizli korelasyon). CRITIC bunu "çatışma azlığı" olarak cezalandırır, Entropi ise görmez.
→ (a) Kriterler arası korelasyon matrisi raporlanmalı. (b) Mümkünse gerçek tüketim verisiyle (İBB veya dağıtım şirketi) **talep modeli doğrulaması** yapılmalı. (c) Sentetik talebin belirsizliği sıralama belirsizliğine yayılmalı.

### R6: "PEB" iddiasının kapsamı

JPI Urban Europe tanımına göre PEB yıllık **yenilenebilir enerji fazlası** ve net-sıfır sera gazı salımı gerektiriyor. Tanım sanal, coğrafi ve işlevsel sınır türlerini de ayırıyor. Projede yalnızca çatı PV ve elektrik dengesi modelleniyor. Isıtma, mobilite ve birincil enerji dönüşümü kapsam dışında.
→ Tezde terim **"elektrik odaklı PEB potansiyeli"** olarak sınırlandırılmalı ve sınır türü (bu çalışmada coğrafi ve sanal) açıkça belirtilmeli.

### R7: "Optimal" sınır ve reçete iddiaları

- `PEDBorderExpander` açgözlü (greedy) bir algoritma. "Optimal PEB sınırı" demek için ya kesin çözümle (küçük örneklerde tam sayımla veya MIP ile) karşılaştırma ya da bölgeselleştirme literatüründeki temel yöntemlerle kıyas gerekiyor: max-p-regions (Duque vd., 2012), SKATER.
- `PrescriptiveMARCOS` için literatür bağlamı *karşı-olgusal açıklamalar* (Wachter vd., 2017/2018). Müdahale birim maliyetleri için Türkiye'ye özgü bir kaynak gerekiyor (ör. Bakanlık birim fiyatları). Bu kaynağın teyidi gerekiyor (bkz. [06](06_acik_sorular.md)).

### R8: Kapsam riski *(kritik)*

Önerilen içerik şunları kapsıyor:

- 3B ve 2,5B gölgeleme
- Dört farklı açık veri API'si
- H3 ile küresel ölçekleme
- Üç ayrı Geo-AI modeli (FT-Transformer, MaskCLIP + FeatUp, nnPU)
- Mekânsal ÇKKDS
- İki inovasyon modülü
- İBB doğrulaması

Buna şimdi XAI, NLP ve graf öğrenme de eklendi. Bu, **bir yüksek lisans tezi için fazla**, doktora düzeyinde bir iş yükü.
→ [04_yol_haritasi.md](04_yol_haritasi.md) içinde işleri **Zorunlu, Güçlü ve Bonus** katmanlarına ayırdım. Tezin başarısı Zorunlu katmanın eksiksiz olmasına bağlı. Bonus katman makale ve gelecek çalışma malzemesi.

### R9: Doğrulama eşiği (ρ > 0,85)

ρ > 0,85 eşiği literatürden türetilmemiş, keyfi bir eşik. Ayrıca az sayıda yapı adasıyla (Caferağa'da onlarca ada) Spearman ρ'nun güven aralığı geniş olacak.
→ Eşik çalışma başında **önceden kayda geçirilmeli** (gerekçesiyle). ρ ile birlikte **bootstrap güven aralığı**, Kendall τ ve "ilk-k örtüşmesi" (top-k overlap) raporlanmalı.

### R10: Ölçek etkisi (MAUP) ve H3 çözünürlüğü

Sonuçlar ada sınırına ve H3 çözünürlüğüne (8, 9, 10) bağlı değişebilir. Bu, Değiştirilebilir Alansal Birim Sorunu (MAUP).
→ Sıralama kararlılığı **çözünürlükler arasında** test edilmeli. T5 testi (enerji toplamlarının korunumu) gerekli ama yeterli değil: toplamlar korunsa bile **oranlar** (SSR, PAR) birleştirmeye duyarlı.

## 4. Sonuç ve öneri

Proje fikri güçlü ve yerel literatürle iyi bağlanıyor. Ancak:

1. MARCOS ile WSM'nin eşdeğerliği metodolojinin anlatısını değiştiriyor. Bunu **zayıflık değil, açıklanabilirlik fırsatı** olarak çerçevelemeyi öneriyorum.
2. Kapsam daraltılmalı ve önceliklendirilmeli.
3. XAI, graf ve NLP katkıları ancak "süs" olarak değil, **ölçülebilir araştırma sorularına** bağlanırsa etkileyici olur. Önerilen tasarım [03_arastirma_tasarimi.md](03_arastirma_tasarimi.md) içinde.
