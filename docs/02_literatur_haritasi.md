# 02: Literatür Haritası

*Tarih: 2026-11-08 · Yöntem: hedefli web taraması ve katalog çapraz kontrolü (CrossRef, yayıncı, kurumsal arşivler). Sistematik tarama (PRISMA) Faz 1'de yapılacak.*

İşaretler: ✅ doğrulandı · ⚠️ kısmi · ❓ doğrulanmadı (bkz. [README](README.md)).

---

## T1. Pozitif Enerji Bölgeleri (PEB): tanım, sınır, KPI

| # | Kaynak | Durum | Teze katkısı |
| --- | --- | --- | --- |
| 1 | Brozovsky, J., Gustavsen, A., Gaitani, N. (2021). *Zero emission neighbourhoods and positive energy districts – A state-of-the-art review.* Sustainable Cities and Society 72, 103013. doi:10.1016/j.scs.2021.103013 | ✅ | 144 makale incelenmiş, 35 farklı terim bulunmuş. KPI, sistem sınırı ve ölçek tanımı eksikliğini belgeliyor → **problem tanımının dayanağı** |
| 2 | Albert-Seifried, V. vd. (2022). *Definitions of Positive Energy Districts: A Review of the Status Quo and Challenges.* Springer, doi:10.1007/978-981-16-6269-0_41 | ✅ | Sınır, enerji dengesi ve nitel gereksinimler açık sorun olarak listelenmiş → **R6 (PEB iddia kapsamı)** |
| 3 | JPI Urban Europe, *PED Reference Framework* ve Driving Urban Transitions, *PED Framework 3.0* | ⚠️ | Resmî tanım: yıllık yenilenebilir fazlası ve net-sıfır sera gazı. Sanal ve coğrafi sınır ayrımı. 3.0 sürümünün sınır bölümü okunmalı |
| 4 | Lindholm, O., Rehman, H., Reda, F. (2021). *Positioning positive energy districts in European cities.* Buildings 11 | ❓ | Cilt, sayı ve DOI teyit edilmeli |
| 5 | IEA EBC Annex 83, *Positive Energy Districts* (alt görev A: tanımlar) | ⚠️ | Uluslararası tanım çerçevesi. Raporlar indirilmeli |

## T2. Yerel temel: İTÜ / Caferağa hattı *(tezin doğrudan dayanağı)*

| # | Kaynak | Durum | Teze katkısı |
| --- | --- | --- | --- |
| 6 | Demirel, H., Koçyiğit, A., Alpagut, B., Muhcu, D. (2025). *Evaluating the solar energy potential for Positive Energy Districts (PED) through advanced 3D GIS analysis.* Open Research Europe 5:81 | ✅ (DOI eklenecek) | Caferağa'da 3B güneş analizi yapılmış. Platformlar arası **%22,29 fark** raporlanmış → **G1/G2 doğrulamasının motivasyonu** |
| 7 | Koçyiğit, A. vd. (2026). *Investigating the Role of GIS in Advancing Positive Energy Districts.* ISPRS Archives XLVIII-4-W18-2025, 221 | ⚠️ | PEB için 2B ve 3B CBS karşılaştırması |
| 8 | Alpagut, B., Lopez Romo, A., Hernández, P., Tabanoğlu, O., Hermoso Martinez, N. (2021). *A GIS-Based Multicriteria Assessment for Identification of PED Boundary in Cities.* Energies 14(22), 7517. doi:10.3390/en14227517 | ✅ | PEB sınırı için CBS ve ÇKKDS yaklaşımı, altı Avrupa şehri → **doğrudan öncül yöntem. Tez buna kıyasla konumlanmalı** |
| 9 | *A GIS-Based Approach to Identifying Suitable Areas for PED Development* (Bratislava). Energies 19(4), 1030 (2026). doi:10.3390/en19041030 | ⚠️ (yazarlar eklenecek) | Ağırlıklı çakıştırma (overlay) ile PEB uygunluk indeksi → **güncel karşılaştırma ölçütü** |
| 10 | Bisello, A., Bottero, M., Volpatti, M., Binda, T. (2023). *Multicriteria Spatial Economic Decision Support Systems to Support PEDs: A Literature Review.* Springer, doi:10.1007/978-3-031-39206-1_2 | ✅ | PEB için mekânsal ÇKKDS'nin durumu → **Bölüm 2'nin omurgası** |

