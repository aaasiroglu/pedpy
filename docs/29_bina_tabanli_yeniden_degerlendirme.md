# 29 — Bina tabanlı yeniden değerlendirme: üretim − tüketim fazlası olan kentsel alanların tespiti (K-070)

## 1. Yeni çerçeve (kullanıcının tarifi)

> Küresel bina verisinden (taban alanı, yükseklik, panel konulabilir alan) her bina için potansiyel güneş
> üretimini ve tüketimini hesapla; üretim − tüketim farkı pozitif olan kentsel alanları bul. Dünyada bölgesel
> çözünürlükte işaret et; sonunda yapı adası yapı adası bulanık bir bölge tanımla: "burası artı verir; şu bina
> dışarıda kalırsa artı verir". Geniş çatılı, az nüfuslu kamusal yapılar ve çevreleri çekirdek olsun.
> İstanbul'da İBB'nin bina bazlı güneş potansiyeliyle doğrula.

## 2. Elimizdeki bulgular bu çerçeveyi destekliyor

| Bulgu | Kaynak | Yeni çerçeve için anlamı |
|---|---|---|
| Kent içinde enerji dengesi = kişi başına çatı alanı | K-065 | Fazlayı belirleyen şey çatı ile tüketici oranı; tam olarak bina ölçeğinde bir büyüklük |
| Gerçek PED'lerde nüfus ve yoğunluk düşük (d = −0,52), bina sayısı az (−0,87), kişi başı çatı yüksek (+1,47) | K-064 | "Az kişinin yaşadığı geniş çatılı yerler" hipotezi veriyle uyumlu. "Kalabalık yerler öne çıkar" hipotezi uyumlu değil; öne çıkan şey kişi başı mekân sayısı (+0,87), yani az nüfus + çok işlev |
| 31 ölçütlü bileşik skor enerji dengesinden ayrılamıyor (0,84 ve 0,82; p = 0,82) | K-065 | Çok veriyi tek skorda eritmek bir şey katmadı |
| Bileşik skor kısmen dönüşüm alanını öğreniyor; denge öğrenmiyor | K-064 | Savunulan çekirdek fiziktir |
| PED'in adını taşıdığı mahalle proje sınırı değil (490 ha ↔ 4 ha); ortanca PED 6 ha | K-068, K-069 | Sınır yapı adası kümesi ölçeğinde aranmalı |
| Veritabanında sınır türü var, geometrisi yok | K-069 | Sınırı üretmek özgün katkı |

## 3. Çözülmesi gereken üç sorun

### 3.1 Tüketim tarafı eksik (en kritik)

Şu an talep = nüfus × ülke ortalaması kişi başı konut elektriği. Konut dışı yapının çatısı sayılıyor, tüketimi
sıfır. Stadyum, okul, AVM, depo bu yüzden **yapay olarak** çok pozitif görünür. "Kamusal yapılar çekirdek olur"
iddiası bu düzeltilmeden sınanamaz.

