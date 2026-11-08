# 16 · Vizyon: PED odaklı yapay zekâ karar destek sistemi ve "kent temel modeli"

*Tarih: 2026-11-08 · Durum: tasarım (uygulanan kısımlar ✅ ile işaretli) · Karar kayıtları: K-038…K-042*

## 1. Tek cümle

**pedx, dünyanın herhangi bir noktasında, tıklanan altıgen veya çizilen proje sahası için, gerçek Pozitif Enerji Bölgelerinden (PED) öğrenen ve kararını fiziksel olarak açıklayan, açık veriyle çalışan bir kentsel dönüşüm karar destek sistemidir.**

Tek referans gerçek PED'lerdir. Model, kendi uydurduğu bir "ideal"e göre değil, Avrupa'da gerçekten planlanmış ya da yapılmış PED ve öncü proje sahalarına göre sınanır (§5, docs/17).

## 1b. Büyük soru: Laplace'ın cini ve bilginin değeri (K-044)

**Soru:** Bir mekâna dair bütün raster, vektör ve tablo verisini birlikte okuyan bir karar destek motoru, bir PED projesi hakkında kesin karar verebilir mi?

Laplace (1814), evrenin bütün durumunu ve yasalarını bilen bir zekânın geleceği ve geçmişi kesin bileceğini söyler. Bu tez iddiayı felsefi bir çerçeve olarak alır, ama **sınanabilir** biçime çevirir:

