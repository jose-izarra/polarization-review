import json
import unittest

from src.internal.pipeline.llm.llm_assess import assess_items
from src.internal.pipeline.llm.types import ItemScore, NormalizedItem


def _make_item(id: str) -> NormalizedItem:
    return NormalizedItem(
        id,
        "some sufficiently long text for testing purposes",
        "https://x",
        "2026",
        5,
        "post",
    )


def _fake_response(items: list[NormalizedItem]) -> str:
    return json.dumps(
        [{"id": item.id, "sentiment": 3, "stance": 1, "animosity": 2} for item in items]
    )


class AssessItemsTests(unittest.TestCase):
    def test_returns_item_scores_for_each_item(self):
        items = [_make_item("1"), _make_item("2"), _make_item("3")]

        def fake_call(system_prompt, user_payload):
            payload = json.loads(user_payload)
            return _fake_response(
                [type("X", (), {"id": i["id"]})() for i in payload["items"]]
            )

        result = assess_items("query", items, call_model=fake_call)
        self.assertEqual(len(result), 3)
        self.assertIsInstance(result[0], ItemScore)

    def test_r_value_is_computed_correctly(self):
        items = [_make_item("1")]

        def fake_call(system_prompt, user_payload):
            return json.dumps(
                [{"id": "1", "sentiment": 4, "stance": 1, "animosity": 2}]
            )

        result = assess_items("query", items, call_model=fake_call)
        self.assertEqual(len(result), 1)
        # r = stance * (sentiment + alpha * animosity) = 1 * (4 + 0.5 * 2) = 5.0
        self.assertAlmostEqual(result[0].r, 5.0)

    def test_retry_on_invalid_json_then_success(self):
        calls = {"n": 0}
        items = [_make_item("1")]

        def fake_call(system_prompt, user_payload):
            calls["n"] += 1
            if calls["n"] == 1:
                return "not-json"
            return json.dumps(
                [{"id": "1", "sentiment": 3, "stance": -1, "animosity": 3}]
            )

        result = assess_items("query", items, call_model=fake_call)
        self.assertEqual(calls["n"], 2)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].stance, -1)

    def test_raises_when_no_items(self):
        with self.assertRaises(ValueError):
            assess_items("query", [], call_model=lambda *_: "[]")

    def test_skips_invalid_items_in_batch(self):
        items = [_make_item("1"), _make_item("2")]

        def fake_call(system_prompt, user_payload):
            # Only one valid item returned; second has out-of-range sentiment
            return json.dumps(
                [
                    {"id": "1", "sentiment": 3, "stance": 0, "animosity": 2},
                    {"id": "2", "sentiment": 99, "stance": 1, "animosity": 2},
                ]
            )

        result = assess_items("query", items, call_model=fake_call)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, "1")

    def test_batches_large_input(self):
        """Items exceeding BATCH_SIZE=15 should result in multiple LLM calls."""
        items = [_make_item(str(i)) for i in range(20)]
        call_count = {"n": 0}

        def fake_call(system_prompt, user_payload):
            call_count["n"] += 1
            payload = json.loads(user_payload)
            return json.dumps(
                [
                    {"id": i["id"], "sentiment": 3, "stance": 1, "animosity": 2}
                    for i in payload["items"]
                ]
            )

        result = assess_items("query", items, call_model=fake_call)
        self.assertEqual(call_count["n"], 2)
        self.assertEqual(len(result), 20)


if __name__ == "__main__":
    unittest.main()
