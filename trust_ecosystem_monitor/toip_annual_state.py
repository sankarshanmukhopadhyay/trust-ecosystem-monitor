"""Append-only observed source revisions and immutable monthly intelligence snapshots.

A month is observed at collection time, never reconstructed as if a current
Confluence page body existed at the month-end cutoff. Original observations
are immutable; later changes are separate dated ledger entries.
"""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "tem-cy-intelligence-v1"

def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()

def _utc(value):
    if not isinstance(value, str):
        raise ValueError("observation timestamp required")
    date = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if date.tzinfo is None:
        raise ValueError("timezone required")
    return date.astimezone(timezone.utc).isoformat()

def _source(page):
    page_id = str(page.get("id", ""))
    if not page_id.isdigit():
        raise ValueError("invalid tracked Confluence ID")
    sections = page.get("section_abstracts", [])
    discussions = page.get("discussion_blocks", [])
    return {
        "id": page_id,
        "url": "https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/" + page_id,
        "title": str(page.get("title", ""))[:160],
        "version": page.get("version"),
        "version_created_at": page.get("version_created_at"),
        "page_kind": page.get("page_kind", "unknown"),
        "github_references": page.get("github_references", []),
        "content_fingerprint": _digest({
            "sections": [(s.get("basis_sha256"), s.get("abstract")) for s in sections],
            "headings": page.get("topic_headings", []),
            "discussion_passages": [(d.get("basis_sha256"), d.get("references", [])) for d in discussions],
            "github_references": page.get("github_references", []),
        }),
        "discussions": [{
            "heading": str(d.get("section", "General"))[:120],
            "summary": str(d.get("abstract", ""))[:280],
            "basis_sha256": d.get("basis_sha256"),
            "signal": list(d.get("language_signals", [])),
            "references": list(d.get("references", []))[:8],
            "source_block_number": d.get("source_block_number"),
        } for d in discussions[:8] if d.get("basis_sha256")],
        "evidence": [{
            "heading": str(s.get("section", "General"))[:120],
            "abstract": str(s.get("abstract", ""))[:300],
            "basis_sha256": s.get("basis_sha256"),
        } for s in sections[:6] if s.get("basis_sha256")],
    }

def empty(year):
    if not isinstance(year, int) or not 2000 <= year <= 2100:
        raise ValueError("unsupported calendar year")
    return {"schema": SCHEMA, "year": year, "months": {},
            "source_ledger": {}, "revision_notices": []}

def validate(data):
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ValueError("invalid annual intelligence schema")
    year = data.get("year")
    if not isinstance(year, int):
        raise ValueError("year required")
    if not isinstance(data.get("months"), dict) or not isinstance(data.get("source_ledger"), dict):
        raise ValueError("annual inventory required")
    if not isinstance(data.get("revision_notices"), list):
        raise ValueError("revision notices must be array")
    for month, record in data["months"].items():
        if not month.startswith(str(year) + "-") or record.get("period") != month:
            raise ValueError("foreign month in annual manifest")
        if record.get("observation_digest") != _digest(record["observation"]):
            raise ValueError("monthly observation digest mismatch")
    return data

def ingest(data, github, content, *, observed_at, tracked_pages=None):
    """Record new monthly snapshot once and append new observed source versions.

    Reruns of the same month don't overwrite history. If independently
    retrieved material differs, record an amendment notice, not a rewrite.
    """
    validate(data)
    when = _utc(observed_at)
    month = github.get("period")
    if not isinstance(month, str) or month[:4] != str(data["year"]) or content.get("month") != month:
        raise ValueError("source reporting periods differ")
    observation = {
        "github": {
            "scope": github.get("collection_scope"),
            "coverage_complete": github.get("coverage_complete"),
            "evidence": github.get("evidence", []),
        },
        "confluence": {
            "coverage": content.get("coverage", "sample_only"),
            "source_count": len(content.get("pages", [])),
            "unavailable_count": content.get("unavailable_count", 0),
            "sources": [_source(p) for p in content.get("pages", [])],
        },
    }
    digest = _digest(observation)
    months = data["months"]
    if month not in months:
        months[month] = {"period": month, "observed_at": when,
                         "observation": observation, "observation_digest": digest,
                         "temporal_basis": "retrospective-current-public-source"}
    elif months[month]["observation_digest"] != digest:
        key = "month:" + month + ":" + digest
        if not any(n["key"] == key for n in data["revision_notices"]):
            data["revision_notices"].append({
                "key": key, "kind": "month_reobservation", "period": month,
                "observed_at": when, "source": "monthly-run",
                "prior_digest": months[month]["observation_digest"],
                "current_digest": digest,
                "impact": "review_required",
                "explanation": "Newly collected evidence differs from the immutable first observation. Earlier report is not overwritten.",
            })
    # Previously tracked pages are re-inspected without being counted as
    # newly observed monthly discussions or recast into that month.
    seen = {p["id"] for p in observation["confluence"]["sources"]}
    tracked = [_source(p) for p in (tracked_pages or []) if str(p.get("id", "")) not in seen]
    for record in observation["confluence"]["sources"] + tracked:
        ident = record["id"]
        ledger = data["source_ledger"].setdefault(ident, [])
        fingerprint = record["content_fingerprint"]
        version = record["version"]
        if not ledger:
            ledger.append({"observed_at": when, "observed_in": month, **record})
            continue
        latest = ledger[-1]
        if latest["version"] == version and latest["content_fingerprint"] == fingerprint:
            continue
        # Do not add a second notice for reprocessing the identical version.
        if any(e["version"] == version and e["content_fingerprint"] == fingerprint for e in ledger):
            continue
        ledger.append({"observed_at": when, "observed_in": month, **record})
        key = "source:" + ident + ":" + fingerprint
        data["revision_notices"].append({
            "key": key, "kind": ("source_version_change" if latest["version"] != version else "interpretation_method_change"), "period": month,
            "observed_at": when, "source": record["url"], "page_id": ident,
            "previous_version": latest["version"], "current_version": version,
            "prior_digest": latest["content_fingerprint"], "current_digest": fingerprint,
            "impact": "review_required",
            "explanation": ("Public page version changed; historical interpretation requires review." if latest["version"] != version else "Extraction results changed while the page version stayed constant; source text change is not established."),
            "first_observed_in": latest["observed_in"],
        })
    data["revision_notices"].sort(key=lambda x: (x["observed_at"], x["key"]))
    validate(data)
    return data

def read(path: Path, year: int):
    if not path.exists():
        return empty(year)
    value = validate(json.loads(path.read_text(encoding="utf-8")))
    if value["year"] != year:
        raise ValueError("wrong annual year")
    return value

def write(path: Path, data):
    validate(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Stable content and atomic replacement after all checks succeed.
    staged = path.with_suffix(".tmp")
    staged.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    staged.replace(path)
