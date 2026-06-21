"""Generate Markdown + CSV + HTML reports from benchmark JSON output.

Reads:  artifacts/metrics/benchmark_3way_opf.json
Writes: artifacts/metrics/benchmark_3way_opf.md
        artifacts/metrics/benchmark_3way_opf.csv
        artifacts/metrics/benchmark_3way_opf.html
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_INPUT = PROJECT_ROOT / "artifacts" / "metrics" / "benchmark_3way_opf.json"


def load_results(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def write_markdown(results: dict, out: Path) -> None:
    lines: list[str] = []
    lines.append("# Greek PII Public Benchmark v1 — 3-Way Model Comparison\n\n")
    lines.append(f"Benchmark: `{results['benchmark']}`\n\n")
    lines.append("## Aggregate Metrics\n\n")
    lines.append("| Model | Cases | Gold spans | Pred spans | "
                  "Untyped P | Untyped R | **Untyped F1** | "
                  "Typed P | Typed R | **Typed F1** | Time (s) |\n")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n")
    for name, r in results["models"].items():
        if "error" in r:
            lines.append(f"| {name} | ERROR: {r['error']} |||||||||\n")
            continue
        a = r["aggregate"]
        lines.append(
            f"| `{name}` | {a['n_cases']} | {a['n_gold']} | {a['n_pred']} | "
            f"{a['untyped']['precision']:.3f} | {a['untyped']['recall']:.3f} | "
            f"**{a['untyped']['f1']:.3f}** | "
            f"{a['typed']['precision']:.3f} | {a['typed']['recall']:.3f} | "
            f"**{a['typed']['f1']:.3f}** | {a.get('elapsed_seconds', 0):.1f} |\n"
        )

    # Per-class breakdown
    lines.append("\n## Per-Class Typed F1\n\n")
    classes = sorted({
        cls
        for r in results["models"].values()
        if "by_class" in r
        for cls in r["by_class"]
    })
    model_names = [n for n in results["models"] if "by_class" in results["models"][n]]
    header = "| Class | " + " | ".join(f"`{n}` F1" for n in model_names) + " |\n"
    lines.append(header)
    lines.append("|---|" + "---:|" * len(model_names) + "\n")
    for cls in classes:
        row = [f"`{cls}`"]
        for name in model_names:
            f1 = results["models"][name]["by_class"].get(cls, {}).get("f1", None)
            row.append(f"{f1:.3f}" if f1 is not None else "—")
        lines.append("| " + " | ".join(row) + " |\n")

    # Boundary / confusion / hallucination summary
    lines.append("\n## Error Breakdown\n\n")
    lines.append("| Model | Boundary | Confusion | Missed | Hallucinated |\n")
    lines.append("|---|---:|---:|---:|---:|\n")
    for name, r in results["models"].items():
        if "error" in r:
            continue
        a = r["aggregate"]
        lines.append(
            f"| `{name}` | {a['boundary_errors']} | {a['confusion_errors']} | "
            f"{a['missed']} | {a['hallucinated']} |\n"
        )

    out.write_text("".join(lines), encoding="utf-8")
    print(f"wrote {out}")


def write_csv(results: dict, out: Path) -> None:
    """One row per (case, model) with prediction details."""
    fieldnames = [
        "model", "case_id", "register", "n_gold", "n_pred",
        "typed_tp", "untyped_tp", "boundary", "confusion",
        "n_missed", "n_hallucinated", "missed_labels", "hallucinated_labels",
    ]
    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for name, r in results["models"].items():
            if "per_case" not in r:
                continue
            for c in r["per_case"]:
                writer.writerow({
                    "model": name,
                    "case_id": c["id"],
                    "register": c["register"],
                    "n_gold": c["n_gold"],
                    "n_pred": c["n_pred"],
                    "typed_tp": c["typed_tp"],
                    "untyped_tp": c["untyped_tp"],
                    "boundary": c["boundary"],
                    "confusion": c["confusion"],
                    "n_missed": len(c["missed"]),
                    "n_hallucinated": len(c["hallucinated"]),
                    "missed_labels": ",".join(s["label"] for s in c["missed"]),
                    "hallucinated_labels": ",".join(s["label"] for s in c["hallucinated"]),
                })
    print(f"wrote {out}")


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="el">
<head>
<meta charset="UTF-8">
<title>Greek PII Public Benchmark v1 — 3-Way Comparison</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, sans-serif;
         max-width: 1100px; margin: 2em auto; padding: 0 1em; color: #222; }}
  h1, h2 {{ border-bottom: 1px solid #ddd; padding-bottom: 0.3em; }}
  table {{ border-collapse: collapse; margin: 1em 0; width: 100%; }}
  th, td {{ border: 1px solid #ddd; padding: 6px 12px; text-align: right; }}
  th {{ background: #f5f5f5; }}
  td:first-child, th:first-child {{ text-align: left; }}
  .f1 {{ font-weight: bold; }}
  .f1.high {{ color: #1a7f37; }}
  .f1.mid  {{ color: #9a6700; }}
  .f1.low  {{ color: #cf222e; }}
  .heatmap {{ display: inline-block; padding: 2px 8px; border-radius: 3px; }}
  .h0 {{ background: #ffe4e6; }} .h1 {{ background: #fef3c7; }}
  .h2 {{ background: #fef9c3; }} .h3 {{ background: #ecfccb; }}
  .h4 {{ background: #d1fae5; }} .h5 {{ background: #a7f3d0; }}
  code {{ background: #f0f0f0; padding: 2px 5px; border-radius: 3px; font-size: 0.9em; }}
  .summary {{ background: #f9fafb; padding: 1em; border-radius: 6px; margin: 1em 0; }}
</style>
</head>
<body>

<h1>Greek PII Public Benchmark v1 — 3-Way Model Comparison</h1>

<div class="summary">
  <p><strong>Benchmark:</strong> {benchmark}</p>
  <p><strong>Cases:</strong> {n_cases} | <strong>Total gold spans:</strong> {n_gold} | <strong>Classes:</strong> 24</p>
</div>

<h2>Aggregate Metrics</h2>
<table>
<thead>
<tr>
  <th>Model</th>
  <th>Untyped P</th><th>Untyped R</th><th>Untyped F1</th>
  <th>Typed P</th><th>Typed R</th><th>Typed F1</th>
  <th>Boundary</th><th>Confusion</th><th>Missed</th><th>Halluc.</th>
  <th>Time (s)</th>
</tr>
</thead>
<tbody>
{aggregate_rows}
</tbody>
</table>

<h2>Per-Class Typed F1 (Heatmap)</h2>
<table>
<thead>
<tr>
  <th>Class</th>
{class_headers}
</tr>
</thead>
<tbody>
{per_class_rows}
</tbody>
</table>

<h2>Notes</h2>
<ul>
  <li><strong>Untyped F1</strong> measures span detection only (any overlapping pair counts) — fair across all 3 models since the OPF base uses an English label space.</li>
  <li><strong>Typed F1</strong> requires exact label match — only meaningful for v2.13 / v3 Lite which share the 24-class taxonomy.</li>
  <li>Boundary errors = correct label, slightly different offsets. Confusion = wrong label on overlapping span.</li>
</ul>

</body>
</html>
"""


