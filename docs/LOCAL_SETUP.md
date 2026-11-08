# Yerelde Kurulum ve Çalıştırma

## A. En hızlı yol: hazır demoyu açmak (Python yeterli, 1 dakika)

```bash
git clone https://github.com/aaasiroglu/pedpy.git
```

```bash
cd pedpy && git checkout claude/dreamy-allen-fvtsux
```

```bash
python -m http.server 8765 -d web
```

Ardından tarayıcıda **http://localhost:8765** adresini açın. Demo verisi (`web/data/`) repoda hazır olduğu için başka bir kurulum gerekmez. Harita karoları için internet bağlantısı gerekir.

## B. Her şeyi açık veriden yeniden üretmek

Gereksinimler: Python 3.10 veya üstü (3.12 önerilir), `make`, internet bağlantısı. Windows'ta WSL ya da Git Bash önerilir.

```bash
python -m venv .venv && source .venv/bin/activate
```

```bash
make install
```

```bash
make data
```

```bash
make build
```

```bash
make test
```

```bash
make serve
```

- `make install`: pedx paketini ve h3, jax, scipy, rasterio ve pytest bağımlılıklarını kurar.
- `make data`: OSM, GHS-POP (~120 MB), UNdata, OWID, PVGIS ve TEDAŞ (yalnızca G2) verilerini `data/raw` klasörüne indirir.
- `make build`: H3 özellik deposunu (`data/processed`) ve web verisini (`web/data`) üretir.
- `make test`: 53 doğrulama testini çalıştırır.
- `make serve`: demoyu http://localhost:8765 adresinde açar.

Windows PowerShell'de sanal ortamı etkinleştirmek için `source` yerine `.venv\Scripts\Activate.ps1` kullanılır. `make` yoksa her hedefin içindeki komut doğrudan çalıştırılabilir (bkz. `Makefile`).

## C. Docker ile

```bash
docker build -t pedx .
```

```bash
docker run --rm -p 8765:8765 pedx
```

## Sık karşılaşılan sorunlar

| Belirti | Çözüm |
| --- | --- |
| Overpass "connection reset" ya da 429 | Sunucu yoğun; betik bekleyip yeniden dener. Gerekirse birkaç dakika sonra `make data` komutunu tekrarlayın. |
| `rasterio` kurulamıyor | Python 3.12 ile `pip install rasterio` hazır paketle (wheel) kurulur; conda ortamında `conda install -c conda-forge rasterio`. |
| Harita boş görünüyor | İnternet bağlantısını ve tarayıcı konsolunu kontrol edin; OSM karo sunucusu erişilebilir olmalı. |
| `jax` Windows'ta sorun çıkarıyor | Tersine motor için gerekli; yalnızca demo için gerekmez. WSL kullanın. |
