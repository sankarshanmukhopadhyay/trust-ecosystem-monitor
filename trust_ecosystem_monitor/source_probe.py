"""Bounded, unauthenticated HTTP reachability probe; no source content is published.

Usage: python -m trust_ecosystem_monitor.source_probe --output source-probe.json
This is a diagnostic, not a source coverage or authorization assessment.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ENDPOINTS = {
    "confluence_v1_spaces": "https://lf-toip.atlassian.net/wiki/rest/api/space?limit=1",
    "confluence_v2_spaces": "https://lf-toip.atlassian.net/wiki/api/v2/spaces?limit=1",
    "confluence_v1_page": "https://lf-toip.atlassian.net/wiki/rest/api/content/22985064?expand=version,space",
    "confluence_v2_page": "https://lf-toip.atlassian.net/wiki/api/v2/pages/22985064",
    "lfx_public_calendar": "https://zoom-lfx.platform.linuxfoundation.org/meetings/ToIP?view=month",
}
MAX_BYTES = 2048


def probe(name: str, url: str, *, opener=urlopen) -> dict:
    result = {"source": name, "url": url, "status": "unavailable", "http_status": None}
    request = Request(url, headers={"User-Agent": "TEM-ReadOnly-Source-Diagnostic/1.0", "Accept": "application/json,text/html;q=0.5"})
    try:
        with opener(request, timeout=12) as response:
            result["http_status"] = response.status
            result["status"] = "reachable"
            result["content_type"] = response.headers.get("Content-Type", "").split(";")[0]
            result["sample_bytes_read"] = len(response.read(MAX_BYTES))
    except HTTPError as exc:
        result["http_status"] = exc.code
        result["status"] = "http_error"
    except (URLError, TimeoutError, OSError) as exc:
        result["status"] = "transport_error"
        result["error_type"] = type(exc).__name__
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = {
        "purpose": "public unauthenticated endpoint reachability only; not historical coverage",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "results": [probe(name, url) for name, url in ENDPOINTS.items()],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
