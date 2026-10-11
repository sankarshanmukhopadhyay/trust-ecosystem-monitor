"""Explicitly gated, bounded Confluence metadata collection; never publishes records."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .toip_confluence_acquisition import acquire_metadata
from .toip_confluence_admission import validate_authorization_decision


def collect(decision: dict, *, review: dict, revoked_ids: set[str],
            as_of: str, months: list[str], fetch=None) -> dict:
    """Collect metadata only after a separate source-use review assertion.

    Caller must independently establish authenticity of decision and review.
    A successful collection is not publication admission or legal verification.
    """
    validate_authorization_decision(decision, as_of=as_of, revoked_ids=revoked_ids)
    if (not isinstance(review, dict)
            or review.get("authorization_decision_id") != decision["decision_id"]
            or review.get("source_use_compliance_verified") is not True
            or review.get("review_evidence_url") != decision.get("independent_source_use_review_url")
            or not isinstance(review.get("reviewer"), str)
            or not review["reviewer"].strip()
            or review["reviewer"] == decision["issuer"]):
        raise PermissionError("independent source-use review record required")
    if (not isinstance(months, list) or not months
            or len(months) != len(set(months))
            or any(month not in decision["scope"]["periods"] for month in months)):
        raise PermissionError("months must be unique and within approved scope")
    results = [
        acquire_metadata(month, approved_space_ids=set(decision["scope"]["space_ids"]),
                         scope_approved=True, reuse_approved=True,
                         retrieved_at=as_of, fetch=fetch)
        for month in months
    ]
    return {
        "schema_version": "1",
        "type": "toip_confluence_metadata_acquisition",
        "authorization_decision_id": decision["decision_id"],
        "source_use_review_evidence_url": review["review_evidence_url"],
        "retrieved_at": as_of,
        "publication_admitted": False,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision", required=True, type=Path)
    parser.add_argument("--source-use-review", required=True, type=Path)
    parser.add_argument("--revocation-register", required=True, type=Path)
    parser.add_argument("--month", action="append", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    decision = json.loads(args.decision.read_text(encoding="utf-8"))
    review = json.loads(args.source_use_review.read_text(encoding="utf-8"))
    revocations = json.loads(args.revocation_register.read_text(encoding="utf-8"))
    if (not isinstance(revocations, dict)
            or not isinstance(revocations.get("revoked_ids"), list)
            or any(not isinstance(x, str) for x in revocations["revoked_ids"])):
        raise ValueError("revocation register requires revoked_ids array")
    now = datetime.now(timezone.utc).isoformat()
    result = collect(decision, review=review, revoked_ids=set(revocations["revoked_ids"]),
                     as_of=now, months=args.month)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