1. **Veri ölçekleme eğrisi** (`scripts/data_scaling.py`): veri aileleri sırası önceden sabitlenerek eklenir; her adımda bir kent dışarıda bırakılarak gerçek PED'leri tanıma AUC'si ve %90 bootstrap aralığı hesaplanır. Eğrinin doyması ek verinin karara katkısının bittiğini gösterir; aralığın genişliği o örneklemle indirgenemeyen belirsizliktir.
2. **Bilginin değeri** (Howard 1966): bir veri katmanı yalnızca kararı değiştirebiliyorsa değerlidir. Ölçekleme eğrisi her ailenin değerini ölçer.
3. **Belirsizlik ayrıştırması:**
   - epistemik belirsizlik veriyle küçülür (ör. nüfus kaynağı GHS-POP ile HRSL);
   - aleatorik belirsizlik (hava, davranış) küçülmez;
   - öz-göndermelilik: kararın kendisi geleceği değiştirir (Morgenstern 1928; Soros'un düşünümselliği);
   - nedensellik korelasyondan çıkmaz (Pearl 2009).
4. **Evrimsel ve olasılıksal modelleme:** Bayesçi güncelleme her yeni kentte posteriordaki belirsizliği daraltır. Evrimsel arama (ör. NSGA-II) ise belirsizlik altında sağlam proje seçenekleri üretir. Sistem tek bir "doğru" vermez; dağılım ve bu dağılımın gerekçesini verir.

**Tezin felsefi iddiası:** Daha fazla veri kesinlik getirmez, ama ne kadar bildiğimizi ölçülebilir kılar. İyi bir karar destek sistemi bilmediğini de raporlar.

Kaynaklar: Laplace, P.-S. (1814). *Essai philosophique sur les probabilités*. · Howard, R. A. (1966). Information value theory. *IEEE Trans. Systems Science and Cybernetics*, 2(1), 22–26. · Pearl, J. (2009). *Causality* (2. bs.). · Kiureghian, A. D., & Ditlevsen, O. (2009). Aleatory or epistemic? *Structural Safety*, 31(2), 105–112. · Lorenz, E. N. (1963). Deterministic nonperiodic flow. *J. Atmos. Sci.*, 20, 130–141. · Deb, K., vd. (2002). NSGA-II. *IEEE Trans. Evol. Comput.*, 6(2), 182–197.

## 2. Kesişim: neden "dünyanın en güncel konuları" bu projede doğal olarak buluşuyor?

| Alan | pedx'teki karşılığı | Durum | Ana kaynak |
|---|---|---|---|
| Enerji ve PED | Saatlik yük eşleme, yıllık denge, batarya, Shapley koalisyonu | ✅ | Salom vd. 2014; Luthander vd. 2015; JPI UE PED Booklet 2020 |
| Kentsel bilişim / GeoAI | H3 altıgen deposu, raster→H3 motoru, Overture/HRSL/GHSL bağlayıcıları | ✅ | Uber H3; Pesaresi vd. 2024 (GHSL); Overture 2026 |
| Uzaktan algılama (CV) | Landsat LST, Sentinel-2 NDVI/NDBI, DEM; uydu gömmeleri | ✅ / ⏳ | SUHII yöntemi; Brown vd. 2025 (AlphaEarth); Clay/Prithvi |
| Sokak görüntüsü (CV/VLM) | Mapillary'den kat sayısı ve cephe tahmini | ⏳ | Biljecki & Ito 2021; Liang vd. 2023 |
| ML / DL | Pozitif-etiketsiz (PU) öğrenme, altıgen transformer'ı (§4) | ⏳ | Bekker & Davis 2020; Vaswani vd. 2017 |
| XAI | Kapalı biçimli log ayrışımı (kesin), Shapley, ters analiz | ✅ | Lundberg & Lee 2017; Shapley 1953 |
| NLP / LLM | PED proje belgelerinden kriter çıkarma; sonuçları sade dille anlatma (yalnızca hesaplanan sayıları anlatır, sayı üretmez) | ⏳ | Krangsås vd. 2021 (7 alan) |
| Karar bilimi | MCDM (CRITIC, BWM, MARCOS), Pareto, referans sınıf tahmini | ✅ | Flyvbjerg 2014; Xie & Zou 2025 |
| Kırılganlık ve afet | Yaşlı, çocuk, genç; ısı maruziyeti; kent dokusunun yaşı; afet tesisleri | ✅ | Meta HRSL; Reid vd. 2009; IPCC AR5 |

## 3. Birleşmiş Milletler SKA (SDG) eşlemesi

Her özellik ailesi ve her çıktı bir SKA hedefine bağlanır. Bağlantı uygulamada da gösterilir.

| SKA | Hedef | pedx ölçüsü |
|---|---|---|
| 7 Erişilebilir ve temiz enerji | 7.2 yenilenebilir payı, 7.3 verimlilik | Yıllık denge, SSR/SCR, çatı FV potansiyeli, yenileme kaldıracı |
| 11 Sürdürülebilir şehirler | 11.1 konut, 11.2 ulaşım, 11.5 afet, 11.6 çevre, 11.7 yeşil alan | 15 dk erişim, toplu taşıma, afet tesisine uzaklık, NDVI, LST |
| 13 İklim eylemi | 13.1 dayanıklılık | Isıya maruz kırılgan nüfus, kentsel ısı adası |
| 3 Sağlık | 3.9 çevre kaynaklı risk | Isı × yaşlı/çocuk, sağlık tesisi erişimi |
| 9 Sanayi ve altyapı | 9.1 dayanıklı altyapı | Şebeke stresi (CVaR), trafo yakınlığı (planlanan) |
| 1, 10 Yoksulluk ve eşitsizlik | Enerji yoksulluğu, adil dönüşüm | Kırılgan grup payları, hedeflenen sakinlerin yeniden yerleşimi (§6) |
| 17 Ortaklıklar | 17.6 açık bilgi | Açık kaynak kütüphane, açık veri, yeniden üretilebilir sürüm |

## 4. "Kent temel modeli": her altıgen bir sözcük (token)

Kullanıcının fikri şuydu: yüzlerce veri sınıfı her altıgende bir vektör olur, bu vektör uzayı gömülür ve gerçek PED'lerle ve literatürle eşlenir. Bunun bilimsel karşılığı aşağıdaki mimaridir.

1. **Token = H3 altıgeni.** Her hücrenin özellik vektörü sözleşmeli kayıttan (registry) gelir. Bugün 120'den fazla özellik vardır; bunlara uydu ve sokak görüntüsü gömmeleri eklenir. Her özellik ailesi ayrı bir "kanal" olarak gömülür; eksik veri maskelenir, uydurulmaz.
2. **Bağlam = komşuluk.** k halkalı H3 diski ya da çizilen saha bir "cümle" olur. Konumu H3 komşuluğu kodlar. Mimari, set/graf transformer'ıdır (Lee vd. 2019; Ying vd. 2021).
3. **Öz-denetimli ön eğitim.** Dünyanın her yerindeki hücrelerde maskelenmiş özellik tahmini yapılır (Devlin vd. 2019 / He vd. 2022 MAE mantığı). Etiket gerekmez, açık veri yeter.
4. **İnce ayar = gerçek PED'ler.** Gerçek PED sahaları pozitif örnektir. Diğer hücreler negatif değil "etiketsiz" sayılır, çünkü pozitif-etiketsiz (PU) öğrenme gerekir (Bekker & Davis 2020). Literatürdeki kriterler (Krangsås'ın 7 alanı, Annex 83) ise öncül ya da kısıt olarak girer.
5. **XAI katmanı.** Model ne derse desin, nihai rapor fiziksel çekirdekten gelir: denge, eşik ve kaldıraçlar kesin ve kapalı biçimlidir. Öğrenilen model "neye benziyor?" sorusunu yanıtlar (en yakın gerçek PED'ler, dikkat ağırlıkları, SHAP). Fizik "neden ve ne yapılmalı?" sorusunu yanıtlar.
6. **Bugünkü ilk adım (✅).** PCA hücre imzası (`pedx.features.embedding`) bu mimarinin doğrusal ve yorumlanabilir taban çizgisidir. Transformer, ancak bu taban çizgisini gerçek PED doğrulamasında (docs/17) geçerse tezde kalır.

> Neden önce taban çizgisi? Gerçek PED sayısı yüzler düzeyinde olduğu için büyük bir model kolayca ezberler. Gruplu (kent bazlı) çapraz doğrulama ve basit-model kıyası bu yüzden zorunludur (docs/07, kırılganlık analizi).

## 5. Doğrulama ilkesi: tek referans gerçek PED'lerdir

- **Vaka–kontrol (✅ kod, docs/17):** gerçek PED sahası ile aynı kentteki rastgele kontrol noktaları aynı kodla puanlanır. Ölçüler: yüzdelik sıra, AUC ve işaret testi. Sonuca bakarak ayar yapılmaz; tohum (seed) sabittir.
- **Caferağa (G2):** küresel açık veriyle elde edilen sonuç yerel verilerle sınanır: TÜİK nüfusu (GHS-POP +%2,7; HRSL +%65), TEDAŞ, EPİAŞ ve Demirel vd. (2025) 3B güneş analizi.
- Gerçek PED'ler yüksek çıkmazsa bu da bir bulgudur. Fiziksel denge tek başına PED seçimini açıklamıyor demektir; eksik ölçüt (yönetişim, mülkiyet, yeni yapım) referans sınıf modeline eklenir.

## 6. Karar destek sistemi (KDS) akışı

```
[1] Seç   : altıgene tıkla (✅ API) · saha çiz (⏳) · mahalle sınırı (✅)
[2] Tanı   : mevcut durum: enerji dengesi, kırılganlık, erişim, ısı, doku yaşı, açık veri tamlığı (✅)
[3] Kıyas  : en benzer gerçek PED'ler (gömme uzayında en yakın komşu) (⏳)
[4] Öner   : kaldıraçlar (✅ çatı kullanımı, talep azaltımı) + fiziksel müdahale paketi (✅ ters analiz motoru)
             + kentsel dönüşüm senaryosu (⏳): aynı nüfusun yeniden yerleşmesi koşuluyla bina yenileme,
             yol dönüşümü (yaya/yeşil), yeni tesis (okul, sağlık, depolama)
[5] Ölç    : yatırım, getiri (ROI) ve geri ödeme; SKA katkısı; kırılgan gruplara etkisi
[6] Açıkla : her sayının kaynağı, lisansı, belirsizlik aralığı ve sade dilde gerekçesi
```

**"Aynı nüfusu yeniden yerleştirme" kısıtı.** Kentsel dönüşüm senaryosunda nüfus korunur (P sabit). Yoğunluk ve kat artışı çatı/kişi oranını düşürür, enerji verimliliği ise d'yi düşürür. B = A·u·η·Y/(P·d) formülü bu ödünleşimi kesin biçimde gösterir. Bu kısıt, sistemin "kârlı ama dışlayıcı" dönüşüm önermesini engeller (SKA 1, 10, 11.1).

## 7. Hibrit küresel mimari (✅ K-040)

- **Hazırlanan katman:** yalnızca büyük döşemelerle dağıtılan veriler (GHS-POP, GHSL) bölge bazında önbelleğe alınır (`make prepare`). Overture satır grubu indeksi sürüm başına bir kez kurulur (10 saniyeden kısa sürer).
- **Tıklama anında:** COG pencereleri (HRSL, DEM), GeoParquet satır grupları (Overture), nokta API'leri (PVGIS) ve küçük Overpass sorguları kullanılır. Önbellekte veri varsa Caferağa'da 6 saniye, ilk tıklamada 15–50 saniye sürer.
- **Hiçbir kaynak sentetik değerle doldurulmaz.** Alınamayan kaynak `failures` alanında raporlanır.

## Kaynaklar (bu belgede yeni olanlar)

- Bekker, J., & Davis, J. (2020). Learning from positive and unlabeled data: a survey. *Machine Learning*, 109, 719–760.
- Biljecki, F., & Ito, K. (2021). Street view imagery in urban analytics and GIS: A review. *Landscape and Urban Planning*, 215, 104217.
- Brown, C. F., vd. (2025). AlphaEarth Foundations. arXiv:2507.22291.
- Devlin, J., vd. (2019). BERT. *NAACL-HLT*.
- He, K., vd. (2022). Masked autoencoders are scalable vision learners. *CVPR*.
- Lee, J., vd. (2019). Set Transformer. *ICML*.
- Reid, C. E., vd. (2009). Mapping community determinants of heat vulnerability. *Environmental Health Perspectives*, 117(11).
- Tiecke, T. G., vd. (2017). Mapping the world population one building at a time. arXiv:1712.05839.
- United Nations (2015). *Transforming our world: the 2030 Agenda for Sustainable Development* (A/RES/70/1).
- Vaswani, A., vd. (2017). Attention is all you need. *NeurIPS*.
- Ying, C., vd. (2021). Do Transformers really perform badly for graph representation? (Graphormer). *NeurIPS*.
- Gollner, C., vd. (2020). *Europe towards Positive Energy Districts* (PED Booklet). JPI Urban Europe.
- Overture Maps Foundation (2026). Release 2026-10-21.0. docs.overturemaps.org.
