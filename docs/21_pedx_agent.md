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
| Arazi kullanımı denetimi | OSM (havalimanı, sanayi, liman, askeri); yedek: Overture havalimanı kümeleri | Alanının %50'sinden fazlası özel arazide olan sahalar önerilmiyor; GHSL NRES bu iş için yetersiz kaldı |
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

### C. LLM planlayıcı: Qwen3 (yerel, CPU) ile kural tabanlı planlayıcı (K-055)

**Kurulum:**
- Qwen'in resmî GGUF modelleri: Qwen3-4B ve Qwen3-8B, Q4_K_M nicemleme, Apache-2.0.
- llama.cpp (llama-cpp-python 0.3.36), 4 CPU çekirdeği, GPU yok.
- İstem Qwen3/Hermes araç çağırma biçiminde. Alan kataloğu ve gösterge sözlüğü bağlam olarak veriliyor; sayı verilmiyor.
- Sıcaklık 0, düşünme kapalı (`/no_think`).
- LLM yalnızca planı üretiyor. Şema koruması uydurulan araçları ve argümanları atıyor; yanıt gözlemlerden yazılıyor.

**Plan onarımı (deterministik):** "@best" kullanan bir adımdan önce aynı alanda `find_sites` yoksa ekleniyor; "best" yazımı "@best" olarak düzeltiliyor. Ham ve onarımlı sonuçlar aynı LLM çıktısından ölçüldü.

**Soru setleri:**
- **Geliştirme (40):** kural tabanlı planlayıcıyla birlikte yazıldı.
- **Bağımsız (30):** önceden yazıldı ve kural tabanlı planlayıcıyı ayarlamak için kullanılmadı. Türkçe ve İngilizce, dolaylı ifadeler içeriyor ("Moda", "kahvehane", "metro ve otobüs").

| Planlayıcı | Geliştirme: tam doğru | Bağımsız: tam doğru | Bağımsız: araç / alan / argüman | Soru başına süre |
|---|---|---|---|---|
| Kural tabanlı | **%100** | %73 | %87 / %93 / %80 | ~0 s |
| Qwen3-4B | %78 | %83 | %93 / %93 / %97 | 5,4 s |
| **Qwen3-4B + plan onarımı** | %83 | **%87** | %97 / %93 / %97 | 5,4 s |
| Qwen3-8B | %85 | %77 | %83 / %87 / %90 | 8,3 s |
| Qwen3-8B + plan onarımı | **%90** | %83 | %90 / %87 / %90 | 8,3 s |

**Okuma:**
1. **Genelleme:** Kurallar yazıldıkları sorularda kusursuz, bağımsız sorularda %73'e düşüyor. Qwen3-4B bağımsız sette %87'ye çıkıyor; LLM'in katkısı ifade çeşitliliğine dayanıklılık.
2. **Büyük model her zaman daha iyi değil:** 8B bağımsız sette 4B'den kötü. 8B sık sık önce `list_areas` çağırıyor; "önce kontrol et" davranışı tek seferlik plan-ve-uygula döngüsünde cezalandırılıyor. Çok turlu ReAct döngüsünde bu davranış avantaja dönebilir; bir sonraki deney bu.
3. **Hataların çoğu yapısal ve onarılabilir:** en iyi sahayı bulmadan tersine analize atlamak. Deterministik onarım bunu kapatıyor. Kalan hatalar anlamsal: "ısı adası" yerine "enerji dengesi", "Moda" yerine "İstanbul" ya da "Kadıköy".
4. **Önerilen yapılandırma:** Qwen3-4B + plan onarımı + kural tabanlı yedek (LLM boş plan döndürürse). 4 çekirdekli bir dizüstünde soru başına ~5 s, GPU gerekmiyor.

**Tartışmalı etiketler:** "Kendi elektriğini karşılayabilecek yerler" için LLM `objective=energy_balance, require_balance=true` seçti; altın etiket `score`. Bu seçim anlamca belki daha doğru. "Moda" da gerçekte Kadıköy'de, Caferağa'ya komşu bir semt. Altın etiketleri değiştirmedik; sonuçlar katı ölçüyle verildi.

**Çalıştırma:** `make agent-qwen` (4B) ya da `make agent-qwen QWEN=Qwen3-8B` ile modeli indirir ve ajan API'sini Qwen planlayıcıyla açar. Sonuç dosyası: `data/validation/agent_llm_benchmark.json`.

### D. Çok turlu ReAct: model araç sonucunu görerek ilerliyor (K-056)

**Kurulum:**
- En çok 4 tur. Model bir araç çağırıyor, kısa bir gözlem görüyor, sonra bir sonraki çağrıya karar veriyor.
- "Etkin plan": sonradan başka çağrı geliyorsa baştaki keşif çağrıları (`list_areas`) atlanıyor; ReAct'te keşif meşru.
- Ölçüler: tam doğruluğun yanında çağrı sayısı ve gereksiz çağrı (kapsam taşması).

