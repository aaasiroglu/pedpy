# 07: Kırılganlık Analizi ("Kırmızı Takım" İncelemesi)

*Tarih: 2026-11-08 · Hedef: pedpy'yi küresel ölçekte referans alınan, "kült" statüsünde bir PEB aracına dönüştürmek. Bu belge projede kırılgan, anlamsız ya da değersiz olan her şeyi bulmak için yazıldı. Tartışmaya açıktır; her madde için bir karar önerisi var.*

**Ciddiyet:** 🔴 ölümcül (düzeltilmeden hedefe ulaşılamaz) · 🟠 ciddi (hakem veya kullanıcı bunu yakalar) · 🟡 orta (güvenilirliği aşındırır)
**Öneri:** **BIRAK** (projeden çıkar) · **DÜZELT** (yeniden tasarla) · **TUT** (olduğu gibi kalsın, dürüstçe konumlandır)

---

## A. Kimlik ve konumlandırma

### A1 🔴 `pedpy` adı PyPI'da zaten alınmış. **DÜZELT**
`pip install pedpy` komutu bugün Forschungszentrum Jülich'in **yaya dinamiği** kütüphanesini (PedPy, MIT, Zenodo DOI 10.5281/zenodo.7194992) kuruyor. PyPI adları büyük-küçük harfe duyarsız. README'deki kurulum satırı yanlış paketi yükler. Küresel tanınırlık hedefleyen bir projede ad çakışması arama, atıf ve kurulum açısından **kalıcı bir handikap**.
→ Yeni ad gerekli. Kısa, telaffuzu kolay ve PyPI ile GitHub'da boş bir ad seçilmeli. Adaylar (müsaitlikleri kontrol edilecek): `pedscape`, `pedkit`, `posidistrict`, `plusdistrict`, `pedx`. Bu karar paket iskeletinden önce verilmeli, çünkü `import` adını belirliyor.

### A2 🟠 Pazarlama dili sonuçlardan önce geliyor. **DÜZELT**
"Kesin ve türevlenebilir", "WOW-1/WOW-2", "uçtan uca doğrulanabilir", "sıfır-sayaç küresel motor" gibi ifadeler henüz kanıtı olmayan iddialar. Kült araçlar (OSMnx, pvlib, PySAL) iddialarıyla değil, **çalışan tek satırlık kullanım deneyimi ve güvenilirlikleriyle** yayıldı. Örneğin Boeing (2017), OSMnx'i "basit, tutarlı, otomatikleştirilebilir ve kuramsal olarak sağlam" olarak tanımlıyor.
→ README'den sıfatlar çıkarılmalı; yerine ölçülmüş sayılar konmalı. "WOW" adları kaldırılmalı.

### A3 🟠 Rakip ve konum analizi yok. **DÜZELT**
City Energy Analyst (ETH, MIT lisanslı UBEM platformu), UMEP/SEBE ve DistrictGenerator zaten var. pedpy'nin bunlardan **neyi farklı** yaptığı tek cümlede söylenebilmeli. Öneri:

> *"Herhangi bir şehrin açık verisinden saatlik çözünürlükte, fiziksel hedefe bağlı ve belirsizliği açıklanmış bir PEB hazırlık analizi; graf tabanlı PEB sınır tasarımı; ve eylem düzeyinde dönüşüm yolları üreten ilk açık araç."*

CEA ile rekabet edilmemeli; tersine **CEA çıktısını girdi olarak kabul eden** bir katman olunmalı.

---

## B. Karar modeli (ÇKKDS)

### B1 🔴 Sıralama kümeye göreli; küresel karşılaştırma imkânsız. **DÜZELT**
MARCOS (ve min-max, CRITIC ile Entropi) ideal ve anti-ideal değerleri **o anki alternatif kümesinden** alıyor. Sonuçları:
- (a) Berlin'de 0,8 alan bir ada ile İstanbul'da 0,8 alan ada **karşılaştırılamaz**.
- (b) Kümeye ada eklemek veya çıkarmak diğer adaların sırasını değiştirebilir (**sıra tersinmesi**; normalizasyonun kümeye bağlılığı literatürde ana neden olarak gösteriliyor).
- (c) CRITIC ve Entropi ağırlıkları şehirden şehre değişiyor. Aynı ada, farklı şehirde farklı ağırlıklarla puanlanıyor.

