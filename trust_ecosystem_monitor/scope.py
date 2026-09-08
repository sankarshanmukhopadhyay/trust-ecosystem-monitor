from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


def build_scope_register(snapshot: dict[str, Any]) -> dict[str, Any]:
    repositories = snapshot.get("repositories", [])
    records = []
    counts = {
        "discovered": len(repositories),
        "included": 0,
        "watch": 0,
        "review": 0,
        "excluded": 0,
        "deep_monitored": 0,
        "watch_monitored": 0,
        "inventory_only": 0,
    }

    for repository in repositories:
        admission = repository.get("admission") or {}
        state = str(admission.get("state", "review"))
        tier = str(admission.get("tier", "inventory"))
        if state in counts:
            counts[state] += 1
        if state == "included" and tier in {"core", "related"}:
            counts["deep_monitored"] += 1
        elif state == "watch" and tier == "watch":
            counts["watch_monitored"] += 1
        else:
            counts["inventory_only"] += 1

        records.append(
            {
                "repository": repository.get("full_name"),
                "url": repository.get("url"),
                "portfolio": repository.get("portfolio"),
                "lifecycle": repository.get("lifecycle"),
                "admission": admission,
                "discovery": repository.get("discovery", {}),
            }
        )

    return {
        "schema_version": "1",
        "ecosystem": snapshot.get("ecosystem_profile", {}),
        "generated_at": snapshot.get("generated_at"),
        "counts": counts,
        "repositories": records,
        "interpretation": {
            "discovered": "Repository was found through a declared discovery source; discovery alone does not authorize deep monitoring.",
            "deep_monitored": "Repository is admitted as included at core or related tier and receives full activity collection.",
            "watch_monitored": "Repository is admitted at watch tier and receives repository metadata plus release signals only.",
            "inventory_only": "Repository is retained for scope provenance but receives no routine activity collection.",
        },
    }


def render_scope(snapshot: dict[str, Any], ecosystem_docs: Path) -> tuple[Path, Path]:
    register = build_scope_register(snapshot)
    data_dir = ecosystem_docs / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    json_path = data_dir / "scope.json"
    json_path.write_text(json.dumps(register, indent=2) + "\n", encoding="utf-8")

    rows = []
    for record in sorted(register["repositories"], key=lambda item: str(item.get("repository") or "")):
        admission = record.get("admission") or {}
        discovery = record.get("discovery") or {}
        sources = discovery.get("sources") or []
        source_text = "; ".join(f"{source.get('type')}:{source.get('value')}" for source in sources) or "—"
        rationale = "; ".join(str(value) for value in admission.get("rationale", [])) or "—"
        evidence = admission.get("evidence", []) or []
        evidence_html = "<br>".join(
            f"<a href='{html.escape(str(url), quote=True)}'>evidence</a>" for url in evidence
        ) or "—"
        repo_url = html.escape(str(record.get("url") or ""), quote=True)
        repo_name = html.escape(str(record.get("repository") or ""))
        rows.append(
            "<tr>"
            f"<td><a href='{repo_url}'>{repo_name}</a></td>"
            f"<td>{html.escape(str(record.get('portfolio') or ''))}</td>"
            f"<td><code>{html.escape(str(admission.get('state', 'review')))}</code></td>"
            f"<td><code>{html.escape(str(admission.get('tier', 'inventory')))}</code></td>"
            f"<td>{html.escape(rationale)}</td>"
            f"<td>{evidence_html}</td>"
            f"<td>{html.escape(source_text)}</td>"
            "</tr>"
        )

    counts = register["counts"]
    profile = register.get("ecosystem", {})
    page = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Scope register · Trust Ecosystem Monitor</title>
<style>body{{font:15.5px/1.5 system-ui,sans-serif;max-width:1320px;margin:auto;padding:2rem;color:#172033}}a{{color:#075985}}.metrics{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.6rem;margin:1rem 0 1.5rem}}.metric{{padding:.75rem;background:#f6f8fb;border:1px solid #d9dee7;border-radius:.45rem}}.metric strong{{display:block;font-size:1.4rem}}table{{border-collapse:collapse;width:100%;font-size:.9rem}}th,td{{border-bottom:1px solid #d9dee7;padding:.5rem;text-align:left;vertical-align:top}}th{{background:#f6f8fb;position:sticky;top:0}}code{{background:#f6f8fb;padding:.1rem .25rem}}.muted{{color:#657083}}</style></head><body>
<p><a href='index.html'>← Ecosystem overview</a> · <a href='data/scope.json'>machine-readable scope</a></p>
<h1>Scope register</h1><p class='muted'>{html.escape(str(profile.get('display_name') or profile.get('id') or 'Unknown ecosystem'))} · generated {html.escape(str(register.get('generated_at') or ''))}</p>
<p>Discovery, admission and collection intensity are separate decisions. Ecosystem or organization membership does not by itself authorize deep monitoring.</p>
<div class='metrics'><div class='metric'><strong>{counts['discovered']}</strong>discovered</div><div class='metric'><strong>{counts['deep_monitored']}</strong>deep monitored</div><div class='metric'><strong>{counts['watch_monitored']}</strong>watch monitored</div><div class='metric'><strong>{counts['inventory_only']}</strong>inventory only</div><div class='metric'><strong>{counts['review']}</strong>review required</div><div class='metric'><strong>{counts['excluded']}</strong>excluded</div></div>
<table><thead><tr><th>Repository</th><th>Portfolio</th><th>Admission</th><th>Tier</th><th>Rationale</th><th>Evidence</th><th>Discovery provenance</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<h2>Interpretation boundary</h2><p><strong>Deep monitored</strong> means full activity collection for included core/related repositories. <strong>Watch monitored</strong> means repository metadata plus release signals only. <strong>Inventory only</strong> means provenance is retained without routine activity collection.</p></body></html>"""
    html_path = ecosystem_docs / "scope.html"
    html_path.write_text(page, encoding="utf-8")
    return html_path, json_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Render governed scope registers from generated ecosystem snapshots.")
    parser.add_argument("ecosystem_docs", nargs="+", help="One or more docs/<ecosystem-id> directories")
    args = parser.parse_args()

    for value in args.ecosystem_docs:
        docs = Path(value)
        latest = docs / "data" / "latest.json"
        if not latest.exists():
            raise SystemExit(f"missing generated snapshot: {latest}")
        snapshot = json.loads(latest.read_text(encoding="utf-8"))
        render_scope(snapshot, docs)


if __name__ == "__main__":
    main()
