# 24 · Sunum anlatısı: konuşma notları, zor sorular, yedek planlar (K-063, K-066)

> Uygulamadaki **Hikâye** sayfası bu belgenin görünen yüzü. Burası yalnız sunanın notu: ne söyleneceği, nereye tıklanacağı, hangi sayının ezberleneceği, hangi soruya ne cevap verileceği. Bütün sayılar dosyalardan doğrulandı (kaynak sütunu). Sunumda başka sayı söyleme.

## 0. Sunum öncesi kontrol listesi (5 dakika)

| | Ne | Nasıl |
|---|---|---|
| 1 | Artifact bağlantısı açılıyor mu? | https://claude.ai/artifact/EyKh7dQLya8MHAK7etDWbB → ilk sayfa **Hikâye** olmalı |
| 2 | Yedek: yerel dosya | `web/pedx_app.html` dosyasını tarayıcıda aç (internet gerekmez; altlık harita gömülü) |
| 3 | Canlı "tıkla → hesapla" gösterilecekse | Kendi bilgisayarında `make demo` → `http://127.0.0.1:8766`. İlk tıklama 1–3 dakika sürer; **sunumda canlı göstermek yerine önceden bir kez çalıştır** (sonuç önbelleğe yazılır) |
| 4 | LLM'i canlı gösterme | Yerel Qwen3-8B soru başına ~1 dakika sürer. Sunumda tarayıcıdaki kural planlayıcı yeter; LLM sonuçları tabloda |
| 5 | Ekran | Tarayıcı yakınlaştırması %100; harita alanı geniş ekranda daha iyi görünür |

## 1. Akış (≈ 20 dakika)

Çerçeve `docs/25`'te: tek soru, dört alt soru. Her adımda tek bir sayı söyle; geri kalanı ekranda. Son dört dakika danışmanın kararlarına ayrılır.

| Adım | Söyle (bir cümle) | Tıkla | Ezberle | Kaynak |
|---|---|---|---|---|
| Soru | "Yalnız açık ve küresel mekânsal veriyle PED'e elverişli yeri ayırt edebilir miyiz, ve bunu gerçek PED'lerle sınayabilir miyiz?" | Tez planını aç | 4 alt soru; 16 PED × 30 kontrol | docs/25 |
| 1 Veri | "Aynı işleme hattı her koordinatta çalışıyor; hiçbir yerel veri yok." | Dünya haritası → bir alan | 32.728 aday saha, ~28 ha | atlas |
| 2 Enerji dengesi (AS1) | "Çatı FV'nin konut elektriğine oranı, 16 gerçek PED'in 16'sını kendi kentinin medyanının üstüne koyuyor." | Lyon Confluence | **16/16; AUC 0,82 [0,76–0,89]** | uncertainty.json |
| 3 Sızıntı | "İlk sonuç 0,91'di. PED'in sonucu olan göstergeleri çıkardım, 0,80'e düştü; düşük olanı raporluyorum." | İstanbul | 0,91 → 0,80 | docs/17, K-050 |
| 4 Ağırlık (AS2) | "Bağlam göstergelerini ekleyip ağırlık şemalarını yarıştırdım. 16 kentle hiçbiri diğerinden, hatta yalnız enerji dengesinden ayrılamıyor; en basitini kullanıyorum." | Kriterler → MCDM tablosu | İç içe 0,84 [0,75–0,91]; p = 0,41–0,82 | nested_loco.json, uncertainty.json |
| 5 Skor neyi öğreniyor | "Bileşik skor kısmen dönüşüm alanını öğreniyor: mevcut mahalle PED'lerinde zayıflıyor. Enerji dengesi iki grupta da aynı." | Kriterler | Denge **0,83 / 0,81**; skor 0,89 / 0,72; dönüşüm endeksi 0,87 / 0,55 | transformation_threat.json |
| 6 Veri miktarı | "Daha çok veri ailesi eklemek sonucu değiştirmiyor; darboğaz etiket sayısı." | Veri ve yöntem | 0,82–0,88 | data_scaling.json |
| 7 Ölçek (AS3) | "Toplam denge her ölçekte 1,625; dengede yaşayan nüfus payı ölçeğe göre %77–93." | Caferağa çok ölçekli | 1,625; %93 / %77 | scales.json, K-046 |
| 8 İstanbul (AS4) | "Model Türkiye'yi hiç görmedi. Açık veriyle çatı FV tüketimin %33–79'u; yerel çalışmada %67." | Caferağa, Kadıköy | Caferağa denge 1,25; OSM −%10,1 | atlas, docs/17 |
| Zayıflıklar | "Dört sınırı ben söyleyeyim: 16 saha; skor kısmen dönüşüm alanı; talep yalnız konut elektriği; maliyet yok." | — | — | docs/25 §6 |
| Kararlar | docs/25 §8'deki altı soru | — | — | docs/25 |

Ajan yalnız sorulursa, bir dakika: "Ekler → Ajan". Sayı: sözlükten sonra yazılan bağımsız 30 soruda %93.