def f1_class(f1: float) -> str:
    if f1 >= 0.8:
        return "f1 high"
    if f1 >= 0.5:
        return "f1 mid"
    return "f1 low"


def heatmap_class(f1: float) -> str:
    if f1 >= 0.9:
        return "h5"
    if f1 >= 0.75:
        return "h4"
    if f1 >= 0.6:
        return "h3"
    if f1 >= 0.4:
        return "h2"
    if f1 >= 0.2:
        return "h1"
    return "h0"


def write_html(results: dict, out: Path) -> None:
    n_cases = 0
    n_gold = 0
    aggregate_rows = []
    for name, r in results["models"].items():
        if "error" in r:
            aggregate_rows.append(
                f'<tr><td><code>{name}</code></td><td colspan="11">ERROR: {r["error"]}</td></tr>'
            )
            continue
        a = r["aggregate"]
        n_cases = a["n_cases"]
        n_gold = a["n_gold"]
        u, t = a["untyped"], a["typed"]
        aggregate_rows.append(
            f'<tr><td><code>{name}</code></td>'
            f'<td>{u["precision"]:.3f}</td><td>{u["recall"]:.3f}</td>'
            f'<td class="{f1_class(u["f1"])}">{u["f1"]:.3f}</td>'
            f'<td>{t["precision"]:.3f}</td><td>{t["recall"]:.3f}</td>'
            f'<td class="{f1_class(t["f1"])}">{t["f1"]:.3f}</td>'
            f'<td>{a["boundary_errors"]}</td><td>{a["confusion_errors"]}</td>'
            f'<td>{a["missed"]}</td><td>{a["hallucinated"]}</td>'
            f'<td>{a.get("elapsed_seconds", 0):.1f}</td></tr>'
        )

    classes = sorted({
        cls
        for r in results["models"].values()
        if "by_class" in r
        for cls in r["by_class"]
    })
    model_names = [n for n in results["models"] if "by_class" in results["models"][n]]
    class_headers = "\n".join(f'  <th><code>{n}</code></th>' for n in model_names)
    per_class_rows = []
    for cls in classes:
        cells = []
        for name in model_names:
            f1 = results["models"][name]["by_class"].get(cls, {}).get("f1", None)
            if f1 is None:
                cells.append('<td>—</td>')
            else:
                cells.append(f'<td><span class="heatmap {heatmap_class(f1)}">{f1:.3f}</span></td>')
        per_class_rows.append(f'<tr><td><code>{cls}</code></td>{"".join(cells)}</tr>')

    html = HTML_TEMPLATE.format(
        benchmark=results["benchmark"],
        n_cases=n_cases,
        n_gold=n_gold,
        aggregate_rows="\n".join(aggregate_rows),
        class_headers=class_headers,
        per_class_rows="\n".join(per_class_rows),
    )
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    args = p.parse_args()

    results = load_results(args.input)

    base = args.input.with_suffix("")
    write_markdown(results, base.with_suffix(".md"))
    write_csv(results, base.with_suffix(".csv"))
    write_html(results, base.with_suffix(".html"))


if __name__ == "__main__":
    main()