Gereken: bina başına talep = kat alanı × kullanım türüne göre yoğunluk.
- Kat alanı: taban alanı × kat sayısı (yükseklikten).
- Kullanım türü: Overture bina sınıfı ve mekânlar, GHSL konut dışı hacim, arazi kullanımı.
- Yoğunluk: ülke düzeyinde hizmet sektörü elektriği (UNSD'de var) konut dışı kat alanına dağıtılır;
  konut elektriği nüfusa. İkisi de ülke toplamına kapanır, yani uydurma katsayı gerekmez.

### 3.2 "55 veriyi bir potada eritip SHAP ile çözüme ulaşmak"

Bunu denedik ve çalışmadı: etiket sayısı (16; envanterle ~140) 55 değişkenli bir modeli taşımaz, sonuç fizikten
ayrılamadı. Önerim sırayı tersine çevirmek:

1. **Hedef değişkeni fizik üretir, etiket değil.** Her yapı adası için fazla (üretim − tüketim) hesaplanır.
   Bu, dünyadaki bütün yapı adalarında vardır: milyonlarca gözlem, etiket kıtlığı yok.
2. **Açıklanabilir yapay zekâ bu fazlayı açıklar.** "Hangi kent dokusu fazla veriyor?" sorusu için fazlayı
   bağlam değişkenleriyle (yoğunluk, kullanım karışımı, bina yaşı, arazi örtüsü, iklim) modelle ve SHAP ile
   oku. Burada SHAP meşrudur, çünkü örnek sayısı çok büyük.
3. **Gerçek PED'ler yalnız doğrulamada kullanılır.** Fazla veren yapı adası kümeleri gerçek PED sahalarıyla
   örtüşüyor mu?

Böylece 50–55 veri boşa gitmez: bir kısmı fiziği iyileştirir (yükseklik, kullanım türü, gölge), geri kalanı
açıklayıcı değişken olur. Ama hiçbiri "PED skoru"nun içine ağırlıkla girmez.

### 3.3 Bina verisi

| Veri | Ne veriyor | Lisans | Not |
|---|---|---|---|
| Overture buildings | Taban alanı, kısmen yükseklik/kat, sınıf | ODbL 1.0 | Mevcut; kat bilgisi kapsamı düşük |
| TUM GlobalBuildingAtlas (Zhu vd. 2025, ESSD) | 2,75 milyar taban alanı, %97'sinde yükseklik, LoD1 | Kaynaklar çelişkili: makale CC BY 4.0, veri sayfaları CC BY-NC 4.0 | Akademik kullanım için uygun görünüyor; lisans mediaTUM kaydından teyit edilmeli |
| Google Open Buildings 2.5D | Yükseklik rasterı | CC BY 4.0 | Küresel Güney ağırlıklı; Avrupa kapsamı sınırlı |
| GHSL BUILT-H, BUILT-V | 100 m yükseklik ve hacim | CC BY 4.0 | Mevcut; bina değil piksel |
| Kent LoD2 modelleri (Berlin, Bavyera, Hamburg, Hollanda 3DBAG) | Çatı geometrisi | Açık | Yalnız doğrulama: düz çatı varsayımının hatası |
| İBB bina bazlı güneş potansiyeli | Bina başına üretim | Yerel | Yalnız doğrulama (G2); erişim gerekiyor |

## 4. "Bulanık PED bölgesi"nin tanımı

Bina *i* için fazla: sᵢ = üretimᵢ − tüketimᵢ. Parametreler aralıklıdır (çatı kullanım katsayısı 0,26–0,50,
modül verimi, talep yoğunluğu), dolayısıyla sᵢ bir aralıktır.

- **Çekirdek (çapa) bina:** sᵢ güvenle pozitif ve büyük (stadyum, okul, depo, hal).
- **Bölge:** çapadan başlayıp komşu yapı adalarını ekleyerek büyüyen bitişik küme; toplam fazla ≥ 0 kaldıkça büyür.
- **Bulanık üyelik:** bir yapı adasının kümede olma derecesi = parametre aralığı içinde kümenin o yapı adası
  dahilken pozitif kalma olasılığı. 1'e yakın: kesin içeride; 0'a yakın: içeri alınırsa bölge eksiye düşer.
- **"Şu bina girmezse artı olur":** kümeyi eksiye düşüren, sᵢ değeri en negatif binaların listesi. Toplam
  toplanabilir olduğu için her binanın katkısı doğrudan sᵢ'dir; ayrıca bir açıklama yöntemine gerek kalmaz.
- **Çevreye verilebilecek enerji:** kümenin toplam fazlası; elektrikli araç şarjı ya da şebeke için üst sınır.

Bu tanım danışmanın birinci sorusuna (PED sınırı nasıl tanımlanır) doğrudan cevaptır ve K-067'deki AS1 ile aynıdır.

## 5. Güncellenmiş araştırma soruları

| | Soru |
|---|---|
| AS1 | Açık küresel bina verisinden bina ve yapı adası düzeyinde üretim − tüketim fazlası ne doğrulukta hesaplanır? (İstanbul'da İBB verisiyle; LoD2 kentlerinde çatı geometrisiyle) |
| AS2 | Fazla veren bitişik yapı adası kümeleri (bulanık PED bölgeleri) nasıl tanımlanır ve hangi yapılar çapa olur? |
| AS3 | Bu bölgeler gerçek PED sahalarıyla (envanter, ~140 saha) örtüşüyor mu? |
| AS4 | Hangi kent dokusu fazla verir? (fazlanın bağlam değişkenleriyle açıklanması; ekonomi kaldıraçlı sahalar ayrı katman) |

## 6. Ne kalıyor, ne değişiyor

| Bileşen | Durum |
|---|---|
| Veri hattı, H3 küresel tarama, yapı adası üretimi | Kalıyor |
| Enerji dengesi (fizik çekirdeği) | Kalıyor; bina ölçeğine iniyor, tüketim tarafı genişliyor |
| Vaka–kontrol, LOCO, belirsizlik aralıkları, MAUP | Kalıyor; AS3'ün yöntemi |
| Küresel PED envanteri | Kalıyor; doğrulama kümesi |
| 31 ölçütlü bileşik PED skoru | Skor olarak bırakılıyor; ölçütler AS4'te açıklayıcı değişken |
| Ajan, dil modeli, sözlük | Ek |

## 7. Adımlar

1. Bina başına tüketim: kat alanı × kullanım türü; ülke toplamlarına kapanan dağıtım.
2. Caferağa pilotu: bina bina fazla, çapa binalar, bulanık bölge haritası.
3. İstanbul doğrulaması: İBB bina bazlı güneş potansiyeli (veri erişimi danışmandan).
4. Aynı yöntemi alanı bilinen PED sahalarına uygula; örtüşmeyi ölç.
5. Yükseklik kaynağı karşılaştırması: Overture, GlobalBuildingAtlas, GHSL.
6. Küresel tarama ve AS4.
