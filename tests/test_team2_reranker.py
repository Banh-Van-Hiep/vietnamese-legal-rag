"""Offline tests: scorer and adapter doubles; no model downloads or API keys."""
import copy
import json
import math
import sys
from contextlib import nullcontext
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from team2_rag.reranker import (
    BGEScorer, RerankInputError, RerankModelError, rerank, rerank_with_details,
)

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "team2_rag/data/samples/reranker_input.json"


def payload(n=3):
    template = json.loads(SAMPLE.read_text(encoding="utf-8"))
    rows = []
    for i in range(n):
        row = copy.deepcopy(template["results"][i % 3])
        row.update(chunk_id=f"mock_chunk_{i}", rank=i + 1)
        rows.append(row)
    return {"question": template["question"], "results": rows}


class RerankerTests(unittest.TestCase):
    def test_descending_scores_and_pairs_use_original_question_and_content(self):
        data = payload()
        scorer = Mock(return_value=[-3, 8, 2])
        result = rerank_with_details(data, scorer=scorer)
        self.assertEqual([r["rank"] for r in result.output["results"]], [2, 3, 1])
        scorer.assert_called_once_with([(data["question"], r["content"]) for r in data["results"]])
        self.assertEqual(result.scores, {"mock_chunk_0": -3.0, "mock_chunk_1": 8.0, "mock_chunk_2": 2.0})
        self.assertIsNone(result.fallback_reason)

    def test_preserves_all_twelve_fields_input_and_independent_copies(self):
        data = payload()
        before = copy.deepcopy(data)
        out = rerank(data, scorer=lambda pairs: [0, 2, 1])
        originals = {r["chunk_id"]: r for r in before["results"]}
        self.assertEqual(set(out), {"question", "results"})
        self.assertEqual(out["question"], before["question"])
        for row in out["results"]:
            self.assertEqual(row, originals[row["chunk_id"]])
            self.assertEqual(len(row), 12)
        self.assertEqual(data, before)
        out["results"][0]["content"] = "changed by caller"
        self.assertEqual(data, before)

    def test_ties_keep_original_retrieval_rank(self):
        out = rerank(payload(), scorer=lambda pairs: [1, 1, 0])
        self.assertEqual([r["rank"] for r in out["results"]], [1, 2, 3])

    def test_entire_pool_reaches_context_builder(self):
        out = rerank(payload(20), scorer=lambda pairs: list(range(len(pairs))))
        self.assertEqual(len(out["results"]), 20)
        self.assertEqual([r["rank"] for r in out["results"]], list(range(20, 0, -1)))

    def test_empty_pool_never_loads_model(self):
        with patch("team2_rag.reranker._default_scorer") as factory:
            result = rerank_with_details(payload(0))
        factory.assert_not_called()
        self.assertEqual(result.output, payload(0))
        self.assertEqual(result.scores, {})
        self.assertIsNone(result.fallback_reason)

    def test_model_exception_falls_back_and_logs_without_user_content(self):
        data = payload()
        scorer = Mock(side_effect=RuntimeError("private model error " + data["question"]))
        with self.assertLogs("team2_rag.reranker", level="WARNING") as logs:
            result = rerank_with_details(data, scorer=scorer)
        self.assertEqual(result.output, data)
        self.assertEqual(result.scores, {})
        self.assertEqual(result.fallback_reason, "RuntimeError")
        self.assertNotIn(data["question"], str(logs.output))

    def test_strict_mode_exposes_failure_instead_of_fake_success(self):
        for error in (TimeoutError("timeout"), RerankModelError("too long"), ImportError("missing")):
            with self.subTest(error=type(error).__name__):
                with self.assertRaises(RerankModelError):
                    rerank(payload(), scorer=Mock(side_effect=error), strict=True)

    def test_bad_score_count_values_and_partial_scores_fall_back(self):
        for scores in ([1], [1, math.nan, 2], [1, math.inf, 2], [1, True, 2], [1, "2", 3], None):
            with self.subTest(scores=scores), self.assertLogs("team2_rag.reranker", level="WARNING"):
                result = rerank_with_details(payload(), scorer=lambda pairs: scores)
                self.assertEqual(result.output, payload())
                self.assertEqual(result.scores, {})
                self.assertIsNotNone(result.fallback_reason)

    def test_invalid_payloads_fail_before_scorer_or_fallback(self):
        cases = [None, [], {}, {"question": "", "results": []},
                 {"question": "  ", "results": []}, {"question": "x" * 4001, "results": []},
                 {"question": "x", "results": "bad"}, payload(51), payload() | {"extra": 1}]
        for data in cases:
            scorer = Mock()
            with self.subTest(data=str(data)[:40]), self.assertRaises(RerankInputError):
                rerank(data, scorer=scorer)
            scorer.assert_not_called()

    def test_invalid_candidates_not_hidden_by_fallback(self):
        changes = [
            {"chunk_id": " "}, {"document_id": "sai ID"}, {"content": ""},
            {"article_id": "Điều 1"}, {"clause": ""}, {"point": False},
            {"source_url": "http://example.com/law"}, {"source_url": "https:///law"},
            {"source_url": "https://example.com/a b"}, {"score": math.nan},
            {"score": True}, {"rank": True}, {"rank": 2},
            {"retrieval_method": "rerank"}, {"extra": 1},
        ]
        for change in changes:
            data = payload()
            data["results"][0].update(change)
            with self.subTest(change=change), self.assertRaises(RerankInputError):
                rerank(data, scorer=Mock())
        for key in payload()["results"][0]:
            data = payload()
            del data["results"][0][key]
            with self.subTest(missing=key), self.assertRaises(RerankInputError):
                rerank(data, scorer=Mock())

    def test_duplicate_ids_or_noncontiguous_ranks_are_rejected(self):
        for key, value in (("rank", 4), ("rank", 1), ("chunk_id", "mock_chunk_0")):
            data = payload()
            data["results"][1][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(RerankInputError):
                rerank(data, scorer=Mock())

    def test_input_and_output_field_types_match_shared_json_schema(self):
        import jsonschema
        schema = json.loads((ROOT / "contracts/v0.1/retrieval_output.schema.json").read_text(encoding="utf-8"))
        jsonschema.validate(payload(), schema, format_checker=jsonschema.FormatChecker())
        # Same fields, but results order is now rerank order, not retrieval rank order.
        jsonschema.validate(rerank(payload(), scorer=lambda pairs: [1, 3, 2]), schema)


class BGEAdapterTests(unittest.TestCase):
    def scorer(self, lengths):
        scorer = BGEScorer(batch_size=2, max_length=8)
        tokenizer = Mock()
        tokenizer.side_effect = lambda qs, texts, **kwargs: {"input_ids": [[1] * n for n in lengths[:len(qs)]]}
        tokenizer.pad.return_value = {"input_ids": "padded inputs"}
        model = Mock()
        model.return_value.logits.reshape.return_value.float.return_value.cpu.return_value.tolist.return_value = [0.3, 0.7]
        scorer._tokenizer, scorer._model = tokenizer, model
        scorer._torch = Mock()
        scorer._torch.inference_mode.side_effect = nullcontext
        return scorer

    def test_token_length_includes_whole_pair_and_disables_truncation(self):
        scorer = self.scorer([8, 7])
        self.assertEqual(scorer([("Q", "A"), ("Q", "B")]), [0.3, 0.7])
        scorer._tokenizer.assert_called_once_with(["Q", "Q"], ["A", "B"], padding=False, truncation=False)
        scorer._model.assert_called_once_with(input_ids="padded inputs", return_dict=True)

    def test_oversized_pair_rejected_before_inference(self):
        scorer = self.scorer([9, 5])
        with self.assertRaises(RerankModelError):
            scorer([("Q", "A"), ("Q", "B")])
        scorer._model.assert_not_called()
        scorer._tokenizer.pad.assert_not_called()

    def test_cuda_moves_inputs_before_inference(self):
        scorer = self.scorer([8, 7])
        scorer.device = "cuda"
        tensor = Mock()
        scorer._tokenizer.pad.return_value = {"input_ids": tensor}
        self.assertEqual(scorer([("Q", "A"), ("Q", "B")]), [0.3, 0.7])
        tensor.to.assert_called_once_with("cuda")
        scorer._model.assert_called_once_with(input_ids=tensor.to.return_value, return_dict=True)

    def test_load_uses_requested_device_and_same_revision_for_model_and_tokenizer(self):
        for device in ("cpu", "cuda"):
            with self.subTest(device=device):
                torch, transformers = Mock(), Mock()
                torch.cuda.is_available.return_value = True
                scorer = BGEScorer(device=device, revision="a" * 40)
                with patch.dict(sys.modules, torch=torch, transformers=transformers):
                    scorer._load()
                    scorer._load()  # Reuse the loaded model.
                transformers.AutoTokenizer.from_pretrained.assert_called_once_with(
                    "BAAI/bge-reranker-v2-m3", revision="a" * 40, trust_remote_code=False)
                transformers.AutoModelForSequenceClassification.from_pretrained.assert_called_once_with(
                    "BAAI/bge-reranker-v2-m3", revision="a" * 40,
                    trust_remote_code=False, use_safetensors=True)
                scorer._model.to.assert_called_once_with(device)
                scorer._model.eval.assert_called_once()

    def test_unavailable_cuda_fails_before_downloading_model(self):
        torch, transformers = Mock(), Mock()
        torch.cuda.is_available.return_value = False
        with patch.dict(sys.modules, torch=torch, transformers=transformers):
            with self.assertRaisesRegex(RerankModelError, "CUDA"):
                BGEScorer(device="cuda")._load()
        transformers.AutoTokenizer.from_pretrained.assert_not_called()
        transformers.AutoModelForSequenceClassification.from_pretrained.assert_not_called()

    def test_empty_adapter_call_does_not_load_model(self):
        scorer = BGEScorer()
        with patch.object(scorer, "_load") as load:
            self.assertEqual(scorer([]), [])
        load.assert_not_called()

    def test_configuration_limits(self):
        for kw in ({"batch_size": 0}, {"batch_size": True}, {"max_length": 0}, {"max_length": 513},
                   {"device": "auto"}, {"device": "mps"}):
            with self.subTest(kw=kw), self.assertRaises(ValueError):
                BGEScorer(**kw)


if __name__ == "__main__":
    unittest.main()
