# pedx — reproducible container: serves the committed demo; `make data build` inside rebuilds from open data.
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir -e ".[dev]"

COPY . .
EXPOSE 8765 8766
# static app on 8765 and the on-demand API on 8766 (the app detects the API automatically)
CMD ["sh", "-c", "python -m uvicorn pedx.api:app --host 0.0.0.0 --port 8766 & python -m http.server 8765 -d web"]