## 2. Zor sorular ve cevaplar

**S1. 16 PED çok az değil mi?**
Evet. Bu yüzden:
- Her PED kendi kentinin 30 yerleşik sahasıyla karşılaştırılıyor ve model test ettiği kenti hiç görmüyor.
- Bütün sonuçlar %95 aralıkla veriliyor: enerji dengesi 0,82 [0,76–0,89].
- Şemalar arasında "kazanan" ilan etmiyorum; 16 kentle ayrılamıyorlar.

İşaret testi: 16'nın 16'sı medyanın üstünde, p = 0,00002. PED kümesini büyütmek sonraki adım.

**S2. Neden eşit ağırlık? Bağlam göstergeleri bir şey katıyor mu?**
Yönler (artı mı eksi mi) gerçek PED'lerden öğreniliyor; büyüklükleri öğrenmek 16 örnekle güvenilir değil. Ağırlık şemasını iç içe doğrulamayla seçtim: AUC 0,84 [0,75–0,91].
- Şemalar birbirinden ayrılamıyor (p = 0,41–0,80).
- Bileşik skor yalnız enerji dengesinden de ayrılamıyor (0,84 ve 0,82; p = 0,82).

Yani dürüst cevap: bağlam göstergelerinin dengeye bir şey kattığını bu veriyle gösteremiyorum. Eşit ağırlığın gerekçesi sadelik (Dawes 1979).

**S3. Bileşik skor tam olarak neyi ölçüyor?**
"PED kurulmuş yerlere benzerlik". Sınadım (K-064): skora girmeyen göstergelerden kurduğum dönüşüm endeksi, yeni gelişim PED'lerini (11) skor kadar iyi buluyor (0,87 ve 0,89); mevcut mahalle PED'lerinde (5) yazı-tura (0,55), skor da 0,72'ye düşüyor. Enerji dengesi iki grupta aynı (0,83 ve 0,81). Bu yüzden iddiam enerji dengesi üzerine; skor ayrı bir sayı olarak yanında duruyor. Sınır: mevcut mahalle grubu 5 saha ve türleri proje tanımlarından ben etiketledim.

**S4. Kontroller PED değil mi, emin misin?**
Hayır, emin değilim. Kontroller "PED olmadığı kanıtlanmış" yerler değil, kentin yerleşik sahaları. Bu, puanın olası bir PED'i kontrol sayıp cezalandırabileceği anlamına geliyor. Etkisi AUC'yi düşürür, şişirmez: muhafazakâr bir tahmin.

**S5. Yerel veri kullanmadın mı? İstanbul'da daha iyi veri var.**
Bilerek. G1 (model) yalnız küresel açık veri; G2 (doğrulama) yerel veri. Böylece aynı model her kentte çalışıyor ve İstanbul'da bağımsız sınanıyor:
- Çatı FV: açık veriyle tüketimin %33–79'u; Yıldırım (2021) %67.
- Bina sayısı: OSM −%10,1, GHSL +%3,6 (Demirel 2025).

EPİAŞ Faz 2'de yalnız doğrulamada kullanılacak.

**S6. OSM/Overture güvenilir mi?**
Demirel (2025) ile İstanbul'da sınandı: bina sayısında OSM %10 eksik. Overture, OSM'ye Microsoft ve Google binalarını ekliyor; GHSL'yle çapraz kontrol yapılıyor. Eksiklik bir kriter olarak da izleniyor ("OSM dışı bina payı").

**S7. Neden H3? Ölçek sonucu değiştirmiyor mu?**
Değiştiriyor; Perde 6 bunu gösteriyor. Toplam denge her ölçekte aynı (1,625), ama dengedeki nüfus payı değişiyor. Bu yüzden karar sabit bir hücrede değil, kullanıcının çizdiği proje sahasında veriliyor. Gerçek PED tanıma 10–92 ha arası saha boyutlarında dayanıklı.

**S8. Haritada saha puanı ile hücre puanı neden farklı? (Caferağa: 67 ve 41)**
- Hücreler, H3 r9 hücresinin merkezindeki ~28 ha'lık diski puanlıyor.
- "Tam noktasında" yazan değer, gerçek proje koordinatını merkez alan diski puanlıyor.

Disk 250 m kayınca bağlam değişiyor; bu, ölçek duyarlılığının (S7) somut bir örneği.

**S9. Tersine analiz gerçekçi mi? Maliyet yok.**
Doğru, şimdilik iki sınırı var:
- Yalnız enerji kaldıraçlarını (çatı kullanımı, modül verimi, talep azaltımı) kapalı biçimde hesaplıyor.
- Maliyet verisi olmadığı için bütçe kısıtı yok.

Eşit ağırlıkla enerji kaldıraçlarının puana etkisi küçüldü: Türkiye pilotlarında hedef 70'e yalnız enerjiyle ulaşılamıyor. Bunu dürüst bir sonuç olarak sunuyorum: puan bağlamı ölçüyor, bağlam da yalnız panelle değişmiyor. Sonraki adım REopt ile bütçeli boyutlandırma (docs/23).

