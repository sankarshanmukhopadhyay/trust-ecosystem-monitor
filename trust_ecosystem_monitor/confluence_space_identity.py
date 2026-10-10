"""Public Confluence space-identity metadata probe, not an authority determination."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

MAX_BYTES = 65536
SPACE_ID = re.compile(r"[0-9]{1,20}$")


def inspect_space(space_id: str, *, opener=urlopen) -> dict:
    if not SPACE_ID.fullmatch(space_id):
        raise ValueError("space ID must be bounded decimal digits")
    result = {"source": "confluence_v2_public_space", "requested_space_id": space_id,
              "identity_verified": False, "authority_verified": False,
              "publication_rights_verified": False, "coverage": "not_checked"}
    request = Request(f"https://lf-toip.atlassian.net/wiki/api/v2/spaces/{space_id}",
                      headers={"Accept": "application/json", "User-Agent": "TEM-Public-Space-Identity/1.0"})
    try:
        with opener(request, timeout=15) as response:
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                return {**result, "coverage": "unavailable", "reason": "response_limit"}
            data = json.loads(raw)
    except HTTPError as exc:
        return {**result, "coverage": "unavailable", "http_status": exc.code}
    except (URLError, TimeoutError, OSError, ValueError, UnicodeError) as exc:
        return {**result, "coverage": "unavailable", "reason": type(exc).__name__}
    if not isinstance(data, dict) or str(data.get("id")) != space_id:
        return {**result, "coverage": "unavailable", "reason": "identity_mismatch"}
    # Only allowlisted public space-level metadata; no page or user content.
    result["identity_verified"] = True
    result["coverage"] = "metadata_only"
    for field in ("key", "name", "type", "status"):
        value = data.get(field)
        if isinstance(value, str) and len(value) <= 150:
            result[field] = value
    result["retrieved_at"] = datetime.now(timezone.utc).isoformat()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--space-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = inspect_space(args.space_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
