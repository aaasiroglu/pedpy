# 20 · Q1 düzeyi için literatür, trend modeller ve temalar

*Sürüm: 2026-11-08 · Amaç: tezi ve iki makaleyi Q1 dergilere taşımak · Kural: her tema için en az 10 sağlam kaynak · İlgili kararlar: K-053*

> **Nasıl okunmalı?** Her tema şu sırayla ilerler:
> 1. Neden önemli?
> 2. Son dönemde Q1 dergilerde ne yükseliyor?
> 3. pedx'te karşılığı ne, ne eksik?
> 4. Kaynaklar (APA 7).
>
> "✔ doğrulandı" künyenin bu çalışmada açık kaynaktan teyit edildiğini, "◐" ise künyenin bilindiğini ama tam metnin henüz okunmadığını gösterir.

## 0. Pilot bölge ve çalışma alanı hiyerarşisi (K-053)

| Düzey | Alan | Rol | Durum |
|---|---|---|---|
| Pilot 1 | **Caferağa** (Kadıköy) | Bina, yapı adası ve H3 ölçeğinde kesin hesap; Demirel vd. (2025) ile G2 | ✅ |
| Pilot 2 | **Kadıköy** ilçesi | Mahalleler arası karşılaştırma; yerel dönüşüm projeleri | ⏳ kent ızgarası kuruluyor |
| Pilot 3 | **İstanbul** (il sınırı) | Kent ölçeği; Yildirim vd. (2021) LiDAR çatı FV ile G2 | ⏳ kent ızgarası kuruluyor |
| Ölçek | **Türkiye** | Ulusal göstergeler (talep, güneş verimi, çatı potansiyeli; Ember 2023) | ⏳ S3 |
| Çalışma alanı | **Dünya** (16 gerçek PED kenti, tıkla→hesapla) | Dış geçerlik, referans sınıfı | ✅ |

**Anlatı:** İstanbul ve Türkiye, Avrupa'nın gerçek PED'leriyle **aynı kodla ve aynı ölçüyle** karşılaştırılır. Böylece Türkiye'nin konumu dünya literatüründe ilk kez nicel ve açık veriyle gösterilir. Bu, Türk bilim altyapısına doğrudan bir katkıdır: açık kaynak kod, açık veri ve Zenodo DOI ile.

## 1. Q1 hedef dergiler ve neden

| Makale | Hedef (Q1) | Uyum gerekçesi |
|---|---|---|
| M1 · AI/BB: gerçek PED imzası, otonom CBS | *Computers, Environment and Urban Systems*; *International Journal of Geographical Information Science*; *International Journal of Digital Earth* | GeoAI, açık veri, açıklanabilirlik, mekânsal doğrulama |
| M2 · YA/EM: kanıt ağırlıklı ÇKKDS, tersine analiz | *Applied Energy*; *Expert Systems with Applications*; *Computers & Industrial Engineering*; *Omega* | Küçük örneklemde ÇKKDS ile ML karşılaştırması, kapalı biçimde tersine optimizasyon |
| M3 · İstanbul vakası ve Türkiye–AB kıyası | *Sustainable Cities and Society*; *Energy and Buildings*; *Cities* | Pilot hiyerarşisi, G2 doğrulaması, politika |

**Q1 hakemlerinin beklediği:**
- açık katkı cümleleri;
- güçlü taban çizgisi karşılaştırması;
- mekânsal (bir kent dışarıda) doğrulama;
- belirsizlik;
- sızıntı kontrolü;
- açık kod ve veri (DOI);
- genellenebilirlik (çok kent).

pedx'te hepsinin karşılığı var (docs/19). Eksikler: Zenodo DOI, proje öncesi görüntü, PED Veritabanı ile genişletilmiş vaka seti.

---

## T1 · Pozitif Enerji Bölgeleri: kavram ve çerçeveler

**Trend:** PED'in tanımı tartışmalı. Son çalışmalar "çerçeve ve değerlendirme göstergeleri" ile "gerçek vakalardan öğrenme" yönünde ilerliyor (Annex 83, syn.ikia, COST PED-EU-NET).
**pedx karşılığı:** gerçek PED vaka–kontrol doğrulaması; elverişlilik çerçevesi.