**S10. LLM halüsinasyon yapmaz mı?**
LLM yanıt yazmıyor, yalnız plan kuruyor: hangi araç, hangi argüman. Yanıt araç gözlemlerinden şablonla yazılıyor ve topraklama testi var: yanıttaki her sayı gözlemde bulunmak zorunda. LLM'in kendi hataları da ölçüldü:
- İstenmeden hedef uydurma 7/70'ti; niyet korumasıyla 0'a indi.
- Yer adı hataları için veriden 6.396 adlık bir sözlük kuruldu.

**S11. Bağımsız test seti gerçekten bağımsız mı?**
- Set-1, planlayıcılar çalıştırılmadan önce yazıldı. Sonra sözlüğün hatalarını teşhis etmekte kullanıldığı için artık bağımsız saymıyorum.
- Bu yüzden sözlükten sonra, hiçbir planlayıcı üzerinde çalıştırılmadan önce set-2 yazıldı.
- Set-2'de bulunan iki tutarlılık hatası düzeltildi ve bu açıkça raporlandı (K-058).

**S12. CEA ya da URBANopt varken bu neden gerekli?**
Onlar verilen bir bölgeyi ayrıntılı simüle ediyor; CEA arz sistemini optimize de ediyor. Bir kentte nereye bakılacağını seçmiyorlar ve gerçek PED'lerden öğrenmiyorlar. pedx sahayı seçiyor; seçilen saha CEA veya URBANopt ile ayrıntılandırılabilir. Rakip değil, önceki adım (docs/23).

**S13. Bu bir geomatik tezi mi, yapay zekâ tezi mi?**
Geomatik. Soru açık mekânsal verinin yeterliliği, ölçek duyarlılığı ve doğrulanması. Ajan ve dil modeli tezin eki; yapay zekâ iddiası yok.

**S14. Katkı tam olarak ne?**
1. Açık küresel veriyle hesaplanan PED uygunluğunun gerçek PED'lere karşı, kentler arası doğrulanması.
2. Ölçek (MAUP) ve veri kaynağı duyarlılığının ölçülmesi; İstanbul'da yerel veriyle karşılaştırma.
3. Bileşik skorun neyi öğrendiğinin ayrıştırılması (dönüşüm alanı ve PED türü).

**S15. Ajan gerçek PED'i ilk 5'te bulamıyorsa ne işe yarar?**
Gerçek PED sahası ortalama 0,71 yüzdelikte (13 kentin 5'inde ilk %10'da). İlk 5'in rastgeleden yakın olmaması bir bulgu, başarısızlık değil: bir kentte gerçek PED kadar elverişli pek çok saha var ve seçimi yönetişim yapıyor (Flyvbjerg 2014). Sistem "nereye bakmalı"yı daraltıyor; "hangisi"ni karar vericiye bırakıyor.

**S16. Enerji dengesi neden bu kadar iyi ayırıyor? Bir yapaylık olabilir mi?**
Kent içinde ışınım ve kişi başı talep sabit; denge pratikte kişi başına çatı alanı (iki ölçütün z-puanı özdeş, K-065). İki sınırı var:
- Talep yalnız konut elektriği. Konut dışı yapıların çatısı sayılıyor, tüketimi sayılmıyor; bu dengeyi sanayi ve ticaret alanlarında şişirir.
- Isıtma, ulaşım ve depolama yok.

Konut dışı payı hesaba katınca etki sürüyor (0,75; mevcut mahallelerde 0,83) ama ilk düzelteceğim yöntem eksiği bu.

**S17. Sırada ne var?**
Konut dışı talebi dengeye eklemek; özdeş ölçütü çıkarıp modeli 30 ölçütle yeniden kurmak; PED türünü kaynakla etiketleyip kümeyi büyütmek; İstanbul doğrulamasını derinleştirmek.

## 3. Bir şey ters giderse

| Durum | Yapılacak |
|---|---|
| Artifact açılmıyor ya da yavaş | `web/pedx_app.html` dosyasını yerelde aç; içerik aynı |
| Harita boş görünüyor | Hikâye'deki "Dünya haritasını aç" düğmesini yeniden tıkla; olmazsa sayfayı yenile (alan seçimi sıfırlanır, veri kaybolmaz) |
| "Yerel API bağlı değil" yazısı | Normal: yayımlanan sayfa ziyaretçinin bilgisayarına bağlanamaz. 19 alan sayfada hesaplanıyor; canlı hesap için `make demo` |
| Ajan beklenmedik bir yanıt veriyor | "Plan ve araç izi" bölümünü aç: hangi aracı çağırdığı görünüyor. Bu, şeffaflığın gösterimi olarak kullanılabilir |
| Bir sayı soruluyor ve emin değilsin | "Kaynak dosyasında bakayım": bu belgenin tablosundaki kaynak sütunu |
