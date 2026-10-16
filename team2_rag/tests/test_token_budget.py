"""Token budget theo context-builder.md. Dùng counter giả (đếm từ) CHỈ để kiểm tra logic budget;
chúng không chứng minh số token thật của bất kỳ model nào."""
import sys, types, unittest
from unittest.mock import patch
from team2_rag.answer import answer_from_rerank
from team2_rag.config.settings import ConfigError, load_settings
from team2_rag.llm.errors import CitationInvalidError, LLMConfigError
from team2_rag.llm.fake import FakeLLMProvider
from team2_rag.llm.service import LLMService
from team2_rag.llm.tokens import TiktokenCounter, TokenBudget, TokenCounter, token_budget_from_settings
from team2_rag.prompts import ContextBudgetError, build_context
from team2_rag.tests.helpers import QUESTION, good_output
from team2_rag.tests.test_context_builder import candidate


class WordCounter:
    def count(self, text): return len(text.split())


def cands(*sizes):
    return [candidate(f"c{i}", " ".join(["từ"] * n), rank=i + 1) for i, n in enumerate(sizes)]

def run(results, budget, history=None):
    p = FakeLLMProvider([good_output("A [C1].") | {"citations": [dict(good_output()["citations"][0], chunk_id="c0", document_id="bll2019_v1", article_id="dieu113", document_title="Bộ luật Lao động 2019", article="Điều 113", clause="Khoản 1", source_url="https://example.com/law")]}])
    return p, answer_from_rerank({"question": QUESTION, "results": results}, LLMService(p), history, token_budget=budget)


class BudgetFormulaTests(unittest.TestCase):
    def test_available_is_min_of_cap_and_remaining(self):
        b = TokenBudget(WordCounter(), context_window_tokens=10000)
        self.assertEqual(b.prompt_limit, 10000 - 1500 - 256)
        self.assertEqual(b.available_for_context(500), 3000)
        small = TokenBudget(WordCounter(), context_window_tokens=4000)
        self.assertEqual(small.available_for_context(500), 4000 - 1500 - 256 - 500)
        self.assertLess(small.available_for_context(5000), 1)

    def test_invalid_budget_values(self):
        with self.assertRaises(ValueError): TokenBudget(WordCounter(), 0)
        self.assertIsInstance(WordCounter(), TokenCounter)


class ContextTokenModeTests(unittest.TestCase):
    def test_token_mode_skips_oversized_and_marks_unit(self):
        one = WordCounter().count(build_context(cands(5)).text)
        ctx = build_context(cands(5, 500, 5), token_counter=WordCounter(), max_tokens=one * 2 + 5)
        self.assertEqual([c.chunk_id for c in ctx.chunks], ["c0", "c2"])
        self.assertEqual(ctx.skipped_chunk_ids, ("c1",))
        self.assertEqual(ctx.budget_unit, "tokens")
        self.assertEqual(build_context(cands(5)).budget_unit, "chars_approx")

    def test_counter_and_max_tokens_must_pair(self):
        with self.assertRaises(ValueError): build_context(cands(5), token_counter=WordCounter())
        with self.assertRaises(ValueError): build_context(cands(5), max_tokens=100)
        with self.assertRaises(ContextBudgetError): build_context(cands(5), token_counter=WordCounter(), max_tokens=0)