Bu "küresel" hedefle **doğrudan çelişiyor**.
→ **Mutlak, fiziksel hedefe bağlı değer fonksiyonları** önerisi: her kriter, PEB hedefine göre sabit referanslarla [0,1]'e eşlenir. Örneğin yıllık denge G/D = 1 → 1,0; SSR hedefi → 1,0. Ortaya bir **PEB Hazırlık İndeksi** çıkar. Bu indeks şehirler arasında karşılaştırılabilir ve kıyaslanabilir (benchmark yapılabilir). Kümeye göreli MARCOS yalnızca "şehir içi önceliklendirme" görünümü olarak kalır.

### B2 🔴 Kriter setinde PEB'in kendisi yok; enerji üç kez sayılıyor. **DÜZELT**
- PEB'in tanımlayıcı koşulu **yıllık yenilenebilir fazlası** (G/D ≥ 1). Ama C1–C6 içinde **yıllık enerji dengesi oranı yok**. SSR bunu ölçmüyor: SSR saatlik eşleşen enerjiyi ölçüyor ve G/D = 3 olan bir ada ile G/D = 0,6 olan bir ada aynı SSR'ye sahip olabiliyor.
- C1 (PV verimi), C2 (SSR) ve C3 (PAR) **aynı simülasyondan** (aynı G_t ve D_t) türetiliyor. Toplamsal modelde bu, enerji boyutunu örtük olarak üç kat ağırlıklandırmak demek.
- C1'in birimi kWh/m² olduğu için gölgeleme dışında neredeyse sabit. Ölçtüğü şey "potansiyel" değil "gölge". Varyansı düşük olduğu için CRITIC bunu cezalandırır.

