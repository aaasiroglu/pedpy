# 15: Mekânsal Uygunluktan Proje Elverişliliğine

*Tarih: 2026-11-08 · Kullanıcının çerçevelemesi: "Amaç mekânsal analiz değil; PED bir projedir; hedef **projeye elverişlilik analizi**."*

## 1. İki soru aynı değil

| | Mekânsal uygunluk (site suitability) | **Proje elverişliliği (project feasibility)** |
| --- | --- | --- |
| Soru | Hangi yer PED'e uygun? | **Bu PED projesi burada yapılabilir mi, başarılı olur mu, değer mi?** |
| Birim | Hücre veya alan | **Proje adayı:** sınır, müdahale paketi, finansman, paydaşlar |
| Ölçütler | Fiziksel ve mekânsal katmanlar | Teknik, piyasa ve finans, bağlam, sosyal, yönetişim, teşvik, süreç |
| Tipik yöntem | CBS ile ÇKKDS, çakıştırma | Fizibilite, kritik başarı faktörleri, referans sınıf tahmini, makine öğrenmesi ve XAI |
| Örnek | Alpagut vd. 2021; Bratislava 2026 | Megaproje yönetimi, inşaat risk tahmini, kentsel dönüşüm fizibilitesi |

## 2. Literatürde ne var? (araştırma, 2026-11-08)

