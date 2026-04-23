from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class PrivacyExample:
    text: str
    spans: dict[str, list[list[int]]] | None = None
    label: list[dict[str, Any]] | None = None
    info: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "PrivacyExample":
        text = payload.get("text")
        spans = payload.get("spans")
        label = payload.get("label")
        info = payload.get("info")

        if not isinstance(text, str) or not text.strip():
            raise ValueError("Field 'text' must be a non-empty string.")
        if spans is None and label is None:
            raise ValueError("At least one of 'spans' or 'label' must be present.")
        text_len = len(text)

        if spans is not None:
            if not isinstance(spans, dict):
                raise ValueError("Field 'spans' must be an object when present.")
            for key, offsets in spans.items():
                if not isinstance(key, str) or not key.strip():
                    raise ValueError("Each 'spans' key must be a non-empty string.")
                if not isinstance(offsets, list):
                    raise ValueError(f"Spans value for key '{key}' must be a list.")
                for idx, offset in enumerate(offsets):
                    if (
                        not isinstance(offset, list)
                        or len(offset) != 2
                        or isinstance(offset[0], bool)
                        or isinstance(offset[1], bool)
                        or not isinstance(offset[0], int)
                        or not isinstance(offset[1], int)
                    ):
                        raise ValueError(
                            f"Span '{key}' index {idx} must be [start, end] with integer offsets."
                        )
                    start, end = offset
                    if not (0 <= start < end <= text_len):
                        raise ValueError(
                            f"Span '{key}' index {idx} has invalid range [{start}, {end}] for text length {text_len}."
                        )

        if label is not None:
            if not isinstance(label, list):
                raise ValueError("Field 'label' must be a list when present.")
            for idx, item in enumerate(label):
                if not isinstance(item, dict):
                    raise ValueError(f"Label entry {idx} must be an object.")
                category = item.get("category")
                start = item.get("start")
                end = item.get("end")
                if not isinstance(category, str) or not category.strip():
                    raise ValueError(f"Label entry {idx} must include non-empty 'category'.")
                if (
                    isinstance(start, bool)
                    or isinstance(end, bool)
                    or not isinstance(start, int)
                    or not isinstance(end, int)
                ):
                    raise ValueError(
                        f"Label entry {idx} must include integer 'start' and 'end'."
                    )
                if not (0 <= start < end <= text_len):
                    raise ValueError(
                        f"Label entry {idx} has invalid range [{start}, {end}] for text length {text_len}."
                    )

        if info is not None and not isinstance(info, dict):
            raise ValueError("Field 'info' must be an object when present.")

        return cls(text=text, spans=spans, label=label, info=info)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"text": self.text}
        if self.spans is not None:
            payload["spans"] = self.spans
        if self.label is not None:
            payload["label"] = self.label
        if self.info is not None:
            payload["info"] = self.info
        return payload
