# 24 · Sunum anlatısı: konuşma notları, zor sorular, yedek planlar (K-063)

> Uygulamadaki **Hikâye** sayfası bu belgenin görünen yüzü. Burası yalnız sunanın notu: ne söyleneceği, nereye tıklanacağı, hangi sayının ezberleneceği, hangi soruya ne cevap verileceği. Bütün sayılar dosyalardan doğrulandı (kaynak sütunu). Sunumda başka sayı söyleme.

## 0. Sunum öncesi kontrol listesi (5 dakika)

| | Ne | Nasıl |
|---|---|---|
| 1 | Artifact bağlantısı açılıyor mu? | https://claude.ai/artifact/EyKh7dQLya8MHAK7etDWbB → ilk sayfa **Hikâye** olmalı |
| 2 | Yedek: yerel dosya | `web/pedx_app.html` dosyasını tarayıcıda aç (internet gerekmez; altlık harita gömülü) |
| 3 | Canlı "tıkla → hesapla" gösterilecekse | Kendi bilgisayarında `make demo` → `http://127.0.0.1:8766`. İlk tıklama 1–3 dakika sürer; **sunumda canlı göstermek yerine önceden bir kez çalıştır** (sonuç önbelleğe yazılır) |
| 4 | LLM'i canlı gösterme | Yerel Qwen3-8B soru başına ~1 dakika sürer. Sunumda tarayıcıdaki kural planlayıcı yeter; LLM sonuçları tabloda |
| 5 | Ekran | Tarayıcı yakınlaştırması %100; harita alanı geniş ekranda daha iyi görünür |

## 1. Akış (≈ 15 dakika), perde perde

Her perdede tek bir sayı söyle; geri kalanı ekranda.

| Perde | Söyle (bir cümle) | Tıkla | Ezberle | Kaynak |
|---|---|---|---|---|
| Açılış | "Laplace'ın cini her şeyi bilseydi her kararı kesin verirdi. Ben o cinin küçük ve dürüst bir kardeşini kurdum." | — | — | docs/00 |
| 0 Soru | "Sonsuz veriyle kesin karar mümkün değil. Ama sınırlı bir alanda, doğrulanmış ve sınırını bilen bir zekâ mümkün." | Kapsamı göster | 19 alan, 0 yerel veri | docs/22 |
| 1 Veri | "Aynı kod dünyanın her koordinatında çalışıyor, yalnız açık verilerle." | Dünya haritasını aç → bir alana tıkla | 55 veri seti, 32.728 aday saha | catalog.py, atlas |
| 2 Fizik | "Yalnız yıllık enerji dengesi, 16 gerçek PED'in 16'sını kendi kentinin medyanının üstüne koyuyor." | Lyon Confluence (skor 85, kent içi %95) | **16/16, AUC 0,82** | ped_validation_summary.json |
| 3 Dürüstlük | "İlk sonuç 0,91'di. PED'in sonucu olan özellikleri çıkardım, 0,80'e düştü. Savunulabilir sayı bu." | İstanbul → havalimanı elenmiş, AoA dışı sahalar önerilmiyor | 0,91 → 0,80 | docs/17, K-050 |
| 4 Yöneylem | "Klasik MCDM ile öğrenilmiş ağırlığı aynı protokolde yarıştırdım. Ağırlık seçimini de çapraz doğrulamanın içine aldım: eşit ağırlık kazandı, çekirdeğe aldım." | Kriterler → MCDM tablosu | **İç içe AUC 0,84**, 9/16 | nested_loco.json, mcdm_benchmark.json |
| 5 Veri miktarı | "Daha çok veri kesinlik getirmiyor. Darboğaz veri değil, etiket: dünyada 16 iyi belgelenmiş PED." | Veri ve yöntem | 0,82–0,88 | data_scaling.json |
| 6 Ölçek | "Toplam denge her ölçekte 1,625. Ama 'dengede yaşayan nüfus' ölçeğe göre %77–93 arasında değişiyor. Bu yüzden karar çizilen saha üzerinden veriliyor." | Caferağa çok ölçekli → yapı adası ve r11 | 1,625 | scales.json, K-046 |
| 7 Türkiye | "Model Türkiye'yi eğitimde hiç görmedi. Caferağa yerinde dengede ama PED bağlamına benzerliği orta." | Caferağa, sonra Kadıköy | 41/100; çatı FV %33–79 (Yıldırım 2021: %67) | atlas, docs/17 |
| 8 Ajan | "Ajan sayı uydurmaz: her sayı bir araçtan gelir, her yanıtın altında literatür vardır." | Ajana sor: Moda | 8B ReAct **%93**; uydurulan hedef 7 → 0 | agent_react_benchmark.json |
| Kapanış | "Biliyoruz: açık veri gerçek PED'leri tanıyor. Bilmiyoruz: hangi elverişli sahanın seçileceğini; o yönetişim." | — | 0,71 yüzdelik, ama ilk 5 rastgeleden yakın değil | agent_benchmark.json |