**Boşluk (T1 ve T2 sentezi):** Mevcut PEB uygunluk çalışmaları (8, 9) (a) yıllık ve statik katmanlarla çalışıyor, saatlik yük eşleşmesini (SSR, PAR) kriter olarak kullanmıyor; (b) sıralamayı açıklamıyor ve reçete üretmiyor; (c) açık veri ile yerel veri farkını sistematik olarak ölçmüyor. **Bu tezin üç ana katkısı bu üç boşluğa denk geliyor.**

## T3. Saatlik yük eşleşmesi ve öz-tüketim

| # | Kaynak | Durum | Teze katkısı |
| --- | --- | --- | --- |
| 11 | Salom, J., Marszal, A.J., Widén, J., Candanedo, J., Lindberg, K.B. (2014). *Analysis of load match and grid interaction indicators in net zero energy buildings with simulated and monitored data.* **Applied Energy** 136, 119–131. doi:10.1016/j.apenergy.2014.09.018 | ✅ | Yük karşılama ve arz karşılama faktörleri (SSR ve SCR'nin karşılığı) ile şebeke etkileşim göstergeleri → **C2 ve C3 tanımları**. *(Not: README'de dergi hatalı olarak J. Building Perf. Sim. yazılmış olabilir. Doğrusu Applied Energy.)* |
| 12 | Luthander, R., Widén, J., Nilsson, D., Palm, J. (2015). *Photovoltaic self-consumption in buildings: A review.* Applied Energy 142, 80–94. doi:10.1016/j.apenergy.2014.12.028 | ✅ | SSR ve SCR terminolojisi. Depolama ile talep yönetiminin etkisi (+13–24 ve +2–15 yüzde puan) → **reçete müdahale seçenekleri** |

## T4. Kentsel bina enerji modellemesi (UBEM), arketipler, güneş

| # | Kaynak | Durum | Teze katkısı |
| --- | --- | --- | --- |
| 13 | Reinhart, C.F., Cerezo Davila, C. (2016). *Urban building energy modeling – A review of a nascent field.* Building and Environment 97, 196–202 | ✅ (DOI eklenecek) | UBEM iş akışı, arketip yaklaşımı ve belirsizlik |
| 14 | Loga, T., Stein, B., Diefenbach, N. (2016). *TABULA building typologies in 20 European countries.* Energy and Buildings 132, 4–12 | ✅ (DOI eklenecek) | Yaş bandı ve U-değeri arketipleri → **C5 vekil indeksi ve talep sentezi** |
| 15 | Lindberg, F. vd. (2018). *UMEP – An integrated tool for city-based climate services.* Environmental Modelling & Software | ⚠️ | SEBE'nin içinde bulunduğu araç seti |
| 16 | Lindberg, F., Jonsson, P., Honjo, T., Wästberg, D. (2015). *Solar energy on building envelopes – 3D modelling in a 2D environment.* Solar Energy 115 | ❓ | SEBE'nin asıl makalesi. Künye teyit edilmeli |
| 17 | Hersbach, H. vd. (2020). *The ERA5 global reanalysis.* Q. J. R. Meteorol. Soc. 146, 1999–2049. doi:10.1002/qj.3803 | ✅ | Saatlik sıcaklık ve ışınım → **talep kalibrasyonu, küresel kapsama** |
| 18 | JRC PVGIS 6 (SARAH-3 ve ERA5, 2014–2024) dokümantasyonu | ⚠️ | Uydu kapsaması 62°30′K'ye kadar. ERA5 yıllık sapması yaklaşık 6 W/m² → **ışınım girdisi seçimi** |
| 19 | Milojevic-Dupont, N. vd. (2020). *Learning from urban form to predict building heights.* PLOS ONE 15(12): e0242010 | ✅ | Açık veriden bina yüksekliği tahmini → **eksik veri tamamlama için temel yöntem** |

## T5. ÇKKDS: ağırlıklandırma ve sıralama

