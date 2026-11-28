# İlerleme raporu — 25 Kasım 2026

**Tez:** Açık küresel veriyle pozitif enerji bölgelerinin (PED) tespiti ve sınırlarının tanımlanması
**Hazırlayan:** Abdurrahim Arif Aşıroğlu · **Danışman:** Prof. Dr. Hande Demirel

## 1. Özet

1. **Sony CSL 15 dakikalık şehir çerçevesi incelendi.** Yöntemi (altıgen ızgara, nüfus ağırlıklı erişim
   ölçüsü, eşitsizlik, yeniden yerleştirme algoritması) PED problemine birebir aktarılabiliyor. Aktarım
   tablosu §2.3'te.
2. **Dünyadaki PED sahaları toplandı.** İki ana kaynak ayrıştırıldı: PED Booklet (61 proje) ve PED
   veritabanı (114 saha, 24 ülke). Avrupa dışında 12 aday kaydedildi. Birleşik envanter yaklaşık 140 saha.
3. **Ana boşluk doğrulandı: hiçbir kaynakta PED sınırının geometrisi yok.** Veritabanı yalnız sınırın
   türünü (coğrafi / işlevsel / sanal) ve tek bir nokta tutuyor.
4. **Çerçeve bina tabanlı hale getirildi:** her bina için üretim − tüketim fazlası; fazla veren bitişik
   yapı adası kümesi = bulanık PED bölgesi; geniş çatılı, az nüfuslu yapılar çapa.

## 2. Sony CSL: "A universal framework for inclusive 15-minute cities"

Bruno, Melo, Campanelli, Loreto (2024), *Nature Cities* 1, 633–641. Açık platform: whatif.sonycsl.it/15mincity.

### 2.1 Yöntem ve kriterler

| Adım | Sony CSL'in yaptığı |
|---|---|
| Kent sınırı | OECD çekirdek kent sınırları; yoksa GHSL kentsel merkez |
| Hizmet noktaları | OpenStreetMap; yalnız insanlara hizmet veren noktalar (ağaç, bina gibi nesneler atılır) |
| Hizmet kategorileri (9) | Açık hava etkinlikleri, eğitim, alışveriş/ihtiyaç, yeme-içme, ulaşım, kültür, spor, hizmetler, sağlık |
| Nüfus | WorldPop, 100 m ızgara, BM kent nüfusuna göre düzeltilmiş |
| Yol süresi | OSRM (OSM yol ağı üzerinde), yürüyüş ve bisiklet |
| Mekânsal birim | Kenarı 200 m olan düzenli altıgen (~10,4 ha); yakınında hizmet olmayan altıgenler çıkarılır |
| Kategori erişimi | Her altıgen ve kategori için en yakın **20** noktaya ortalama süre |
| Yakınlık Süresi (PT) | Altıgende 9 kategorinin ortalaması |
| Kent ölçüsü | PT'nin nüfus ağırlıklı ortalaması |
| F15 | PT ≤ 15 dk olan altıgenlerde yaşayan nüfus yüzdesi |
| Eşitsizlik | Kişi başı PT üzerinden Gini katsayısı |
| Yeniden yerleştirme | Kişi başı hizmet sayısını kent içinde eşitlemek: kapasite = nüfus ÷ hizmet sayısı; boş kentten başlayıp her adımda karşılanmamış talebin en yüksek olduğu altıgene hizmet koyar, 15 dk içindeki talepten kapasite kadar düşer |
| Çıktılar | Yer değiştirmesi gereken hizmet oranı; nüfusun %90'ının 15 dakikalık koşulda olması için gereken hizmet/1000 kişi |
| Kapsam | 50'den fazla kent ayrıntılı; platform yaklaşık 10.000 kent |

### 2.2 Yazarların kendi belirttiği sınırlar

- OSM tamlığı kente göre değişiyor; kategoriler yanlış ya da yinelenmiş olabiliyor.
- Yaya altyapısı OSM'de var gibi görünse de gerçekte yürünebilir olmayabilir.
- Kategoriler keyfi ve hepsi eşit ağırlıkta; "en yakın 20 nokta" seçimi de keyfi.
- Kent sınırının tanımı sonucu etkileyebilir (nüfus ağırlıklandırma bunu azaltıyor).

İzleyen çalışma (Hill, Bruno, Melo, Takeuchi, Loreto 2024, arXiv 2411.12335, "Cities beyond proximity"):
yalnız mesafeye bakmanın yetmediğini, hizmet noktalarına **değer** öznitelikleri eklenmesi gerektiğini
öneriyor: dağılım ve çeşitlilik, doku ve yapı adası boyutu, mülkiyet, konum, erişilebilirlik, uyarlanabilirlik,
açık olma saatleri, sermaye maliyeti, giriş ücreti; ölçülmesi zor olanlar: hizmet kalitesi, algı, vazgeçilmezlik.