1. Brozovsky, J., Gustavsen, A., & Gaitani, N. (2021). Zero emission neighbourhoods and positive energy districts – A state-of-the-art review. *Sustainable Cities and Society*, 72, 103013.
2. Lindholm, O., Rehman, H. ur, & Reda, F. (2021). Positioning positive energy districts in European cities. *Buildings*, 11(1), 19.
3. Derkenbaeva, E., Halleck Vega, S., Hofstede, G. J., & van Leeuwen, E. (2022). Positive energy districts: Mainstreaming energy transition in urban areas. *Renewable and Sustainable Energy Reviews*, 153, 111782.
4. Krangsås, S. G., Steemers, K., Konstantinou, T., Soutullo, S., Liu, M., Giancola, E., … Reda, F. (2021). Positive energy districts: Identifying challenges and interdependencies. *Sustainability*, 13(19), 10551.
5. Bossi, S., Gollner, C., & Theierling, S. (2020). Towards 100 positive energy districts in Europe: Preliminary data analysis of 61 European cases. *Energies*, 13(22), 6083.
6. Zhang, X., Penaka, S. R., Giriraj, S., Sánchez, M. N., Civiero, P., & Vandevyvere, H. (2021). Characterizing positive energy district (PED) through a preliminary review of 60 existing projects in Europe. *Buildings*, 11(8), 318.
7. Hedman, Å., Rehman, H. U., Gabaldón, A., Bisello, A., Albert-Seifried, V., Zhang, X., … Reda, F. (2021). IEA EBC Annex 83 positive energy districts. *Buildings*, 11(3), 130.
8. Sareen, S., Albert-Seifried, V., Aelenei, L., Reda, F., Etminan, G., Andreucci, M.-B., … Vandevyvere, H. (2022). Ten questions concerning positive energy districts. *Building and Environment*, 216, 109017.
9. Salom, J., Tamm, M., Andresen, I., Cali, D., Magyari, Á., Bukovszki, V., … (2021). An evaluation framework for sustainable plus energy neighbourhoods. *Energies*, 14(14), 4314.
10. Alpagut, B., Lopez Romo, A., Hernández, P., Tabanoğlu, O., & Hermoso Martinez, N. (2021). A GIS-based multicriteria assessment for identification of positive energy districts boundary in cities. *Energies*, 14(22), 7517.
11. Gollner, C., vd. (2020). *Europe towards Positive Energy Districts* (PED Booklet). JPI Urban Europe.
12. Demirel, H., Koçyiğit, A., Alpagut, B., & Muhcu, D. (2025). Evaluating the solar energy potential for PED through advanced 3D GIS analysis. *Open Research Europe*, 5, 81. ✔ doğrulandı (tam metin okundu)

## T2 · Kentsel bina enerjisi ve çatı FV potansiyeli

**Trend:**
- Küresel ve yüksek çözünürlüklü çatı FV haritaları (Joshi vd. 2021, *Nature Communications*).
- Saatlik ve iklim duyarlı talep (Staffell vd. 2023, *Nature Energy*).
- Belirsizliği raporlayan potansiyel tahmini (Walch vd. 2020).

**pedx karşılığı:** A·u·η·Y çekirdeği, u ve η aralıkları, Demand.ninja; eksik olan saatlik eşleme (Faz 2).

1. Reinhart, C. F., & Cerezo Davila, C. (2016). Urban building energy modeling – A review of a nascent field. *Building and Environment*, 97, 196–202.
2. Swan, L. G., & Ugursal, V. I. (2009). Modeling of end-use energy consumption in the residential sector: A review of modeling techniques. *Renewable and Sustainable Energy Reviews*, 13(8), 1819–1835.
3. Ferrando, M., Causone, F., Hong, T., & Chen, Y. (2020). Urban building energy modeling (UBEM) tools: A state-of-the-art review of bottom-up physics-based approaches. *Sustainable Cities and Society*, 62, 102408.
4. Bódis, K., Kougias, I., Jäger-Waldau, A., Taylor, N., & Szabó, S. (2019). A high-resolution geospatial assessment of the rooftop solar photovoltaic potential in the European Union. *Renewable and Sustainable Energy Reviews*, 114, 109309.
5. Joshi, S., Mittal, S., Holloway, P., Shukla, P. R., Ó Gallachóir, B., & Glynn, J. (2021). High resolution global spatiotemporal assessment of rooftop solar photovoltaics potential for renewable electricity generation. *Nature Communications*, 12, 5738.
6. Walch, A., Castello, R., Mohajeri, N., & Scartezzini, J.-L. (2020). Big data mining for the estimation of hourly rooftop photovoltaic potential and its uncertainty. *Applied Energy*, 262, 114404.
7. Mainzer, K., Killinger, S., McKenna, R., & Fichtner, W. (2017). Assessment of rooftop photovoltaic potentials at the urban level using publicly available geodata and image recognition techniques. *Solar Energy*, 155, 561–573.
8. Huld, T., Müller, R., & Gambardella, A. (2012). A new solar radiation database for estimating PV performance in Europe and Africa. *Solar Energy*, 86(6), 1803–1815.
9. Gagnon, P., Margolis, R., Melius, J., Phillips, C., & Elmore, R. (2016). *Rooftop solar photovoltaic technical potential in the United States* (NREL/TP-6A20-65298).
10. Staffell, I., Pfenninger, S., & Johnson, N. (2023). A global model of hourly space heating and cooling demand at multiple spatial scales. *Nature Energy*, 8, 1328–1344.
11. Salom, J., vd. (2014). Analysis of load match and grid interaction indicators in net zero energy buildings with simulated and monitored data. *Applied Energy*, 136, 119–131.
12. Luthander, R., Widén, J., Nilsson, D., & Palm, J. (2015). Photovoltaic self-consumption in buildings: A review. *Applied Energy*, 142, 80–94.

## T3 · Küresel açık mekânsal veri ve kalitesi

**Trend:** OSM tamlığı ve eşitsizlik (Herfort vd. 2023, *Nature Communications*); küresel 3B yapı stoku (Esch vd. 2022); Overture ve makine öğrenmesiyle çıkarılmış binalar; nüfus ızgaralarının karşılaştırması.
**pedx karşılığı:** G1/G2 karşılaştırmaları:
- nüfus: GHS-POP +%2,7, HRSL +%65;
- yapı alanı: OSM −%10, GHSL +%3,6;
- toplu taşıma: Overture 1/40.

