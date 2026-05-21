#!/usr/bin/env python3
"""Extract systems-research facts from published paper chunks.

This script is deliberately outside the OKG publish path. It reads a
published generation, builds evidence-bounded extraction prompts, caches
LLM responses, and writes a deterministic JSONL manifest. The OKG source
adapter then projects the manifest without network calls.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import psycopg
import requests


DEFAULT_DSN = "postgres://postgres:okg@localhost:5433/engram_memex_sr_profile_smoke"
DEFAULT_OUT = Path("deployments/memex-sr/manifests/paper_research_facts.jsonl")
DEFAULT_CACHE = Path("deployments/memex-sr/.cache/paper_fact_extraction")
DEFAULT_MODEL = "openai/gpt-5-mini"

ALLOWED_DOMAINS = {
    "networking",
    "ml_systems",
    "databases",
    "distributed_systems",
    "other",
}
ALLOWED_MECHANISM_KINDS = {
    "algorithm",
    "design_pattern",
    "data_structure",
    "protocol",
    "architecture",
    "other",
}
STRENGTHS = {"weak", "moderate", "high", "strong"}


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _sha(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _slug(value: str, fallback: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:80] or fallback


def _first_sentence(text: str, max_chars: int = 260) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return ""
    match = re.search(r"(?<=[.!?])\s+", text)
    sentence = text[: match.start()] if match else text
    return sentence[:max_chars].strip()


def _load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _generation_predicate(generation_id: int) -> str:
    return (
        f"valid_from_gen <= {generation_id} "
        f"AND coalesce(valid_to_gen, 2147483647) > {generation_id}"
    )


def _load_documents(
    dsn: str,
    generation_id: int,
    *,
    source_pack: str,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    pred = _generation_predicate(generation_id)
    sql = f"""
        SELECT node_id, attrs
        FROM okg.nodes_live
        WHERE subtype = 'document'
          AND {pred}
          AND attrs->>'source_pack' = %s
        ORDER BY attrs->>'venue_id', attrs->>'year', attrs->>'title'
        LIMIT %s OFFSET %s
    """
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (source_pack, limit, offset))
            return [{"node_id": row[0], "attrs": row[1]} for row in cur.fetchall()]


def _load_chunks(
    dsn: str,
    generation_id: int,
    *,
    document_id: str,
    source_pack: str,
) -> list[dict[str, Any]]:
    pred = _generation_predicate(generation_id)
    sql = f"""
        SELECT node_id, attrs
        FROM okg.nodes_live
        WHERE subtype = 'document_chunk'
          AND {pred}
          AND attrs->>'source_pack' = %s
          AND attrs->>'document_id' = %s
        ORDER BY (attrs->>'chunk_index')::int
    """
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (source_pack, document_id))
            return [{"node_id": row[0], "attrs": row[1]} for row in cur.fetchall()]


def _select_evidence_chunks(chunks: list[dict[str, Any]], max_chunks: int) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    seen: set[str] = set()
    signals = (
        "abstract",
        "introduction",
        "design",
        "approach",
        "algorithm",
        "implementation",
        "evaluation",
        "discussion",
        "limitation",
        "conclusion",
    )

    def add(chunk: dict[str, Any]) -> None:
        if chunk["node_id"] in seen or len(selected) >= max_chunks:
            return
        seen.add(chunk["node_id"])
        attrs = chunk["attrs"]
        selected.append(
            {
                "chunk_id": chunk["node_id"],
                "chunk_index": str(attrs.get("chunk_index", "")),
                "text": re.sub(r"\s+", " ", str(attrs.get("text") or "")).strip(),
            }
        )

    for chunk in chunks[:2]:
        add(chunk)
    for chunk in chunks:
        text = str(chunk["attrs"].get("text") or "").lower()
        if any(signal in text[:1000] for signal in signals):
            add(chunk)
    for chunk in chunks:
        add(chunk)
    return selected


def _build_prompt(doc: dict[str, Any], chunks: list[dict[str, str]], max_chars: int) -> str:
    attrs = doc["attrs"]
    abstract = re.sub(r"\s+", " ", str(attrs.get("abstract") or "")).strip()
    pieces = [
        f"Paper id: {attrs.get('paper_id')}",
        f"Document id: {doc['node_id']}",
        f"Title: {attrs.get('title')}",
        f"Venue: {attrs.get('venue_id')} {attrs.get('year')}",
        f"Abstract: {abstract}",
        "",
        "Evidence chunks:",
    ]
    used = sum(len(piece) for piece in pieces)
    for chunk in chunks:
        header = f"\n[chunk_id={chunk['chunk_id']} chunk_index={chunk['chunk_index']}]\n"
        room = max(0, max_chars - used - len(header))
        if room <= 0:
            break
        text = chunk["text"][: min(room, 2600)]
        pieces.append(header + text)
        used += len(header) + len(text)
    pieces.append(
        """
