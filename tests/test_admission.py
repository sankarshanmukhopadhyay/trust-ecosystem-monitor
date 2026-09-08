import unittest

from trust_ecosystem_monitor.admission import make_admission_decision, unresolved_admission


class AdmissionDecisionTests(unittest.TestCase):
    def test_unresolved_discovery_fails_closed(self):
        decision = unresolved_admission()
        self.assertEqual(decision.state, "review")
        self.assertEqual(decision.tier, "inventory")
        self.assertFalse(decision.deep_collection_allowed)

    def test_included_core_requires_evidence_and_allows_deep_collection(self):
        decision = make_admission_decision(
            state="included",
            tier="core",
            rationale=["normative trust-infrastructure deliverable"],
            evidence=["w3c-group:example"],
        )
        self.assertTrue(decision.deep_collection_allowed)

    def test_included_without_evidence_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "included admission requires evidence"):
            make_admission_decision(
                state="included",
                tier="core",
                rationale=["looks relevant"],
            )

    def test_watch_cannot_be_promoted_to_core_collection(self):
        with self.assertRaisesRegex(ValueError, "not permitted"):
            make_admission_decision(
                state="watch",
                tier="core",
                rationale=["possible composition seam"],
                evidence=["source:example"],
            )

    def test_review_cannot_receive_watch_collection(self):
        with self.assertRaisesRegex(ValueError, "not permitted"):
            make_admission_decision(
                state="review",
                tier="watch",
                rationale=["evidence unresolved"],
            )

    def test_excluded_is_inventory_only(self):
        decision = make_admission_decision(
            state="excluded",
            tier="inventory",
            rationale=["institutional infrastructure outside portfolio"],
            evidence=["policy:scope-v1"],
        )
        self.assertFalse(decision.deep_collection_allowed)

    def test_unknown_state_and_tier_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "unsupported admission state"):
            make_admission_decision(state="maybe", tier="inventory", rationale=["unknown"])
        with self.assertRaisesRegex(ValueError, "unsupported collection tier"):
            make_admission_decision(state="review", tier="deep", rationale=["unknown"])

    def test_serialized_decision_preserves_audit_fields(self):
        decision = make_admission_decision(
            state="watch",
            tier="watch",
            rationale=["emerging work"],
            evidence=["group:123", "repo:w3c/example"],
            method="explicit-policy",
        )
        payload = decision.as_dict()
        self.assertEqual(payload["state"], "watch")
        self.assertEqual(payload["tier"], "watch")
        self.assertEqual(payload["evidence"], ["group:123", "repo:w3c/example"])
        self.assertEqual(payload["method"], "explicit-policy")
        self.assertFalse(payload["deep_collection_allowed"])


if __name__ == "__main__":
    unittest.main()
