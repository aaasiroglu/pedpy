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

## Yerelde çalıştırma

`make serve` ile hazır demoyu açın; her şeyi yeniden üretmek için `make install data build`. Ayrıntılar: [`docs/LOCAL_SETUP.md`](docs/LOCAL_SETUP.md). Mimari: [`docs/13_sistem_mimarisi.md`](docs/13_sistem_mimarisi.md).

## Web demo (v0.2): yalnızca küresel açık veri

```bash
python scripts/build_features.py
```

```bash
python -m http.server 8765 -d web
```

Ardından tarayıcıda `http://localhost:8765/pedx_app.html` adresini açın. Demo, OSM haritası üzerinde H3 altıgenlerinde yıllık konut elektriği dengesini, PV potansiyelini ve gereken çatı payını gösteriyor; yanında yöntem, veri kaynakları, G2 doğrulaması ve eksikler panelleri var. Kaynak kütüğü: `docs/11_veri_kaynaklari.md`.

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
| `ingest` | Küresel açık veri katmanları (OSM, GHS-POP, UNdata, PVGIS) ile çevrimdışı test edilebilir ayrıştırıcılar |
| `export` | Web demo için GeoJSON ve JSON dışa aktarımı |

## Yöntemsel ilkeler

- **Arama için yumuşak model, raporlama için kesin model.** Türevlenebilir model yalnızca arama yönünü bulmak için kullanılır. Raporlanan her sayı kesin modelle yeniden hesaplanır ve denetimden geçer.
- **Kriterler değil, fiziksel müdahaleler optimize edilir.** SSR, denge ve tepe rahatlaması aynı saatlik denklemlerin çıktısıdır.
- **Mutlak indeks.** Skorlar kümeye göreli değil; yeni bir hücre eklemek diğer hücrelerin skorunu değiştirmez.
- **Yalnızca küresel açık veri.** Girdiler her ülkede bulunan açık veri setlerinden gelir; İstanbul verisi yalnızca doğrulamada kullanılır. Sentetik veri sonuçlara hiçbir zaman girmez (K-025).

## Doğrulama

```bash
pytest
```

44 test çalışıyor. Bunlar T1–T5 yazılım doğrulaması, MARCOS ≡ κ·WSM özdeşliği, yumuşatma hata sınırı, Shapley aksiyomları, ızgara aramasına ve ikiye bölme yöntemine karşı tersine çözücü kontrolleri ile çevrimdışı ayrıştırıcıları kapsıyor. Bunlar yazılım doğrulamasıdır. Gözleme karşı bilimsel doğrulama, İBB verisiyle yapılacak G1/G2 karşılaştırmasında ele alınacak (bkz. `docs/`).

## Belgeler

**Başlangıç noktası: [`docs/PROJE_DOSYASI.md`](docs/PROJE_DOSYASI.md)** (mimari, veriler, adımlar, sonuçlar, plan) ve [`docs/00_TEZ_PUSULASI.md`](docs/00_TEZ_PUSULASI.md) (tek sayfa, tek doğruluk kaynağı). Diğer belgeler: [`docs/`](docs/README.md).

## Veri ve lisans

Bina verisi © OpenStreetMap katkıcıları, ODbL 1.0. Işınım verisi: EU JRC PVGIS. Kodun lisansı henüz belirlenmedi (docs/06).