| # | Kaynak | Durum | Teze katkısı |
| --- | --- | --- | --- |
| 20 | Diakoulaki, D., Mavrotas, G., Papayannakis, L. (1995). *Determining objective weights in multiple criteria problems: The CRITIC method.* Computers & Operations Research 22(7), 763–770. doi:10.1016/0305-0548(94)00059-H | ✅ | CRITIC |
| 21 | Zhu, Y., Tian, D., Yan, F. (2020). *Effectiveness of Entropy Weight Method in Decision-Making.* Mathematical Problems in Engineering, 3564835. doi:10.1155/2020/3564835 | ✅ | Entropi yönteminin sıfır ve bozulma sorunları → **R3** |
| 22 | Rezaei, J. (2015). *Best-worst multi-criteria decision-making method.* Omega 53, 49–57. doi:10.1016/j.omega.2014.11.009 | ✅ | BWM |
| 23 | Rezaei, J. (2016). *BWM: Some properties and a linear model.* Omega 64, 126–130. doi:10.1016/j.omega.2015.12.001 | ✅ | Doğrusal BWM, tekil çözüm → **uygulanacak sürüm** |
| 24 | Stević, Ž., Pamučar, D., Puška, A., Chatterjee, P. (2020). *Sustainable supplier selection in healthcare industries using a new MCDM method: MARCOS.* Computers & Industrial Engineering 140, 106231. doi:10.1016/j.cie.2019.106231 | ✅ | MARCOS |
| 25 | Xie, A., Zou, L. (2025). *A Comparative Study on the Performance of MARCOS Method and Weighted Sum Method.* IAENG Int. J. Applied Mathematics 55(4), 911–917 | ✅ | **MARCOS ≡ WSM kanıtı → R1** (bu repoda sayısal olarak da doğrulandı) |
| 26 | Chen, Y., Yu, J., Khan, S. (2010). *Spatial sensitivity analysis of multi-criteria weights in GIS-based land suitability evaluation.* Environmental Modelling & Software 25(12), 1582–1591. doi:10.1016/j.envsoft.2010.06.001 | ✅ | Mekânsal ağırlık duyarlılığı → **R4** |
| 27 | Lahdelma, R., Salminen, P. — SMAA (Stochastic Multicriteria Acceptability Analysis) | ❓ | Belirsizlik altında "sıra kabul edilebilirliği" → **XAI-3**. Künye teyit edilmeli |
| 28 | Malczewski, J. — GIS-tabanlı ÇKKDS derlemesi (2006) ve Malczewski & Rinner (2015) kitabı | ❓ | Mekânsal ÇKKDS'nin temel kaynağı. Künye teyit edilmeli |

## T6. Mekânsal bölgeselleştirme ve sınır genişletme (graf)

| # | Kaynak | Durum | Teze katkısı |
| --- | --- | --- | --- |
| 29 | Duque, J.C., Anselin, L., Rey, S.J. (2012). *The max-p-regions problem.* Journal of Regional Science 52(3), 397–419 | ✅ (DOI eklenecek) | Eşik kısıtlı bitişik bölgeleme. "Yıllık denge ≥ 1" eşiği ile doğrudan eşleniyor → **WOW-1 için temel karşılaştırma yöntemi** |
| 30 | Assunção, R.M. vd. (2006). SKATER, IJGIS | ❓ | Ağaç tabanlı bölgeselleştirme, ikinci karşılaştırma yöntemi |
| 31 | Hu vd. (2021). ST-GCN ile binalar arası gölgeleme etkisi, arXiv:2105.13399 | ⚠️ | Binaların graf olarak temsili |
| 32 | Halaçlı vd. (2023). *A Novel GNN for Zone-Level Urban-Scale Building Energy Use Estimation.* ACM BuildSys 2023, 169–176 (ODTÜ) | ⚠️ | Türkiye'den GNN ve UBEM çalışması (5.866 bina) → **Graf-2 için güçlü yerel referans** |

## T7. Açıklanabilir yapay zekâ (XAI) ve karşı-olgusal açıklama

