# 19 · Doğrulama protokolü ve sonuçları (akademik, uçtan uca)

*Sürüm: 2026-11-08 · pedx v0.8 · Karar kayıtları: K-041, K-043, K-049, K-050, K-052*
*Tekrar üretim: `make data build`, ardından `python scripts/validate_ped_sites.py 30`, `python scripts/feature_analysis.py`, `python scripts/build_atlas.py`, `python scripts/maup_validation.py`, `python scripts/multiscale_caferaga.py`, `python scripts/data_scaling.py`. Tohum 20261108; Overture sürümü 2026-10-21.0.*

## 1. Amaç ve çerçeve

Bu belge, pedx'in ürettiği her sayının **doğru hesaplandığını** (doğrulama, *verification*) ve **gerçekliği temsil ettiğini** (geçerleme, *validation*) gösterir. Ayrım, benzetim modellerinde yerleşik ayrıma dayanır (Sargent 2013; Oberkampf ve Roy 2010):

1. **Doğrulama:** Kod, yazılan denklemi uyguluyor mu?
2. **Geçerleme:** Denklem ve veri, amaçlanan kullanım için gerçek dünyayı yeterince temsil ediyor mu?

Amaçlanan kullanım: dünyanın herhangi bir yerinde bir aday sahanın PED projesine elverişliliğini **açık veriyle** sıralamak ve gerekçelendirmek. Kesin bir enerji tasarımı yapmak amaçlanmaz.

Geçerleme düzeyleri, birbirine dayanan sekiz katman olarak kuruldu (V0–V8). Her katman için yöntem, ölçü, kabul ölçütü, sonuç ve sınırlılık verilmiştir. Kabul ölçütleri sonuçlar görülmeden yazılmıştır (K-041). Sonradan yapılan her değişiklik ayrı bir karar kaydıyla belgelenmiştir (K-043, K-050).

## 2. Özet tablo

| Düzey | Soru | Yöntem | Sonuç | Durum |
|---|---|---|---|---|
| V0 Yazılım | Denklemler doğru mu? | 80 birim testi (T1–T5, kesin katkı, gradyan, tersine analiz, ölçek tutarlılığı) | 80/80 geçti | ✅ |
| V1 Veri (G1/G2) | Açık veri yereli temsil ediyor mu? | Açık veri ile resmî veri karşılaştırması | Nüfus GHS-POP +%2,7; HRSL +%65; güneşlenen yüzey OSM −%10,1, GHSL +%3,6 | ✅ |
| V2 İç tutarlılık | Hesap ölçekten ve yoldan bağımsız mı? | Toplam dengenin ölçekler arası eşitliği; toplu hesap ile servis | 1,625 her ölçekte; toplu 1,60, servis 1,65 | ✅ |
| V3 Dış geçerlik | Gerçek PED'leri tanıyor mu? | 16 gerçek PED × 30 yerleşik kontrol, bir kent dışarıda | Denge AUC 0,82 (16/16); PED puanı AUC 0,79–0,80 | ✅ |
| V4 Duyarlılık | Sonuç ölçek, saha ve parametreye bağlı mı? | MAUP (yapı adası, r11, r10, r9; 10–92 ha saha), u ve η aralığı | AUC 0,79–0,89; denge 1,36–3,85 | ✅ |
| V5 Sızıntı | Model projenin sonucunu mu öğreniyor? | Sonuç-şüpheli kriterlerin çıkarılması | AUC 0,91 → 0,79 (savunulabilir değer) | ✅ |
| V6 Yöntem karşılaştırması | Hangi ağırlıklandırma? | 7 şema aynı protokolle | ÇKKDS ≥ ML (16 vaka) | ✅ |
| V7 Açıklama | Açıklama doğru mu? | Katkılar toplamı = logit; doğrusal SHAP eşitliği; sonlu farkla gradyan | Makine hassasiyetinde eşit | ✅ |
| V8 Tersine analiz | Reçete hedefe ulaştırıyor mu? | Kapalı biçim reçetenin modele geri verilmesi | Hedef puan 1e-6 hassasiyetle; olanaksızsa açıkça raporlanıyor | ✅ |
| Faz 2 | Yerel ve saatlik | İBB, TÜİK mahalle, EPİAŞ, PED Veritabanı, proje öncesi görüntü | — | ⏳ |

## 3. Düzeyler

### V0 · Yazılım doğrulaması

