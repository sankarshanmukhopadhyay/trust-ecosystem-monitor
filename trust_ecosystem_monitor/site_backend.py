from __future__ import annotations

import html
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def link(url: str, label: str) -> str:
    return f'<a href="{esc(url)}">{esc(label)}</a>' if url else esc(label)


STYLE = """
:root{--ink:#172033;--muted:#657083;--line:#d9dee7;--panel:#f6f8fb;--accent:#075985;--warn:#92400e}
*{box-sizing:border-box}body{margin:0;font:15.5px/1.55 system-ui,-apple-system,sans-serif;color:var(--ink);background:white}
header{border-bottom:1px solid var(--line);background:#fff;position:sticky;top:0;z-index:3}.bar{max-width:1240px;margin:auto;padding:.8rem 1.4rem;display:flex;gap:1.2rem;align-items:center;flex-wrap:wrap}.brand{font-weight:750;margin-right:auto}.bar a{text-decoration:none;color:var(--accent)}
main{max-width:1240px;margin:auto;padding:2rem 1.4rem 4rem}h1{font-size:2rem;margin:.2rem 0 .5rem}h2{margin-top:2.2rem}.lede{font-size:1.08rem;color:#39465b;max-width:900px}.muted{color:var(--muted)}
.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:.7rem;margin:1.4rem 0}.metric{background:var(--panel);border:1px solid var(--line);padding:.9rem;border-radius:.55rem}.metric strong{font-size:1.55rem;display:block}.metric span{color:var(--muted)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:1rem}.card{border:1px solid var(--line);border-radius:.55rem;padding:1rem;background:white}.card h3{margin-top:0}.priority{border-left:4px solid var(--warn)}
table{border-collapse:collapse;width:100%;margin:1rem 0;font-size:.94rem}th,td{padding:.55rem;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{background:var(--panel);position:sticky;top:52px}code,pre{background:var(--panel);padding:.1rem .25rem;border-radius:.2rem}pre{padding:1rem;overflow:auto}a{color:var(--accent)}
.pill{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:.12rem .48rem;font-size:.8rem;margin-right:.25rem}.open{border-color:#f59e0b}.resolved,.accepted{border-color:#16a34a}.suppressed{border-color:#64748b}
footer{max-width:1240px;margin:auto;border-top:1px solid var(--line);padding:1.3rem;color:var(--muted)}
"""


def nav() -> str:
    return (
        '<header><div class="bar"><span class="brand">ToIP Portfolio Monitor</span>'
        '<a href="index.html">Overview</a><a href="findings.html">Findings</a>'
        '<a href="portfolios.html">Portfolios</a><a href="lifecycle.html">Lifecycle</a>'
        '<a href="seams.html">Review seams</a><a href="evidence.html">Evidence</a>'
        '<a href="methodology.html">Method</a></div></header>'
    )


def page(title: str, body: str, generated: str) -> str:
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{esc(title)} · ToIP Portfolio Monitor</title><style>{STYLE}</style></head>'
        f'<body>{nav()}<main>{body}</main><footer>Independent observatory · generated {esc(generated)} · '
        'not an official Trust Over IP Foundation publication.</footer></body></html>'
    )


def _evidence_links(values: list[str]) -> str:
    return " · ".join(link(url, "source") for url in values[:4]) or "—"


def _table(headers: list[str], rows: list[str], empty_columns: int, empty_text: str) -> str:
    body = "".join(rows) if rows else f'<tr><td colspan="{empty_columns}">{esc(empty_text)}</td></tr>'
    return '<table><thead><tr>' + ''.join(f'<th>{esc(h)}</th>' for h in headers) + '</tr></thead><tbody>' + body + '</tbody></table>'