Return JSON with this exact top-level shape:
{
  "evidence": [
    {"id": "e1", "statement": "...", "rationale": "...", "source_chunk_id": "...", "strength": "high|moderate|weak"}
  ],
  "design_principles": [
    {"id": "p1", "statement": "...", "why_it_matters": "...", "domain": "networking|ml_systems|databases|distributed_systems|other", "topic_slugs": ["..."], "strength": "high|moderate|weak", "evidence_ids": ["e1"]}
  ],
  "mechanisms": [
    {"id": "m1", "name": "...", "mechanism_kind": "algorithm|data_structure|protocol|architecture|design_pattern|other", "applicability": "...", "known_limits": "...", "topic_slugs": ["..."], "strength": "high|moderate|weak", "evidence_ids": ["e1"], "instantiates": ["p1"]}
  ],
  "trade_offs": [
    {"id": "t1", "objective_a": "...", "objective_b": "...", "tension": "...", "failure_modes": "...", "topic_slugs": ["..."], "strength": "high|moderate|weak", "evidence_ids": ["e1"], "restricts": ["m1"]}
  ],
  "anti_patterns": [
    {"id": "a1", "approach": "...", "why_it_tends_to_fail": "...", "topic_slugs": ["..."], "strength": "high|moderate|weak", "evidence_ids": ["e1"], "mitigated_by": ["m1"]}
  ]
}

