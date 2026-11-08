# pedx — one-command local workflow (see docs/LOCAL_SETUP.md)
PY ?= python3
PORT ?= 8765

.PHONY: help install data build serve test docker docker-run clean

help:
	@echo "make install    # Python paketlerini kur (pedx + h3 + jax + scipy + rasterio + pytest)"
	@echo "make serve      # uygulamayı aç: http://localhost:$(PORT)/pedx_app.html"
	@echo "make data       # tüm ham açık verileri indir (data/raw)"
	@echo "make build      # H3 özellik deposunu ve web verisini yeniden üret"
	@echo "make test       # testleri çalıştır"
	@echo "make docker     # Docker imajı oluştur;  make docker-run ile çalıştır"

install:
	$(PY) -m pip install -e ".[dev]"

data:
	$(PY) scripts/fetch_data.py

build:
	$(PY) examples/build_demo_caferaga.py
	$(PY) web/build_app.py

serve:
	@echo "Uygulama: http://localhost:$(PORT)/pedx_app.html  (eski demo: /index.html)"
	$(PY) -m http.server $(PORT) -d web

test:
	$(PY) -m pytest -q

docker:
	docker build -t pedx .

docker-run:
	docker run --rm -p $(PORT):8765 pedx

clean:
	rm -rf data/processed .pytest_cache
