from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PRIVATE_TRACKED_PATHS = (
    "data/realworld_benchmark/",
    "scripts/realworld_benchmark/",
    "scripts/build_realworld_benchmark.py",
    "scripts/v3/regex_pii_postpass.py",
    "scripts/v3/benchmark_teacher.py",
    "scripts/aws/ec2_v3_benchmark.sh",
    "scripts/aws/iam_ssm_teacher_policy.json",
)

PRIVATE_METRIC_PREFIXES = (
    "artifacts/metrics/benchmark_triage",
    "artifacts/metrics/failure_mining",
    "artifacts/metrics/realworld",
)

TRACE_KEYS = {
    "per_case",
    "expected",
    "predicted",
    "detected_spans",
    "redacted_text",
    "context",
}

LOCAL_WINDOWS_ROOT = "C:" + "\\\\" + "Users" + "\\\\"
LOCAL_WORKSPACE_MARKER = "Desktop" + "\\\\" + "Business_Projects"
LOCAL_USER_WORKSPACE_MARKER = "harit" + "\\\\" + "Desktop"

TEXT_BOUNDARY_PATTERNS = {
    LOCAL_WINDOWS_ROOT: "local Windows user path",
    LOCAL_WORKSPACE_MARKER: "local project workspace path",
    LOCAL_USER_WORKSPACE_MARKER: "local username/workspace path",
}

TEXT_EXTENSIONS = {
    ".cfg",
    ".csv",
    ".ini",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".ps1",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}


def git_ls_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def has_trace_key(value: object) -> bool:
    if isinstance(value, dict):
        if TRACE_KEYS.intersection(value):
            return True
        return any(has_trace_key(child) for child in value.values())
    if isinstance(value, list):
        return any(has_trace_key(child) for child in value)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail if public git state contains private benchmark/release artefacts."
    )
    parser.add_argument(
        "--check-json",
        action="store_true",
        help="Also parse tracked artifacts/metrics/*.json and reject trace-shaped keys.",
    )
    args = parser.parse_args()

    tracked = git_ls_files()
    issues: list[str] = []

    for path in tracked:
        if path.startswith(PRIVATE_TRACKED_PATHS) or path in PRIVATE_TRACKED_PATHS:
            issues.append(f"private path is tracked: {path}")
        if path.startswith(PRIVATE_METRIC_PREFIXES):
            issues.append(f"private benchmark trace metric is tracked: {path}")
        if Path(path).suffix.lower() in TEXT_EXTENSIONS:
            full_path = PROJECT_ROOT / path
            if full_path.is_file():
                text = full_path.read_text(encoding="utf-8", errors="ignore")
                for pattern, description in TEXT_BOUNDARY_PATTERNS.items():
                    if pattern in text:
                        issues.append(f"{description} found in tracked file: {path}")

    if args.check_json:
        for path in tracked:
            if not path.startswith("artifacts/metrics/") or not path.endswith(".json"):
                continue
            full_path = PROJECT_ROOT / path
            if not full_path.is_file():
                continue
            try:
                payload = json.loads(full_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                issues.append(f"invalid JSON in public metric {path}: {exc}")
                continue
            if has_trace_key(payload):
                issues.append(f"trace-shaped JSON keys found in public metric: {path}")

    if issues:
        print("FAIL: public release boundary violations found:", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1

    print("OK: public release boundary checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
