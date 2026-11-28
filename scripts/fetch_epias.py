"""Download Türkiye's national hourly electricity consumption (EPİAŞ, 2023) for the hourly demand model.

EPİAŞ requires a free account (https://kayit.epias.com.tr). Credentials are read ONLY from the
environment — never write them into code, files or chat:

    export EPIAS_USERNAME="..."; export EPIAS_PASSWORD="..."
    python scripts/fetch_epias.py

Output: data/raw/sources/epias_realtime_consumption_2023.csv  (attribution: EPİAŞ Şeffaflık Platformu)
"""

from pathlib import Path

from pedx.demand import fetch_epias_realtime

OUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "sources" / "epias_realtime_consumption_2023.csv"

if __name__ == "__main__":
    df = fetch_epias_realtime(2023)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT)
    print(f"{OUT}: {len(df)} saat, toplam {df['consumption_mwh'].sum() / 1e6:.1f} TWh")