| Planlayıcı | Geliştirme: tam doğru | Bağımsız: tam doğru | Çağrı/soru | Gereksiz çağrı/soru | Süre/soru |
|---|---|---|---|---|---|
| Kural tabanlı | %100 | %73 | 1–3 | 0 | ~0 s |
| Qwen3-4B, tek seferlik + onarım | %83 | %87 | 1–3 | ~0 | 5,4 s |
| Qwen3-8B, tek seferlik + onarım | %90 | %83 | 1–3 | ~0 | 8,3 s |
| Qwen3-4B, ReAct | — | %87 | 2,5 | 1,4 | 37 s |
| Qwen3-8B, ReAct | %95 | %93 | 2,2–2,4 | 0,9–1,3 | 54–59 s |
| **Qwen3-8B, ReAct + niyet koruması** | **%95** | **%93** | 2,0–2,3 | 0,8–1,2 | 54–59 s |

**Okuma:**
1. **Hipotez doğrulandı.** 8B'nin tek seferlik düzende ceza yiyen "önce kontrol et" davranışı, sonucu görerek ilerleyince avantaja dönüyor. Bağımsız sette %77 → %93; en iyi planlayıcı bu.
2. **4B ReAct'ten kazanmıyor** (%87 → %87), ama daha çok gereksiz çağrı yapıyor (1,4). Sonucu görerek ilerlemenin faydası model kapasitesine bağlı.
3. **Bedel:** soru başına ~1 gereksiz çağrı ve 54–59 s. 8B, 70 sorunun 7'sinde kullanıcı istemediği hâlde **bir hedef puan uydurdu** ("70", "95") ve tersine analiz yaptı (niyet uydurma; Ji vd. 2023). Yanıt gözlemlerden yazıldığı için sahte sayı söylenmedi, ama istenmemiş bir analiz yapıldı. **Önlem:** soruda sayı ya da hedef ifadesi yoksa tersine analiz çağrısı yürütülmüyor.
4. **Niyet korumasıyla yeniden ölçüm (aynı 70 soru, aynı model):**
   - İstenmemiş tersine analiz: 7/70 → **0/70**.
   - Gereksiz çağrı/soru: bağımsız 0,93 → 0,77; geliştirme 1,30 → 1,18.
   - Tam doğruluk değişmedi (%93 / %95). Koruma doğru planları bozmadı; yalnız fazladan, istenmemiş analizi kesti. Doğruluk aynı kaldı, çünkü puanlama ilk aracı ve argümanları ölçüyor; uydurulan hedef bu ölçüye girmiyordu.
   - Koruma bir kuraldır, öğrenilmiş bir davranış değildir: hedefi sayı ya da hedef sözcüğü olmadan dile getiren bir soru ("daha iyi bir saha için ne gerekir?") tersine analize gidemez. Bu bilinçli bir tercih: istenmemiş bir analiz yapmaktansa eksik kalmak.
   - Süreler aynı makinede eşzamanlı başka iş (altlık harita derlemesi) varken ölçüldü; süre farkları anlamlı değil.
5. **Kalan 4 hata her iki koşuda da aynı ve anlamsal:**
   - "ısı adası" → enerji dengesi ve öteki göstergeler denendi;
   - "Moda" → İstanbul;
   - "kendi elektriğini karşılayan yerler" → `energy_balance` (tartışmalı etiket).

**Önerilen yapılandırma:**
- Doğruluk öncelikliyse Qwen3-8B + ReAct + niyet koruması (~1 dk/soru, 4 CPU çekirdeği).
- Etkileşim hızı öncelikliyse Qwen3-4B tek seferlik + onarım (~5 s/soru).

Sonuç dosyası: `data/validation/agent_react_benchmark.json`.

## 5. Başarısızlıktan öğrenilen: havalimanı vakası

İlk sürümde İstanbul'un en yüksek puanlı sahası **İstanbul Havalimanı terminali** çıktı. Nedeni zincirleme iki hata:
1. HRSL nüfus haritası terminal binasına 1.757 kişi yazmış.
2. Dev çatılar bu "nüfusu" fazlasıyla dengelemiş.

Uygulanabilirlik alanı denetimi bunu yakalamadı, çünkü kriter uzayında bu saha brownfield PED'lere benziyor. Overture arazi kullanımında havalimanı poligonu yoktu. İlk önlem GHSL konut dışı yapı payıydı, ama GHSL de havalimanı sahasında yalnızca %4 konut dışı gösterdi. Bu yüzden önlem OSM özel arazi katmanı oldu: havalimanı, sanayi, liman, askeri alan ve demiryolu alanı (sahanın %50'sinden fazlası bu arazideyse öneri yok). Overpass sunucusu dört kentte (İstanbul, Fontaine d'Ouche, Fornebu, Kaukovainio) yanıt vermediği için orada yedek kural uygulandı: güven puanı ≥ 0,7 olan en az 5 Overture "airport" noktasının ~400 m çevresi özel arazi sayıldı. Bu yedek kural sanayi ve liman alanlarını kapsamaz; bu sınırlılık kayıtlı. İstanbul'da 202 saha elendi; Atatürk ve İstanbul havalimanları ilk sıralardan çıktı. Bu vaka tezde "veri hatası × model" etkileşiminin örneği olarak anlatılacak.

## 6. Sıradaki adımlar

1. LLM planlayıcısı: yerel Qwen3-8B (Apache-2.0) ile kural tabanlı planlayıcının bağımsız soru setinde karşılaştırılması.
2. Görsel ajan: Qwen2.5-VL ile Mapillary ve Commons fotoğraflarından saha betimi (sayı değil, yalnızca betim).
3. Ajanın çizilen sahayı ve kentsel dönüşüm senaryosunu ("aynı nüfus") araç olarak kullanması.
