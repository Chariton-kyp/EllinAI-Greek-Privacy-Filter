"""SHA-256 manifest generator for dataset artefacts.

Produces `artifacts/manifest/manifest.json` with {path, size_bytes,
sha256, line_count, git_commit, timestamp_utc}. Pair this with the
current git commit hash to prove that a fine-tune run used a specific
dataset build.

Usage:

    python scripts/hash_manifest.py \
        --inputs data/processed/train.jsonl \
                 data/processed/validation.jsonl \
                 data/processed/test.jsonl \
                 data/processed/hard_test.jsonl \
        --output artifacts/manifest/manifest.json
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fp:
        while True:
            data = fp.read(chunk)
            if not data:
                break
            h.update(data)
    return h.hexdigest()


def _line_count(path: Path) -> int:
    n = 0
    with path.open("rb") as fp:
        for _ in fp:
            n += 1
    return n


def _git_commit(cwd: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=cwd, stderr=subprocess.DEVNULL,
        )
        return out.decode("ascii").strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def _git_dirty(cwd: Path) -> bool:
    try:
        out = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=cwd,
            stderr=subprocess.DEVNULL,
        )
        return bool(out.strip())
    except Exception:  # noqa: BLE001
        return True


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--inputs", nargs="+", required=True)
    p.add_argument("--output", default="artifacts/manifest/manifest.json")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    entries = []
    for item in args.inputs:
        path = Path(item)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        if not path.exists():
            entries.append(
                {"path": str(path), "error": "missing"}
            )
            continue
        entries.append(
            {
                "path": str(path.relative_to(PROJECT_ROOT).as_posix()),
                "size_bytes": path.stat().st_size,
                "sha256": _sha256(path),
                "line_count": _line_count(path),
            }
        )
    manifest = {
        "generated_at_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "git_commit": _git_commit(PROJECT_ROOT),
        "git_dirty": _git_dirty(PROJECT_ROOT),
        "entries": entries,
    }
    out = Path(args.output)
    if not out.is_absolute():
        out = PROJECT_ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fp:
        json.dump(manifest, fp, ensure_ascii=False, indent=2)
    print(f"Manifest: {out}")
    for e in entries:
        if "sha256" in e:
            print(f"  {e['path']} ({e['size_bytes']} B, {e['line_count']} lines)")
            print(f"    sha256: {e['sha256']}")
        else:
            print(f"  {e['path']}: {e.get('error','?')}")


if __name__ == "__main__":
    main()