1. Pesaresi, M., Schiavina, M., Politis, P., Freire, S., Krasnodębska, K., Uhl, J. H., … Kemper, T. (2024). Advances on the Global Human Settlement Layer by joint assessment of Earth Observation and population survey data. *International Journal of Digital Earth*, 17(1), 2390454.
2. Haklay, M. (2010). How good is volunteered geographical information? A comparative study of OpenStreetMap and Ordnance Survey datasets. *Environment and Planning B*, 37(4), 682–703.
3. Barrington-Leigh, C., & Millard-Ball, A. (2017). The world's user-generated road map is more than 80% complete. *PLoS ONE*, 12(8), e0180698.
4. Herfort, B., Lautenbach, S., Porto de Albuquerque, J., Anderson, J., & Zipf, A. (2023). A spatio-temporal analysis investigating completeness and inequalities of global urban building data in OpenStreetMap. *Nature Communications*, 14, 3985.
5. Biljecki, F., Chow, Y. S., & Lee, K. (2023). Quality of crowdsourced geospatial building information: A global assessment of OpenStreetMap attributes. *Building and Environment*, 237, 110295.
6. Esch, T., Brzoska, E., Dech, S., Leutner, B., Palacios-Lopez, D., Metz-Marconcini, A., … Zeidler, J. (2022). World Settlement Footprint 3D – A first three-dimensional survey of the global building stock. *Remote Sensing of Environment*, 270, 112877.
7. Sirko, W., Kashubin, S., Ritter, M., Annkah, A., Bouchareb, Y. S. E., Dauphin, Y., … Quinn, J. (2021). Continental-scale building detection from high resolution satellite imagery. arXiv:2107.12283.
8. Tiecke, T. G., Liu, X., Zhang, A., Gros, A., Li, N., Yetman, G., … Dang, H.-A. H. (2017). Mapping the world population one building at a time. arXiv:1712.05839.
9. Stevens, F. R., Gaughan, A. E., Linard, C., & Tatem, A. J. (2015). Disaggregating census data for population mapping using random forests with remotely-sensed and ancillary data. *PLoS ONE*, 10(2), e0107042.
10. Zanaga, D., Van De Kerchove, R., Daems, D., De Keersmaecker, W., Brockmann, C., Kirches, G., … Arino, O. (2022). *ESA WorldCover 10 m 2021 v200*. Zenodo. https://doi.org/10.5281/zenodo.7254221
11. Boeing, G. (2017). OSMnx: New methods for acquiring, constructing, analyzing, and visualizing complex street networks. *Computers, Environment and Urban Systems*, 65, 126–139.
12. Overture Maps Foundation. (2026). *Overture Maps data release 2026-10-21.0*. https://docs.overturemaps.org ✔ doğrulandı (veri okundu)

## T4 · GeoAI ve coğrafi temel modeller (en sıcak tema)

**Trend:**
- Uydu verisi için temel modeller: Prithvi-EO-2.0, TerraMind, Clay, SatlasPretrain, OlmoEarth.
- Konum gömmeleri: SatCLIP, GeoCLIP.
- Küresel gömme ürünleri: AlphaEarth.
- "Uydu verisi ayrı bir modalitedir" tartışması (Rolf vd. 2024, ICML).

**pedx karşılığı:** PCA hücre imzası, yani doğrusal ve yorumlanabilir taban çizgisi. Faz 3'te Prithvi veya Clay gömmeleri eklenecek ve taban çizgisiyle kıyaslanacak (docs/16).

1. Janowicz, K., Gao, S., McKenzie, G., Hu, Y., & Bhaduri, B. (2020). GeoAI: Spatially explicit artificial intelligence techniques for geographic knowledge discovery and beyond. *International Journal of Geographical Information Science*, 34(4), 625–636.
2. Mai, G., Huang, W., Sun, J., Song, S., Mishra, D., Liu, N., … Lao, N. (2024). On the opportunities and challenges of foundation models for GeoAI. *ACM Transactions on Spatial Algorithms and Systems*, 10(2).
3. Jakubik, J., Roy, S., Phillips, C. E., Fraccaro, P., Godwin, D., Zadrozny, B., … Ramachandran, R. (2023). Foundation models for generalist geospatial artificial intelligence. arXiv:2310.18660.
4. Szwarcman, D., Roy, S., Fraccaro, P., Gíslason, Þ. E., Blumenstiel, B., Ghosal, R., … Moreno, J. B. (2024). Prithvi-EO-2.0: A versatile multi-temporal foundation model for Earth observation applications. arXiv:2412.02732.
5. Cong, Y., Khanna, S., Meng, C., Liu, P., Rozi, E., He, Y., Burke, M., Lobell, D., & Ermon, S. (2022). SatMAE: Pre-training transformers for temporal and multi-spectral satellite imagery. *NeurIPS*.
6. Klemmer, K., Rolf, E., Robinson, C., Mackey, L., & Rußwurm, M. (2025). SatCLIP: Global, general-purpose location embeddings with satellite imagery. *AAAI*.
7. Vivanco Cepeda, V., Nayak, G. K., & Shah, M. (2023). GeoCLIP: Clip-inspired alignment between locations and images for effective worldwide geo-localization. *NeurIPS*.
8. Bastani, F., Wolters, P., Gupta, R., Ferdinando, J., & Kembhavi, A. (2023). SatlasPretrain: A large-scale dataset for remote sensing image understanding. *ICCV*.
9. Brown, C. F., vd. (2025). AlphaEarth Foundations: An embedding field model for accurate and efficient global mapping from sparse label data. arXiv:2507.22291.
10. Jakubik, J., vd. (2025). TerraMind: Large-scale generative multimodality for Earth observation. arXiv:2504.11171. ◐
11. Rolf, E., Klemmer, K., Robinson, C., & Kerner, H. (2024). Position: Mission critical – Satellite data is a distinct modality in machine learning. *ICML*.
12. Wang, Y., Albrecht, C. M., Ait Ali Braham, N., Mou, L., & Zhu, X. X. (2022). Self-supervised learning in remote sensing: A review. *IEEE Geoscience and Remote Sensing Magazine*, 10(4), 213–247.
13. Radford, A., Kim, J. W., Hallacy, C., Ramesh, A., Goh, G., Agarwal, S., … Sutskever, I. (2021). Learning transferable visual models from natural language supervision. *ICML*.

