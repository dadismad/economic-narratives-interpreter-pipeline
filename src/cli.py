import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from src.config import load_settings
from src.ingestion.capital_flows import fetch_defillama_protocols, fetch_treasury_rates
from src.ingestion.filings import fetch_sec_submissions
from src.ingestion.fred import fetch_fred_series
from src.ingestion.macro import fetch_bls_cpi, fetch_ecb_exr_xml, fetch_world_bank_gdp
from src.ingestion.papers import fetch_arxiv, fetch_crossref, fetch_openalex, fetch_pubmed_ids
from src.ingestion.patents import (
    fetch_google_patents_page,
    fetch_uspto_bulk_page,
    fetch_wipo_patentscope_page,
)
from src.ingestion.positioning import fetch_cftc_finfutwk
from src.ingestion.rss import dedupe_rss_records, fetch_rss
from src.key_parser import discover_api_keys, write_key_audit
from src.processing.narrative_extractor import build_narrative_radar, extract_candidates
from src.schemas import SchemaError, validate_rss_record
from src.storage.jsonl_store import load_jsonl_with_errors, store_json, store_jsonl, store_run_manifest


def _latest_jsonl(base: Path):
    files = sorted(base.glob("*.jsonl"))
    return files[-1] if files else None


def run_ingest(source: str, series_ids: str = "", urls: str = ""):
    settings = load_settings()
    started_at = datetime.now(timezone.utc)
    run_manifest: Dict = {
        "command": "ingest",
        "source": source,
        "started_at": started_at.isoformat(),
        "status": "success",
        "sources": {},
        "errors": [],
    }

    if source in {"fred", "all"}:
        chosen_series = (
            [item.strip() for item in series_ids.split(",") if item.strip()]
            if series_ids
            else settings.fred_series_ids
        )
        fred_rows: List[Dict] = []
        fred_errors: List[Dict] = []
        for series_id in chosen_series:
            try:
                fred_rows.extend(fetch_fred_series(series_id, api_key=settings.fred_api_key))
            except Exception as exc:  # noqa: BLE001
                fred_errors.append({"series_id": series_id, "error": str(exc)})

        if fred_rows:
            path = store_jsonl(fred_rows, settings.data_dir, "raw", "fred")
            print(f"Stored {len(fred_rows)} FRED rows -> {path}")
            run_manifest["sources"]["fred"] = {
                "rows": len(fred_rows),
                "output_path": str(path),
                "series_ids": chosen_series,
                "errors": fred_errors,
            }
        else:
            run_manifest["sources"]["fred"] = {
                "rows": 0,
                "output_path": None,
                "series_ids": chosen_series,
                "errors": fred_errors,
            }
            if not fred_errors:
                run_manifest["errors"].append("No FRED rows returned")

    if source in {"rss", "all"}:
        chosen_urls = (
            [item.strip() for item in urls.split(",") if item.strip()] if urls else settings.rss_urls
        )
        if not chosen_urls:
            raise ValueError("No RSS URLs configured. Set RSS_URLS or pass --urls.")

        rss_rows: List[Dict] = []
        rss_errors: List[Dict] = []
        for feed_url in chosen_urls:
            try:
                rss_rows.extend(fetch_rss(feed_url))
            except Exception as exc:  # noqa: BLE001
                rss_errors.append({"feed_url": feed_url, "error": str(exc)})

        deduped_rows, duplicates_removed = dedupe_rss_records(rss_rows)
        if deduped_rows:
            path = store_jsonl(deduped_rows, settings.data_dir, "raw", "rss")
            print(f"Stored {len(deduped_rows)} RSS rows -> {path}")
            run_manifest["sources"]["rss"] = {
                "rows": len(deduped_rows),
                "output_path": str(path),
                "feed_urls": chosen_urls,
                "duplicates_removed": duplicates_removed,
                "errors": rss_errors,
            }
        else:
            run_manifest["sources"]["rss"] = {
                "rows": 0,
                "output_path": None,
                "feed_urls": chosen_urls,
                "duplicates_removed": duplicates_removed,
                "errors": rss_errors,
            }
            if not rss_errors:
                run_manifest["errors"].append("No RSS rows returned")

    if run_manifest["errors"] or any(
        source_info.get("errors") for source_info in run_manifest["sources"].values()
    ):
        run_manifest["status"] = "partial_success"

    finished_at = datetime.now(timezone.utc)
    run_manifest["finished_at"] = finished_at.isoformat()
    run_manifest["duration_seconds"] = round((finished_at - started_at).total_seconds(), 3)
    manifest_path = store_run_manifest(run_manifest, settings.data_dir, "ingest")
    print(f"Run manifest -> {manifest_path}")