class AnswerWithTokenBudgetTests(unittest.TestCase):
    def test_prompt_sent_stays_within_limit(self):
        budget = TokenBudget(WordCounter(), context_window_tokens=2400, output_reserve_tokens=1000, safety_margin_tokens=100)
        p, resp = run(cands(30, 30, 30), budget)
        prompt = p.calls[0][0]
        self.assertLessEqual(WordCounter().count(prompt.system) + WordCounter().count(prompt.user), budget.prompt_limit)
        self.assertEqual(resp["status"], "answered")

    def test_fixed_prompt_exceeding_limit_raises_without_calling_llm(self):
        budget = TokenBudget(WordCounter(), context_window_tokens=1000, output_reserve_tokens=900, safety_margin_tokens=90)
        p = FakeLLMProvider([])
        with self.assertRaises(ContextBudgetError):
            answer_from_rerank({"question": QUESTION, "results": cands(5)}, LLMService(p), token_budget=budget)
        self.assertEqual(p.calls, [])

    def test_long_history_counts_toward_fixed_tokens(self):
        budget = TokenBudget(WordCounter(), context_window_tokens=2400, output_reserve_tokens=1000, safety_margin_tokens=100)
        hist = [{"role": "user", "content": " ".join(["lịch"] * 1500)}]
        with self.assertRaises(ContextBudgetError): run(cands(5), budget, hist)

    def test_all_chunks_too_big_gives_insufficient_without_llm(self):
        budget = TokenBudget(WordCounter(), context_window_tokens=2400, output_reserve_tokens=1000, safety_margin_tokens=100)
        p = FakeLLMProvider([])
        r = answer_from_rerank({"question": QUESTION, "results": cands(5000)}, LLMService(p), token_budget=budget)
        self.assertEqual((r["status"], r["citations"]), ("insufficient_context", []))
        self.assertEqual(p.calls, [])

    def test_chunk_skipped_by_token_budget_cannot_be_cited(self):
        budget = TokenBudget(WordCounter(), context_window_tokens=2400, output_reserve_tokens=1000, safety_margin_tokens=100)
        cits = dict(good_output()["citations"][0], chunk_id="c1", citation_id="C1")
        p = FakeLLMProvider([{"status": "answered", "answer": "A [C1].", "citations": [cits]}])
        with self.assertRaises(CitationInvalidError):  # c1 quá lớn nên không có trong prompt; C1 là c0
            answer_from_rerank({"question": QUESTION, "results": cands(5, 5000)}, LLMService(p), token_budget=budget)
        self.assertNotIn("chunk_id=c1 ", p.calls[0][0].user)


class NonAdditiveCounter(WordCounter):
    """Giả lập tokenizer không cộng tính: prompt đầy đủ đắt hơn tổng các phần (ví dụ do ghép/biến đổi)."""
    def count(self, text):
        return super().count(text) + (10_000 if "<QUESTION>" in text and "[C1]" in text else 0)


class FinalPromptGuardTests(unittest.TestCase):
    def test_final_prompt_recount_blocks_over_limit_prompt(self):
        budget = TokenBudget(NonAdditiveCounter(), context_window_tokens=5000, output_reserve_tokens=1000, safety_margin_tokens=100)
        p = FakeLLMProvider([])
        with self.assertRaises(ContextBudgetError):
            answer_from_rerank({"question": QUESTION, "results": cands(5)}, LLMService(p), token_budget=budget)
        self.assertEqual(p.calls, [])


class TokenizerFactoryTests(unittest.TestCase):
    def test_missing_window_and_unsupported_provider_raise_not_guess(self):
        env = {"LLM_PROVIDER": "openai", "LLM_MODEL": "gpt-4o", "OPENAI_API_KEY": "k"}
        with self.assertRaises(ConfigError): token_budget_from_settings(load_settings(env=env))
        for prov in ("gemini", "qwen"):
            s = load_settings(env=env | {"LLM_PROVIDER": prov, "LLM_CONTEXT_WINDOW_TOKENS": "100000"})
            with self.assertRaises(ConfigError): token_budget_from_settings(s)

    def test_openai_without_tiktoken_raises_config_error(self):
        with patch.dict(sys.modules, {"tiktoken": None}):
            with self.assertRaises(LLMConfigError): TiktokenCounter("gpt-4o")

    def test_tiktoken_wrapper_logic_with_stub_module(self):
        class Enc:
            def encode(self, text, disallowed_special=()): return list(text.split())
        stub = types.SimpleNamespace(encoding_for_model=lambda m: Enc() if m == "gpt-4o" else (_ for _ in ()).throw(KeyError(m)))
        with patch.dict(sys.modules, {"tiktoken": stub}):
            self.assertEqual(TiktokenCounter("gpt-4o").count("a b c"), 3)
            with self.assertRaises(LLMConfigError): TiktokenCounter("model-la")
            s = load_settings(env={"LLM_PROVIDER": "openai", "LLM_MODEL": "gpt-4o", "OPENAI_API_KEY": "k", "LLM_CONTEXT_WINDOW_TOKENS": "128000"})
            b = token_budget_from_settings(s)
            self.assertEqual((b.context_window_tokens, b.max_context_tokens, b.output_reserve_tokens, b.safety_margin_tokens), (128000, 3000, 1500, 256))

if __name__ == "__main__": unittest.main()