- **Yöntem:** Her denklem için bağımsız bir test.
- **Kapsam:**
  - Yük eşleme göstergeleri (SSR, SCR; Salom vd. 2014; Luthander vd. 2015).
  - MARCOS ≡ κ·WSM özdeşliği (Xie ve Zou 2025).
  - Shapley aksiyomları.
  - Batarya durum denklemi.
  - Ters ağırlık kararlılığı (LP/QP).
  - Kırılganlık yeniden tabanlama.
  - Overture alan ve kat alanı.
  - Disk özelliklerinin vektörel ve döngülü hesapta eşitliği.
  - PED puanı:
    - logit = sabit + Σ katkı;
    - gradyan sonlu farkla 1e-4 göreli hata;
    - ağırlıklı toplam ile Platt sırası birebir aynı;
    - tersine reçete hedefi 1e-6 ile tutturuyor.
- **Ölçüt:** Hepsi geçmeli.
- **Sonuç:** 80/80.

### V1 · Veri geçerlemesi (açık veri G1 ile yerel veri G2)

| Gösterge | G1 (küresel, açık) | G2 (yerel/bağımsız) | Fark | Kaynak |
|---|---|---|---|---|
| Caferağa nüfusu | GHS-POP 22.005 | TÜİK ADNKS 2020: 21.421 | +%2,7 | Pesaresi vd. 2024; TÜİK |
| Caferağa nüfusu | Meta HRSL 35.375 | 21.421 | +%65,1 | Tiecke vd. 2017 |
| Güneşlenen yüzey | OSM taban alanı 401.140 m² | Demirel vd. 2025: 629 GWh / 1.410 kWh/m² ≈ 446.099 m² | −%10,1 | Demirel vd. 2025 |
| Güneşlenen yüzey | GHSL yapı alanı 462.255 m² | 446.099 m² | +%3,6 | Pesaresi vd. 2024 |
| Kişi başı elektrik | Ember (TR) 3.713 kWh | TEDAŞ 2023 İstanbul 2.678 kWh | +%38,7 | Ember; TEDAŞ |
| Toplu taşıma öğesi (Caferağa kutusu) | Overture altyapı: 1 | OSM: 40 (16 durak, 5 istasyon, 4 metro girişi) | −%97,5 | Overture 2026-10; OSM |

**Yorum:**
- Overture'un altyapı katmanı toplu taşımada İstanbul'da neredeyse boş. Bu yüzden durak yoğunluğu OSM'den alınıyor (K-052); Overture çapraz kontrol olarak kalıyor. Kaynak bir katmanı "küresel" diye güvenmeden önce G2 ile sınamanın önemini gösteriyor.
- GHS-POP mahalle ölçeğinde güvenilir; HRSL ticari çekirdeklerde nüfusu şişiriyor. Bu yüzden nüfus tabanı GHS-POP, yaş payları HRSL'den.
- OSM ile GHSL, Demirel vd.'nin 3B analizinin iki yanına düşüyor. Platformlar arası %22,29 farkla (Demirel vd. 2025) karşılaştırıldığında, açık verinin hatası 3B araçların kendi aralarındaki farkın içinde kalıyor.

### V2 · İç tutarlılık

- **Ölçek tutarlılığı (K-052):** Her birim binaların toplamıdır. Toplam denge yapı adası, r11, r10 ve r9'da aynıdır: **1,625**. Dasimetrik dağıtımda binası olmayan 8 altıgendeki 339 kişi açıkça raporlanır ve uydurulmaz.
- **Yol tutarlılığı:** Toplu hat (OSM binaları) 1,60; tıkla→hesapla servisi (Overture binaları, PVGIS anlık değer, 2024 talebi) 1,65.

### V3 · Dış geçerlik: gerçek PED'ler (vaka–kontrol)

**Tasarım:**
- **Vakalar:** 16 gerçek PED ve öncü proje sahası (Gollner vd. 2020; Bossi vd. 2020; H2020 SCC projeleri). Konumlar adla OSM'den alındı, nesne kimlikleri kayıtlı.
- **Kontroller:** Saha başına 30 disk. Merkez hücre yerleşik ve dolu: HRSL ≥ 20 kişi, taban alanı > 0, sahadan ≥ 1,5 km.
- **Birim:** k = 2 disk (19 × r10 ≈ 28 ha).
- **Ölçü:** Vakanın kontrolleri içindeki yüzdeliği. Ortalaması tabakalı AUC'dir, yani Mann–Whitney ile eşdeğer (Hanley ve McNeil 1982).
- **Test:** Tek yönlü işaret testi.
- **Kent dışarıda:** Modelin ağırlıkları, yönleri ve kalibrasyonu sınanan kenti hiç görmez (Roberts vd. 2017).