def run_extract(input_path: str = ""):
    settings = load_settings()
    started_at = datetime.now(timezone.utc)

    source_path = input_path
    if not source_path:
        latest = _latest_jsonl(Path(settings.data_dir) / "raw" / "rss")
        if latest is None:
            raise FileNotFoundError(
                "No RSS JSONL file found. Run `python -m src.cli ingest --source rss` first or pass --input."
            )
        source_path = str(latest)

    rows, parse_errors = load_jsonl_with_errors(source_path)
    valid_rows: List[Dict] = []
    invalid_rows: List[Dict] = list(parse_errors)
    for index, row in enumerate(rows, start=1):
        try:
            valid_rows.append(validate_rss_record(row))
        except (SchemaError, KeyError, TypeError) as exc:
            invalid_rows.append({"line": index, "error": str(exc)})

    candidates = extract_candidates(
        records=valid_rows,
        openai_enabled=settings.openai_enabled,
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        cache_path=str(Path(settings.data_dir) / "cache" / "openai_cache.json"),
        max_items=settings.openai_max_items,
    )
    output = store_jsonl(candidates, settings.data_dir, "processed", "narratives")
    print(f"Stored {len(candidates)} narrative candidates -> {output}")

    radar_payload = build_narrative_radar(candidates, top_k=5)
    radar_output = store_json(radar_payload, settings.data_dir, "processed", "radar")
    print(f"Stored narrative radar snapshot -> {radar_output}")

    finished_at = datetime.now(timezone.utc)
    manifest = {
        "command": "extract",
        "status": "partial_success" if invalid_rows else "success",
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_seconds": round((finished_at - started_at).total_seconds(), 3),
        "input_path": source_path,
        "input_rows": len(rows) + len(parse_errors),
        "valid_input_rows": len(valid_rows),
        "invalid_input_rows": len(invalid_rows),
        "input_errors": invalid_rows,
        "output_path": str(output),
        "output_rows": len(candidates),
        "method": candidates[0]["method"] if candidates else "none",
        "radar_output_path": str(radar_output),
        "radar_counts": {
            "aligned": len(radar_payload["short_term_tactical"]["aligned"]),
            "contradicting": len(radar_payload["short_term_tactical"]["contradicting"]),
        },
    }
    manifest_path = store_run_manifest(manifest, settings.data_dir, "extract")
    print(f"Run manifest -> {manifest_path}")