## T5 · Sokak görüntüsü, kent algısı ve mekânın ruhu

**Trend:**
- 10 milyon görüntülük küresel sokak veri setleri (Hou vd. 2024).
- Algı tahmini: güvenli, canlı, güzel.
- Bilgisayarlı görü ile mekân duygusu ölçümü.
- Fotoğraflardan güzellik ve manzara.

**pedx karşılığı:** üçüncü mekânlar, kolektif dikkat (Wikidata), fotoğraflanmış önemli yerler, meydanlar. Faz 3'te Commons ve Mapillary görüntülerinde CLIP/SigLIP ile algı puanları.

1. Biljecki, F., & Ito, K. (2021). Street view imagery in urban analytics and GIS: A review. *Landscape and Urban Planning*, 215, 104217.
2. Naik, N., Philipoom, J., Raskar, R., & Hidalgo, C. (2014). Streetscore – Predicting the perceived safety of one million streetscapes. *CVPR Workshops*.
3. Dubey, A., Naik, N., Parikh, D., Raskar, R., & Hidalgo, C. A. (2016). Deep learning the city: Quantifying urban perception at a global scale. *ECCV*.
4. Zhang, F., Zhou, B., Liu, L., Liu, Y., Fung, H. H., Lin, H., & Ratti, C. (2018). Measuring human perceptions of a large-scale urban region using machine learning. *Landscape and Urban Planning*, 180, 148–160.
5. Seresinhe, C. I., Preis, T., & Moat, H. S. (2017). Using deep learning to quantify the beauty of outdoor places. *Royal Society Open Science*, 4(7), 170170.
6. Hou, Y., Quintana, M., Khomiakov, M., Yap, W., Ouyang, J., Ito, K., … Biljecki, F. (2024). Global Streetscapes – A comprehensive dataset of 10 million street-level images across 688 cities for urban science and analytics. *ISPRS Journal of Photogrammetry and Remote Sensing*, 215, 216–238.
7. Kang, Y., Zhang, F., Gao, S., Lin, H., & Liu, Y. (2020). A review of urban physical environment sensing using street view imagery in public health studies. *Annals of GIS*, 26(3), 261–275.
8. Liu, Y., Liu, X., Gao, S., Gong, L., Kang, C., Zhi, Y., Chi, G., & Shi, L. (2015). Social sensing: A new approach to understanding our socioeconomic environments. *Annals of the Association of American Geographers*, 105(3), 512–530.
9. Norberg-Schulz, C. (1980). *Genius Loci: Towards a Phenomenology of Architecture*. Rizzoli.
10. Oldenburg, R. (1989). *The Great Good Place*. Paragon House.
11. Gehl, J. (2010). *Cities for People*. Island Press.
12. Jacobs, J. (1961). *The Death and Life of Great American Cities*. Random House.

## T6 · Açıklanabilir yapay zekâ (mekânsal ve enerji)

**Trend:**
- Mekânsal SHAP: GeoShapley (Li 2024).
- "Kara kutu yerine yorumlanabilir model" çağrısı (Rudin 2019).
- Enerji sistemlerinde XAI derlemeleri.

**pedx karşılığı:** Kapalı biçimde kesin katkılar; doğrusal model için katkı ile SHAP aynıdır. Ağaç modeli için TreeSHAP; karşı-olgusal açıklama için tersine analiz.

1. Lundberg, S. M., & Lee, S.-I. (2017). A unified approach to interpreting model predictions. *NeurIPS*.
2. Lundberg, S. M., Erion, G., Chen, H., DeGrave, A., Prutkin, J. M., Nair, B., … Lee, S.-I. (2020). From local explanations to global understanding with explainable AI for trees. *Nature Machine Intelligence*, 2, 56–67.
3. Rudin, C. (2019). Stop explaining black box machine learning models for high stakes decisions and use interpretable models instead. *Nature Machine Intelligence*, 1, 206–215.
4. Li, Z. (2022). Extracting spatial effects from machine learning model using local interpretation method: An example of SHAP and XGBoost. *Computers, Environment and Urban Systems*, 96, 101845.
5. Li, Z. (2024). GeoShapley: A game theory approach to measuring spatial effects in machine learning models. *Annals of the American Association of Geographers*. ◐
6. Machlev, R., Heistrene, L., Perl, M., Levy, K. Y., Belikov, J., Mannor, S., & Levron, Y. (2022). Explainable artificial intelligence (XAI) techniques for energy and power systems: Review, challenges and opportunities. *Energy and AI*, 9, 100169.
7. Barredo Arrieta, A., Díaz-Rodríguez, N., Del Ser, J., Bennetot, A., Tabik, S., Barbado, A., … Herrera, F. (2020). Explainable artificial intelligence (XAI): Concepts, taxonomies, opportunities and challenges toward responsible AI. *Information Fusion*, 58, 82–115.
8. Ribeiro, M. T., Singh, S., & Guestrin, C. (2016). "Why should I trust you?": Explaining the predictions of any classifier. *KDD*.
9. Wachter, S., Mittelstadt, B., & Russell, C. (2018). Counterfactual explanations without opening the black box. *Harvard Journal of Law & Technology*, 31(2), 841–887.
10. Štrumbelj, E., & Kononenko, I. (2014). Explaining prediction models and individual predictions with feature contributions. *Knowledge and Information Systems*, 41, 647–665.
11. Shapley, L. S. (1953). A value for n-person games. In *Contributions to the Theory of Games II* (pp. 307–317). Princeton University Press.
12. Molnar, C. (2022). *Interpretable Machine Learning* (2nd ed.).