**Sonuçlar:**

| Model | AUC | Medyan üstü | p |
|---|---|---|---|
| Yalnız enerji dengesi | 0,82 | 16/16 | 0,00002 |
| Yoğunluk eşlemeli denge (13 saha) | 0,79 | — | — |
| **PED puanı** (5 temiz kriter, kanıt ağırlığı, kent dışarıda) | **0,80** | 15/16 | — |

**Yorum:** Fizik çekirdeği gerçek PED sahalarını kendi kentlerindeki yerleşik alanlardan ayırıyor. Etki, nüfus yoğunluğu eşlendiğinde sürüyor; yani yalnızca "seyrek nüfus" etkisi değil.

### V4 · Duyarlılık

**Değiştirilebilir alansal birim problemi (MAUP; Openshaw 1984; Fotheringham ve Wong 1991):**

| Ölçek | Birim | Medyan alan | Dengede nüfus payı | Gini (denge) |
|---|---|---|---|---|
| Yapı adası | 113 | 0,46 ha | %93 | 0,17 |
| H3 r11 | 391 | 0,24 ha | %79 | 0,29 |
| H3 r10 | 78 | 1,67 ha | %77 | 0,36 |
| H3 r9 | 18 | 11,7 ha | %100 | 0,32 |

Yapı adası ile r10 arasında Spearman ρ = 0,82.

**Yorum:** Toplam aynı, ama "dengede yaşayan nüfus" ölçeğe göre %77 ile %100 arasında değişiyor. Bu yüzden karar her zaman bir **proje sahası** (bina kümesi) üzerinden verilir ve ölçek raporlanır.

**Saha büyüklüğü** (gerçek PED doğrulaması; `maup_validation.json`):

| k | Saha alanı | AUC (denge) | AUC (puan) |
|---|---|---|---|
| 1 | 10,5 ha | 0,83 | 0,87 |
| 2 | 28,6 ha | 0,82 | 0,89 |
| 3 | 55,7 ha | 0,81 | 0,88 |
| 4 | 91,8 ha | 0,79 | 0,84 |

Puan ağırlıkları k = 2'de öğrenildi; bu satır iyimserdir. Kent dışarıda değer 0,80'dir.

**Parametre aralığı:** Çatı kullanımı u ∈ [0,26; 0,50] ve modül verimi η ∈ [0,17; 0,25] (Gagnon vd. 2016; Fraunhofer ISE) aralığında Caferağa dengesi 1,36–3,85.

**Veri ölçekleme eğrisi** (bilginin değeri; Howard 1966): Veri aileleri eklendikçe AUC 0,82 → 0,88 → 0,82 aralığında kalıyor ve %90 aralıklar örtüşüyor. 16 vakayla daha fazla katman kesinlik getirmiyor; belirleyici olan vaka sayısı.

### V5 · Sızıntı ve ters nedensellik

Bazı kriterler PED projesinin **sonucu** olabilir: 2021–23 görüntüsü inşaat hâlindeki sahayı görüyor. Bu kriterler karar puanından çıkarıldı:
- çıplak alan (WorldCover);
- bisiklet altyapısı;
- EV şarj;
- jeneratör;
- haritalanmış kat alanı (yeni sahalar daha ayrıntılı haritalanır).

Kanıt ağırlıklı AUC 0,91'den 0,79'a düştü. **Savunulabilir değer 0,79–0,80'dir.** Kalan risk: kriterlerin proje öncesi değil 2021–23 değerleri kullanılıyor. Faz 2'de proje öncesi (2015) GHSL, Landsat ve Overture geçmişi ile sınanacak.

### V6 · Yöntem karşılaştırması (kent dışarıda AUC)

| Şema | AUC | Medyan üstü |
|---|---|---|
| Eşit ağırlık (41 kriter) | 0,89 | 16/16 |
| CRITIC (Diakoulaki vd. 1995) | 0,87 | 16/16 |
| Entropi (Shannon) | 0,87 | 16/16 |
| Kanıt (\|d\|, q < 0,10) | 0,91 | 16/16 |
| Öğrenilmiş lojistik | 0,82 | 13/16 |
| Gradyan artırma (Friedman 2001) | 0,85 | 14/16 |
| **Temiz kanıt (PED puanı)** | **0,79** | 15/16 |

