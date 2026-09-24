from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path

from . import site_backend


PROJECT_TITLE = "Trust Ecosystem Monitor"


def _brand_html(text: str, profile: dict) -> str:
    organization = str(profile.get("organization", "unknown"))
    weekly_title = str(profile.get("weekly_brief_title", "Weekly Ecosystem Brief"))
    disclaimer = str(
        profile.get(
            "disclaimer",
            "Independent observatory; not an official publication of the monitored ecosystem.",
        )
    )
    replacements = {
        "ToIP Portfolio Monitor": PROJECT_TITLE,
        "ToIP Weekly Portfolio Brief": weekly_title,
        "<code>trustoverip</code>": f"<code>{html.escape(organization)}</code>",
        "not an official Trust Over IP Foundation publication.": html.escape(disclaimer),
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def _add_taxonomy_nav(text: str) -> str:
    marker = '<a href="methodology.html">Method</a>'
    addition = '<a href="taxonomy.html">Taxonomy</a>' + marker
    return text.replace(marker, addition) if "taxonomy.html" not in text else text


def _add_catalog_nav(text: str, catalog_href: str) -> str:
    """Add a persistent route back to the root ecosystem catalog.

    Normal ecosystem pages have a shared sticky header. Archived weekly pages
    predate that navigation shell, so they receive a small return link directly
    after the opening body tag instead.
    """
    if "All ecosystems" in text:
        return text
    escaped_href = html.escape(catalog_href, quote=True)
    brand = f'<span class="brand">{PROJECT_TITLE}</span>'
    if brand in text:
        return text.replace(
            brand,
            brand + f'<a class="catalog-link" href="{escaped_href}">All ecosystems</a>',
            1,
        )
    body = "<body>"
    fallback = (
        f'<div style="max-width:1180px;margin:1rem auto 0;padding:0 1.4rem">'
        f'<a href="{escaped_href}">← All ecosystems</a></div>'
    )
    return text.replace(body, body + fallback, 1) if body in text else text


def _render_taxonomy(snapshot: dict, docs: Path) -> None:
    profile = snapshot.get("ecosystem_profile", {})
    repositories = snapshot.get("repositories", [])
    rows = []
    for repository in sorted(repositories, key=lambda item: (str(item.get("portfolio", "")), str(item.get("name", "")).lower())):
        classification = repository.get("classification", {})
        method = str(classification.get("method", "legacy/unknown"))
        rule = classification.get("rule") or "—"
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(repository.get('portfolio', '')))}</td>"
            f"<td><a href='{html.escape(str(repository.get('url', '')))}'>{html.escape(str(repository.get('name', '')))}</a></td>"
            f"<td>{html.escape(str(repository.get('lifecycle', '')))}</td>"
            f"<td><code>{html.escape(method)}</code></td>"
            f"<td><code>{html.escape(str(rule))}</code></td>"
            "</tr>"
        )

    counts = {"override": 0, "rule": 0, "unclassified": 0, "legacy/unknown": 0}
    for repository in repositories:
        method = str(repository.get("classification", {}).get("method", "legacy/unknown"))
        counts[method] = counts.get(method, 0) + 1

    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Taxonomy · {PROJECT_TITLE}</title>
