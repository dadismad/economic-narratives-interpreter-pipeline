import hashlib
import json
import os
import tempfile
from collections import Counter
from datetime import datetime, timezone
from typing import Dict, Iterable, List
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.schemas import validate_narrative_candidate

KEYWORD_TO_FACTOR = {
    "inflation": "inflation",
    "cpi": "inflation",
    "rate": "interest_rates",
    "fed": "interest_rates",
    "yield": "interest_rates",
    "credit": "credit_conditions",
    "spread": "credit_conditions",
    "liquidity": "liquidity",
    "dollar": "currency",
    "fx": "currency",
    "oil": "geopolitical_risk",
    "war": "geopolitical_risk",
    "jobs": "growth",
    "gdp": "growth",
    "recession": "growth",
}

CAPITAL_EXPRESSION_KEYWORDS = {
    "flow",
    "flows",
    "position",
    "positioning",
    "volatility",
    "spread",
    "yield",
    "treasury",
    "bond",
    "equity",
    "stocks",
    "fx",
    "dollar",
    "credit",
}

CONTRADICTION_CUES = {
    "despite",
    "however",
    "but",
    "yet",
    "although",
    "contrary",
    "versus",
    "vs",
    "while",
}


def _cache_key(records: Iterable[Dict], model: str) -> str:
    compact = "|".join(
        f"{item.get('title', '')[:120]}::{item.get('summary', '')[:120]}" for item in records
    )
    return hashlib.sha256(f"{model}:{compact}".encode("utf-8")).hexdigest()


def _load_cache(path):
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}

    if not isinstance(payload, dict):
        return {}
    return payload


def _save_cache(path, cache):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(cache, handle)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def extract_with_keywords(records: List[Dict], top_k: int = 5) -> List[Dict]:
    counts: Dict[str, int] = {}
    for item in records:
        text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
        for keyword, factor in KEYWORD_TO_FACTOR.items():
            if keyword in text:
                counts[factor] = counts.get(factor, 0) + 1

    total = max(sum(counts.values()), 1)
    ranked = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:top_k]
    candidates = [
        {
            "narrative": f"{factor.replace('_', ' ').title()} pressure building",
            "macro_factors": [factor],
            "confidence": round(score / total, 3),
            "method": "keyword_fallback",
        }
        for factor, score in ranked
    ]
    return [validate_narrative_candidate(item) for item in candidates]


