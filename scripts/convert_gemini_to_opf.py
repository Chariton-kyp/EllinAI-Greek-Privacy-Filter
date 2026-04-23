from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert Gemini span_text JSONL to OPF label-span JSONL."
    )
    parser.add_argument("--input", required=True, help="Input gemini_raw.jsonl")
    parser.add_argument("--output", required=True, help="Output OPF JSONL")
    return parser.parse_args()


def _resolve(path_value: str, project_root: Path) -> Path:
    path = Path(path_value).expanduser()
    if not path.is_absolute():
        path = project_root / path
    return path


def convert(input_path: Path, output_path: Path) -> tuple[int, list[str]]:
    successes = 0
    errors: list[str] = []

    with input_path.open("r", encoding="utf-8") as fin, output_path.open(
        "w", encoding="utf-8"
    ) as fout:
        for line_no, line in enumerate(fin, 1):
            line = line.strip()
            if not line:
                continue
            try:
                ex = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"Line {line_no}: invalid JSON - {exc}")
                continue

            text = ex.get("text", "")
            raw_spans = ex.get("spans", [])
            if not isinstance(text, str):
                errors.append(f"Line {line_no}: field 'text' must be a string")
                continue
            if not isinstance(raw_spans, list):
                errors.append(f"Line {line_no}: field 'spans' must be a list")
                continue

            out_labels: list[dict[str, object]] = []
            used_positions: dict[str, int] = {}

            for sp in raw_spans:
                if not isinstance(sp, dict):
                    errors.append(f"Line {line_no}: span entry must be an object")
                    continue
                span_text = sp.get("span_text", "")
                label = sp.get("label", "")
                if not isinstance(span_text, str) or not isinstance(label, str):
                    errors.append(f"Line {line_no}: span_text/label must be strings")
                    continue
                if not span_text or not label:
                    errors.append(f"Line {line_no}: empty span_text or label")
                    continue

                search_start = used_positions.get(span_text, 0)
                idx = text.find(span_text, search_start)
                if idx == -1:
                    idx = text.find(span_text)
                if idx == -1:
                    errors.append(
                        f"Line {line_no}: span_text not found in text: {span_text!r}"
                    )
                    continue

                end = idx + len(span_text)
                out_labels.append({"category": label, "start": idx, "end": end})
                used_positions[span_text] = end

            out_obj = {"text": text, "label": out_labels}
            fout.write(json.dumps(out_obj, ensure_ascii=False) + "\n")
            successes += 1

    return successes, errors


def main() -> None:
    args = parse_args()
    project_root = Path(__file__).resolve().parents[1]
    input_path = _resolve(args.input, project_root)
    output_path = _resolve(args.output, project_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    successes, errors = convert(input_path, output_path)
    print(f"Wrote {successes} examples to {output_path}")
    if errors:
        print(f"Found {len(errors)} issues.")
        for item in errors[:20]:
            print(f"- {item}")
        if len(errors) > 20:
            print(f"- ... and {len(errors) - 20} more")


if __name__ == "__main__":
    main()
