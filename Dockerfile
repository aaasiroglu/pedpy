# pedx — reproducible container: serves the committed demo; `make data build` inside rebuilds from open data.
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir -e ".[dev]"

COPY . .
EXPOSE 8765
CMD ["python", "-m", "http.server", "8765", "-d", "web"]
