import unittest

from src.pipeline.llm_assess import assess_polarization
from src.pipeline.types import NormalizedItem


class LLMAssessTests(unittest.TestCase):
    def test_retry_on_invalid_json_then_success(self):
        calls = {"n": 0}

        def fake_call(system_prompt, user_payload):
            calls["n"] += 1
            if calls["n"] == 1:
                return "not-json"
            return '{"polarization_score": 55, "confidence": 0.7, "rationale": "Mixed strong disagreement.", "evidence_ids": ["1"]}'

        items = [NormalizedItem("1", "text", "https://x", "2026", 5, "post")]
        result = assess_polarization("query", items, call_model=fake_call)
        self.assertEqual(calls["n"], 2)
        self.assertEqual(result.polarization_score, 55)
        self.assertEqual(result.evidence_ids, ["1"])

    def test_raises_when_no_items(self):
        with self.assertRaises(ValueError):
            assess_polarization("query", [], call_model=lambda *_: "{}")


if __name__ == "__main__":
    unittest.main()