def render_site(root: str | Path = ".") -> None:
    root = Path(root)
    source = root / "docs" / "data" / "latest.json"
    if not source.exists():
        raise FileNotFoundError("docs/data/latest.json does not exist; run collect first")

    snapshot = json.loads(source.read_text(encoding="utf-8"))
    docs = root / "docs"
    generated = snapshot["generated_at"]
    repositories = snapshot.get("repositories", [])
    events = snapshot.get("events", [])
    units = snapshot.get("change_units", [])
    findings = snapshot.get("findings", [])
    changes = snapshot.get("lifecycle_changes", [])
    seams = snapshot.get("cross_portfolio_seams", [])
    review_seams = [seam for seam in seams if seam.get("review_required", True)]
    tooling_observations = [seam for seam in seams if not seam.get("review_required", True)]
    open_findings = [f for f in findings if f.get("status") == "open"]
    critical = [f for f in open_findings if int(f.get("materiality", 0)) >= 4]
    unclassified = [r for r in repositories if r.get("portfolio") == "Unclassified" and r.get("lifecycle") == "active"]
    portfolios = sorted({r.get("portfolio", "Unclassified") for r in repositories})
    period = snapshot.get("period", {})
    week = datetime.fromisoformat(generated).isocalendar()
    week_label = f"{week.year}-W{week.week:02d}"

    priority_cards: list[str] = []
    for finding in critical[:8]:
        priority_cards.append(
            "<div class='card priority'>"
            f"<h3>{esc(finding['subject'])}</h3><p>{esc(finding['summary'])}</p>"
            f"<p><span class='pill open'>open</span> materiality {finding['materiality']} · urgency {finding['urgency']} · assurance {finding['assurance_impact']}</p>"
            f"<p>{_evidence_links(finding.get('evidence', []))}</p></div>"
        )
    if not priority_cards:
        priority_cards.append("<div class='card'><h3>No high-materiality open findings</h3><p class='muted'>The current observation has no open finding at materiality 4 or 5.</p></div>")

    material_rows: list[str] = []
    for unit in units:
        if int(unit.get("materiality", 0)) < 4:
            continue
        material_rows.append(
            "<tr>"
            f"<td>{esc(unit['portfolio'])}</td><td>{esc(unit['repository'])}</td><td>{esc(unit['title'])}</td>"
            f"<td>{unit['materiality']}</td><td>{_evidence_links(unit.get('evidence', []))}</td></tr>"
        )
    material_table = _table(["Portfolio", "Repository", "Change", "Materiality", "Evidence"], material_rows, 5, "No material change units in this observation.")

    explicit_count = sum(s.get("strength") == "explicit-reference" for s in review_seams)
    movement_count = sum(s.get("strength") == "related-co-movement" for s in review_seams)
    overview = (
        f"<h1>Weekly organization brief · {esc(week_label)}</h1>"
        '<p class="lede">A decision-first view of material movement across public repositories in the <code>trustoverip</code> GitHub organization. Raw activity remains available as auditable evidence, while the overview prioritizes findings, lifecycle changes, and cross-portfolio review seams.</p>'
        f"<p class='muted'>Observation window: {esc(period.get('since'))} → {esc(period.get('until'))}</p>"
        '<div class="metrics">'
        f"<div class='metric'><strong>{len(repositories)}</strong><span>repositories observed</span></div>"
        f"<div class='metric'><strong>{sum(r.get('lifecycle') == 'active' for r in repositories)}</strong><span>active repositories</span></div>"
        f"<div class='metric'><strong>{len(units)}</strong><span>change units</span></div>"
        f"<div class='metric'><strong>{len(open_findings)}</strong><span>open findings</span></div>"
        f"<div class='metric'><strong>{len(changes)}</strong><span>lifecycle deltas</span></div>"
        f"<div class='metric'><strong>{len(review_seams)}</strong><span>review seams</span></div></div>"
        f"<h2>What needs attention</h2><div class='grid'>{''.join(priority_cards)}</div>"
        '<h2>Organization pulse</h2><div class="grid">'
        f"<div class='card'><h3>Lifecycle movement</h3><p><strong>{len(changes)}</strong> repository-state changes detected against the prior retained observation.</p><p><a href='lifecycle.html'>Review lifecycle deltas →</a></p></div>"
        f"<div class='card'><h3>Cross-portfolio review</h3><p><strong>{explicit_count}</strong> explicit cross-portfolio references and <strong>{movement_count}</strong> weaker co-movement signals. <strong>{len(tooling_observations)}</strong> tooling/publication observations are retained separately and do not inflate the review count.</p><p><a href='seams.html'>Review seams →</a></p></div>"
        f"<div class='card'><h3>Classification hygiene</h3><p><strong>{len(unclassified)}</strong> active repositories remain explicitly unclassified.</p><p><a href='portfolios.html'>Inspect portfolio registry →</a></p></div></div>"
        f"<h2>Material change units</h2>{material_table}"
    )
    (docs / "index.html").write_text(page("Weekly overview", overview, generated), encoding="utf-8")

    finding_rows: list[str] = []
    for finding in findings:
        finding_rows.append(
            "<tr>"
            f"<td><span class='pill {esc(finding['status'])}'>{esc(finding['status'])}</span></td>"
            f"<td>{esc(finding['category'])}</td><td>{esc(finding['subject'])}</td>"
            f"<td>{esc(finding['summary'])}<br><code>{esc(finding['id'])}</code></td>"
            f"<td>{finding['materiality']}/{finding['urgency']}/{finding['assurance_impact']}</td>"
            f"<td>{_evidence_links(finding.get('evidence', []))}</td></tr>"
        )
    findings_table = _table(["Status", "Category", "Subject", "Finding", "M/U/A", "Evidence"], finding_rows, 6, "No findings generated.")
    findings_body = (
        '<h1>Findings</h1><p class="lede">Stable, machine-addressable observations with separate materiality, urgency, and assurance-impact dimensions. Non-open states are applied only from the governed disposition ledger.</p>'
        + findings_table
        + '<p>Governance decisions are recorded in <code>data/dispositions.json</code>; the monitor never auto-authorizes a disposition.</p>'
    )
    (docs / "findings.html").write_text(page("Findings", findings_body, generated), encoding="utf-8")

    by_portfolio: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for repo in repositories:
        by_portfolio[repo.get("portfolio", "Unclassified")].append(repo)
    portfolio_rows: list[str] = []
    for portfolio in portfolios:
        members = by_portfolio[portfolio]
        p_units = [u for u in units if u.get("portfolio") == portfolio]
        portfolio_rows.append(
            "<tr>"
            f"<td>{esc(portfolio)}</td><td>{len(members)}</td>"
            f"<td>{sum(r.get('lifecycle') == 'active' for r in members)}</td>"
            f"<td>{sum(r.get('lifecycle') == 'dormant' for r in members)}</td>"
            f"<td>{sum(r.get('lifecycle') == 'archived' for r in members)}</td>"
            f"<td>{len(p_units)}</td><td>{sum(int(u.get('materiality', 0)) >= 4 for u in p_units)}</td></tr>"
        )
    repository_rows = [
        "<tr>"
        f"<td>{esc(repo['portfolio'])}</td><td>{link(repo['url'], repo['name'])}</td>"
        f"<td>{esc(repo['kind'])}</td><td>{esc(repo['lifecycle'])}</td><td>{esc(repo.get('description'))}</td></tr>"
        for repo in repositories
    ]
    portfolios_body = (
        '<h1>Portfolio registry</h1><p class="lede">Dynamic organization discovery with deterministic portfolio, repository-kind, and lifecycle classification. <strong>Unclassified</strong> is an explicit review state, not an omission.</p>'
        '<h2>Portfolio summary</h2>'
        + _table(["Portfolio", "Repos", "Active", "Dormant", "Archived", "Change units", "Material"], portfolio_rows, 7, "No repositories discovered.")
        + '<h2>Repository registry</h2>'
        + _table(["Portfolio", "Repository", "Kind", "Lifecycle", "Description"], repository_rows, 5, "No repositories discovered.")
    )
    (docs / "portfolios.html").write_text(page("Portfolio registry", portfolios_body, generated), encoding="utf-8")

    lifecycle_rows = [
        "<tr>"
        f"<td>{esc(change['type'])}</td><td>{esc(change['portfolio'])}</td>"
        f"<td>{link(change.get('url', ''), change['repository'])}</td>"
        f"<td>{esc(change.get('from'))}</td><td>{esc(change.get('to'))}</td></tr>"
        for change in changes
    ]
    lifecycle_body = (
        '<h1>Lifecycle movement</h1><p class="lede">Changes are computed against the immediately preceding retained organization snapshot.</p>'
        + _table(["Type", "Portfolio", "Repository", "From", "To"], lifecycle_rows, 5, "No lifecycle deltas are available. The first baseline observation intentionally has no prior state.")
    )
    (docs / "lifecycle.html").write_text(page("Lifecycle movement", lifecycle_body, generated), encoding="utf-8")

    seam_rows: list[str] = []
    for seam in review_seams:
        seam_rows.append(
            "<tr>"
            f"<td><span class='pill'>{esc(seam['strength'])}</span></td>"
            f"<td>{esc(seam.get('relationship_class', 'cross-portfolio'))}</td>"
            f"<td>{esc(seam['source_portfolio'])} → {esc(seam['target_portfolio'])}</td>"
            f"<td>{esc(seam['source_repository'])}<br>{esc(seam['target_repository'])}</td>"
            f"<td>{esc(seam['summary'])}</td><td>{_evidence_links(seam.get('evidence', []))}</td></tr>"
        )
    tooling_rows: list[str] = []
    for seam in tooling_observations:
        tooling_rows.append(
            "<tr>"
            f"<td><span class='pill'>{esc(seam['strength'])}</span></td>"
            f"<td>{esc(seam.get('relationship_class', 'tooling-publication'))}</td>"
            f"<td>{esc(seam['source_repository'])}<br>{esc(seam['target_repository'])}</td>"
            f"<td>{esc(seam['summary'])}</td><td>{_evidence_links(seam.get('evidence', []))}</td></tr>"
        )
    seams_body = (
        '<h1>Cross-portfolio review seams</h1><p class="lede">A seam is a reason to review across portfolio boundaries, not a claim that a formal technical dependency exists. <code>explicit-reference</code> is stronger evidence than <code>related-co-movement</code>. Tooling/publication references are observed evidence but are not material review seams unless separate evidence establishes normative, semantic, conformance, governance, protocol, or machine-consumable impact.</p>'
        + _table(["Strength", "Class", "Portfolios", "Repositories", "Why surfaced", "Evidence"], seam_rows, 6, "No material cross-portfolio seams surfaced.")
        + '<h2>Tooling / publication observations</h2><p class="muted">Retained for auditability. These observations do not contribute to the review-seam count by default.</p>'
        + _table(["Strength", "Class", "Repositories", "Why retained", "Evidence"], tooling_rows, 5, "No tooling/publication observations surfaced.")
    )
    (docs / "seams.html").write_text(page("Cross-portfolio review seams", seams_body, generated), encoding="utf-8")

    evidence_rows = [
        "<tr>"
        f"<td>{esc(event.get('timestamp'))}</td><td>{esc(event.get('portfolio'))}</td>"
        f"<td>{esc(event.get('repository'))}</td><td>{esc(event.get('kind'))}</td>"
        f"<td>{esc(event.get('state'))}</td><td>{link(event.get('url', ''), event.get('title', ''))}</td></tr>"
        for event in events[:500]
    ]
    evidence_body = (
        '<h1>Evidence register</h1><p class="lede">Normalized source events remain the audit trail underneath change units, findings, and the weekly brief.</p>'
        + _table(["Time", "Portfolio", "Repository", "Type", "State", "Evidence"], evidence_rows, 6, "No evidence events in this observation.")
        + '<p><a href="data/latest.json">Download latest machine-readable snapshot →</a></p>'
    )
    (docs / "evidence.html").write_text(page("Evidence register", evidence_body, generated), encoding="utf-8")

    provenance = esc(json.dumps(snapshot.get("provenance", {}), indent=2))
    methodology_body = (
        '<h1>Method and governance boundary</h1><p class="lede">The monitor separates discovery, evidence collection, normalization, change-unit consolidation, organization semantics, findings, dispositions, and publication.</p>'
        '<div class="grid">'
        '<div class="card"><h3>Discovery</h3><p>Public repositories are dynamically enumerated from <code>trustoverip</code>. New repositories cannot silently fall outside a hand-maintained watch list.</p></div>'
        '<div class="card"><h3>Evidence</h3><p>Commits, issues, pull requests, releases, and repository metadata are normalized into auditable source records.</p></div>'
        '<div class="card"><h3>Interpretation</h3><p>Materiality and classification are deterministic. Change units intentionally favor false separation over accidental over-merging.</p></div>'
        '<div class="card"><h3>Review seams</h3><p>Explicit references and related co-movement are evidence-graded. A seam requests cross-review; it does not assert a dependency. Tooling/publication references remain observable but are excluded from material review counts unless stronger impact evidence exists.</p></div>'
        '<div class="card"><h3>Disposition</h3><p>Accepting, resolving, or suppressing a finding requires explicit authority, rationale, timestamp, and evidence in the durable ledger.</p></div>'
        '<div class="card"><h3>Upstream boundary</h3><p>The monitor observes public activity but does not automatically open issues, comment, merge changes, or otherwise modify TrustOverIP repositories.</p></div>'
        f'</div><h2>Snapshot provenance</h2><pre>{provenance}</pre>'
    )
    (docs / "methodology.html").write_text(page("Methodology", methodology_body, generated), encoding="utf-8")

    manifest = {
        "generated_at": generated,
        "week": week_label,
        "pages": ["index.html", "findings.html", "portfolios.html", "lifecycle.html", "seams.html", "evidence.html", "methodology.html"],
        "counts": {
            "repositories": len(repositories),
            "events": len(events),
            "change_units": len(units),
            "findings": len(findings),
            "open_findings": len(open_findings),
            "lifecycle_changes": len(changes),
            "cross_portfolio_seams": len(review_seams),
            "tooling_publication_observations": len(tooling_observations),
        },
    }
    (docs / "data" / "site-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