## T7 · Çok kriterli karar verme ve yöneylem araştırması

**Trend:**
- Nesnel ağırlıklandırma: CRITIC, Entropi.
- Tutarlılık odaklı uzman ağırlıkları: BWM.
- Sıra dönmesi ve kararlılık.
- Stokastik ÇKKDS (SMAA).
- Mekânsal karar destek sistemlerinde tasarım tercihleri.

**pedx karşılığı:**
- Kanıt ağırlıklı ÇKKDS küçük örneklemde ML'i yeniyor (V6).
- Sıra dönmesiz mutlak endeks; Dirichlet sıra aralıkları (SMAA benzeri).
- Kapalı biçimde tersine analiz.

1. Diakoulaki, D., Mavrotas, G., & Papayannakis, L. (1995). Determining objective weights in multiple criteria problems: The CRITIC method. *Computers & Operations Research*, 22(7), 763–770.
2. Rezaei, J. (2015). Best-worst multi-criteria decision-making method. *Omega*, 53, 49–57.
3. Rezaei, J. (2016). Best-worst multi-criteria decision-making method: Some properties and a linear model. *Omega*, 64, 126–130.
4. Stević, Ž., Pamučar, D., Puška, A., & Chatterjee, P. (2020). Sustainable supplier selection in healthcare industries using a new MCDM method: Measurement of alternatives and ranking according to COmpromise solution (MARCOS). *Computers & Industrial Engineering*, 140, 106231.
5. Hwang, C.-L., & Yoon, K. (1981). *Multiple Attribute Decision Making: Methods and Applications*. Springer.
6. Lahdelma, R., Hokkanen, J., & Salminen, P. (1998). SMAA – Stochastic multiobjective acceptability analysis. *European Journal of Operational Research*, 106(1), 137–143.
7. Wang, Y.-M., & Luo, Y. (2009). On rank reversal in decision analysis. *Mathematical and Computer Modelling*, 49(5–6), 1221–1229.
8. Malczewski, J. (2006). GIS-based multicriteria decision analysis: A survey of the literature. *International Journal of Geographical Information Science*, 20(7), 703–726.
9. Ferretti, V., & Montibeller, G. (2016). Key challenges and meta-choices in designing and applying multi-criteria spatial decision support systems. *Decision Support Systems*, 84, 41–52.
10. Greco, S., Ehrgott, M., & Figueira, J. R. (Eds.). (2016). *Multiple Criteria Decision Analysis: State of the Art Surveys* (2nd ed.). Springer.
11. Keeney, R. L., & Raiffa, H. (1976). *Decisions with Multiple Objectives: Preferences and Value Tradeoffs*. Wiley.
12. Deb, K., Pratap, A., Agarwal, S., & Meyarivan, T. (2002). A fast and elitist multiobjective genetic algorithm: NSGA-II. *IEEE Transactions on Evolutionary Computation*, 6(2), 182–197.
13. Ehrgott, M. (2005). *Multicriteria Optimization* (2nd ed.). Springer.

## T8 · Mekânsal doğrulama, MAUP ve belirsizlik

**Trend:**
- Mekânsal çapraz doğrulama olmadan küresel haritaların başarısı abartılıyor (Ploton vd. 2020; Meyer ve Pebesma 2022).
- Uygulanabilirlik alanı kavramı.
- Belirsiz coğrafi bağlam.

**pedx karşılığı:**
- Bir kent dışarıda doğrulama.
- Yapı adası, r11, r10, r9 ve 10–92 ha arasında MAUP sınaması.
- Bootstrap aralıkları, BH-FDR.
- V0–V8 protokolü.

1. Openshaw, S. (1984). *The Modifiable Areal Unit Problem*. CATMOG 38. Geo Books.
2. Fotheringham, A. S., & Wong, D. W. S. (1991). The modifiable areal unit problem in multivariate statistical analysis. *Environment and Planning A*, 23(7), 1025–1044.
3. Kwan, M.-P. (2012). The uncertain geographic context problem. *Annals of the Association of American Geographers*, 102(5), 958–968.
4. Roberts, D. R., Bahn, V., Ciuti, S., Boyce, M. S., Elith, J., Guillera-Arroita, G., … Dormann, C. F. (2017). Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. *Ecography*, 40(8), 913–929.
5. Ploton, P., Mortier, F., Réjou-Méchain, M., Barbier, N., Picard, N., Rossi, V., … Pélissier, R. (2020). Spatial validation reveals poor predictive performance of large-scale ecological mapping models. *Nature Communications*, 11, 4540.
6. Meyer, H., & Pebesma, E. (2021). Predicting into unknown space? Estimating the area of applicability of spatial prediction models. *Methods in Ecology and Evolution*, 12(9), 1620–1633.
7. Meyer, H., & Pebesma, E. (2022). Machine learning-based global maps of ecological variables and the challenge of assessing them. *Nature Communications*, 13, 2208.
8. Mennis, J. (2003). Generating surface models of population using dasymetric mapping. *The Professional Geographer*, 55(1), 31–42.
9. Sargent, R. G. (2013). Verification and validation of simulation models. *Journal of Simulation*, 7(1), 12–24.
10. Oberkampf, W. L., & Roy, C. J. (2010). *Verification and Validation in Scientific Computing*. Cambridge University Press.
11. Benjamini, Y., & Hochberg, Y. (1995). Controlling the false discovery rate: A practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society B*, 57(1), 289–300.
12. Hanley, J. A., & McNeil, B. J. (1982). The meaning and use of the area under a receiver operating characteristic (ROC) curve. *Radiology*, 143(1), 29–36.

