"""Health check of the thesis data (K-071): every registered product exists, matches its checksum and
passes its schema contract. Exit code 1 if anything fails.

    python scripts/check_data.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from pedx.store import manifest, schema  # noqa: E402


def read(f: Path):
    import pandas as pd
    if f.suffix == ".parquet":
        import geopandas as gpd
        return gpd.read_parquet(f)
    return pd.read_csv(f)


def main():
    m = manifest.load()
    if not m:
        print("manifest is empty: run make inventory / make lake AREA=...")
        return 1
    fails = manifest.check()
    for key, e in m.items():
        f = ROOT / e["file"]
        if not f.exists():
            print(f"--   {key:32s} not built here (make lake AREA={key.split('/')[1]})" if key.startswith("lake/") else f"FAIL {key}: missing")
            continue
        sc = schema.SCHEMAS[e["schema"]]
        probs = schema.validate(read(f), sc)
        if e["schema_version"] != sc.version:
            probs.append(f"schema version {e['schema_version']} in manifest, {sc.version} in code: rebuild")
        fails += [f"{key}: {p}" for p in probs]
        print(f"{'ok  ' if not probs else 'FAIL'} {key:32s} {e['rows']:>7} rows  {e['schema']} v{e['schema_version']}  built {e['created_utc'][:10]} @ {e['code']}")
    for p in fails:
        print("  -", p)
    print("healthy" if not fails else f"{len(fails)} problem(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