→ Yeniden yapılanma önerisi. Kriterler **iki eksende** toplanır:
- **Enerji ekseni:** E1 = yıllık denge G/D, E2 = SSR, E3 = şebeke stresi (aşağıda C2'ye bakın)
- **Dönüşüm ekseni:** T1 = ısıl iyileştirme ihtiyacı, T2 = işlev karması, T3 = altyapı

Eksenler ayrı raporlanır (README'deki "enerji, uygunluk ve müdahale ayrımı" fikriyle de uyumlu). Birleşik skor ikincil olur.

### B3 🟠 MARCOS manşet yöntem olamaz. **DÜZELT, TUT olarak konumlandır**
MARCOS ≡ κ·WSM (Xie & Zou, 2025; bu repoda sayısal olarak doğrulandı). "Mekânsal-MARCOS" markası hakem tarafından ilk okumada çürütülür.
→ ÇKKDS katmanı yöntemden bağımsız olmalı: WSM/MARCOS, TOPSIS ve PROMETHEE II. Katkı yöntemde değil; **belirsizlik, açıklama ve eylem** katmanlarında aranmalı.

### B4 🟠 Ağırlık füzyonu bir "çatallanan yollar bahçesi". **DÜZELT**
CRITIC ile Entropi'nin ölçtüğü şey **varyans ve korelasyon**, önem değil. Politika kararında "verideki değişkenlik büyük diye kriter önemlidir" çıkarımı zayıf. α, λ ve alt sınır olmak üzere üç serbest parametre, sonucu istenilen yöne çekmeye açık.
→ Ağırlıklar **sabit bir doğru** olarak değil, **senaryo ve belirsizlik boyutu** olarak ele alınmalı. Ağırlık uzayında örnekleme yapılır; her ada için sıra aralığı ve "ilk-k olasılığı" raporlanır (SMAA mantığı). CRITIC, Entropi ve BWM bu uzayda **işaretli noktalar** olur. Bu daha dürüst ve daha yeni bir yaklaşım.

### B5 🟠 Mekânsal gecikme (Spatial Lag) karar birimini bulanıklaştırıyor. **BIRAK**
X̃ = (1−ρ)X + ρWX işlemi, bir adanın skoruna komşularının değerlerini karıştırıyor. Karar verici "bu ada"yı değerlendirirken komşunun çatısını puanlamış oluyor. ρ'nun bir gerekçesi yok. Mekânsal etkileşim, açık bir graf mekanizmasıyla (Graf-1: tamamlayıcılık ve paylaşım) zaten modelleniyor.
→ Çıkarılmalı; istenirse yalnızca duyarlılık analizinde kullanılmalı.

### B6 🟡 Smooth-MARCOS, SmoothMax ve T4 testi. **BIRAK**
Sıralama WSM'ye eşdeğer olduğu için bu bileşenler bilimsel bir katkı sağlamıyor (K-005).

### B7 🟡 C4'ün "koşullu fayda" yönü toplamsal modelde tanımsız. **DÜZELT**
Toplamsal bir modelde bir kriterin yönü koşula bağlı olamaz. → İşlev karması ya tamamlayıcılığın (Graf-1) **açıklayıcı değişkeni** olarak kullanılmalı ya da doğrusal olmayan, tek tepeli (unimodal) bir değer fonksiyonuyla tanımlanmalı.

---

## C. Enerji modeli

### C1 🔴 Tamamlayıcılık sonuçları büyük ölçüde talep profili kütüphanesinin bir ürünü (döngüsellik). **DÜZELT**
Gerçek sayaç verisi yoksa saatlik talep birkaç standart günlük şekilden (konut akşam tepesi, ofis gündüz) sentezleniyor. Bu durumda Graf-1'in "gündüz ve gece tamamlayıcı adaları birleştir" bulgusu, **profil kütüphanesine konan varsayımın geri okunması** olur. Model, kendisine verileni "keşfetmiş" görünür.
→ Üç önlem:
- (a) En az iki **bağımsız** profil kütüphanesiyle duyarlılık analizi.
- (b) Mümkünse gerçek veriyle doğrulama: toplulaştırılmış sayaç verisi veya ulusal saatlik yük eğrisi.
- (c) Graf-1 sonuçlarının "profil varsayımı koşullu" olarak raporlanması.

Bu yapılmazsa AS4 (H4) bulguları savunulamaz.

### C2 🟠 PAR tek bir saatin (maksimumun) kararına bağlı. **DÜZELT**
K-003'te tanımlanan PAR = max(I_t) / ortalama talep. Maksimum, uç değere en duyarlı istatistik. Hele sentetik profillerde tek bir saat tüm kriteri belirliyor.
→ Yerine **yüksek yüzdelik** (ör. %99 çekiş) ya da yük-süre eğrisinin üst %1'lik dilimindeki ortalama kullanılmalı. Tanım danışmanla netleşecek.

### C3 🟠 PV ile talep farklı hava-durumu yıllarından gelirse aradaki korelasyon kırılır. **DÜZELT**
PVGIS tipik yıl (TMY) ışınımı ile ERA5'in belirli bir yılından türetilen sıcaklık bazlı talep birlikte kullanılırsa, saatlik eşleşmeler (SSR) yapay olur.
→ PV ve talep **aynı yılın** aynı saatlik hava verisinden türetilmeli. Çok yıllık analizle (ör. 2019–2023) yıllar arası değişkenlik raporlanmalı.

### C4 🟠 Ada içi ve kümeler arası enerji paylaşımının hukuki dayanağı belirsiz. **DÜZELT**
`block_shared` modu ve küme SSR'si, binaların enerjiyi serbestçe paylaştığını varsayıyor. Türkiye'de bunun mevzuat karşılığı (kolektif öz-tüketim, enerji toplulukları) **teyit edilmedi**. Paylaşım mümkün değilse küme kazançları varsayımsal kalır.
→ Paylaşım bir **senaryo parametresi** olarak raporlanmalı. Mevzuat durumu danışman veya hukuk kaynağıyla netleştirilmeli (bkz. 06).

### C5 🟡 Saatlik çözünürlük öz-tüketimi olduğundan yüksek gösterebilir. **TUT, belirt**
Saat içi dalgalanmalar ortalamayla düzleştiği için SSR ve SCR iyimser çıkar. Sınırlılık olarak yazılmalı; kaynağı Faz 1'de bulunmalı.

### C6 🟡 Güneş modelini yeniden yazmak değersiz. **DÜZELT**
Demirel vd. (2025), aynı alan için platformlar arasında %22,29 fark buldu. Belirsizliğin en büyük kaynağı güneş modeli. Basitleştirilmiş 2,5B ufuk gölgelemesi SEBE'den daha kötü olacak.
→ pedpy güneş motoru yazmamalı. **"Kendi ışınım verini getir"** arayüzü (SEBE, CEA veya PVGIS çıktısı) ve basit bir yedek model sunmalı. Belirsizliği, bu kaynaklar arası farkı kullanarak XAI-3'e aktarmalı.

### C7 🟡 Çatı kullanım katsayısı 0,6 baskın ama kaynaksız bir sabit. **DÜZELT**
Birçok sonuç (C1, C2, G/D) bu tek sabite doğrusal olarak bağlı. → Kaynaklı bir değer (veya çatı tipine göre değerler) seçilmeli ve duyarlılık analizine eklenmeli.

---

## D. Veri ve küresellik

### D1 🔴 Tek alanda (Caferağa) yapılan doğrulama "küresel" iddiayı taşımaz. **DÜZELT**
G1 ile G2 karşılaştırması, İstanbul'daki bir mahallede açık verinin yerel veriyi ne kadar temsil ettiğini ölçer. Dünyadaki diğer şehirler hakkında **hiçbir şey söylemez**.
→ Kült araçların gücü **açık kıyaslama setlerinden** gelir. Öneri: açık ve yüksek doğruluklu referans verisi olan 2–3 şehirden küçük bir benchmark (ör. 3B bina yüksekliği resmî ve açık olan bir Avrupa ülkesi; açık bina enerji tüketimi yayımlayan bir şehir) ve Caferağa. Hangi şehirlerin uygun olduğu Faz 1'de araştırılacak.

### D2 🔴 G1 ile G2'nin uyuşması "doğru" olduğunu göstermiyor. **DÜZELT**
G1 ve G2 **aynı modeli** farklı girdilerle çalıştırıyor. Yüksek ρ yalnızca "girdi verisine duyarlılık düşük" demek. Model, gerçeğe karşı hiç sınanmıyor: gerçek tüketim ve gerçek PV üretimiyle karşılaştırma yok.
→ Doğrulama iki ayrı soru olarak ayrılmalı:
- (i) **Veri sadakati:** G1 ile G2 karşılaştırması
- (ii) **Model geçerliliği:** model ile gerçek ölçüm (sayaç, gerçek PV tesisi üretimi) karşılaştırması

(ii) olmadan "doğrulandı" denmemeli. Ayrıca ρ > 0,85 eşiği keyfi (R9).

### D3 🟠 OSM'deki POI ve trafo verisinin tamlığı bölgeden bölgeye değişiyor. **DÜZELT veya BIRAK**
- C4 (POI çeşitliliği), OSM'de ticaretin ne kadar iyi haritalandığını ölçüyor; işlev karmasını değil. Haritalama tamlığı ülkeler arasında çok farklı.
- C6 için OSM'deki trafo ve dağıtım konumları çoğu ülkede seyrek ve eksik. Küresel ölçekte C6 büyük ölçüde gürültü olur.

→ C6 ya kaldırılmalı ya da yalnızca güvenilir yerel veri varsa etkinleşen **isteğe bağlı** bir kriter olmalı. C4 için bina kullanım etiketleri ile POI birlikte kullanılmalı ve **tamlık göstergesi** raporlanmalı.

### D4 🟠 H3 hücresinin karar vericisi yok. **TUT, konumlandır**
PEB bir **yönetişim** birimi: yapı adası, parsel ya da mahalle. Altıgen hücrelerin sahibi yok. → **H3 küresel tarama** için, **ada yerel planlama** için kullanılmalı. İki ölçek arası tutarlılık MAUP analiziyle (E5) raporlanmalı.

### D5 🟡 Uydurma sabitler. **DÜZELT**
C5 içindeki 0,6 yaş ağırlığı ve A/V üst sınırı 1,2; C6 içindeki 300/400/500 m azalma mesafeleri; ve bu oturumda yazdığım taslak koddaki değerler **kaynaksız**. Her sabit ya kaynaklanmalı ya da duyarlılık analizine girmeli. Bu kuralı K-012 olarak kayda geçirmeyi öneriyorum.

---

## E. "İnovasyon" modülleri

### E1 🔴 Kriter uzayındaki reçete uygulanamaz. **DÜZELT**
Mevcut PrescriptiveMARCOS bir reçeteyi "SSR'yi 0,12 artır, PAR'ı 0,3 düşür" biçiminde veriyor. Kimse SSR'yi doğrudan artıramaz. Uygulanabilen şeyler **eylemlerdir**: PV alanı (m²), batarya (kWh), yalıtım (bina sayısı), EV şarj noktası. Ve bu eylemler birden çok kriteri, saatlik simülasyon üzerinden **doğrusal olmayan biçimde** birlikte değiştirir.

Ayrıca hedef "skor ≥ 0,80" göreli bir hedef. Bir adayı iyileştirmek ideal değeri kaydırarak diğer adaların skorunu da değiştirir (B1). "PEB statüsü" ise **fiziksel** bir koşul (G/D ≥ 1).

→ **Eylem uzayında karşı-olgusal analiz** önerisi:
- Karar değişkenleri: müdahale seviyeleri
- Hedef: fiziksel koşul (G/D ≥ 1 ve SSR ≥ s*) veya mutlak PEB Hazırlık İndeksi
- Hesaplama: her aday çözüm için saatlik simülasyon yeniden çalıştırılır
- Çözüm: küçük eylem kümelerinde ızgara veya tam sayım, büyüklerde MILP
- Çıktı: "en ucuz 3 PEB dönüşüm yolu"

Bu, Wachter vd.'nin karşı-olgusal açıklama kavramının **fiziksel modelli** bir uyarlaması. Hem daha yeni, hem uygulayıcı için anlamlı.

### E2 🟠 XAI-1 (kesin Shapley) matematiksel olarak önemsiz. **TUT, ama katkı sayma**
Doğrusal modelde φ_ij = κ·w_j·(n_ij − n̄_j). Hakem "bu sadece ağırlıklı sapma" der ve haklı olur. Bu bir **özellik**; katkı değil.
→ XAI'deki gerçek katkılar şunlar olmalı:
- (a) Sıra düzeyinde açıklama (ShaRP)
- (b) Belirsizlik farkında açıklama ("bu ada ağırlıkların %80'inde ilk-10'da")
- (c) Eylem uzayında karşı-olgusal yollar (E1)
- (d) Aşağıdaki **graf-XAI**

### E3 🟠 Graf-1 açgözlü algoritmasının kendi başına yeniliği zayıf. **DÜZELT, gerçek yeniliği öne çıkar**
max-p-regions zaten eşik kısıtlı bitişik bölgeleme yapıyor. Asıl özgün nokta şu: küme SSR'si **toplamsal değil**. SSR(C ∪ j) ≠ SSR(C) + SSR(j), çünkü saatlik eşleşme kümeyle birlikte değişiyor. Klasik bölgeselleştirme yöntemleri toplamsal amaçlar varsayar.
→ İki öneri:
- Katkı şöyle çerçevelenmeli: **"zamansal olarak birbirine bağlı, toplamsal olmayan amaçlı bölgeselleştirme."**
- **Graf-XAI** eklenmeli: kümedeki her adanın küme öz-yeterliliğine katkısı, **işbirlikçi oyun kuramındaki Shapley değeriyle** hesaplanır (12 adaya kadar kesin: 2¹² alt küme × 8760 saat, yapılabilir). Bu hem "bu ada kümeye neden girdi?" sorusunu açıklıyor, hem de enerji topluluklarında **adil fayda paylaşımına** (kim ne kadar katkı veriyor?) doğrudan bağlanıyor.

Bu, **XAI ile grafı gerçekten birleştiren** katkı ve önceliğinizle tam örtüşüyor.

### E4 🟡 T1–T5 testleri "doğrulama protokolü" değil, birim testi. **TUT, adını düzelt**
Enerji korunumu ve NaN politikası yazılım testidir; bilimsel doğrulama değil. README'de "doğrulama" sözcüğü D2'deki gerçek doğrulama için saklanmalı.

---

## F. Bir aracı "kült" yapan şeyler: pedpy'de olanlar ve olmayanlar

| Etken | Örnek | pedpy'deki durum |
| --- | --- | --- |
| Tek satırla gerçek sonuç | `ox.graph_from_place("Piedmont, CA")` | **Yok** → hedef: `pedx.assess("Caferağa, Kadıköy")` → harita, sıralama, açıklama |
| Benzersiz ve aranabilir ad | osmnx, pvlib | **Çakışma var** (A1) |
| Hakemli yazılım makalesi | Boeing 2017 (CEUS); JOSS | Planlanmalı: tez makalesi + JOSS |
| Açık kıyaslama verisi | — | **Yok** (D1) |
| Galeri ve notebook örnekleri | pvlib, PySAL dokümantasyonu | Planlanmalı (5 şehir galerisi) |
| Kararlı API ve sürümleme | SemVer, değişiklik günlüğü | Planlanmalı |
| Az bağımlılık, kolay kurulum | — | K-001 ile uyumlu |
| Ekosistemle uyum | GeoPandas, xarray | GeoDataFrame girdi ve çıktısı; CEA, SEBE ve PVGIS adaptörleri |

**Kült statüsü algoritmik yenilikten değil, "herkesin yaşadığı bir sorunu en az sürtünmeyle çözmekten" gelir.** Tezin bilimsel katkısı (E1, E3, B1) ile aracın yayılma potansiyeli (F tablosu) **ayrı hedefler** ve ikisi de planlanmalı.

---

## G. Özet: tut, düzelt, bırak

| Bırak | Düzelt | Tut |
| --- | --- | --- |
| Smooth-MARCOS ve SmoothMax (B6) | Paket adı (A1) | Bina→ada saatlik enerji çekirdeği |
| Mekânsal gecikme (B5) | Kümeye göreli skor → mutlak PEB Hazırlık İndeksi (B1) | MARCOS (WSM eşdeğeri olarak, şehir içi görünümde) |
| Geo-AI modülleri (K-006) | Kriter seti: G/D eklenmeli, çift sayım giderilmeli (B2) | CRITIC, Entropi, BWM (belirsizlik uzayında işaret noktası olarak) |
| "WOW" ve pazarlama dili (A2) | Kriter uzayında reçete → eylem uzayında yollar (E1) | XAI-1 (bir özellik olarak) |
| Kendi güneş motoru (C6) | Döngüsel tamamlayıcılık → bağımsız profil duyarlılığı (C1) | G1/G2 karşılaştırması (veri sadakati olarak) |
| | G1/G2 ≠ doğrulama → model geçerliliği testi (D2) | Graf-1 (toplamsal olmayan bölgeselleştirme olarak) |
| | PAR'da maksimum → yüzdelik (C2) | |
| | Tek alan → küçük çok-şehirli benchmark (D1) | |

## H. Yeniden çerçevelenmiş "state-of-the-art" iddiası (tartışma için)

> **pedx/pedpy, açık küresel veriden saatlik çözünürlükte, fiziksel PEB hedefine bağlı ve şehirler arasında karşılaştırılabilir bir PEB Hazırlık İndeksi üretir. Bunun üstüne üç katman ekler: (1) sıranın ağırlık ve veri belirsizliği altındaki güvenilirliğini açıklar; (2) saatlik tamamlayıcılığı gözeten, toplamsal olmayan bir graf bölgeselleştirmesiyle PEB sınırı önerir ve her adanın kümeye katkısını Shapley değeriyle açıklar; (3) fiziksel simülasyona dayalı, eylem düzeyinde en düşük maliyetli PEB dönüşüm yollarını üretir. Bu iddialar açık bir çok-şehirli benchmark ve Caferağa'daki yerel veriyle sınanır.**

Bu çerçevenin üç bilimsel katkısı (B1, E3, E1) ve bir topluluk katkısı (benchmark ile tek satırlık kullanım) var. Tamamı XAI ve graf önceliğinizle uyumlu.
