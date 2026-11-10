# 08: Tersine (Reçeteleyici) Analiz: Tasarım, Eleştiri ve Uygulama

*Tarih: 2026-11-08 · Kod: `src/pedx/inverse/` · Testler: `tests/test_graph_xai_inverse.py`*

## 1. Öğrencinin hedefleri ve ne kadarının karşılandığı

Önerilen `SmoothMARCOS` kurgusunun dört hedefi şunlardı. **Dördü de korunuyor; değişen yalnızca türevin nereden alındığı.**

| Hedef | Durum | Nasıl karşılandı |
| --- | --- | --- |
| 1. Tanımlayıcı analizden reçeteleyici analize geçiş | ✅ | "28. sırada, uygun değil" yerine bütçe–skor eğrisi ve en ucuz müdahale paketi üretiliyor |
| 2. Karşı-olgusal mühendislik reçetesi (en küçük ve en ucuz müdahale) | ✅ | Karar değişkenleri: PV m², kabuk iyileştirme derinliği, batarya kWh, yük dönüşümü oranı |
| 3. Fiziksel kutu kısıtları | ✅ | 0 ≤ PV ≤ boş kullanılabilir çatı alanı; depolama ve dönüşüm sınırları; bütçe kısıtı izdüşümle (projeksiyon) kesin sağlanıyor |
| 4. Sadakat (yumuşatmanın sonucu bozmaması) | ✅ (güçlendirildi) | ρ > 0,999 hedefinin yerine **kanıtlanabilir bir hata sınırı** konuldu (aşağıda) |

## 2. Neden "MARCOS'u yumuşatmak" yerine "fiziği türevlemek"?

1. **MARCOS'un gradyanı bilgi taşımıyor.** f(K) = κ·Σ w_j n_j(x_j). Fayda kriterlerinde ∂f/∂x_j = κ·w_j/AI_j, yani **sabit**. SmoothMax yalnızca ideal değeri (AI_j) yumuşatıyor; bu da etkin ağırlıkları ölçeklemekten ibaret. "Gradyan alanı" aslında sabit bir vektör.
2. **Kriter uzayındaki gradyan uygulanamaz.** "SSR'yi artır" bir eylem değil. Asıl bilgi, eylemden kritere giden **fiziksel zincirde** (u → saatlik G_t, D_t, batarya → denge, SSR, rahatlama) bulunuyor. pedx türevi bu zincir üzerinden alıyor (JAX, saatlik `lax.scan` ile batarya dinamiği dahil).
3. **Hedef göreli olmamalı.** MARCOS skoru kümeye göreli. Bir adayı iyileştirmek ideal değeri kaydırıp diğer adaların skorunu da değiştiriyor. pedx, hedefi **mutlak indeks** üzerinden ya da fiziksel olarak (denge ≥ 1, SSR ≥ s*) tanımlıyor.
4. **ρ > 0,999 yerine kanıtlanabilir sınır.** Yumuşak minimum için şu eşitsizlik geçerli: min − τ·ln2 ≤ softmin_τ ≤ min. Buradan SSR hatası ≤ τ·ln2 / ortalama(D) çıkıyor. `tau_for_ssr_tolerance` istenen toleranstan τ'yu hesaplıyor; test bu sınırı 0,05, 0,01 ve 0,001 toleranslarında doğruluyor. **Ayrıca yumuşak model raporlamaya hiç girmiyor:** her sonuç kesin modelle yeniden hesaplanıyor.

## 3. Paylaşılan `PhysicsCoupledInverseEngine` kodunun incelemesi

Kurgu (üç problem: hedef, bütçe, ağırlık kararlılığı) çok iyi; pedx'te üçü de uygulandı. Ancak kodun fizik ve optimizasyon tarafında aşağıdaki sorunlar var. Her biri pedx'te giderildi:

| # | Sorun | Neden önemli | pedx'teki çözüm |
| --- | --- | --- | --- |
| 1 | Depolama yıllık toplamla modellenmiş: `min(Σsurplus·0,9, Σdeficit, cap·gün·0,85)` | Yaz fazlası kış açığını kapatamaz; SSR **çok iyimser** çıkar | Saatlik şarj durumu (SoC) dinamiği; verim ve C-oranı sınırı |
| 2 | Tepe tıraşlama `max(açık) − cap·0,5` | Bataryanın zirve saatinde dolu olduğunu varsayıyor; kış akşamı boş olabilir | Tepe rahatlaması saatlik akışlardan CVaR ile hesaplanıyor |
| 3 | `talep·(1−yalıtım)` tüm elektrik talebini düşürüyor | Yalıtım yalnızca ısıtma ve soğutma payını etkiler. **İstanbul'da ısıtma çoğunlukla doğalgazla yapıldığı için** elektrik etkisi küçük | Yalnızca `envelope_load` (kabuğa duyarlı elektrik yükü) azalıyor; ısı pompası senaryosu ayrı ele alınacak |
| 4 | C5 = taban·(1−0,8·r), C6 = taban + 0,15·depolama, alt sınırlar 0,05 | Kaynaksız katsayılar; düz bölgeler sıfır gradyan üretiyor | Kriterler doğrudan fizikten hesaplanıyor; uydurma sabit yok |
| 5 | Yalıtım maliyeti "%1 başına 4500 €", ada büyüklüğünden bağımsız | 10 binalık ve 100 binalık ada aynı ücreti ödüyor | Maliyet kabuk alanına bağlı (€/m²) |
| 6 | Kısıt göreli MARCOS skoru; ideal değer adayla birlikte değişiyor | Hedef hareket ediyor; kısıt türevlenemiyor (max/min) | Mutlak indeks ya da fiziksel hedef |
| 7 | SLSQP, türevlenemeyen fonksiyonda sonlu farklarla ve tek başlangıçla | Yerel ve kararsız; yakınsama garantisi yok | Analitik gradyan, çoklu başlangıç, kesin modelle seçim; ızgara aramasına ve ikiye bölmeye karşı testler |
| 8 | "Bağımsız denetim" aynı simülatörü çağırıp yalnızca sınırları kontrol ediyor | Bağımsız değil | Kesin model ile saat saat enerji korunumu, SoC sınırları, depo dengesi, bütçe ve sınır kontrolü (7 kontrol) |
| 9 | Ağırlık kararlılığında aday yalnızca mevcut lideri geçmeye zorlanıyor | Lideri geçip başka bir adanın gerisinde kalabilir | Adayın **tüm** rakipleri geçmesi isteniyor; önce LP ile fizibilite kontrol ediliyor |
| 10 | Çözüm yoksa "Pareto baskın" deniyor | Yanlış terim | Doğrusu "potansiyel olarak optimal değil" (SMAA birincilik olasılığı = 0) |

## 4. Uygulanan matematik

- **Bütçe problemi:** max_u S(u) kısıtlar: c·u ≤ B, 0 ≤ u ≤ ū. Projeksiyonlu Adam adımları, kutu ∩ bütçe kümesine kesin izdüşüm ve çoklu başlangıç kullanılıyor. Kesin modelle en iyi nokta seçiliyor, ardından gereksiz harcama kırpılıyor.
- **Hedef problemi:** min c·u kısıt: S(u) ≥ S*. Bütçe problemindeki optimal skor B'de azalmayan bir fonksiyon olduğu için **bütçe üzerinde ikiye bölme** yapılıyor. Fiziksel üst sınırlar altında hedefe ulaşılamıyorsa bu açıkça raporlanıyor.
- **Pareto eğrisi:** bütçe ızgarası üzerinde bütçe problemi; monotonluk zorunlu tutuluyor.
- **Marjinal değer (XAI):** her müdahalede 1000 € başına skor artışı. **Kesin** sonlu farkla hesaplanıyor. Yumuşak gradyan, PV'siz hücrede bataryaya "hayalet" bir değer atfettiği için açıklamada kullanılmıyor; bunu bir test kontrol ediyor.
- **Ağırlık kararlılığı:** min ‖w − w0‖² kısıtlar: (v_k − v_j)·w ≥ 0 ∀ j, w simplex üzerinde. Dışbükey bir QP. Öncesinde LP ile potansiyel optimallik kontrol ediliyor.

## 5. Doğrulama sonuçları (testler)

| Test | Sonuç |
| --- | --- |
| Bütçe optimumu ile ızgara araması (PV + batarya) | Motor ≥ ızgara − 0,005 |
| Yalnızca PV ile en düşük maliyet ve kesin ikiye bölme | Maliyet farkı < %2 |
| τ → 0 iken yumuşak skor → kesin skor | Hata monoton azalıyor; τ = 0,01'de < 1e-3 |
| Pareto monotonluğu ve denetim | Tüm noktalar geçti |
| Ulaşılamaz hedef | `feasible = False` raporlandı |

## 6. Caferağa v0'dan ilk gözlemler (sentetik talep profilleriyle)

- En düşük skorlu üç hücrede 25k–200k € bütçe aralığında **PV baskın**. Batarya yalnızca yüksek bütçelerde devreye giriyor. Kabuk iyileştirme ve yük dönüşümü hiç seçilmiyor: kabuğa duyarlı elektrik payı %10 varsayıldı ve dönüşüm maliyeti yer tutucu bir değer.
- Bu sonuçlar **varsayım tablosuna duyarlı** (`assumptions.csv`). Tezde "hangi bütçe eşiğinde hangi müdahale devreye giriyor" sorusu, İBB ve literatür kaynaklı maliyetlerle yeniden üretilecek.

## 7. Açık konular

- EV ve akıllı şarj: esnek yük olarak modellenecek (S4).
- Isı pompası ile elektrifikasyon senaryosu: elektrik talebini artırır; yalıtımın elektrik etkisini büyütür (S5).
- Küme düzeyinde birlikte optimizasyon (birden çok hücre ve paylaşım): S7–S8.