## T9 · LLM ajanları ve otonom CBS

**Trend:**
- Otonom CBS (Li ve Ning 2023) ve GIS Copilot.
- Coğrafi bilgiyi LLM'den çıkarma (GeoLLM, ICLR 2024).
- Akıl yürüt ve eyle (ReAct) yaklaşımı ve araç kullanan modeller.
- Erişimle güçlendirilmiş üretim (RAG).
- Uydurma (halüsinasyon) riski.

**pedx karşılığı:** pedx-agent. LLM yalnızca araç çağırır ve sonucu anlatır, sayı üretmez. Faz 3'te gerçek PED görev setiyle sınanacak.

1. Li, Z., & Ning, H. (2023). Autonomous GIS: The next-generation AI-powered GIS. *International Journal of Digital Earth*, 16(2), 4668–4686.
2. Akinboyewa, T., Li, Z., Ning, H., & Lessani, M. N. (2025). GIS Copilot: Towards an autonomous GIS agent for spatial analysis. *International Journal of Digital Earth*. ◐
3. Manvi, R., Khanna, S., Mai, G., Burke, M., Lobell, D., & Ermon, S. (2024). GeoLLM: Extracting geospatial knowledge from large language models. *ICLR*.
4. Zhang, Y., Wei, C., He, Z., & Yu, W. (2024). GeoGPT: An assistant for understanding and processing geospatial tasks. *International Journal of Applied Earth Observation and Geoinformation*, 131, 103976. ◐
5. Roberts, J., Lüddecke, T., Das, S., Han, K., & Albanie, S. (2023). GPT4GEO: How a language model sees the world's geography. arXiv:2306.00020.
6. Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). ReAct: Synergizing reasoning and acting in language models. *ICLR*.
7. Schick, T., Dwivedi-Yu, J., Dessì, R., Raileanu, R., Lomeli, M., Zettlemoyer, L., Cancedda, N., & Scialom, T. (2023). Toolformer: Language models can teach themselves to use tools. *NeurIPS*.
8. Wang, L., Ma, C., Feng, X., Zhang, Z., Yang, H., Zhang, J., … Wen, J.-R. (2024). A survey on large language model based autonomous agents. *Frontiers of Computer Science*, 18, 186345.
9. Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., … Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *NeurIPS*.
10. Ji, Z., Lee, N., Frieske, R., Yu, T., Su, D., Xu, Y., … Fung, P. (2023). Survey of hallucination in natural language generation. *ACM Computing Surveys*, 55(12), 1–38.
11. Bommasani, R., vd. (2021). On the opportunities and risks of foundation models. arXiv:2108.07258.
12. Mai, G., vd. (2024). (bkz. T4-2): coğrafi temel modellerin LLM ile birleşimi.

## T10 · Kentsel dönüşüm, 15 dakikalık kent, sosyal altyapı ve kırılganlık

**Trend:**
- 15 dakikalık kent ve yakınlık.
- Kent ölçekleme yasaları.
- Sosyal kırılganlık endeksleri.
- Isı ve kırılgan nüfus.
- Türkiye'de devlet öncülüğündeki kentsel dönüşümün eleştirisi.

**pedx karşılığı:** 36 göstergeli saha raporu, kırılganlık katmanları ve "aynı nüfusu yeniden yerleştirme" kısıtı.

1. Moreno, C., Allam, Z., Chabaud, D., Gall, C., & Pratlong, F. (2021). Introducing the "15-minute city": Sustainability, resilience and place identity in future post-pandemic cities. *Smart Cities*, 4(1), 93–111.
2. Pozoukidou, G., & Chatziyiannaki, Z. (2021). 15-minute city: Decomposing the new urban planning eutopia. *Sustainability*, 13(2), 928.
3. Cutter, S. L., Boruff, B. J., & Shirley, W. L. (2003). Social vulnerability to environmental hazards. *Social Science Quarterly*, 84(2), 242–261.
4. Reid, C. E., O'Neill, M. S., Gronlund, C. J., Brines, S. J., Brown, D. G., Diez-Roux, A. V., & Schwartz, J. (2009). Mapping community determinants of heat vulnerability. *Environmental Health Perspectives*, 117(11), 1730–1736.
5. Klinenberg, E. (2018). *Palaces for the People*. Crown.
6. Bettencourt, L. M. A. (2013). The origins of scaling in cities. *Science*, 340(6139), 1438–1441.
7. Batty, M. (2013). *The New Science of Cities*. MIT Press.
8. Boeing, G. (2019). Urban spatial order: Street network orientation, configuration, and entropy. *Applied Network Science*, 4, 67.
9. Fleischmann, M., Romice, O., & Porta, S. (2021). Measuring urban form: Overcoming terminological inconsistencies for a quantitative and comprehensive morphologic analysis of cities. *Environment and Planning B*, 48(8), 2133–2150.
10. Ewing, R., & Cervero, R. (2010). Travel and the built environment: A meta-analysis. *Journal of the American Planning Association*, 76(3), 265–294.
11. Kuyucu, T., & Ünsal, Ö. (2010). 'Urban transformation' as state-led property transfer: An analysis of two cases of urban renewal in Istanbul. *Urban Studies*, 47(7), 1479–1499.
12. Güzey, Ö. (2009). Urban regeneration and increased competitive power: Ankara in an era of globalization. *Cities*, 26(1), 27–37.

