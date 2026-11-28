# 25 — Kavramsal çerçeve ve ilk danışman toplantısı için temel

Bu belge çalışmanın *ne olduğunu, ne olmadığını ve neden böyle kurulduğunu* tek yerde sabitler.
Sayılar `data/validation/` altındaki dosyalardan gelir; karar numaraları `docs/05_karar_gunlugu.md` içindedir.

## 1. Tek cümle

> Yalnızca açık ve küresel veriyle, bir şehrin içinde Pozitif Enerji Bölgesi (PED) kurmaya elverişli yerleri
> ayırt edebilir miyiz — ve bunu gerçek PED'lerle sınayabilir miyiz?

## 2. Problem ve boşluk

- PED yer seçimi bugün proje bazında, yerel veriyle ve uzman görüşüyle yapılıyor; şehirler arasında
  karşılaştırılamıyor, veri olmayan şehirde hiç yapılamıyor.
- Literatürdeki ÇKKV (MCDM) çalışmalarının çoğunda ağırlıklar uzman anketinden gelir ve sonuç gerçek bir
  dış ölçütle **doğrulanmaz**.
- Boşluk: (a) küresel açık veriyle çalışan, (b) ağırlıkları veriden öğrenen, (c) gerçek PED'lere karşı
  sınanmış bir uygunluk ölçüsü yok.

## 3. Araştırma soruları ve hipotezler

| | Soru | Hipotez | Sınama | Sonuç |
|---|---|---|---|---|
| AS1 | Fiziksel enerji dengesi (çatı PV ÷ konut elektrik talebi) gerçek PED'leri ayırır mı? | PED'ler kendi şehirlerinin medyanının üstündedir | 16 PED × 30 kontrol, AUC | 16/16 medyan üstü, AUC 0,82 [0,76–0,89]; yoğunluk eşlemeli 0,79 |
| AS2 | Bağlam göstergeleri eklemek ayrımı iyileştirir mi, hangi ağırlıkla? | Basit (eşit) ağırlık, karmaşık şemalardan kötü değildir | Şehir-dışarıda-bırak (LOCO), iç içe LOCO | İç içe LOCO 0,84 [0,75–0,91]; şemalar ve yalnız denge arasında fark yok (p = 0,41–0,82) |
| AS3 | Sonuç mekânsal ölçeğe ve veri kaynağına duyarlı mı? | Denge ölçekten bağımsız, nüfus ataması bağımlıdır | MAUP (blok / r9 / r10 / r11), İstanbul G2 | Denge AUC 0,79–0,83; nüfus payı %93 (blok) ↔ %77 (r10) |
| AS4 | Yöntem eğitim şehirlerinin dışına (İstanbul) taşınabilir mi? | Uygulanabilirlik alanı içinde evet | AOA + yerel veriyle G2 | Çatı PV tüketimin %33–79'u; Yıldırım 2021: %67 |

## 4. Kavramsal model

Üç katman, her biri bir öncekinin üstüne oturur:

1. **Fizik** — enerji dengesi. Bir yer kendi çatısından, kendi konut elektriğinden fazlasını üretebilir mi?
   Tek ölçülebilir, yoruma kapalı büyüklük.
2. **Bağlam** — 31 açık gösterge (yapı, nüfus, erişim, arazi kullanımı, iklim). Şehir içi z-skoruna
   çevrilir: "bu şehrin ortalamasına göre nasıl?"
3. **Karar** — PED skoru. Göstergelerin yönü eğitim şehirlerinden öğrenilir, ağırlıklar eşittir,
   sonuç 0–100'e kalibre edilir.

Sabitlenmesi gereken dört kavram ayrımı:

- **Uygunluk ≠ seçim.** Skor "burada PED kurulmalı" demez; "burası, PED kurulmuş yerlere benziyor ve enerji
  dengesi şu" der. Karar planlamacınındır.
- **Potansiyel ≠ performans.** Ölçtüğümüz üretim potansiyelidir. Gerçek PED'lerin ölçülmüş yıllık dengesi
  elimizde yok.