**Bulgu:** 16 vaka ve 41 kriterle, şeffaf ÇKKDS ağırlıkları makine öğrenmesi kadar ya da daha iyi ayırıyor. Bu, küçük örneklemde basit modellerin üstünlüğünü gösteren bulgularla uyumludur (Hand 2006).

### V7 · Açıklamanın doğrulanması

- **Kesin katkılar:** PED puanı doğrusal-lojistik olduğu için c_j = β_j z_j katkıları toplamı logit'e eşittir. Bağımsız özelliklerde bu, doğrusal SHAP değeriyle aynıdır (Lundberg ve Lee 2017).
- **Ağaç modeli:** TreeSHAP ile karşılaştırma (Lundberg vd. 2020). Kaynak payları: bina %37, arazi örtüsü %23, altyapı %18, enerji %7.
- **Gradyan:** Sonlu farkla doğrulandı.

### V8 · Tersine analizin doğrulanması

- **Yöntem:** Kapalı biçim reçete (çatı → verim → talep) modele geri verildiğinde hedef puanı 1e-6 ile tutturuyor.
- **Olanaksız hedef:** Kaldıraçlar sınırda hâlâ yetmiyorsa "olanaksız" diye raporlanıyor, sahte bir çözüm üretilmiyor.

## 4. Geçerliliğe yönelik tehditler (Shadish, Cook ve Campbell 2002)

| Tür | Tehdit | Önlem | Kalan risk |
|---|---|---|---|
| Yapı geçerliği | "PED elverişliliği" yalnız yıllık konut elektriğiyle ölçülüyor | Ölçü açıkça sınırlandı; saatlik ve ısı Faz 2'de | Orta |
| Yapı geçerliği | Gerçek PED'ler fizik dışında yönetişim ve mülkiyetle de seçiliyor | Referans sınıf yaklaşımı (Flyvbjerg 2014); 7 alan (Krangsås vd. 2021) | Yüksek, tartışmada |
| İç geçerlik | Ters nedensellik (proje sonrası görüntü) | Şüpheli kriterler çıkarıldı (V5) | Orta |
| İç geçerlik | Kontrol seçimi yoğunluk yanlılığı | Yoğunluk eşlemeli duyarlılık | Düşük |
| İstatistiksel sonuç | 16 vaka, çoklu test | BH-FDR, bootstrap aralıkları, işaret testi | Orta |
| İstatistiksel sonuç | Sonuçları gördükten sonra seçim | Kararlar kayıtlı; bütün şemalar raporlanıyor | Düşük |
| Dış geçerlik | Vakalar yalnız Avrupa (iklim, gelir) | Kent içi z-puanı; Faz 2'de PED Veritabanı ile genişletme | Yüksek |
| Ölçüm | Nüfus kaynağı yanlılığı (HRSL) | G2 ile ölçüldü; nüfus tabanı GHS-POP | Düşük–orta |
| Ölçüm | OSM ve Overture tamlığı | GHSL karşılaştırması; OSM dışı bina payı göstergesi | Orta |

## 5. Yeniden üretilebilirlik

- **Ortam:** Bütün kaynaklar anahtarsız ve açık lisanslı.
- **Sürümler:** Overture sürümü, Landsat ve Sentinel sahne kimlikleri ile Commons ve Wikidata sorgu zamanı provenance dosyalarına yazılıyor.
- **Rastlantısallık:** Tek tohum (20261108).
- **Veri sözleşmesi:** Kayıtsız özellik depoya giremez; her özelliğin kaynağı ve lisansı katalogda (`pedx.features.registry`, `pedx.datalake.catalog`).
- **Başarısız kaynak:** Sentetik değerle doldurulmaz. Örnek: Commons hız sınırında katman "eksik" olarak işaretleniyor.

## 6. Bekleyen geçerleme (Faz 2)

1. **İBB ve TÜİK:** Mahalle ve yapı adası nüfusuyla dasimetrik dağıtımın sınanması (Mennis 2003).
2. **EPİAŞ mesken profili:** Saatlik talebin sınanması (SSR, batarya).
3. **PED Veritabanı:** Vaka sayısını 16'dan 60'a çıkarmak (Gollner vd. 2020: 61 vaka). Veri ölçekleme eğrisi en çok bundan kazanır.
4. **Proje öncesi durum:** 2015 GHSL ve Landsat ile ters nedensellik testi.
5. **Görüntü algısı:** Commons ve Mapillary fotoğraflarında CLIP algı puanlarının yerel anketle sınanması (Zhang vd. 2018 yöntemi).
6. **Demirel vd. (2025):** 3B bina başına güneş potansiyeliyle bina düzeyinde karşılaştırma (Zenodo verisi).