## 2. Zor sorular ve cevaplar

**S1. 16 PED çok az değil mi?**
Evet, bu yüzden üç önlem var:
- Kent içi kontrollerle kurulan vaka–kontrol tasarımı: her PED, kendi kentinin 30 yerleşik sahasıyla karşılaştırılıyor; 16 × 30 karşılaştırma.
- Kentler arası dışarıda bırakma: model test ettiği kenti hiç görmüyor.
- İşaret testi: 16'nın 16'sı medyanın üstünde, p = 0,00002.

Az örnek ayrıca eşit ağırlığı seçmemizin gerekçesi (Dawes 1979). Etiket sayısı tezin açıkça söylenen sınırı (Perde 5).

**S2. Neden eşit ağırlık? Öğrenme işe yaramadı mı?**
Öğrenme yönleri belirliyor: 31 kriterin her birinin artı mı eksi mi etkilediği gerçek PED'lerden öğreniliyor. Büyüklükleri öğrenmek ise 16 örnekle güvenilir değil. Ağırlık şemasını iç içe LOCO ile seçtim:
- Eşit ağırlık 16 katlamanın 9'unda seçildi, kanıt ağırlıkları hiçbirinde.
- İç içe AUC 0,84; önceki model 0,80.
- Fark anlamlı değil (p = 0,31).

Yani "daha iyi" değil, "en az o kadar iyi ve daha basit" diyorum.

**S3. Enerji dengesi puanın yalnız 1/31'i mi? Bu nasıl bir PED puanı?**
Puan "PED bağlamına benzerlik" ölçüyor. Fiziksel denge (çatı FV ≥ konut tüketimi) ayrı ve zorunlu bir koşul olarak her sahada yanında raporlanıyor. Ajan "yalnız dengede olanlar" filtresini uygulayabiliyor. İkisini tek sayıya sıkıştırmak bilgiyi saklardı.

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

**S13. "AGI" ya da "Geospatial AGI" abartı değil mi?**
Tezde AGI iddiası yok. Laplace'ın cini çıkış sorusu. Cevap şu: genel değil, alanı sınırlı ve doğrulanmış bir zekâ. "Otonom CBS" (Li ve Ning 2023) çizgisinde, kendi sınırını bilen bir planlama ajanı.

**S14. Q1 katkısı tam olarak ne?**
1. Gerçek PED'lerden öğrenen ve kentler arası doğrulanan, küresel açık veriyle çalışan saha uygunluğu.
2. Öğrenilmiş ve klasik MCDM ağırlıklandırmasının, gerçek etiketle ve iç içe doğrulamayla karşılaştırılması (yöneylem araştırması).
3. Sayı uydurmayan, kendi hatalarını ölçen bir planlama ajanı (yapay zekâ mühendisliği).

**S15. Ajan gerçek PED'i ilk 5'te bulamıyorsa ne işe yarar?**
Gerçek PED sahası ortalama 0,71 yüzdelikte (13 kentin 5'inde ilk %10'da). İlk 5'in rastgeleden yakın olmaması bir bulgu, başarısızlık değil: bir kentte gerçek PED kadar elverişli pek çok saha var ve seçimi yönetişim yapıyor (Flyvbjerg 2014). Sistem "nereye bakmalı"yı daraltıyor; "hangisi"ni karar vericiye bırakıyor.

## 3. Bir şey ters giderse

| Durum | Yapılacak |
|---|---|
| Artifact açılmıyor ya da yavaş | `web/pedx_app.html` dosyasını yerelde aç; içerik aynı |
| Harita boş görünüyor | Hikâye'deki "Dünya haritasını aç" düğmesini yeniden tıkla; olmazsa sayfayı yenile (alan seçimi sıfırlanır, veri kaybolmaz) |
| "Yerel API bağlı değil" yazısı | Normal: yayımlanan sayfa ziyaretçinin bilgisayarına bağlanamaz. 19 alan sayfada hesaplanıyor; canlı hesap için `make demo` |
| Ajan beklenmedik bir yanıt veriyor | "Plan ve araç izi" bölümünü aç: hangi aracı çağırdığı görünüyor. Bu, şeffaflığın gösterimi olarak kullanılabilir |
| Bir sayı soruluyor ve emin değilsin | "Kaynak dosyasında bakayım": bu belgenin tablosundaki kaynak sütunu |
