# pedx — one-command local workflow (see docs/LOCAL_SETUP.md)
PY ?= python3
PORT ?= 8765

.PHONY: help install data epias build serve api prepare test docker docker-run clean

help:
	@echo "make install    # Python paketlerini kur (pedx + h3 + jax + scipy + rasterio + pytest)"
	@echo "make serve      # uygulamayı aç: http://localhost:$(PORT)/pedx_app.html"
	@echo "make api        # tıkla→hesapla API: http://127.0.0.1:8766/assess?lat=40.986&lon=29.028 (uygulama bunu otomatik bulur)"
	@echo "make prepare LAT=.. LON=..  # bir bölgenin GHS-POP/GHSL döşemelerini önbelleğe al (data/cache)"
	@echo "make data       # tüm ham açık verileri indir (data/raw)"
	@echo "make epias      # EPİAŞ ulusal saatlik tüketim (EPIAS_USERNAME/EPIAS_PASSWORD gerekli)"
	@echo "make build      # H3 özellik deposunu ve web verisini yeniden üret"
	@echo "make test       # testleri çalıştır"
	@echo "make docker     # Docker imajı oluştur;  make docker-run ile çalıştır"

install:
	$(PY) -m pip install -e ".[dev]"

data:
	$(PY) scripts/fetch_data.py
	$(PY) scripts/fetch_eo.py
	$(PY) scripts/fetch_layers.py

epias:
	$(PY) scripts/fetch_epias.py

build:
	$(PY) scripts/build_features.py
	$(PY) web/build_app.py

serve:
	@echo "Uygulama: http://localhost:$(PORT)/pedx_app.html"
	$(PY) -m http.server $(PORT) -d web

api:
	@echo "API: http://127.0.0.1:8766/assess?lat=40.986&lon=29.028&k=3"
	$(PY) -m uvicorn pedx.api:app --host 127.0.0.1 --port 8766

LAT ?= 40.986
LON ?= 29.028
prepare:
	$(PY) scripts/prepare_tiles.py $(LAT) $(LON)

test:
	$(PY) -m pytest -q

docker:
	docker build -t pedx .

docker-run:
	docker run --rm -p $(PORT):8765 -p 8766:8766 pedx

clean:
	rm -rf data/processed .pytest_cache
