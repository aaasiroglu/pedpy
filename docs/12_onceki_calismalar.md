# 12: Önceki Çalışmaların Değerlendirmesi

*Tarih: 2026-11-08 · Kullanıcının yüklediği belgeler: Geomatik Mühendisliği Tasarımı II (Mayıs 2024, danışmanlar Prof. Dr. Hande Demirel ve Araş. Gör. Koray Aksu), YL tez önerisi (Şubat 2025), IEEE bildirisi (MRI, 2025; bildiri biçimi örneği olarak).*

## 1. Tasarım projesi: "Pozitif Enerji Bölgelerinin CBS ile Analizi" (2024)

**Yapılan:** JPI Urban Europe PED kitapçığından 60 PED şehri ve "benzer özellikli" 60 PED olmayan şehir seçilmiş. Her şehir merkezinin (Nominatim) 1 km çevresinden OSM POI ve altyapı verisi, ayrıca Dünya Bankası GSYH verisi toplanmış. Sonuç 120 × 366 boyutlu bir tablo. SVM, k-NN, GB, XGBoost ve RF karşılaştırılmış; ayarlanmış RF ile doğruluk **0,722** elde edilmiş. Gradio servisiyle yeni şehirler için puan üretilmiş.

**Güçlü yönler:**
- Baştan **küresel ve açık veri** ile **API tabanlı, tekrarlanabilir** bir hat kurulmuş ("kod tüm dünyada aynı tutarlılıkta çalışacak"). pedx'in bugünkü ilkesiyle aynı.
- Etiket olarak **gerçek PED projeleri** kullanılmış.
- Birden çok model karşılaştırılmış, hiperparametre ayarı yapılmış, uçtan uca bir servis kurulmuş, SKA bağlantısı kurulmuş.
- Sınırlılık dürüstçe yazılmış: şehir merkezi PED'in gerçek konumu değil.

**Yöntemsel zayıflıklar (tezde düzeltilmeli):**

| # | Sorun | Etkisi | Düzeltme |
| --- | --- | --- | --- |
| 1 | n = 120, p = 366 | Aşırı öğrenme. Yaklaşık 36 şehirlik bir test kümesinde 0,72 doğruluğun %95 güven aralığı yaklaşık ±0,15 | Tekrarlı ve gruplu çapraz doğrulama; güven aralığı; temel model karşılaştırması |
| 2 | Şehir merkezinin 1 km çevresi, PED'in konumu değil | Özellikler PED alanını değil şehir merkezini anlatıyor | PED Veritabanındaki proje koordinatları; H3 hücreleri |
| 3 | En önemli özellikler: otopark, ATM, bar, sağlık, GSYH | Bunlar kentsellik, refah ve **OSM haritalama yoğunluğu** vekilleri. Model "iyi haritalanmış Batı Avrupa kent merkezi" öğreniyor olabilir | OSM tamlık göstergesiyle kontrol; nüfus ve yoğunlukla normalizasyon |
| 4 | GSYH ülke düzeyinde | Ülke kimliği sızıntısı | Ülke düzeyinde gruplu çapraz doğrulama |
| 5 | Kontrol grubunun seçimi tarif edilmemiş | Seçim yanlılığı | Eşleştirme ölçütleri ön kayıtla; eğilim skoru eşleştirmesi |
| 6 | "PED olmayan" etiketi kitapçıkta olmamak demek | Etiket gürültüsü (PU öğrenme durumu) | Pozitif-etiketsiz (PU) öğrenme ya da açıkça "kitapçıkta yer almama" tanımı |
| 7 | Gini özellik önemi | Sürekli ve çok değerli özelliklere doğru yanlı | Permütasyon önemi ve SHAP |
| 8 | Sorulan soru "bu şehirde PED projesi var mı?" | Bu bir **benimseme ve kurumsal hazırlık** sorusu; **enerji fiziği** sorusu değil | İki soruyu ayırmak (aşağıda) |

**Genel değerlendirme:** Lisans tasarım projesi için hedefi ve mühendisliği ortalamanın üzerinde, zamanının ötesinde bir deneme. Zayıflıkları bu tür ilk çalışmalarda tipik ve hepsi düzeltilebilir. En değerli yanı, bugünkü teze **"Aşama 1"** olarak doğal bir evrim hikâyesi sunması.

## 2. YL tez önerisi: "Investigation of PEDs with GIS and AI" (2025)

**Güçlü yönler:** Vizyon güncel (GeoAI, Geo-LLM, VLM, birleşik model); anahtar kelimeler iyi; açık veri vurgusu tutarlı.