### 2.3 PED problemine aktarım (önerim)

| Sony CSL | PED karşılığı |
|---|---|
| Hizmet noktası (POI) | Bina: çatısıyla üretici, kullanımıyla tüketici |
| 9 hizmet kategorisi | Bina kullanım sınıfları (konut, kamu, eğitim, spor, ticaret, sanayi/depo) |
| Altıgen PT (erişim süresi) | Yapı adası ya da altıgen başına **enerji fazlası** (üretim − tüketim) |
| Kent PT (nüfus ağırlıklı) | Kent fazlası, kişi başına |
| F15 | **F+**: fazla veren bölgelerde yaşayan nüfus payı. Bu ölçüyü Caferağa'da zaten hesapladık: yapı adası ölçeğinde %93, H3 r10'da %77 |
| Gini | Fazlanın kent içindeki dağılımının eşitsizliği |
| Kapasite = nüfus ÷ hizmet | Çapa binanın fazlasının besleyebileceği komşu tüketim |
| Yeniden yerleştirme algoritması | Bölge büyütme: çapa binadan başlayıp komşu yapı adalarını ekleme; toplam fazla ≥ 0 kaldıkça büyür → bulanık PED sınırı |
| %90 için gereken hizmet/1000 kişi | F+ hedefi için gereken çatı kullanımı ya da kurulu güç |
| 200 m kenarlı altıgen (~10,4 ha) | H3 r9 (~10,5 ha): aynı ölçek; küresel tarama birimi. Karar ve sınır birimi yapı adası |
| Değer katmanı (Hill vd.) | Ekonomi katmanı: mülkiyet, finansman, maliyet (PED veritabanında bu alanlar var) |

Bu aktarımla tez, Sony CSL'in "her kent 15 dakikalık olabilir mi?" sorusunun enerji karşılığını sorar:
"her kentte pozitif enerji bölgesi nerede kurulabilir, sınırı nerede biter?"

## 3. Dünyadaki PED sahaları: mevcut çalışmalar ve yaptıklarımız

### 3.1 Mevcut kaynaklar

| Kaynak | İçerik | Ne yaptık |
|---|---|---|
| PED Booklet, Şubat 2020 (JPI Urban Europe, Gollner vd.) | 61 proje: 29 PED, 32 "PED'e doğru"; 19 ülke | Tamamı tabloya çevrildi: durum, yapı türü, büyüklük, arazi kullanımı, finansman |
| PED veritabanı (COST PED-EU-NET, IEA EBC Annex 83, JPI UE/DUT) | 114 saha, 24 ülke (Annex 83 raporu, Mart 2025: 110 PED, 35 proje) | Tamamı indirildi: sınıf, aşama, sınır türü, alan, mülkiyet, finansman, koordinat |
| IEA EBC Annex 83 raporları | Tanım çerçevesi, yöntemler, yönetişim, gösterim vakaları | Avrupa dışı vakalar çıkarıldı (Kanada, Japonya) |
| Avrupa dışı kaynaklar | ABD Sıfır Enerji Bölgeleri programı, Japonya pilot alanları, Çin sıfıra yakın karbon toplulukları | 12 aday kaydedildi; henüz doğrulanmadı |

### 3.2 Envanterden çıkan bulgular

- **Sınıf (veritabanı):** 38 PED vaka çalışması, 44 PED ile ilgili vaka, 18 PED laboratuvarı, 8 karma, 6 sınıfsız.
- **Aşama:** 45 planlama, 27 uygulama, 18 işletmede, 18 tamamlandı.
- **Türkiye'den 4 saha:** Kadıköy Caferağa, Özyeğin Üniversitesi kampüsü, Ankara Çamlık, İzmir Karşıyaka.
- **Sınır türü** (79 saha): 52 coğrafi, 14 işlevsel, 9 sanal, 4 diğer. Geometri hiçbirinde yok.
- **Alan** (59 saha): ortanca 6,2 ha; yarısı 2,9–72,5 ha arasında. Bu ölçek Sony CSL altıgeniyle ve H3 r9 ile aynı.
- **Finansman** (81 saha): en sık AB araştırma fonu (38); 27 sahada özel finansman, 19'unda gayrimenkul.
- **Veri kalitesi:** 65 kayıtta enlem ve boylam yer değiştirmişti (düzeltildi), 7 kayıtta koordinat yok.
- **PED'in adını taşıdığı mahalle proje sınırı değil:** Kaukovainio (Oulu) OSM'de 490 ha, proje 4 ha;
  Pietralata (Roma) 587 ha, proje 7 ha. Sınır, mahalle adından değil proje belgesinden ve yapı adalarından çıkarılmalı.