- **Şehir içi sıralama ≠ şehirler arası karşılaştırma.** z-skorları şehir içidir; Kadıköy'ün 17'si ile
  Lyon'un 85'i mutlak ölçekte kıyaslanmaz.
- **Vaka–kontrol ≠ sınıflandırma.** Kontroller "PED değil" diye kanıtlanmış değildir; yalnızca "PED ilan
  edilmemiş, yerleşik" yerlerdir.

## 5. Veri → yöntem → doğrulama zinciri

```
açık küresel veri ─→ H3 ızgarası ─→ ~28 ha aday diskler ─→ 31 gösterge (şehir içi z)
                                                             │
        gerçek 16 PED + şehir başına 30 kontrol ─────────────┤
                                                             ▼
                              yön öğren (eğitim şehirleri) + eşit ağırlık + Platt
                                                             ▼
                     şehir-dışarıda-bırak → AUC      (ağırlık şeması seçimi: iç içe LOCO)
                                                             ▼
                        duyarlılık: MAUP · sızıntı temizliği · AOA · İstanbul G2
```

## 6. Dürüst değerlendirme

### Sağlam olan
- **Tasarım.** Vaka–kontrol + şehir-dışarıda-bırak, bu alanda nadir görülen bir dış doğrulamadır.
- **Sızıntı dürüstlüğü.** PED'in kendisini ele veren göstergeler çıkarılınca AUC 0,91 → 0,80 düştü ve
  düşük olan raporlandı.
- **Seçim yanlılığına karşı önlem.** Ağırlık şeması iç içe LOCO ile seçildi; 25 kombinasyonun en iyisi
  (0,88) değil, 0,84 raporlanıyor.
- **Fizik çekirdeği yoruma kapalı.** 16/16 sonucu hiçbir ağırlığa bağlı değil.

### Zayıf olan (toplantıda biz söylemeliyiz)
1. **n = 16.** Güven aralıkları geniştir; 0,80 ile 0,88 arasındaki fark istatistiksel olarak ayrılamaz.
   Şemalar arasında "kazanan" ilan edilemez; yalnızca "eşit ağırlık daha kötü değil" denebilir.
2. **Ölçtüğümüz şey kısmen tarihsel yer seçimi (sınandı, K-064).** Skora girmeyen göstergelerden kurulan
   dönüşüm endeksi, yeni gelişim PED'lerini (11) skor kadar iyi buluyor (0,87 ve 0,89); mevcut mahalle
   PED'lerinde (5) yazı-tura (0,55), skor da zayıflıyor (0,72). Enerji dengesi iki grupta aynı (0,83 ve
   0,81). Bileşik skor "PED kurulmuş yerlere benzerlik"tir; savunulan çekirdek enerji dengesidir.
3. **Enerji dengesi dar.** Yalnızca çatı PV ve konut elektriği; ısıtma, ulaşım, depolama, verimlilik yok.
   Talep ülke ortalaması kişi başı değerden gelir. PED tanımının (üretim + verimlilik + esneklik) yalnız
   bir ayağıdır.
4. **Kent içinde enerji dengesi = kişi başına çatı alanı (K-065).** İki ölçüt z-puanında özdeş; bağımsız
   ölçüt sayısı 30. Talep yalnız konut elektriği olduğu için konut dışı yapıların çatısı sayılıyor,
   tüketimi sayılmıyor; bu, dengeyi sanayi ve ticaret alanlarında şişirir. İlk düzeltilecek yöntem
   eksiği budur.
5. **Aktarım.** Eğitim şehirleri dışındaki kent dokularında (İstanbul) skorun anlamı yalnızca
   uygulanabilirlik alanı içinde savunulabilir.
6. **Maliyet ve mülkiyet yok.** Uygulanabilirlik (kim sahip, ne kadar tutar) kapsam dışıdır.
7. **Kapsam genişlemesi.** Ajan, yerel dil modeli, alan sözlüğü, "kentsel yapay zekâ" modülleri çalışıyor
   ama tezin sorusuna cevap vermiyor. İlk toplantıda bunlar soruyu bulandırır.

