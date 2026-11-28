"""Product registry: data/manifest.json (K-071).

Every product written by a build script is registered with its path, schema version, row count, SHA-256,
creation time, code version (git commit) and inputs (source id, version, licence). ``check`` re-hashes the
files so that a product edited by hand or rebuilt without registration is detected.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "data" / "manifest.json"

__all__ = ["register", "load", "check", "sha256", "MANIFEST"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _commit() -> str:
    try:
        sha = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=10).stdout.strip()
        dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--untracked-files=no"], capture_output=True, text=True, timeout=10).stdout.strip()
        return sha + ("+dirty" if dirty else "")
    except Exception:
        return "unknown"


def load(path: Path = MANIFEST) -> Dict[str, dict]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def register(key: str, file: Path, schema: str, schema_version: str, rows: int, inputs: List[dict],
             params: Optional[dict] = None, stats: Optional[dict] = None, path: Path = MANIFEST) -> dict:
    """Add or replace the entry ``key`` (e.g. 'lake/caferaga/buildings')."""
    file = Path(file)
    entry = {"file": str(file.resolve().relative_to(ROOT)), "schema": schema, "schema_version": schema_version, "rows": int(rows),
             "sha256": sha256(file), "bytes": file.stat().st_size, "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
             "code": _commit(), "inputs": inputs, "params": params or {}, "stats": stats or {}}
    m = load(path)
    m[key] = entry
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(sorted(m.items())), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return entry


def check(path: Path = MANIFEST) -> List[str]:
    """Problems: missing files and checksum mismatches."""
    out = []
    for key, e in load(path).items():
        f = ROOT / e["file"]
        if not f.exists():
            if not e["file"].startswith("data/lake/"):  # lake products are not in git: absent = not built on this machine
                out.append(f"{key}: file missing ({e['file']}); rebuild it")
        elif sha256(f) != e["sha256"]:
            out.append(f"{key}: checksum differs from manifest ({e['file']} changed after registration)")
    return out
