import unittest
from trust_ecosystem_monitor.toip_confluence_admission import validate_authorization_decision

NOW = "2026-10-10T10:00:00Z"


def decision():
    return {
        "schema_version": "1", "decision_id": "synthetic-1",
        "issuer": "test-source-owner", "issuer_role": "source_owner",
        "reviewer": "test-rights-reviewer", "rationale": "Synthetic test only",
        "authority_independently_verified": True,
        "decision": "approved", "revoked": False,
        "scope": {"source": "confluence", "host": "lf-toip.atlassian.net",
                  "space_ids": ["22970380"], "periods": ["2026-08"],
                  "permitted_uses": ["metadata_acquisition", "derived_publication"]},
        "content_categories": ["page_metadata"],
        "authority_evidence_url": "https://example.org/authority",
        "permission_evidence_url": "https://example.org/permission",
        "issued_at": "2026-10-01T00:00:00Z",
        "expires_at": "2026-11-01T00:00:00Z",
    }


class DecisionTests(unittest.TestCase):
    def test_synthetic_valid_decision(self):
        self.assertEqual(validate_authorization_decision(
            decision(), as_of=NOW, revoked_ids=set())["decision_id"], "synthetic-1")

    def test_requires_current_revocation_register(self):
        with self.assertRaises(ValueError):
            validate_authorization_decision(decision(), as_of=NOW)

    def test_revocation_blocks_approval(self):
        with self.assertRaises(ValueError):
            validate_authorization_decision(decision(), as_of=NOW, revoked_ids={"synthetic-1"})

    def test_bounded_experiment_sponsor_policy(self):
        d = dict(decision(), issuer="sankarshanmukhopadhyay",
                 issuer_role="experiment_sponsor",
                 policy_basis="toip_experiment_2026_10_11",
                 source_use_compliance_verified=True,
                 independent_source_use_review_url="https://example.org/source-use-review")
        self.assertEqual(validate_authorization_decision(
            d, as_of=NOW, revoked_ids=set())["issuer_role"], "experiment_sponsor")

    def test_sponsor_requires_source_use_review(self):
        d = dict(decision(), issuer="sankarshanmukhopadhyay",
                 issuer_role="experiment_sponsor",
                 policy_basis="toip_experiment_2026_10_11",
                 source_use_compliance_verified=True)
        with self.assertRaises(ValueError):
            validate_authorization_decision(d, as_of=NOW, revoked_ids=set())

    def test_sponsor_cannot_self_assert_compliance_without_gate(self):
        d = dict(decision(), issuer="sankarshanmukhopadhyay",
                 issuer_role="experiment_sponsor",
                 policy_basis="toip_experiment_2026_10_11",
                 source_use_compliance_verified=False,
                 independent_source_use_review_url="https://example.org/review")
        with self.assertRaises(ValueError):
            validate_authorization_decision(d, as_of=NOW, revoked_ids=set())

    def test_wrong_sponsor_rejected(self):
        d = dict(decision(), issuer="someone-else",
                 issuer_role="experiment_sponsor",
                 policy_basis="toip_experiment_2026_10_11",
                 source_use_compliance_verified=True,
                 independent_source_use_review_url="https://example.org/review")
        with self.assertRaises(ValueError):
            validate_authorization_decision(d, as_of=NOW, revoked_ids=set())

    def test_expiry_blocks_approval(self):
        with self.assertRaises(ValueError):
            validate_authorization_decision(decision(), as_of="2026-12-01T00:00:00Z", revoked_ids=set())

    def test_experiment_sponsor_is_not_source_owner(self):
        with self.assertRaises(ValueError):
            validate_authorization_decision(dict(decision(), issuer_role="experiment_sponsor"),
                                            as_of=NOW, revoked_ids=set())

    def test_unverified_authority_rejected(self):
        with self.assertRaises(ValueError):
            validate_authorization_decision(dict(decision(), authority_independently_verified=False),
                                            as_of=NOW, revoked_ids=set())

    def test_publication_use_required(self):
        d = decision()
        d["scope"]["permitted_uses"] = ["metadata_acquisition"]
        with self.assertRaises(ValueError):
            validate_authorization_decision(d, as_of=NOW, revoked_ids=set())


if __name__ == "__main__":
    unittest.main()
