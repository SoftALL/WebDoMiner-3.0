from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Protocol


class JsonSerializable(Protocol):
    def to_dict(self) -> dict:
        ...


def write_jsonl(records: Iterable[JsonSerializable], output_path: str | Path) -> int:
    """
    Write records to a JSONL file.

    Returns the number of records written.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
            count += 1

    return count


def write_json(data: dict, output_path: str | Path) -> None:
    """
    Write a single JSON object to disk.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)