def run_bootstrap_sources(cik: str = "0000320193"):
    settings = load_settings()
    started_at = datetime.now(timezone.utc)

    keys = discover_api_keys(extra_env_files=[str(Path(".env")), str(Path(".env.local"))])
    audit_path = write_key_audit(keys, str(Path(settings.data_dir) / "runs" / "key_audit.json"))

    outcomes: List[Dict] = []

    def _try(name: str, fn, category: str, as_jsonl: bool = True):
        try:
            payload = fn()
            if as_jsonl:
                if isinstance(payload, list):
                    out_path = store_jsonl(payload, settings.data_dir, "raw", category)
                    rows = len(payload)
                else:
                    out_path = store_json(payload, settings.data_dir, "raw", category)
                    rows = 1
            else:
                out_path = store_json(payload, settings.data_dir, "raw", category)
                rows = 1
            outcomes.append(
                {
                    "source": name,
                    "status": "success",
                    "rows": rows,
                    "output_path": str(out_path),
                    "error": None,
                }
            )
        except Exception as exc:  # noqa: BLE001
            outcomes.append(
                {
                    "source": name,
                    "status": "error",
                    "rows": 0,
                    "output_path": None,
                    "error": str(exc),
                }
            )

    _try("sec_submissions", lambda: fetch_sec_submissions(cik), "sec_submissions")
    _try("cftc_finfutwk", lambda: fetch_cftc_finfutwk(max_rows=250), "cftc_finfutwk")
    _try("bls_cpi", fetch_bls_cpi, "bls")
    _try("world_bank_gdp", fetch_world_bank_gdp, "world_bank")
    _try("openalex", fetch_openalex, "openalex")
    _try("crossref", fetch_crossref, "crossref")
    _try("pubmed", fetch_pubmed_ids, "pubmed")
    _try("arxiv", fetch_arxiv, "arxiv")
    _try("defillama", fetch_defillama_protocols, "defillama")
    _try("fiscaldata_rates", fetch_treasury_rates, "fiscaldata")

    # XML / HTML page captures
    _try("ecb_exr_xml", lambda: {"xml": fetch_ecb_exr_xml()}, "ecb_exr", as_jsonl=False)
    _try("uspto_bulk_page", fetch_uspto_bulk_page, "uspto_bulk", as_jsonl=False)
    _try("wipo_patentscope_page", fetch_wipo_patentscope_page, "wipo", as_jsonl=False)
    _try("google_patents_page", fetch_google_patents_page, "google_patents", as_jsonl=False)

    # key-gated optional connector
    fred_key = keys.get("FRED_API_KEY", settings.fred_api_key)
    if fred_key:
        _try(
            "fred_cpi",
            lambda: fetch_fred_series("CPIAUCSL", api_key=fred_key),
            "fred",
        )
    else:
        outcomes.append(
            {
                "source": "fred_cpi",
                "status": "skipped",
                "rows": 0,
                "output_path": None,
                "error": "FRED_API_KEY not found",
            }
        )

    finished_at = datetime.now(timezone.utc)
    manifest = {
        "command": "bootstrap_sources",
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_seconds": round((finished_at - started_at).total_seconds(), 3),
        "key_audit_path": audit_path,
        "sources": outcomes,
        "status": "partial_success" if any(o["status"] in {"error", "skipped"} for o in outcomes) else "success",
    }
    path = store_run_manifest(manifest, settings.data_dir, "bootstrap_sources")
    print(f"Bootstrap manifest -> {path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Economic Narratives Interpreter CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Ingest source data")
    ingest_parser.add_argument("--source", choices=["fred", "rss", "all"], required=True)
    ingest_parser.add_argument("--series-ids", default="", help="Comma-separated FRED series ids")
    ingest_parser.add_argument("--urls", default="", help="Comma-separated RSS URLs")

    extract_parser = subparsers.add_parser("extract", help="Extract narrative candidates")
    extract_parser.add_argument("--input", default="", help="Path to RSS JSONL input file")

    bootstrap_parser = subparsers.add_parser(
        "bootstrap-sources",
        help="Collect from validated source connectors and write manifests",
    )
    bootstrap_parser.add_argument("--cik", default="0000320193", help="SEC CIK for submissions bootstrap")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "ingest":
        run_ingest(source=args.source, series_ids=args.series_ids, urls=args.urls)
    elif args.command == "extract":
        run_extract(input_path=args.input)
    elif args.command == "bootstrap-sources":
        run_bootstrap_sources(cik=args.cik)


if __name__ == "__main__":
    main()