## T11 · Proje elverişliliği ve referans sınıf tahmini

**Trend:** Megaproje riskleri, "dış bakış" yaklaşımı ve referans sınıf tahmininin enerji ile altyapıda kullanımı.
**pedx karşılığı:** Gerçek PED'ler referans sınıf olarak kullanılıyor; PED puanı "benzerlik" olarak sunuluyor.

1. Flyvbjerg, B. (2014). What you should know about megaprojects and why: An overview. *Project Management Journal*, 45(2), 6–19.
2. Flyvbjerg, B. (2006). From Nobel Prize to project management: Getting risks right. *Project Management Journal*, 37(3), 5–15.
3. Flyvbjerg, B., Holm, M. S., & Buhl, S. (2002). Underestimating costs in public works projects: Error or lie? *Journal of the American Planning Association*, 68(3), 279–295.
4. Kahneman, D., & Tversky, A. (1979). Intuitive prediction: Biases and corrective procedures. *TIMS Studies in Management Science*, 12, 313–327.
5. Lovallo, D., & Kahneman, D. (2003). Delusions of success: How optimism undermines executives' decisions. *Harvard Business Review*, 81(7), 56–63.
6. Flyvbjerg, B., & Gardner, D. (2023). *How Big Things Get Done*. Currency.
7. Ansar, A., Flyvbjerg, B., Budzier, A., & Lunn, D. (2014). Should we build more large dams? The actual costs of hydropower megaproject development. *Energy Policy*, 69, 43–56.
8. Sovacool, B. K., Gilbert, A., & Nugent, D. (2014). An international comparative assessment of construction cost overruns for electricity infrastructure. *Energy Research & Social Science*, 3, 152–160.
9. Batselier, J., & Vanhoucke, M. (2016). Practical application and empirical evaluation of reference class forecasting for project management. *Project Management Journal*, 47(5), 36–51.
10. Love, P. E. D., & Ahiaga-Dagbui, D. D. (2018). Debunking fake news in a post-truth era: The plausible untruths of cost underestimation in transport infrastructure projects. *Transportation Research Part A*, 113, 357–368.

## T12 · Türkiye ve İstanbul: enerji, güneş, kent

**Trend:** İstanbul çatı FV potansiyeli LiDAR ve CBS ile ölçülüyor:
- tüketimin %67'si (Yildirim vd. 2021);
- tüketimin %70'i (Kartal ve Alkan 2025).

Türkiye çatı potansiyeli 120 GW (Ember 2023). Ulusal Enerji Planı 2035'te 52,9 GW güneş hedefliyor.

**pedx karşılığı:** Pilot hiyerarşi (Caferağa → Kadıköy → İstanbul). İstanbul ölçeğinde Yildirim vd. (2021) ile G2; Türkiye–AB kıyası.

1. Yildirim, D., Büyüksalih, G., & Şahin, A. D. (2021). Rooftop photovoltaic potential in Istanbul: Calculations based on LiDAR data, measurements and verifications. *Applied Energy*, 304, 117743. ✔ doğrulandı (özet)
2. Kartal, ?, & Alkan, ? (2025). Solar energy based model for decarbonization: A case study in Istanbul. *International Journal of Engineering and Geosciences*. ✔ doğrulandı (özet; yazar adları tam metinden tamamlanacak)
3. Demirel, H., Koçyiğit, A., Alpagut, B., & Muhcu, D. (2025). (bkz. T1-12). ✔ doğrulandı
4. Ember. (2023). *Türkiye can expand solar by 120 GW through rooftops*. ✔ doğrulandı
5. T.C. Enerji ve Tabii Kaynaklar Bakanlığı. (2022). *Türkiye Ulusal Enerji Planı*.
6. International Energy Agency. (2021). *Turkey 2021 Energy Policy Review*. IEA.
7. Kuyucu, T., & Ünsal, Ö. (2010). (bkz. T10-11).
8. Güzey, Ö. (2009). (bkz. T10-12).
9. Gulaydin, O., & Mourshed, M. (2025). Türkiye'nin yenilenebilir potansiyeli ve talep–arz dinamikleri üzerine meta-analiz. *Energy for Sustainable Development*. ◐ (başlık tam metinden doğrulanacak)
10. Alpagut, B., vd. (2021). (bkz. T1-10).
11. Terzi, F., Aksu, K., Koçyiğit, A., & Demirel, H. (2026). Mapping social vulnerability through accessibility patterns: The Istanbul case. *ISPRS Archives*. ◐
12. İstanbul Büyükşehir Belediyesi. (2021). *İstanbul İklim Değişikliği Eylem Planı*. İBB.