def dedupe_candidates(candidates: List[Dict]) -> List[Dict]:
    deduped: List[Dict] = []
    seen = set()
    for candidate in candidates:
        key = (
            candidate.get("narrative", "").strip().lower(),
            tuple(sorted(candidate.get("macro_factors", []))),
            candidate.get("method", "").strip().lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def _extract_matched_factors(text: str) -> set:
    matched_factors = set()
    for keyword, factor in KEYWORD_TO_FACTOR.items():
        if keyword in text:
            matched_factors.add(factor)
    return matched_factors


def _has_capital_expression(text: str) -> bool:
    return any(keyword in text for keyword in CAPITAL_EXPRESSION_KEYWORDS)


def _has_contradiction_cue(text: str) -> bool:
    return any(keyword in text for keyword in CONTRADICTION_CUES)


def _parse_published(value: str):
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(candidate)
    except ValueError:
        return None


def _lifecycle_tag(narrative_score: float, temporal_coherence_score: float) -> str:
    if narrative_score >= 0.6 and temporal_coherence_score >= 0.3:
        return "green"
    if narrative_score >= 0.3:
        return "yellow"
    return "red"


def _macro_alignment(factors: set, contradiction_ratio: float) -> str:
    if len(factors) >= 2 and contradiction_ratio >= 0.3:
        return "contradicting"
    return "aligned"


def enrich_candidates(candidates: List[Dict], records: List[Dict]) -> List[Dict]:
    factor_support = Counter()
    analyzed_records = []
    for item in records:
        text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
        matched_factors = _extract_matched_factors(text)
        has_capital_expression = _has_capital_expression(text)
        has_contradiction_cue = _has_contradiction_cue(text)
        published_dt = _parse_published(item.get("published", ""))
        analyzed_records.append(
            {
                "matched_factors": matched_factors,
                "has_capital_expression": has_capital_expression,
                "has_contradiction_cue": has_contradiction_cue,
                "published_dt": published_dt,
            }
        )
        for factor in matched_factors:
            factor_support[factor] += 1

    total_records = max(len(records), 1)
    enriched: List[Dict] = []
    for candidate in candidates:
        factors = set(candidate.get("macro_factors", []))
        support_count = max((factor_support.get(factor, 0) for factor in factors), default=0)
        support_ratio = round(support_count / total_records, 3)
        signal_strength = round(float(candidate.get("confidence", 0.0)) * support_ratio, 3)

        matched_records = [row for row in analyzed_records if row["matched_factors"].intersection(factors)]
        capital_support = sum(1 for row in matched_records if row["has_capital_expression"])
        capital_expression_score = round(capital_support / max(len(matched_records), 1), 3)

        contradiction_support = sum(1 for row in matched_records if row["has_contradiction_cue"])
        contradiction_ratio = round(contradiction_support / max(len(matched_records), 1), 3)

        temporal_dates = [row["published_dt"] for row in matched_records if row["published_dt"] is not None]
        if temporal_dates:
            span_days = max((max(temporal_dates) - min(temporal_dates)).days, 0) + 1
            temporal_coherence_score = round(min(1.0, len(temporal_dates) / span_days), 3)
        else:
            temporal_coherence_score = 0.0

        factor_alignment_score = round(min(1.0, len(factors) / 2), 3)
        recurrence_score = support_ratio
        gate_blend = (
            recurrence_score
            + factor_alignment_score
            + capital_expression_score
            + temporal_coherence_score
        ) / 4
        narrative_score = round(min(1.0, gate_blend * float(candidate.get("confidence", 0.0))), 3)

        enriched_candidate = dict(candidate)
        enriched_candidate["support_count"] = support_count
        enriched_candidate["support_ratio"] = support_ratio
        enriched_candidate["signal_strength"] = signal_strength
        enriched_candidate["recurrence_score"] = recurrence_score
        enriched_candidate["factor_alignment_score"] = factor_alignment_score
        enriched_candidate["capital_expression_score"] = capital_expression_score
        enriched_candidate["temporal_coherence_score"] = temporal_coherence_score
        enriched_candidate["macro_contradiction_score"] = contradiction_ratio
        enriched_candidate["narrative_score"] = narrative_score
        enriched_candidate["lifecycle_tag"] = _lifecycle_tag(narrative_score, temporal_coherence_score)
        enriched_candidate["macro_alignment"] = _macro_alignment(factors, contradiction_ratio)
        enriched.append(enriched_candidate)
    return enriched


def extract_with_openai(
    records: List[Dict],
    api_key: str,
    model: str,
    cache_path: str,
    max_items: int = 25,
) -> List[Dict]:
    from pathlib import Path

    selected = records[:max_items]
    key = _cache_key(selected, model)
    cache_file = Path(cache_path)
    cache = _load_cache(cache_file)
    if key in cache:
        return [validate_narrative_candidate(item) for item in cache[key]]

    prompt_items = [
        {
            "title": item.get("title", ""),
            "summary": item.get("summary", ""),
            "published": item.get("published", ""),
        }
        for item in selected
    ]
    request_body = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Extract up to 5 economic narrative candidates from the provided news items. "
                    "Return strict JSON array, each with keys: narrative, macro_factors (array), confidence (0-1)."
                ),
            },
            {"role": "user", "content": json.dumps(prompt_items, ensure_ascii=False)},
        ],
        "temperature": 0.0,
        "max_tokens": 350,
    }

    req = Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(request_body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urlopen(req, timeout=60) as response:  # nosec B310
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return extract_with_keywords(selected)

    content = payload.get("choices", [{}])[0].get("message", {}).get("content", "[]")
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return extract_with_keywords(selected)

    normalized = []
    for item in parsed:
        normalized.append(
            validate_narrative_candidate(
                {
                    "narrative": item.get("narrative", ""),
                    "macro_factors": item.get("macro_factors", []),
                    "confidence": float(item.get("confidence", 0.0)),
                    "method": "openai",
                }
            )
        )

    cache[key] = normalized
    _save_cache(cache_file, cache)
    return normalized


def rank_candidates(candidates: List[Dict]) -> List[Dict]:
    return sorted(
        candidates,
        key=lambda item: (
            float(item.get("narrative_score", 0.0)),
            float(item.get("confidence", 0.0)),
        ),
        reverse=True,
    )


def _radar_item(candidate: Dict) -> Dict:
    return {
        "narrative": candidate.get("narrative", ""),
        "signal_strength": float(candidate.get("signal_strength", 0.0)),
        "narrative_score": float(candidate.get("narrative_score", 0.0)),
        "lifecycle_tag": candidate.get("lifecycle_tag", "red"),
        "macro_factors": list(candidate.get("macro_factors", [])),
        "drivers": list(candidate.get("macro_factors", [])),
        "constituent_assets": list(candidate.get("constituent_assets", [])),
        "method": candidate.get("method", ""),
    }


def build_narrative_radar(candidates: List[Dict], top_k: int = 5) -> Dict:
    ranked = sorted(candidates, key=lambda c: float(c.get("signal_strength", 0.0)), reverse=True)
    aligned = [_radar_item(c) for c in ranked if c.get("macro_alignment") != "contradicting"][:top_k]
    contradicting = [_radar_item(c) for c in ranked if c.get("macro_alignment") == "contradicting"][:top_k]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "horizon": "short_term_tactical",
        "short_term_tactical": {
            "aligned": aligned,
            "contradicting": contradicting,
        },
    }


def extract_candidates(
    records: List[Dict],
    openai_enabled: bool,
    api_key: str,
    model: str,
    cache_path: str,
    max_items: int = 25,
) -> List[Dict]:
    if openai_enabled and api_key:
        candidates = extract_with_openai(
            records=records,
            api_key=api_key,
            model=model,
            cache_path=cache_path,
            max_items=max_items,
        )
    else:
        candidates = extract_with_keywords(records=records)

    deduped = dedupe_candidates(candidates)
    enriched = enrich_candidates(deduped, records)
    return rank_candidates(enriched)