## 7. Çekirdek ve uzantı sınırı

| Çekirdek (tezin iddiası) | Uzantı (araç, gelecek çalışma) |
|---|---|
| Araştırma sorusu, AS1–AS4 | Soru-cevap ajanı, Qwen planlayıcı |
| Açık veri hattı, H3, 31 gösterge | Alan sözlüğü, gazetteer |
| Vaka–kontrol, LOCO, iç içe LOCO | Kentsel dönüşüm / emlak değerleme kapsamı |
| MAUP, sızıntı, AOA, İstanbul G2 | Web uygulaması, yerel API |
| ÇKKV karşılaştırması (6 yöntem) | CEA / URBANopt / Ladybug bağlantıları |

Öneri: tez bir **geomatik** tezi olarak çerçevelensin — *"açık küresel mekânsal verinin PED uygunluk
analizi için yeterliliği, ölçek duyarlılığı ve doğrulanması"*. AS3 ve AS4 (MAUP, veri kaynağı
karşılaştırması) danışmanın kendi çalışma alanıyla doğrudan örtüşür ve çalışmanın en özgün kısmıdır.
ÇKKV katkısı ikinci eksen, ajan en fazla bir uygulama bölümüdür.

## 8. Danışmandan istenecek kararlar

1. Tezin ana ekseni: mekânsal veri yeterliliği/ölçek (geomatik) mi, karar yöntemi (ÇKKV) mi?
2. Enerji dengesi bu darlıkta kabul edilebilir mi, yoksa ısıtma talebi eklenmeli mi?
3. İstanbul'un rolü: yalnızca doğrulama (G2) mı, yoksa uygulama alanı mı? Yerel veriye erişim mümkün mü?
4. n = 16 yeterli mi; PED veri tabanı genişletilmeli mi (planlama aşamasındaki PED'ler dahil)?
5. Ajan ve yazılım tezde yer alsın mı, ayrı bir bildiri mi olsun?
6. Hedef: tez + bir makale mi; hangi dergi ailesi?

## 9. Toplantı akışı (20 dk)

| dk | Ne | Gösterilecek |
|---|---|---|
| 0–2 | Problem ve tek cümle (§1–2) | — |
| 2–5 | Kavramsal model: fizik → bağlam → karar (§4) | Hikâye, 1.–2. perde |
| 5–10 | AS1 ve AS2 bulguları | 16/16 grafiği, LOCO tablosu |
| 10–13 | AS3–AS4: ölçek ve İstanbul | MAUP tablosu, Caferağa örneği |
| 13–16 | Zayıflıklar (§6) — biz söylüyoruz | — |
| 16–20 | Kararlar (§8) | — |

Ajan yalnızca sorulursa, bir dakika gösterilir.

## 10. Sonraki adımlar

| Durum | İş | Çıktı |
|---|---|---|
| Yapıldı | Dönüşüm alanı tehdidi sınandı (K-064) | `data/validation/transformation_threat.json` |
| Yapıldı | Bootstrap aralıkları, permütasyon testleri, özdeş ölçüt tespiti (K-065) | `data/validation/uncertainty.json` |
| Yapıldı | Tez çerçevesi ve uygulama geomatik eksenine çekildi (K-066) | Hikâye, Tez planı |
| Sırada | Özdeş ölçütü çıkar, atlası 30 ölçütle yeniden kur | Güncel saha puanları |
| Sırada | Konut dışı talebi dengeye ekle (GHSL konut dışı hacim × yoğunluk) | Düzeltilmiş denge, AS1 tekrarı |
| Sırada | PED türünü kaynakla etiketle; PED kümesini büyüt | n > 16, tür ayrımı doğrulanmış |
| Danışman kararı | Isıtma talebi; İstanbul'un rolü; ajanın tezdeki yeri | — |