Rules:
- Use only the paper text above.
- Prefer concrete algorithms, data structures, protocols, architectures, and design patterns.
- Omit weak guesses. It is acceptable for an array to be empty.
- Keep every statement concise and useful for an autonomous systems researcher.
- Every fact must cite an evidence id, and every evidence item must cite one provided chunk_id.
"""
    )
    return "\n".join(pieces)


def _call_openrouter(prompt: str, *, model: str, timeout: int) -> dict[str, Any]:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    payload = {
        "model": model,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "usage": {"include": True},
        "messages": [
            {
                "role": "system",
                "content": (
                    "You extract grounded systems-research design knowledge "
                    "from papers. Return only valid JSON."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "X-Title": "Memex-SR paper fact extraction",
    }
    last_error: str | None = None
    for attempt in range(4):
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=timeout,
            )
            if response.status_code in {429, 500, 502, 503, 504}:
                last_error = f"HTTP {response.status_code}: {response.text[:500]}"
                time.sleep(2**attempt)
                continue
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return {
                "payload": _parse_json_object(content),
                "metadata": {
                    "response_id": data.get("id"),
                    "response_model": data.get("model"),
                    "provider": data.get("provider"),
                    "usage": data.get("usage"),
                },
            }
        except Exception as exc:  # noqa: BLE001 - keep retries around remote model calls.
            last_error = str(exc)
            time.sleep(2**attempt)
    raise RuntimeError(f"OpenRouter extraction failed after retries: {last_error}")


def _parse_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start < 0 or end < start:
        raise ValueError(f"model did not return a JSON object: {text[:200]}")
    return json.loads(stripped[start : end + 1])


def _heuristic_extract(doc: dict[str, Any], chunks: list[dict[str, str]]) -> dict[str, Any]:
    attrs = doc["attrs"]
    title = str(attrs.get("title") or "this system")
    abstract = str(attrs.get("abstract") or "")
    chunk_id = chunks[0]["chunk_id"] if chunks else doc["node_id"]
    topic = _slug(title.split(":")[0], "systems")
    statement = _first_sentence(abstract) or f"{title} proposes a systems mechanism with measurable trade-offs."
    return {
        "evidence": [
            {
                "id": "e1",
                "statement": statement,
                "rationale": "Derived from the paper abstract or first full-text chunk.",
                "source_chunk_id": chunk_id,
                "strength": "moderate",
            }
        ],
        "design_principles": [
            {
                "id": "p1",
                "statement": "Make the dominant bottleneck explicit before optimizing the system design.",
                "why_it_matters": (
                    "The paper frames its contribution around a specific bottleneck, "
                    "constraint, or inefficiency and then builds the design around it."
                ),
                "domain": _infer_domain(title, abstract),
                "topic_slugs": [topic],
                "strength": "moderate",
                "evidence_ids": ["e1"],
            }
        ],
        "mechanisms": [
            {
                "id": "m1",
                "name": title,
                "mechanism_kind": _infer_mechanism_kind(title, abstract),
                "applicability": statement,
                "known_limits": "Use the paper evaluation and limitations before applying this mechanism outside the studied setting.",
                "topic_slugs": [topic],
                "strength": "moderate",
                "evidence_ids": ["e1"],
                "instantiates": ["p1"],
            }
        ],
        "trade_offs": [],
        "anti_patterns": [],
    }


def _infer_domain(title: str, abstract: str) -> str:
    text = f"{title} {abstract}".lower()
    if any(term in text for term in ("network", "routing", "packet", "switch", "tcp", "rdma", "wan")):
        return "networking"
    if any(term in text for term in ("database", "query", "transaction", "sql", "index")):
        return "databases"
    if any(term in text for term in ("training", "gpu", "model", "ml", "inference")):
        return "ml_systems"
    if any(term in text for term in ("consensus", "distributed", "replication", "cluster")):
        return "distributed_systems"
    return "other"


def _infer_mechanism_kind(title: str, abstract: str) -> str:
    text = f"{title} {abstract}".lower()
    if any(term in text for term in ("algorithm", "scheduler", "scheduling", "optimization", "solver")):
        return "algorithm"
    if any(term in text for term in ("protocol", "tcp", "consensus")):
        return "protocol"
    if any(term in text for term in ("index", "tree", "hash table", "sketch", "queue")):
        return "data_structure"
    if any(term in text for term in ("architecture", "framework", "stack", "fabric")):
        return "architecture"
    return "design_pattern"


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _sanitize_extraction(
    raw: dict[str, Any],
    *,
    doc: dict[str, Any],
    chunks: list[dict[str, str]],
    extractor: str,
    model: str,
    extracted_at: str,
    llm_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    attrs = doc["attrs"]
    chunk_ids = {chunk["chunk_id"] for chunk in chunks}
    fallback_chunk = chunks[0]["chunk_id"] if chunks else doc["node_id"]
    record: dict[str, Any] = {
        "paper_id": attrs.get("paper_id"),
        "document_id": doc["node_id"],
        "title": attrs.get("title"),
        "venue_id": attrs.get("venue_id"),
        "year": attrs.get("year"),
        "doi": attrs.get("doi"),
        "source_chunk_ids": [chunk["chunk_id"] for chunk in chunks],
        "extractor": extractor,
        "model": model,
        "extracted_at": extracted_at,
        "domain": _infer_domain(str(attrs.get("title") or ""), str(attrs.get("abstract") or "")),
    }
    if llm_metadata:
        record["llm_metadata"] = llm_metadata

    evidence: list[dict[str, Any]] = []
    for index, item in enumerate(_as_list(raw.get("evidence")), start=1):
        if not isinstance(item, dict):
            continue
        statement = str(item.get("statement") or "").strip()
        if not statement:
            continue
        source_chunk_id = str(item.get("source_chunk_id") or fallback_chunk)
        if source_chunk_id not in chunk_ids:
            source_chunk_id = fallback_chunk
        local_id = _slug(str(item.get("id") or statement), f"e{index}")
        evidence.append(
            {
                "id": local_id,
                "kind": "paper_extraction",
                "statement": statement[:700],
                "rationale": str(item.get("rationale") or "")[:900],
                "source_chunk_id": source_chunk_id,
                "strength": _strength(item.get("strength")),
            }
        )
    if not evidence:
        evidence = _heuristic_extract(doc, chunks)["evidence"]
    evidence_ids = {item["id"] for item in evidence}
    first_evidence = evidence[0]["id"]
    record["evidence"] = evidence

    record["design_principles"] = _sanitize_principles(
        raw.get("design_principles"), evidence_ids, first_evidence, record["domain"]
    )
    record["mechanisms"] = _sanitize_mechanisms(
        raw.get("mechanisms"), evidence_ids, first_evidence
    )
    principle_ids = {item["id"] for item in record["design_principles"]}
    mechanism_ids = {item["id"] for item in record["mechanisms"]}
    for mechanism in record["mechanisms"]:
        mechanism["instantiates"] = [
            ref for ref in _as_list(mechanism.get("instantiates")) if ref in principle_ids
        ][:3]
    record["trade_offs"] = _sanitize_tradeoffs(
        raw.get("trade_offs"), evidence_ids, first_evidence, mechanism_ids
    )
    record["anti_patterns"] = _sanitize_antipatterns(
        raw.get("anti_patterns"), evidence_ids, first_evidence, mechanism_ids
    )
    record["content_hash"] = _sha(record)
    return record


def _strength(value: Any) -> str:
    text = str(value or "moderate").lower()
    return text if text in STRENGTHS else "moderate"


def _topics(value: Any) -> list[str]:
    topics = []
    for item in _as_list(value):
        slug = _slug(str(item), "")
        if slug:
            topics.append(slug)
    return topics[:8]


def _evidence_refs(value: Any, evidence_ids: set[str], fallback: str) -> list[str]:
    refs = [_slug(str(item), "") for item in _as_list(value)]
    refs = [ref for ref in refs if ref in evidence_ids]
    return refs[:5] or [fallback]


def _sanitize_principles(
    value: Any,
    evidence_ids: set[str],
    fallback_evidence: str,
    fallback_domain: str,
) -> list[dict[str, Any]]:
    out = []
    for index, item in enumerate(_as_list(value), start=1):
        if not isinstance(item, dict):
            continue
        statement = str(item.get("statement") or "").strip()
        if not statement:
            continue
        domain = str(item.get("domain") or fallback_domain)
        if domain not in ALLOWED_DOMAINS:
            domain = fallback_domain if fallback_domain in ALLOWED_DOMAINS else "other"
        out.append(
            {
                "id": _slug(str(item.get("id") or statement), f"p{index}"),
                "statement": statement[:600],
                "why_it_matters": str(item.get("why_it_matters") or "")[:900],
                "domain": domain,
                "topic_slugs": _topics(item.get("topic_slugs")),
                "strength": _strength(item.get("strength")),
                "evidence_ids": _evidence_refs(item.get("evidence_ids"), evidence_ids, fallback_evidence),
            }
        )
    return out[:3]


def _sanitize_mechanisms(
    value: Any,
    evidence_ids: set[str],
    fallback_evidence: str,
) -> list[dict[str, Any]]:
    out = []
    for index, item in enumerate(_as_list(value), start=1):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        kind = str(item.get("mechanism_kind") or "other")
        if kind not in ALLOWED_MECHANISM_KINDS:
            kind = "other"
        out.append(
            {
                "id": _slug(str(item.get("id") or name), f"m{index}"),
                "name": name[:260],
                "mechanism_kind": kind,
                "applicability": str(item.get("applicability") or "")[:900],
                "known_limits": str(item.get("known_limits") or "")[:900],
                "topic_slugs": _topics(item.get("topic_slugs")),
                "strength": _strength(item.get("strength")),
                "evidence_ids": _evidence_refs(item.get("evidence_ids"), evidence_ids, fallback_evidence),
                "instantiates": [_slug(str(ref), "") for ref in _as_list(item.get("instantiates"))],
            }
        )
    return out[:4]


def _sanitize_tradeoffs(
    value: Any,
    evidence_ids: set[str],
    fallback_evidence: str,
    mechanism_ids: set[str],
) -> list[dict[str, Any]]:
    out = []
    for index, item in enumerate(_as_list(value), start=1):
        if not isinstance(item, dict):
            continue
        objective_a = str(item.get("objective_a") or "").strip()
        objective_b = str(item.get("objective_b") or "").strip()
        tension = str(item.get("tension") or "").strip()
        if not objective_a or not objective_b or not tension:
            continue
        out.append(
            {
                "id": _slug(str(item.get("id") or f"{objective_a}-{objective_b}"), f"t{index}"),
                "objective_a": objective_a[:180],
                "objective_b": objective_b[:180],
                "tension": tension[:700],
                "failure_modes": str(item.get("failure_modes") or "")[:900],
                "topic_slugs": _topics(item.get("topic_slugs")),
                "strength": _strength(item.get("strength")),
                "evidence_ids": _evidence_refs(item.get("evidence_ids"), evidence_ids, fallback_evidence),
                "restricts": [
                    ref for ref in [_slug(str(ref), "") for ref in _as_list(item.get("restricts"))]
                    if ref in mechanism_ids
                ][:3],
            }
        )
    return out[:3]


def _sanitize_antipatterns(
    value: Any,
    evidence_ids: set[str],
    fallback_evidence: str,
    mechanism_ids: set[str],
) -> list[dict[str, Any]]:
    out = []
    for index, item in enumerate(_as_list(value), start=1):
        if not isinstance(item, dict):
            continue
        approach = str(item.get("approach") or "").strip()
        why = str(item.get("why_it_tends_to_fail") or "").strip()
        if not approach or not why:
            continue
        out.append(
            {
                "id": _slug(str(item.get("id") or approach), f"a{index}"),
                "approach": approach[:500],
                "why_it_tends_to_fail": why[:900],
                "topic_slugs": _topics(item.get("topic_slugs")),
                "strength": _strength(item.get("strength")),
                "evidence_ids": _evidence_refs(item.get("evidence_ids"), evidence_ids, fallback_evidence),
                "mitigated_by": [
                    ref for ref in [_slug(str(ref), "") for ref in _as_list(item.get("mitigated_by"))]
                    if ref in mechanism_ids
                ][:3],
            }
        )
    return out[:2]


def _cache_path(cache_dir: Path, *, model: str, prompt_hash: str) -> Path:
    safe_model = re.sub(r"[^a-zA-Z0-9_.-]+", "_", model)
    return cache_dir / safe_model / f"{prompt_hash}.json"


def _extract_one(
    doc: dict[str, Any],
    chunks: list[dict[str, str]],
    *,
    backend: str,
    model: str,
    cache_dir: Path,
    max_chars: int,
    timeout: int,
    force: bool,
) -> dict[str, Any]:
    prompt = _build_prompt(doc, chunks, max_chars)
    prompt_hash = _sha({"model": model, "prompt": prompt})
    path = _cache_path(cache_dir, model=model, prompt_hash=prompt_hash)
    if path.is_file() and not force:
        raw = json.loads(path.read_text(encoding="utf-8"))
        extractor = raw.get("_extractor", backend)
        payload = raw.get("payload", raw)
        extracted_at = raw.get("_extracted_at") or _utc_now()
        llm_metadata = raw.get("_response_metadata") or {}
        if "_extracted_at" not in raw:
            raw["_extracted_at"] = extracted_at
            path.write_text(json.dumps(raw, sort_keys=True, indent=2), encoding="utf-8")
    else:
        extracted_at = _utc_now()
        if backend == "heuristic":
            payload = _heuristic_extract(doc, chunks)
            llm_metadata = {}
        else:
            response_payload = _call_openrouter(prompt, model=model, timeout=timeout)
            payload = response_payload["payload"]
            llm_metadata = response_payload["metadata"]
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = {
            "_extractor": backend,
            "_model": model,
            "_extracted_at": extracted_at,
            "_prompt_hash": prompt_hash,
            "_response_metadata": llm_metadata,
            "payload": payload,
        }
        path.write_text(json.dumps(raw, sort_keys=True, indent=2), encoding="utf-8")
        extractor = backend
    return _sanitize_extraction(
        payload,
        doc=doc,
        chunks=chunks,
        extractor=extractor,
        model=model,
        extracted_at=extracted_at,
        llm_metadata=llm_metadata,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dsn", default=DEFAULT_DSN)
    parser.add_argument("--generation-id", type=int, default=10)
    parser.add_argument("--source-pack", default="systems-db-2022-2026")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--env-file", type=Path, default=Path("/Users/jason/projects/mit/okg/.env"))
    parser.add_argument("--backend", choices=["openrouter", "heuristic"], default="openrouter")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--max-chunks", type=int, default=6)
    parser.add_argument("--max-prompt-chars", type=int, default=18000)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    _load_env_file(args.env_file)
    docs = _load_documents(
        args.dsn,
        args.generation_id,
        source_pack=args.source_pack,
        limit=args.limit,
        offset=args.offset,
    )
    if not docs:
        raise SystemExit("no source documents found")

    records = []
    for index, doc in enumerate(docs, start=1):
        chunks = _load_chunks(
            args.dsn,
            args.generation_id,
            document_id=doc["node_id"],
            source_pack=args.source_pack,
        )
        selected = _select_evidence_chunks(chunks, args.max_chunks)
        record = _extract_one(
            doc,
            selected,
            backend=args.backend,
            model=args.model,
            cache_dir=args.cache_dir,
            max_chars=args.max_prompt_chars,
            timeout=args.timeout,
            force=args.force,
        )
        records.append(record)
        counts = {
            key: len(record.get(key) or [])
            for key in ("evidence", "design_principles", "mechanisms", "trade_offs", "anti_patterns")
        }
        print(
            f"[{index}/{len(docs)}] {record['paper_id']} "
            f"e={counts['evidence']} p={counts['design_principles']} "
            f"m={counts['mechanisms']} t={counts['trade_offs']} a={counts['anti_patterns']}",
            file=sys.stderr,
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.out.with_suffix(args.out.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    tmp.replace(args.out)

    summary = {
        "out": str(args.out),
        "records": len(records),
        "evidence": sum(len(record.get("evidence") or []) for record in records),
        "design_principles": sum(len(record.get("design_principles") or []) for record in records),
        "mechanisms": sum(len(record.get("mechanisms") or []) for record in records),
        "trade_offs": sum(len(record.get("trade_offs") or []) for record in records),
        "anti_patterns": sum(len(record.get("anti_patterns") or []) for record in records),
        "backend": args.backend,
        "model": args.model,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
