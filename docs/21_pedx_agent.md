# 21 · pedx-agent: tasarım, literatür dayanağı ve kıyaslama

*Karar: K-054 · Kod: `src/pedx/agent/`, `scripts/agent_benchmark.py` · Arayüz: uygulamada "Ajan" sekmesi · API: `GET /agent?q=...`*

## 1. Ne yapıyor?

Kullanıcı Türkçe ya da İngilizce bir soru sorar. Örnek: "İstanbul'da PED için en uygun 3 sahayı bul, en iyisini açıkla, 70 puana ne gerekir?" Ajan şu sırayla çalışır:
1. Soruyu bir **plana** çevirir.
2. pedx **araçlarını** çağırır.
3. **Yalnızca araçların döndürdüğü sayılarla** yanıt yazar.
4. Her yanıtla birlikte araç izini ve **dayanak literatürü** gösterir.

## 2. Literatürün koddaki karşılığı

| İlke | Kaynak | pedx-agent'teki karşılığı |
|---|---|---|
| Otonom CBS: kendini oluşturan, yürüten, doğrulayan | Li ve Ning (2023) | Veri gölü, kent ızgarası, PED puanı ve doğrulama araç olarak sunuluyor; ajan bunları zincirliyor |
| ReAct: düşünce → eylem → gözlem | Yao vd. (2023) | Her yanıt: "Düşünce", "Plan", araç izi (eylem ve gözlem) |
| Araç kullanan dil modelleri | Schick vd. (2023) | Araçlar JSON-şemalı; OpenAI uyumlu bir LLM (yerel Qwen3) aynı araçları çağırabiliyor |
| Erişimle güçlendirilmiş üretim (RAG) | Lewis vd. (2020) | Literatür haritası (docs/20) bir bilgi tabanı; her araç kendi dayanak kaynaklarını getiriyor |
| Uydurma riski | Ji vd. (2023) | LLM sayı üretmez; yanıt gözlemlerden yazılıyor. Testte, yanıttaki her sayının gözlemlerde bulunduğu doğrulanıyor |
| Uygulanabilirlik alanı | Meyer ve Pebesma (2021) | Doğrulanmış sahalara ağırlıklı en yakın komşu uzaklığı; eşik, bir kent dışarıda bırakılarak hesaplanan uzaklıkların 95. yüzdeliği (0,41). Dışarıdaki sahalar önerilmiyor ve sayıları raporlanıyor (İstanbul'da 667) |
| Arazi kullanımı denetimi | Pesaresi vd. (2024), GHSL BUILT-S NRES | Yapı yüzeyinin %80'inden fazlası konut dışı olan sahalar (havalimanı, liman, sanayi) önerilmiyor |
| Referans sınıfı ve dış bakış | Flyvbjerg (2014) | Puan "gerçek PED'lere benzerlik" olarak sunuluyor; seçimle elverişlilik ayrımı açıkça yazılıyor |
| Kesin açıklama, karşı-olgusal | Lundberg ve Lee (2017); Wachter vd. (2018) | Kesin logit katkıları; hedef puan için kapalı biçim tersine analiz |
| Kentsel işlev ve mekânın ruhu | Jacobs (1961); Oldenburg (1989); Klinenberg (2018) | Hedef göstergeye göre sıralama: üçüncü mekân, sosyal altyapı, kültür, meydan, inşaat (dönüşüm) |

## 3. Mimari

```
soru ──► planlayıcı ──► plan [(araç, argümanlar), …]
          ├─ kural tabanlı (varsayılan; çevrimdışı, tekrarlanabilir)
          └─ LLM (isteğe bağlı: PEDX_LLM_BASE_URL + PEDX_LLM_MODEL; ör. Ollama'da qwen3:8b)
      ──► araçlar (list_areas · find_sites · assess_site · inverse · compare_areas · validation · applicability · literature)
      ──► gözlemler ──► yanıt yazıcı (yalnızca gözlemlerden) + dayanak literatür + uyarılar
```

**Araçların veri kaynağı:**
- atlas: 19 alan; 16 gerçek PED kenti ve 3 Türk pilotu;
- doğrulama sonuçları;
- literatür haritası.

Bütün araçlar tarayıcıda da (artifact) aynı mantıkla çalışıyor.

## 4. Kıyaslama sonuçları (`data/validation/agent_benchmark.json`)

### A. Gerçek PED'i bulma (bir kent dışarıda)

Her gerçek PED kenti için PED puanının ağırlıkları, yönleri ve kalibrasyonu o kent **hiç görülmeden** yeniden öğrenildi. Ardından kentteki bütün yerleşik aday sahalar sıralandı.

| Ölçü | Sonuç |
|---|---|
| Değerlendirilen kent | 13 (3 kentte gerçek saha merkezi aday filtresinde: nüfus < 100) |
| Gerçek sahanın ajan sıralamasındaki ortalama yüzdeliği | **0,71** |
| Gerçek saha ilk %10'da | 5/13 (Leppävaara 14., Rosendal 35.) |
| İlk 5 önerinin gerçek sahaya uzaklığı (medyan) | 2,97 km (rastgele 5 saha: 2,47 km) |

**Okuma:**
1. Ajan gerçek PED sahasını genelde üst sıralara koyuyor.
2. Ama ilk 5 önerisi gerçek sahaya rastgeleden daha yakın değil.
3. Bunun nedeni bir kentte gerçek PED kadar uygun pek çok saha olması ve gerçek seçimin yönetişim, mülkiyet ve fırsatla yapılması.
4. Bu bir başarısızlık değil, tezin bulgusudur: **elverişlilik seçim değildir** (Flyvbjerg 2014; Krangsås vd. 2021). Ajanın rolü "tek doğru sahayı" söylemek değil, elverişli adayların kısa listesini gerekçeleriyle sunmaktır.

### B. Soru anlama (40 Türkçe soru)

Araç, alan ve argüman doğruluğu %100. **Sınırlılık:** sorular planlayıcıyla birlikte yazıldı. Bağımsız sorularla (Hande Hoca ve İBB uzmanları, en az 50 soru) yeniden ölçülecek. LLM planlayıcısı da aynı setle karşılaştırılacak.

## 5. Başarısızlıktan öğrenilen: havalimanı vakası

İlk sürümde İstanbul'un en yüksek puanlı sahası **İstanbul Havalimanı terminali** çıktı. Nedeni zincirleme iki hata:
1. HRSL nüfus haritası terminal binasına 1.757 kişi yazmış.
2. Dev çatılar bu "nüfusu" fazlasıyla dengelemiş.

Uygulanabilirlik alanı denetimi bunu yakalamadı, çünkü kriter uzayında bu saha brownfield PED'lere benziyor. Overture arazi kullanımında havalimanı poligonu yoktu. Önlem olarak GHSL konut dışı yapı payı denetimi eklendi (§2). Bu vaka tezde "veri hatası × model" etkileşiminin örneği olarak anlatılacak.

## 6. Sıradaki adımlar

1. LLM planlayıcısı: yerel Qwen3-8B (Apache-2.0) ile kural tabanlı planlayıcının bağımsız soru setinde karşılaştırılması.
2. Görsel ajan: Qwen2.5-VL ile Mapillary ve Commons fotoğraflarından saha betimi (sayı değil, yalnızca betim).
3. Ajanın çizilen sahayı ve kentsel dönüşüm senaryosunu ("aynı nüfus") araç olarak kullanması.
