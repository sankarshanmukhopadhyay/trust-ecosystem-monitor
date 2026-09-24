from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VALID_TYPES = {
    "normative_dependency", "informative_reference", "profiles", "implements",
    "extends", "interfaces_with", "shared_dependency", "semantic_overlap",
    "potential_conflict", "supersedes",
}
VALID_GRADES = {"A", "B", "C"}
VALID_STATES = {"candidate", "reviewed", "accepted", "rejected", "superseded"}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_registry(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != "1":
        errors.append("relationship registry schema_version must be '1'")
    seen: set[str] = set()
    for index, item in enumerate(payload.get("relationships", [])):
        prefix = f"relationships[{index}]"
        rid = str(item.get("id", "")).strip()
        if not rid:
            errors.append(f"{prefix}: id is required")
        elif rid in seen:
            errors.append(f"{prefix}: duplicate id {rid}")
        seen.add(rid)
        if item.get("type") not in VALID_TYPES:
            errors.append(f"{prefix}: unsupported relationship type {item.get('type')!r}")
        if item.get("evidence_grade") not in VALID_GRADES:
            errors.append(f"{prefix}: unsupported evidence grade {item.get('evidence_grade')!r}")
        if item.get("state") not in VALID_STATES:
            errors.append(f"{prefix}: unsupported state {item.get('state')!r}")
        evidence = item.get("evidence") or []
        if not evidence:
            errors.append(f"{prefix}: evidence is required")
        if item.get("evidence_grade") == "C" and item.get("state") == "accepted":
            errors.append(f"{prefix}: Grade C evidence cannot be accepted")
        if item.get("state") == "accepted" and item.get("evidence_grade") not in {"A", "B"}:
            errors.append(f"{prefix}: accepted relationships require Grade A or B evidence")
        for side in ("source", "target"):
            node = item.get(side) or {}
            for key in ("ecosystem", "repository", "artifact"):
                if not str(node.get(key, "")).strip():
                    errors.append(f"{prefix}: {side}.{key} is required")
    return errors


def _repository_index(root: Path) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    docs = root / "docs"
    for latest in docs.glob("*/data/latest.json"):
        try:
            snapshot = _load_json(latest)
        except (OSError, json.JSONDecodeError):
            continue
        ecosystem = snapshot.get("ecosystem_profile", {}).get("id") or latest.parents[1].name
        for repository in snapshot.get("repositories", []):
            name = repository.get("full_name")
            if name:
                index[name] = {
                    "ecosystem": ecosystem,
                    "lifecycle": repository.get("lifecycle"),
                    "portfolio": repository.get("portfolio"),
                    "url": repository.get("url"),
                    "snapshot_generated_at": snapshot.get("generated_at"),
                }
    return index


def derive_relationships(root: str | Path = ".") -> dict[str, Any]:
    root = Path(root)
    registry_path = root / "relationships" / "registry.json"
    payload = _load_json(registry_path)
    errors = validate_registry(payload)
    if errors:
        raise ValueError("; ".join(errors))

    repository_index = _repository_index(root)
    relationships: list[dict[str, Any]] = []
    for item in payload["relationships"]:
        record = dict(item)
        source_repo = item["source"]["repository"]
        target_repo = item["target"]["repository"]
        source_observed = repository_index.get(source_repo)
        target_observed = repository_index.get(target_repo)
        record["observation"] = {
            "source_observed": source_observed is not None,
            "target_observed": target_observed is not None,
            "source": source_observed,
            "target": target_observed,
        }
        record["publication_state"] = (
            "established"
            if item["state"] == "accepted" and item["evidence_grade"] in {"A", "B"}
            else "candidate"
        )
        relationships.append(record)

    return {
        "schema_version": "1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "authority": "derived",
        "interpretation": (
            "Cross-ecosystem relationships are derived from independently collected evidence. "
            "Candidate or Grade C records are discovery propositions, not dependencies, recognition, "
            "alignment, governance coordination, or interoperability claims."
        ),
        "relationships": relationships,
        "counts": {
            "established": sum(r["publication_state"] == "established" for r in relationships),
            "candidate": sum(r["publication_state"] == "candidate" for r in relationships),
            "grade_a": sum(r["evidence_grade"] == "A" for r in relationships),
            "grade_b": sum(r["evidence_grade"] == "B" for r in relationships),
            "grade_c": sum(r["evidence_grade"] == "C" for r in relationships),
        },
    }


def render(root: str | Path = ".") -> dict[str, Any]:
    root = Path(root)
    output = derive_relationships(root)
    docs = root / "docs"
    data = docs / "data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "relationships.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")

    rows = []
    for item in output["relationships"]:
        evidence = " ".join(
            f"<a href='{html.escape(url, quote=True)}'>evidence</a>" for url in item.get("evidence", [])
        )
        rows.append(
            "<tr>"
            f"<td><code>{html.escape(item['publication_state'])}</code></td>"
            f"<td>{html.escape(item['evidence_grade'])}</td>"
            f"<td>{html.escape(item['type'])}</td>"
            f"<td>{html.escape(item['source']['artifact'])}<br><small>{html.escape(item['source']['repository'])}</small></td>"
            f"<td>{html.escape(item['target']['artifact'])}<br><small>{html.escape(item['target']['repository'])}</small></td>"
            f"<td>{html.escape(item['rationale'])}</td>"
            f"<td>{evidence}</td>"
            "</tr>"
        )

    c = output["counts"]
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cross-ecosystem relationships · Trust Ecosystem Monitor</title>
<style>:root{{--ink:#172033;--muted:#657083;--line:#d9dee7;--panel:#f6f8fb;--accent:#075985}}*{{box-sizing:border-box}}body{{margin:0;font:15px/1.5 system-ui,-apple-system,sans-serif;color:var(--ink)}}header,main,footer{{max-width:1280px;margin:auto;padding:1rem 1.4rem}}header{{border-bottom:1px solid var(--line)}}a{{color:var(--accent)}}.metrics{{display:flex;gap:.7rem;flex-wrap:wrap;margin:1rem 0}}.metric{{background:var(--panel);padding:.7rem 1rem;border:1px solid var(--line);border-radius:.5rem}}.metric strong{{font-size:1.4rem;display:block}}table{{border-collapse:collapse;width:100%;font-size:.9rem}}th,td{{padding:.55rem;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{background:var(--panel)}}small{{color:var(--muted)}}.note{{max-width:950px;color:#39465b}}</style></head><body>
<header><strong>Trust Ecosystem Monitor</strong> · <a href="index.html">All ecosystems</a></header>
<main><h1>Cross-ecosystem relationships</h1>
<p class="note">{html.escape(output['interpretation'])}</p>
<div class="metrics"><div class="metric"><strong>{c['established']}</strong>established</div><div class="metric"><strong>{c['candidate']}</strong>candidate</div><div class="metric"><strong>{c['grade_a']}</strong>Grade A</div><div class="metric"><strong>{c['grade_b']}</strong>Grade B</div><div class="metric"><strong>{c['grade_c']}</strong>Grade C</div></div>
<table><thead><tr><th>State</th><th>Grade</th><th>Type</th><th>Source</th><th>Target</th><th>Why</th><th>Evidence</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
</main><footer>Generated {html.escape(output['generated_at'])} · derived layer; profile-local evidence remains authoritative for observations.</footer></body></html>"""
    (docs / "relationships.html").write_text(page, encoding="utf-8")
    return output


def main() -> int:
    render(".")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