### 3.3 Avrupa dışı ve "kendine PED demeyen" adaylar

| Ülke | Aday | Not |
|---|---|---|
| Kanada | West 5 / EVE Park (London, Ontario) | 28 ha, net sıfır hedefi; geliştirici ile dağıtım şirketinin kurduğu mikro-kamu hizmeti |
| Kanada | Drake Landing | Annex 83 sunumunda net sıfır vakası |
| Japonya | Ishikari, Higashi-Matsushima, Kitakyushu | Belediye pilot alanları; yerel ekonomiyi canlandırma açık hedef |
| Japonya | 74 pilot alan (ulusal program), Fujisawa SST | Saha listesi alınacak |
| ABD | Denver (Peña Station NEXT, National Western Center), FortZED, UC Davis West Village | Sıfır enerji bölgesi çalışmaları |
| Çin | Shenzhen sıfıra yakın karbon toplulukları | Bölge ölçeğindekiler seçilecek |

## 4. Güncellenmiş araştırma soruları

| | Soru |
|---|---|
| AS1 | Açık küresel bina verisinden bina ve yapı adası düzeyinde üretim − tüketim fazlası ne doğrulukta hesaplanır? (İstanbul'da İBB bina bazlı güneş potansiyeliyle doğrulama) |
| AS2 | Fazla veren bitişik yapı adası kümeleri (bulanık PED bölgeleri) nasıl tanımlanır; hangi yapılar çapa olur? |
| AS3 | Bu bölgeler gerçek PED sahalarıyla (~140 saha) örtüşüyor mu? |
| AS4 | Hangi kent dokusu fazla verir? Ekonomiyi kaldıraç olarak kullanan sahalar farklı mı? |

## 5. Sonraki adımlar

| Ne zaman | İş |
|---|---|
| Sonraki 2–3 gün | Booklet ile veritabanını tek tabloda birleştirmek; yinelenenleri çözmek |
| Sonraki 2–3 gün | Bina başına tüketim: kat alanı × kullanım türü (konut dışı yapıların tüketimi şu an sıfır sayılıyor; çapa iddiası bundan önce sınanamaz) |
| 1–2 hafta | Caferağa pilotu: bina bina fazla, çapa binalar, bulanık bölge haritası; F+ ve Gini |
| 1–2 hafta | Alanı bilinen PED sahalarında sınırları proje belgelerinden sayısallaştırmak |
| Sonra | İBB verisiyle bina bazlı doğrulama; küresel tarama |

## 6. Görüşünüzü istediğim konular

1. **İBB bina bazlı güneş potansiyeli verisi:** doğrulama için erişim mümkün mü?
2. **Envanter kapsamı:** PED laboratuvarları (18) ve tek binalık kayıtlar dahil edilsin mi?
3. **Referans sınır:** proje belgesindeki harita yeterli mi, proje ekibinden teyit gerekir mi?
4. **Ekonomi kaldıracı:** ölçüt olarak finansman türü, mülkiyet ya da iş modeli mi kullanılsın?
5. **Sony CSL aktarımı (§2.3):** bu çerçeve tezin ana yöntemi olarak uygun mu?

## Kaynaklar

- Bruno, M., Melo, H. P. M., Campanelli, B., Loreto, V. (2024). A universal framework for inclusive 15-minute cities. *Nature Cities* 1, 633–641. arXiv:2408.03794
- Hill, D., Bruno, M., Melo, H. P. M., Takeuchi, Y., Loreto, V. (2024). Cities beyond proximity. arXiv:2411.12335
- Gollner, C. vd. (2020). Europe towards Positive Energy Districts, first update. JPI Urban Europe.
- PED veritabanı: peddatabase.dutpartnership.eu (COST PED-EU-NET, IEA EBC Annex 83, JPI UE/DUT)
- IEA EBC Annex 83, Deliverable 4: Demo cases on positive energy districts; "Lessons learned from analysing PED case studies"
- Zhu, X. X. vd. (2025). GlobalBuildingAtlas. *Earth System Science Data* 17, 6647.

Ayrıntılı dosyalar: `docs/28` (envanter), `docs/29` (bina tabanlı çerçeve), `data/inventory/`.