## Kaynaklar

- Bossi, S., Gollner, C., & Theierling, S. (2020). Towards 100 positive energy districts in Europe. *Energies*, 13(22), 6083.
- Demirel, H., Koçyiğit, A., Alpagut, B., & Muhcu, D. (2025). Evaluating the solar energy potential for Positive Energy Districts (PED) through advanced 3D GIS analysis. *Open Research Europe*, 5, 81.
- Diakoulaki, D., Mavrotas, G., & Papayannakis, L. (1995). Determining objective weights in multiple criteria problems: The CRITIC method. *Computers & Operations Research*, 22(7), 763–770.
- Fleischmann, M., Romice, O., & Porta, S. (2020). Measuring urban form: Overcoming terminological inconsistencies for a quantitative and comprehensive morphologic analysis of cities. *Environment and Planning B*, 48(8), 2133–2150.
- Flyvbjerg, B. (2014). What you should know about megaprojects and why. *Project Management Journal*, 45(2), 6–19.
- Fotheringham, A. S., & Wong, D. W. S. (1991). The modifiable areal unit problem in multivariate statistical analysis. *Environment and Planning A*, 23(7), 1025–1044.
- Friedman, J. H. (2001). Greedy function approximation: A gradient boosting machine. *Annals of Statistics*, 29(5), 1189–1232.
- Gagnon, P., Margolis, R., Melius, J., Phillips, C., & Elmore, R. (2016). *Rooftop solar photovoltaic technical potential in the United States* (NREL/TP-6A20-65298).
- Gollner, C., vd. (2020). *Europe towards Positive Energy Districts*. JPI Urban Europe.
- Hand, D. J. (2006). Classifier technology and the illusion of progress. *Statistical Science*, 21(1), 1–14.
- Hanley, J. A., & McNeil, B. J. (1982). The meaning and use of the area under a ROC curve. *Radiology*, 143(1), 29–36.
- Howard, R. A. (1966). Information value theory. *IEEE Transactions on Systems Science and Cybernetics*, 2(1), 22–26.
- Krangsås, S. G., vd. (2021). Positive Energy Districts: Identifying challenges and interdependencies. *Sustainability*, 13(19), 10551.
- Lundberg, S. M., & Lee, S.-I. (2017). A unified approach to interpreting model predictions. *NeurIPS*.
- Lundberg, S. M., vd. (2020). From local explanations to global understanding with explainable AI for trees. *Nature Machine Intelligence*, 2, 56–67.
- Luthander, R., Widén, J., Nilsson, D., & Palm, J. (2015). Photovoltaic self-consumption in buildings: A review. *Applied Energy*, 142, 80–94.
- Mennis, J. (2003). Generating surface models of population using dasymetric mapping. *The Professional Geographer*, 55(1), 31–42.
- Oberkampf, W. L., & Roy, C. J. (2010). *Verification and Validation in Scientific Computing*. Cambridge University Press.
- Openshaw, S. (1984). *The Modifiable Areal Unit Problem*. CATMOG 38.
- Pesaresi, M., vd. (2024). Advances on the Global Human Settlement Layer by joint assessment of Earth Observation and population survey data. *International Journal of Digital Earth*, 17(1).
- Roberts, D. R., vd. (2017). Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. *Ecography*, 40(8), 913–929.
- Salom, J., vd. (2014). Analysis of load match and grid interaction indicators in net zero energy buildings with simulated and monitored data. *Applied Energy*, 136, 119–131.
- Sargent, R. G. (2013). Verification and validation of simulation models. *Journal of Simulation*, 7(1), 12–24.
- Shadish, W. R., Cook, T. D., & Campbell, D. T. (2002). *Experimental and Quasi-Experimental Designs for Generalized Causal Inference*. Houghton Mifflin.
- Tiecke, T. G., vd. (2017). Mapping the world population one building at a time. arXiv:1712.05839.
- Xie, Y., & Zou, X. (2025). MARCOS ile ağırlıklı toplam yönteminin denkliği (künye docs/references.bib'de).
- Zhang, F., vd. (2018). Measuring human perceptions of a large-scale urban region using machine learning. *Landscape and Urban Planning*, 180, 148–160.
