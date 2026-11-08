# pedx: Pozitif Enerji Bölgeleri için açıklanabilir ve fizik kenetli karar destek

*PED eXplain · v0.1.0.dev0 · yüksek lisans tezi çalışması (İTÜ Geomatik, danışman Prof. Dr. Hande Demirel)*

`pedx`, **ücretsiz ve açık verilerden** (OpenStreetMap, EU JRC PVGIS) bina düzeyinde saatlik enerji dengesi hesaplar. Sonuçları **H3 altıgen hücrelerinde** toplar ve her hücreyi **fiziksel hedefe bağlı, mutlak bir PEB hazırlık indeksiyle** puanlar. Ardından şu üç soruyu yanıtlar:

1. **Neden?** Skorlar nasıl oluştu ve sıralama ağırlık belirsizliği altında ne kadar güvenilir?
2. **Nerede?** Saatlik tamamlayıcılığı gözeten bir PEB sınırı hangi hücreleri kapsamalı? Her hücre kümenin öz-yeterliliğine ne kadar katkı veriyor (Shapley değeri)?
3. **Ne yapmalı?** Fiziksel müdahale uzayında (PV, kabuk iyileştirme, batarya, yük dönüşümü) en düşük maliyetli dönüşüm yolları ve bütçe–skor Pareto eğrisi.

> Ad notu: PyPI'daki `pedpy` adı Jülich'in yaya dinamiği kütüphanesine ait. Bu yüzden paket adı `pedx` (docs/05, K-013).

## Kurulum

```bash
pip install -e ".[dev]"
```

Ek paket grupları: `h3` (altıgen hücreler), `diff` (JAX ile türevlenebilir tersine analiz), `mcdm` (SciPy ile BWM ve ağırlık kararlılığı).

## Web demo (v0.1): yalnızca küresel açık veri

```bash
python examples/build_demo_caferaga.py
```

```bash
python -m http.server 8765 -d web
```

Ardından tarayıcıda `http://localhost:8765` adresini açın. Demo, OSM haritası üzerinde H3 altıgenlerinde yıllık konut elektriği dengesini, PV potansiyelini ve gereken çatı payını gösteriyor; yanında yöntem, veri kaynakları, G2 doğrulaması ve eksikler panelleri var. Kaynak kütüğü: `docs/11_veri_kaynaklari.md`.

## Hızlı başlangıç: Caferağa v0

```bash
python examples/v0_caferaga.py
```

Betik OSM binalarını (Overpass) ve PVGIS 2019 ışınımını indirip önbelleğe alır. Ardından tüm iş akışını çalıştırır ve sonuçları `results/v0/OZET.md` ile CSV dosyalarına yazar. Bir kaynağa erişilemezse açıkça **SENTETİK** etiketli veriye geçer.

```python
from pedx.pipeline import assess
res = assess(buildings_df, irradiance_kw_m2, resolution=10)
res.scores             # hücre skorları (teknik potansiyel senaryosu)
res.rank_uncertainty   # sıra aralıkları, birinci olma olasılığı
res.shapley            # PEB kümesinde hücre katkıları
res.prescriptions      # bütçe–skor Pareto eğrisi ve marjinal değer (€ başına)
```

## Modüller

| Modül | İçerik |
| --- | --- |
| `energy` | Bina kayıtları; SSR, SCR, yıllık denge, CVaR tabanlı şebeke stresi ve tepe rahatlaması; H3 toplulaştırma (paylaşımlı ve bağımsız modlar) |
| `spatial` | H3 atama ve komşuluk |
| `index` | Mutlak PEB hazırlık indeksi, kesin katkılar, SMAA benzeri sıra aralıkları |
| `mcdm` | CRITIC, Entropi, doğrusal BWM, WSM, MARCOS (κ·WSM eşdeğerliği), TOPSIS |
| `graph` | Öz-tüketim koalisyon oyunu, kesin Shapley değeri, PEB sınır büyütme, kesin ve rastgele karşılaştırma yöntemleri |
| `inverse` | Fizik kenetli müdahale modeli, saatlik batarya dinamiği, JAX ile türevlenebilir arama, kesin modelle bağımsız denetim |
| `xai` | Açıklanabilirlik giriş noktaları; ters ağırlık (politika) kararlılığı |
| `ingest` | OSM Overpass ve PVGIS istemcileri ile çevrimdışı test edilebilir ayrıştırıcılar |
| `assumptions` | Her sayısal varsayım, kaynağı ve durumuyla tek bir tabloda |

## Yöntemsel ilkeler

- **Arama için yumuşak model, raporlama için kesin model.** Türevlenebilir model yalnızca arama yönünü bulmak için kullanılır. Raporlanan her sayı kesin modelle yeniden hesaplanır ve denetimden geçer.
- **Kriterler değil, fiziksel müdahaleler optimize edilir.** SSR, denge ve tepe rahatlaması aynı saatlik denklemlerin çıktısıdır.
- **Mutlak indeks.** Skorlar kümeye göreli değil; yeni bir hücre eklemek diğer hücrelerin skorunu değiştirmez.
- **Kaynaksız sabit yoktur.** `varsayim` durumundaki değerler duyarlılık analizine girer ve gerçek veriyle değiştirilecektir.

## Doğrulama

```bash
pytest
```

44 test çalışıyor. Bunlar T1–T5 yazılım doğrulaması, MARCOS ≡ κ·WSM özdeşliği, yumuşatma hata sınırı, Shapley aksiyomları, ızgara aramasına ve ikiye bölme yöntemine karşı tersine çözücü kontrolleri ile çevrimdışı ayrıştırıcıları kapsıyor. Bunlar yazılım doğrulamasıdır. Gözleme karşı bilimsel doğrulama, İBB verisiyle yapılacak G1/G2 karşılaştırmasında ele alınacak (bkz. `docs/`).

## Belgeler

Planlama, literatür, kararlar, kırılganlık analizi, v0 sunumu ve sprint planı: [`docs/`](docs/README.md).

## Veri ve lisans

Bina verisi © OpenStreetMap katkıcıları, ODbL 1.0. Işınım verisi: EU JRC PVGIS. Kodun lisansı henüz belirlenmedi (docs/06).