**Zayıflıklar:**
- Dört alt çalışmanın her biri ayrı bir tez büyüklüğünde; **kapsam yüksek lisans için fazla**. Bu, docs/07'deki R8 riskiyle aynı.
- Araştırma soruları ve hipotezler yok; değerlendirme ölçütleri (Geo-LLM ve VLM nasıl doğrulanacak?) tanımsız.
- **Enerji fiziği yok:** PED'in tanımlayıcı ölçütü olan yıllık enerji dengesi hiç hesaplanmıyor; NASA POWER yalnızca bir özellik olarak kullanılıyor.
- Kaynakça yalnızca Breiman (2001). Özet sonda yer alıyor. Yazım hataları var ("lotions", "Positive Energy Regions").

## 3. Bugünkü teze nasıl bağlanıyor?

Önceki çalışma ile pedx **iki farklı ve tamamlayıcı soruya** yanıt veriyor:

| | Aşama 1 (2024): veri güdümlü | Aşama 2 (2026): fizik kenetli (pedx) |
| --- | --- | --- |
| Soru | Hangi kentsel bağlamlar PED projelerine **ev sahipliği yapıyor**? (sosyo-kurumsal hazırlık) | Bir altıgende PED **fiziksel olarak mümkün mü**, ne gerekir? (enerji potansiyeli ve reçete) |
| Etiket ve veri | PED Veritabanındaki projeler; OSM ve açık veri | OSM, GHS-POP, PVGIS, UNSD |
| XAI | SHAP ve permütasyon önemi | Kesin katkılar, sıra aralıkları, Shapley ile graf-XAI, eylem uzayında reçete |
| Birleşim | İki skorun haritada **çakıştırılması**: "fiziksel olarak mümkün ama bağlamı hazır değil" ile "bağlamı hazır ama fiziksel potansiyeli düşük" dörtlü sınıflaması | |

**Öneri:** Aşama 1'in düzeltilmiş hâli (PED Veritabanı koordinatları, H3 özellikleri, gruplu mekânsal çapraz doğrulama, OSM tamlık kontrolü, SHAP) **B1 bildirisine** dönüştürülebilir. Kod ve veri deneyimi zaten olduğu için en hızlı yayın yolu bu. Biçim olarak yüklenen IEEE şablonu kullanılabilir.

## 4. Kaynakçanızdan literatür haritasına eklenenler

- Zhang, X., Penaka, S.R., Giriraj, S., Sánchez, M.N., Civiero, P., Vandevyvere, H. (2021). *Characterizing PED through a preliminary review of 60 existing projects in Europe.* Buildings 11(8), 318. (02'deki #4 ve #56 kayıtlarını düzeltir)
- **Bruck, A., Díaz Ruano, S., Auer, H. (2022).** *One piece of the puzzle towards 100 PEDs across Europe by 2025: An open-source approach to unveil favourable locations of PV-based PEDs from a techno-economic perspective.* Energy 254, 124152. → **pedx'e en yakın çalışma; konumlandırmada mutlaka karşılaştırılmalı**
- Bruck, A., Díaz Ruano, S., Auer, H. (2021). *A critical perspective on positive energy districts in climatically favoured regions.* Energies 14(16), 4864.
- **Schneider, S., Zelger, T., Sengl, D., Baptista, J. (2023).** *A Quantitative PED Definition with Contextual Targets.* Buildings 13(5), 1210. → **mutlak indeksin (K-014) hedef değerleri için doğrudan dayanak**
- Casamassima, L. vd. (2022). *Economic, social, and environmental aspects of PEDs – A review.* WIREs Energy and Environment 11(6), e452.
- Shnapp, S., Paci, D., Bertoldi, P. (2020). *Enabling PEDs across Europe.* JRC, Publications Office of the EU.
- Vandevyvere, H., Ahlers, D., **Alpagut, B.** vd. (2020). *PED Solution Booklet.*
- JPI Urban Europe (2020). *Europe Towards PEDs* (kitapçık) ve *White Paper on PED Reference Framework.*
- Good, N., Ceseña, E.M., Mancarella, P. (2017). *Energy Positivity and Flexibility in Districts.*
- Jepsen, Haut, Jradi (2022). Danimarka'da bir adada PED tasarımı.
- Kobaş, B. vd. (2021). Sürdürülebilir kent için veri erişimi (Türkiye bağlamı).
- Breiman, L. (2001). *Random Forests.* Machine Learning 45, 5–32.