**Hat A: Büyük projelerde planlama ve "dış bakış"**
- **Flyvbjerg (2014)**, *What You Should Know About Megaprojects and Why*, Project Management Journal 45(2):6–19, doi:10.1002/pmj.21409.
  - "Demir yasa": megaprojeler "bütçeyi aşar, gecikir, tekrar tekrar".
  - Çare olarak **referans sınıf tahmini** öneriyor: projenin kendi senaryosuna değil, **benzer geçmiş projelerin sonuç dağılımına** bakmak (Kahneman ve Tversky'nin "dış bakış" kavramı).
  - → pedx'te karşılığı: **gerçek PED projeleri bir referans sınıfı.** Yeni aday, bu dağılımda nereye düştüğüne göre değerlendirilir.

**Hat B: İnşaat projelerinde makine öğrenmesi ve XAI ile başarı ve risk tahmini**
- **Egwim (2024, Hertfordshire doktora tezi):** BIM projelerinde gecikme riskinin sinir ağıyla tahmini ve SHAP ile açıklanması.
- **Gana çalışması (2023):** XGBoost ve SHAP ile maliyet aşımı tahmini; en etkili değişkenler sözleşme bedeli, kat sayısı ve kapsam değişiklikleri.
- **Kentsel dönüşümde maliyet tahmini sistematik derlemesi (Buildings, 2026; 50 makale):** makine öğrenmesine geçiş var, ama **standart veri eksikliği ve bölgeler arası aktarılabilirliğin zayıflığı** temel sorun.
  - → Ders: XAI ile proje sonucu tahmini yerleşik bir yaklaşım; **aktarılabilirlik** ise açık bir sorun (bizim G1/G2 ve bölge dışarıda bırakma testimizle örtüşüyor).

**Hat C: Kentsel dönüşüm ve büyük alanlarda uygunluk ile kritik başarı faktörleri**
- **Scientific Reports (2025):** Doğu Hindistan'da dönüşüm uygunluğunun sinir ağı, RF ve SVM ile haritalanması.
- **Land (2024):** Makine öğrenmesi özellik önemlerinin CBS-ÇKKDS ağırlığı olarak kullanılması (AHP ve eşit ağırlıkla karşılaştırma).
- **Çin'de kentsel dönüşüm gayrimenkul yatırım ortaklıkları (REIT):** TISM–MICMAC yöntemiyle 11 kritik başarı faktörü ve bunların birbirine etkisi.

**Hat D: PED'e özgü uygulama zorlukları ve başarı faktörleri**
- **Krangsås vd. (2021)**, *Positive Energy Districts: Identifying Challenges and Interdependencies*, Sustainability 13, 10551. Delphi yöntemiyle **7 birbirine bağlı zorluk alanı** belirlenmiş: **yönetişim, teşvik, sosyal, süreç, piyasa, teknoloji, bağlam.** "Hiçbiri diğerlerinden bağımsız ele alınamaz."
- **Steemers, Krangsås vd. (2022):** Yönetişim, sosyal katılım, piyasa ve finans, teknik entegrasyon öncelikli alanlar.
- **PED uygulama vakaları** (Brüksel, Stockholm, Viyana, Évora, Lizbon, Salzburg): net yol haritası, paydaş işbirliği, bütünleşik karar süreçleri, siyasi kararlılık, koordinasyon platformları.

**Boşluk (sentez):** Bu dört hattı birleştiren bir çalışma bulunamadı. Yani **PED'i bir proje olarak** ele alan, **fizik kenetli**, **XAI ile açıklanan**, **gerçek PED projelerini referans sınıfı** olarak kullanan ve **küresel açık veriyle çalışan** bir elverişlilik analizi yok. **Tezin özgün konumu burası.**

## 3. pedx'te proje elverişlilik çerçevesi

**Analiz birimi: proje adayı** P = (sınır S, müdahale paketi u, bağlam x, finansman).
- **S:** graf modülünün ürettiği altıgen kümesi (PEB sınırı).
- **u:** tersine analizin ürettiği fiziksel paket (PV, depolama, kabuk, yük dönüşümü).
- **x:** H3 özellik deposundan, sınır içindeki değerlerin toplulaştırılması.

**Ölçüt aileleri (Krangsås vd. 2021'in 7 alanına eşlenmiş):**

| Alan | pedx'teki ölçüt (açık veri) | Durum |
| --- | --- | --- |
| Teknoloji | Yıllık denge, SSR, tepe rahatlaması, gereken çatı payı | ✅ yıllık; saatlik talep kararını bekliyor |
| Piyasa | ROI: NPV, IRR, geri dönüş süresi | Planlı (S8) |
| Bağlam | Yoğunluk, morfoloji, POI karması, yürüme erişimi, iklim | ✅ 55 özellik |
| Sosyal | Sosyal katman (GDELT, WVS, OSM sivil altyapı) | Planlı (S3) |
| Yönetişim | Şehrin iklim taahhütleri: **Küresel Belediye Başkanları Sözleşmesi imzacılığı ve SECAP varlığı** (JRC açık verisi, teyit edilecek) | Araştırılacak |
| Teşvik | Ülke düzeyinde yenilenebilir enerji destek mekanizmaları (açık politika veritabanları, teyit edilecek) | Araştırılacak |
| Süreç | Doğrudan gözlenemez → yalnızca nitel tartışma ve senaryo | Kapsam sınırı |

**Elverişlilik kararı (karar motoru, docs/13 §5 güncellenmiş hâli):**
1. **Fiziksel yapılabilirlik:** Enerji dengesi ve öz-yeterlilik bu sınır ve paketle tutuyor mu? Kesin fizikle hesaplanır.
2. **Referans sınıfta konum (dış bakış):** Aday, gerçek PED projelerinin dağılımında hangi yüzdelikte (ölçek, yoğunluk, PV payı, hedef denge)? Benzerlik modelinin olasılığı ve en yakın üç gerçek proje gösterilir (örnek tabanlı açıklama).
3. **Değer:** ROI.
4. **Açıklama:** Her alanın katkısı. Fizik için kesin katkılar, öğrenen model için Krangsås alanlarına göre gruplanmış SHAP.
5. **"Ne yapılırsa olur":** Fiziksel tersine analiz (nedensel). Eyleme dönük bağlam değişiklikleri için karşı-olgusal analiz (ilişkisel; böyle etiketlenir).

**Çıktı örneği (hedef):**

> "Bu 9 hücrelik aday, fiziksel olarak 1,4 yıllık dengeye ulaşabiliyor. Ancak gerçek PED projelerine göre nüfus yoğunluğunda 92. yüzdelikte. Benzer üç proje: X, Y, Z. Engelleyen en büyük alan 'piyasa': NPV < 0 (tarife senaryosu A). 120 kWh depolama ve %10 gündüz işlevine dönüşümle NPV pozitif oluyor."

## 4. Doğrulama

- **Referans sınıf modeli:** Gerçek PED projelerinin bilinmeyen bir bölgeye aktarılması, bölge dışarıda bırakılarak sınanır; kalibrasyon raporlanır.
- **Fizik:** G2 (İstanbul) ile doğrulanır.
- **Uzman doğrulaması:** Hande Hoca ve İBB uzmanlarıyla, 3–5 aday proje üzerinden yapılandırılmış değerlendirme (Delphi benzeri, Krangsås vd. 2021 ile tutarlı).

## 5. Tez başlığına etkisi

> **Öneri:** *Pozitif Enerji Bölgesi Projeleri için Açıklanabilir ve Fizik Kenetli Elverişlilik Analizi: Küresel Açık Veri, Referans Sınıf Tahmini ve İstanbul Doğrulaması*