| # | Kaynak | Durum | Teze katkısı |
| --- | --- | --- | --- |
| 33 | Lundberg, S.M., Lee, S.-I. (2017). *A Unified Approach to Interpreting Model Predictions.* NeurIPS 30, 4765–4774 | ✅ | SHAP. Doğrusal modelde kesin Shapley değeri → **XAI-1** |
| 34 | Labreuche, C., Fossier, S. (2018). *Explaining Multi-Criteria Decision Aiding Models with an Extended Shapley Value.* IJCAI 2018 | ✅ | ÇKKDS'ye özgü Shapley etki indeksi → **XAI-1'in ÇKKDS dayanağı** |
| 35 | Pliatsika, V. vd. *ShaRP: Explaining Rankings and Preferences with Shapley Values.* PVLDB 18 (arXiv:2401.16744) | ✅ | **Sıra düzeyinde** (ilk-k, ikili tercih) açıklama. Skor açıklaması ile sıra açıklamasının farklı olduğunu gösteriyor → **XAI-1b** |
| 36 | Wachter, S., Mittelstadt, B., Russell, C. (2017/2018). *Counterfactual Explanations Without Opening the Black Box.* Harvard J. Law & Technology 31(2) | ✅ | En küçük değişiklikle olumlu sonuç → **WOW-2 reçetesinin kuramsal çerçevesi** |
| 37 | Mothilal, R.K., Sharma, A., Tan, C. (2020). DiCE: *Explaining ML classifiers through diverse counterfactual explanations.* FAT* 2020 | ❓ | Çeşitli (birden çok) reçete üretimi. Künye teyit edilmeli |

## T8. Büyük dil modelleri (LLM) ve NLP ile ÇKKDS

| # | Kaynak | Durum | Teze katkısı |
| --- | --- | --- | --- |
| 38 | *Doc2AHP*, arXiv:2601.16479 (2026) | ⚠️ | Belgelerden AHP hiyerarşisi ve kriter çıkarımı → **NLP-1** |
| 39 | *Transforming User Defined Criteria into Explainable Indicators with an Integrated LLM-AHP System*, arXiv:2601.05267 | ⚠️ | LLM'lerin öznel ağırlıkta merkeze yığılma (central tendency) yanlılığı → **NLP-1 için uyarı ve kontrol tasarımı** |
| 40 | LLM'lerin "sanal uzman" olarak güneş santrali yer seçiminde AHP ağırlığı vermesi; altı LLM ile on uzmanın karşılaştırması (2026, Heidelberg katalog kaydı) | ❓ | **NLP-1'in en yakın benzeri.** Künye bulunmalı |
| 41 | Aksoy, Adem, Dağdeviren (2025). LLM güvenilirliğinin bulanık AHP ile değerlendirilmesi, IEEE Access | ⚠️ | Türkiye'den LLM ve ÇKKDS çalışması |

**Boşluk (T7 ve T8 sentezi):** (a) PEB ve mekânsal ÇKKDS bağlamında, sıralamanın **kesin** açıklamasını ve **fiziksel kısıtlı karşı-olgusal reçeteyi** birlikte sunan bir çalışma bulunamadı. (b) LLM ile ağırlık çıkarımı çalışmaları AHP'ye odaklanıyor. **BWM ile LLM** birleşimi ve tutarlılık oranıyla denetimi taramada görülmedi. Bu bir **yenilik fırsatı** (sistematik taramayla teyit edilmeli).

## T9. Açık küresel veri ve mekânsal indeksleme

| # | Kaynak | Durum | Not |
| --- | --- | --- | --- |
| 42 | Uber H3 dokümantasyonu (h3geo.org) | ⚠️ | Altıgen ızgara, çözünürlük 8, 9 ve 10 |
| 43 | Overture Maps, OSM, Microsoft Global Building Footprints, GHSL | ⚠️ | Lisanslar (ODbL, CDLA) ve tarihler kayda geçirilmeli |
| 44 | Openshaw, S. (1984). *The Modifiable Areal Unit Problem.* | ❓ | **R10** |

---

## Yapılacaklar (Faz 1)

- [ ] ❓ ve ⚠️ işaretli tüm kaynakların künyesini ve DOI'sini tamamlamak
- [ ] Scopus ve WoS sorgusu: `("positive energy district*" OR "PED") AND (GIS OR "multi-criteria" OR MCDM OR "load match*")`; PRISMA akış diyagramı
- [ ] Alpagut vd. (2021) ve Demirel vd. (2025) **tam metin okuma notları** (kullanılan kriterler, ağırlıklar, veri, sınırlılıklar)
- [ ] Xie & Zou (2025) tam metni: κ sabitinin ifadesini kendi türetimimizle karşılaştırmak
- [ ] JPI UE PED Framework 3.0: sınır türleri bölümü
