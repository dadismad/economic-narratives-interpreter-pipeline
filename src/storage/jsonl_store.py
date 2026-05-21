import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def store_jsonl(records: Iterable[Dict], data_dir: str, category: str, source: str) -> Path:
    base = Path(data_dir) / category / source
    ensure_dir(base)
    output_path = base / f"{utc_timestamp()}.jsonl"
    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return output_path


def store_json(payload: Dict[str, Any], data_dir: str, category: str, source: str) -> Path:
    base = Path(data_dir) / category / source
    ensure_dir(base)
    output_path = base / f"{utc_timestamp()}.json"
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    return output_path


def store_run_manifest(manifest: Dict[str, Any], data_dir: str, command: str) -> Path:
    base = Path(data_dir) / "runs" / command
    ensure_dir(base)
    output_path = base / f"{utc_timestamp()}.json"
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
    return output_path


def load_jsonl(path: str) -> List[Dict]:
    rows, _ = load_jsonl_with_errors(path)
    return rows


def load_jsonl_with_errors(path: str) -> Tuple[List[Dict], List[Dict]]:
    rows: List[Dict] = []
    errors: List[Dict] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                errors.append({"line": line_no, "error": f"Malformed JSON: {exc.msg}"})
    return rows, errors