---

## 2. Hugging Face model incelemesi ve öneri (canlı sorgu, 2026-11-08)

**Ölçüt:**
- Açık lisans (tez ve yayın için).
- CPU'da ya da tek GPU'da çalışabilme.
- Topluluk kullanımı (indirme sayısı).
- Görevimize uygunluk.

| Görev | Önerilen model | Lisans | Neden | Alternatif |
|---|---|---|---|---|
| Uydu görüntüsü gömmesi (altıgen imzası) | **ibm-nasa-geospatial/Prithvi-EO-2.0-300M** | Apache-2.0 | NASA-IBM, HLS (Landsat+Sentinel) üzerinde eğitilmiş; çok zamanlı; 16,7 bin indirme | made-with-clay/Clay (Apache-2.0), ibm-esa-geospatial/TerraMind-1.0-base (Apache-2.0), allenai/OlmoEarth-v1-Base |
| Konum gömmesi (her yer için hazır vektör) | **microsoft/SatCLIP-ResNet50-L40** | MIT | Küresel, hafif; altıgen merkezine doğrudan gömme | GeoCLIP (GitHub) |
| Fotoğraftan mekân algısı (sıfır-atış) | **google/siglip2-base-patch16-224** | Apache-2.0 | CLIP'ten güncel, açık lisanslı; 1,4 milyon indirme | openai/clip-vit-base-patch32 (MIT, 17,7 milyon indirme), laion/CLIP-ViT-B-32 (MIT) |
| Sokak görüntüsü bölütleme (gökyüzü, yeşil, bina oranı) | **openmmlab/upernet-convnext-small** (ADE20K) | MIT | Açık lisans; kentsel sınıflar | nvidia/segformer (lisans "other", dikkat), facebook/mask2former (other) |
| Görüntü özellik çıkarımı | **facebook/dinov2-base** | Apache-2.0 | Genel amaçlı güçlü gömme | dinov3 (lisans kapılı) |
| Kat sayısı ve derinlik ipucu | **depth-anything/Depth-Anything-V2-Small-hf** | Apache-2.0 | Tek görüntüden derinlik → kat tahmini | Intel/dpt-large (Apache-2.0) |
| Metin gömmesi (Türkçe ve çok dilli yer metni) | **intfloat/multilingual-e5-small** | MIT | Hafif, çok dilli, 9,4 milyon indirme | BAAI/bge-m3 (MIT), paraphrase-multilingual-MiniLM (Apache-2.0) |
| Ajan için LLM (araç kullanımı) | **Qwen/Qwen3-8B** | Apache-2.0 | Açık ağırlık, araç çağırma, Türkçe yeterli | Qwen2.5-7B-Instruct (Apache-2.0), Mistral-7B-Instruct-v0.3 (Apache-2.0) |
| Görüntü + metin (VLM) | **Qwen/Qwen2.5-VL-7B-Instruct** | Apache-2.0 | Fotoğrafı betimleme ve yer anlatısı | HuggingFaceTB/SmolVLM-Instruct (Apache-2.0, küçük), microsoft/Phi-3.5-vision-instruct (MIT) |
| Türkçe dil modeli | ytu-ce-cosmos/Turkish-Llama-8b-Instruct-v0.1 | Llama-3 | YTÜ, Türk bilim altyapısı | dbmdz/bert-base-turkish-cased (MIT) |

**Kaçınılacak modeller:**
- geolocal/StreetCLIP: CC BY-NC (ticari dışı) ve konum tahmini amaçlı.
- meta-llama ve gemma: lisansları kapılı.
- Lisansı "other" olan bölütleme modelleri: yayın öncesi lisans okunmalı.

**Kural:** LLM ve VLM sayı üretmez. Ajan yalnızca pedx araçlarını çağırır; görüntü modelleri ölçülebilir öznitelik üretir (algı puanı, yeşil oranı). Her yeni model, docs/16'daki taban çizgisini (PCA ve fizik) bir kent dışarıda doğrulamada geçmek zorundadır.

## 3. pedx'e alınacak ilham (öncelik sırası)

1. **Herfort vd. (2023) tarzı veri eşitsizliği haritası:** OSM ve Overture tamlığının kentler arası farkı. Türkiye ile AB'yi kıyaslar ve Türkiye'yi görünür kılar.
2. **Joshi vd. (2021) ve Yildirim vd. (2021) ile İstanbul ölçeği G2:** Çatı FV'nin tüketime oranı (%67–70) ile pedx tahmininin karşılaştırılması.
3. **Ploton vd. (2020) ve Meyer ve Pebesma (2021):** Uygulanabilirlik alanı. Tıklanan nokta eğitim kentlerine ne kadar benziyor? Benzemiyorsa uyarı ver.
4. **Hou vd. (2024) ve Biljecki ve Ito (2021):** Sokak görüntüsünden algı (SigLIP2) ve yeşil oranı (UperNet). Mapillary anahtarı gelince.
5. **Prithvi-EO-2.0 ve SatCLIP gömmeleri:** Altıgen imzasının derin sürümü; PCA taban çizgisiyle kıyas (veri ölçekleme eğrisine yeni bir nokta).
6. **Li ve Ning (2023) ile Yao vd. (2023):** pedx-agent: ReAct döngüsü ve araç tanımları. Gerçek PED görev setiyle değerlendirme.
7. **Li (2024) GeoShapley:** Katkılarda konum etkisini ayırmak; M1 için güçlü bir yöntem eki.