<style>:root{{--ink:#172033;--muted:#657083;--line:#d9dee7;--panel:#f6f8fb;--accent:#075985}}*{{box-sizing:border-box}}body{{margin:0;font:15.5px/1.55 system-ui,-apple-system,sans-serif;color:var(--ink)}}header{{border-bottom:1px solid var(--line);position:sticky;top:0;background:white}}.bar,main,footer{{max-width:1240px;margin:auto;padding:1rem 1.4rem}}.bar{{display:flex;gap:1rem;align-items:center;flex-wrap:wrap}}.brand{{font-weight:750;margin-right:auto}}a{{color:var(--accent)}}.bar a{{text-decoration:none}}.lede{{max-width:900px;color:#39465b}}.metrics{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.7rem;margin:1.2rem 0}}.metric{{background:var(--panel);border:1px solid var(--line);padding:.8rem;border-radius:.5rem}}.metric strong{{display:block;font-size:1.45rem}}table{{border-collapse:collapse;width:100%;font-size:.93rem}}th,td{{padding:.55rem;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{background:var(--panel)}}code{{background:var(--panel);padding:.1rem .25rem}}footer{{border-top:1px solid var(--line);color:var(--muted)}}</style></head><body>
<header><div class="bar"><span class="brand">{PROJECT_TITLE}</span><a href="index.html">Overview</a><a href="findings.html">Findings</a><a href="portfolios.html">Portfolios</a><a href="lifecycle.html">Lifecycle</a><a href="seams.html">Review seams</a><a href="evidence.html">Evidence</a><a href="taxonomy.html">Taxonomy</a><a href="methodology.html">Method</a></div></header>
<main><h1>Taxonomy provenance</h1><p class="lede">Why the monitor placed each repository in its current portfolio. Exact profile overrides take precedence over ordered pattern rules. Repositories with no defensible match remain explicitly <strong>Unclassified</strong>.</p>
<div class="metrics"><div class="metric"><strong>{counts.get('override',0)}</strong> explicit overrides</div><div class="metric"><strong>{counts.get('rule',0)}</strong> rule classifications</div><div class="metric"><strong>{counts.get('unclassified',0)}</strong> unclassified</div></div>
<table><thead><tr><th>Portfolio</th><th>Repository</th><th>Lifecycle</th><th>Method</th><th>Rule / override</th></tr></thead><tbody>{''.join(rows)}</tbody></table></main>
<footer>Profile: {html.escape(str(profile.get('id','unknown')))} · classification provenance is monitor metadata, not an upstream governance assertion.</footer></body></html>"""
    (docs / "taxonomy.html").write_text(page, encoding="utf-8")


def render_site(root: str | Path = ".") -> None:
    """Render one profile's site in a staging root."""
    root = Path(root)
    site_backend.render_site(root)

    latest = root / "docs" / "data" / "latest.json"
    if not latest.exists():
        return
    snapshot = json.loads(latest.read_text(encoding="utf-8"))
    profile = snapshot.get("ecosystem_profile", {})
    docs = root / "docs"
    _render_taxonomy(snapshot, docs)

    for path in docs.glob("*.html"):
        text = _brand_html(path.read_text(encoding="utf-8"), profile)
        text = _add_taxonomy_nav(text)
        path.write_text(_add_catalog_nav(text, "../index.html"), encoding="utf-8")

    reports = docs / "reports"
    if reports.exists():
        for path in reports.glob("*.html"):
            text = _brand_html(path.read_text(encoding="utf-8"), profile)
            path.write_text(_add_catalog_nav(text, "../../index.html"), encoding="utf-8")


def _ecosystem_cards(root: Path) -> list[dict]:
    cards: list[dict] = []
    docs = root / "docs"
    if not docs.exists():
        return cards
    for candidate in sorted(docs.iterdir()):
        latest = candidate / "data" / "latest.json"
        if not candidate.is_dir() or not latest.exists():
            continue
        try:
            snapshot = json.loads(latest.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        profile = snapshot.get("ecosystem_profile", {})
        findings = snapshot.get("findings", [])
        repositories = snapshot.get("repositories", [])
        open_findings = [finding for finding in findings if finding.get("status") == "open"]
        taxonomy_review = [finding for finding in open_findings if finding.get("category") == "classification"]
        substantive = [finding for finding in open_findings if finding.get("category") != "classification"]
        priority = [
            finding for finding in substantive
            if int(finding.get("materiality", 0)) >= 4 or int(finding.get("urgency", 0)) >= 3
        ]
        material_changes = [unit for unit in snapshot.get("change_units", []) if int(unit.get("materiality", 0)) >= 4]
        previous = snapshot.get("provenance", {}).get("previous_snapshot")
        cards.append(
            {
                "id": profile.get("id") or candidate.name,
                "display_name": profile.get("display_name") or snapshot.get("organization") or candidate.name,
                "organization": snapshot.get("organization", ""),
                "generated_at": snapshot.get("generated_at", ""),
                "repositories": len(repositories),
                "active": sum(r.get("lifecycle") == "active" for r in repositories),
                "material_changes": len(material_changes),
                "priority_findings": len(priority),
                "substantive_open": len(substantive),
                "taxonomy_review": len(taxonomy_review),
                "unclassified": sum(
                    r.get("portfolio") == "Unclassified" and r.get("lifecycle") == "active"
                    for r in repositories
                ),
                "observation_state": "stateful observation" if previous else "first baseline",
            }
        )
    return cards


def render_catalog(root: str | Path = ".") -> None:
    """Render the top-level multi-ecosystem landing page."""
    root = Path(root)
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    cards = _ecosystem_cards(root)

    rendered_cards = []
    for card in cards:
        generated = card["generated_at"]
        try:
            generated_label = datetime.fromisoformat(generated).strftime("%Y-%m-%d %H:%M UTC")
        except (TypeError, ValueError):
            generated_label = generated or "not yet generated"
        rendered_cards.append(
            "<article class='card'>"
            f"<h2>{html.escape(str(card['display_name']))}</h2>"
            f"<p><code>{html.escape(str(card['organization']))}</code> · {html.escape(str(card['observation_state']))}</p>"
            "<div class='metrics'>"
            f"<span><strong>{card['repositories']}</strong> repositories</span>"
            f"<span><strong>{card['active']}</strong> active</span>"
            f"<span><strong>{card['material_changes']}</strong> material changes</span>"
            f"<span><strong>{card['priority_findings']}</strong> priority findings</span>"
            f"<span><strong>{card['substantive_open']}</strong> substantive open</span>"
            f"<span><strong>{card['taxonomy_review']}</strong> taxonomy review</span>"
            "</div>"
            f"<p class='muted'>Generated {html.escape(generated_label)} · {card['unclassified']} active repositories remain unclassified.</p>"
            f"<p><a class='button' href='{html.escape(str(card['id']))}/index.html'>Open ecosystem brief →</a></p>"
            "</article>"
        )

    body = "".join(rendered_cards) or (
        "<article class='card'><h2>No ecosystem reports yet</h2>"
        "<p>Run collection for at least one organization profile.</p></article>"
    )
    relationship_summary = ""
    relationship_data = docs / "data" / "relationships.json"
    if relationship_data.exists():
        try:
            relationship_payload = json.loads(relationship_data.read_text(encoding="utf-8"))
            relationship_counts = relationship_payload.get("counts", {})
            relationship_summary = (
                "<section class='card'>"
                "<h2>Cross-ecosystem intelligence</h2>"
                f"<p><strong>{int(relationship_counts.get('established', 0))}</strong> established relationships · "
                f"<strong>{int(relationship_counts.get('candidate', 0))}</strong> candidates awaiting stronger evidence or review.</p>"
                "<p class='muted'>Relationships are derived above profile-local evidence; co-location never implies dependency or alignment.</p>"
                "<p><a class='button' href='relationships.html'>Open relationship register →</a></p>"
                "</section>"
            )
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            relationship_summary = ""

    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{PROJECT_TITLE}</title>
<style>
:root{{--ink:#172033;--muted:#657083;--line:#d9dee7;--panel:#f6f8fb;--accent:#075985}}
*{{box-sizing:border-box}}body{{margin:0;font:16px/1.55 system-ui,-apple-system,sans-serif;color:var(--ink)}}
header{{border-bottom:1px solid var(--line)}}header div,main,footer{{max-width:1180px;margin:auto;padding:1.2rem 1.4rem}}
h1{{margin:.3rem 0}}.lede{{max-width:850px;color:#39465b;font-size:1.08rem}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:1rem;margin:2rem 0}}
.card{{border:1px solid var(--line);border-radius:.65rem;padding:1.2rem;background:white}}.metrics{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.5rem;margin:1rem 0}}.metrics span{{background:var(--panel);padding:.65rem;border-radius:.4rem}}.metrics strong{{display:block;font-size:1.35rem}}
.muted{{color:var(--muted)}}a{{color:var(--accent)}}.button{{font-weight:650;text-decoration:none}}code{{background:var(--panel);padding:.1rem .25rem;border-radius:.2rem}}footer{{border-top:1px solid var(--line);color:var(--muted)}}
</style></head><body>
<header><div><strong>{PROJECT_TITLE}</strong></div></header>
<main><h1>Monitored trust ecosystems</h1>
<p class="lede">Independent, evidence-backed observation of GitHub-based trust ecosystems. Taxonomy-review items are shown separately from substantive findings so classification maintenance is not presented as ecosystem operational risk.</p>
{relationship_summary}
<div class="grid">{body}</div>
<h2>Interpretation boundary</h2>
<p>Co-location in this catalog does not assert a technical, governance or dependency relationship between ecosystems. Cross-ecosystem analysis is separately derived from explicit evidence; candidate and Grade C propositions are never presented as established dependencies.</p>
</main><footer>Trust Ecosystem Monitor · independently maintained</footer></body></html>"""
    (docs / "index.html").write_text(page, encoding="utf-8")

    manifest = {
        "project": "trust-ecosystem-monitor",
        "ecosystems": cards,
    }
    (docs / "ecosystems.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
