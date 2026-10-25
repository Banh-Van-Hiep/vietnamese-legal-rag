"""Startup/configuration boundaries of `build_runtime` and the LLM settings that feed it (no network, no models).

`build_runtime` validates manifests and LLM settings BEFORE importing qdrant/sentence-transformers, so these checks
run without those packages. A fully valid environment is intentionally not exercised here (needs real indexes).
"""
import json
import tempfile
import unittest
from pathlib import Path

from team2_rag.config.settings import ConfigError, LLMSettings, load_settings
from team2_rag.runtime import build_runtime

SECRET = "sk-super-secret-value-123"


def manifests(root, bm_version="v1", dense_version="v1", dense_chunks=("a", "b")):
    bm, dense = Path(root) / "bm25", Path(root) / "dense"
    for d, version, chunks in ((bm, bm_version, ("a", "b")), (dense, dense_version, dense_chunks)):
        d.mkdir()
        (d / "index_manifest.json").write_text(
            json.dumps({"index_version": version, "chunk_ids": list(chunks)}), encoding="utf-8")
    return {"RAG_BM25_INDEX": str(bm), "RAG_DENSE_INDEX": str(dense)}


class BuildRuntimeStartupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_missing_index_settings(self):
        with self.assertRaises(ConfigError):
            build_runtime(env={})

    def test_index_version_or_chunk_ids_mismatch(self):
        with self.assertRaises(ConfigError):
            build_runtime(env=manifests(self.tmp.name, dense_version="v2"))

    def test_chunk_id_mismatch(self):
        with self.assertRaises(ConfigError):
            build_runtime(env=manifests(self.tmp.name, dense_chunks=("a", "c")))

    def test_missing_llm_key_fails_before_models_load_and_names_only_the_variable(self):
        env = manifests(self.tmp.name) | {"LLM_PROVIDER": "openai", "LLM_MODEL": "gpt-4o"}
        with self.assertRaises(ConfigError) as ctx:
            build_runtime(env=env)
        self.assertIn("OPENAI_API_KEY", str(ctx.exception))

    def test_missing_model_fails(self):
        env = manifests(self.tmp.name) | {"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": SECRET}
        with self.assertRaises(ConfigError) as ctx:
            build_runtime(env=env)
        self.assertNotIn(SECRET, str(ctx.exception))

    def test_context_window_too_small_fails_at_startup_without_leaking_key(self):
        env = manifests(self.tmp.name) | {"LLM_PROVIDER": "qwen", "LLM_MODEL": "qwen-plus", "QWEN_API_KEY": SECRET,
                                           "LLM_CONTEXT_WINDOW_TOKENS": "1000"}
        with self.assertRaises(ConfigError) as ctx:
            build_runtime(env=env)
        self.assertNotIn(SECRET, str(ctx.exception))


class SettingsSecretAndLimitTests(unittest.TestCase):
    ENV = {"LLM_PROVIDER": "openai", "LLM_MODEL": "gpt-4o", "OPENAI_API_KEY": SECRET}

    def test_keys_never_appear_in_repr_or_str(self):
        s = load_settings(env=self.ENV)
        self.assertNotIn(SECRET, repr(s))
        self.assertNotIn(SECRET, str(s))

    def test_timeout_and_retry_limits_are_enforced(self):
        for extra in ({"LLM_TIMEOUT_SECONDS": "31"}, {"LLM_TIMEOUT_SECONDS": "0"}, {"LLM_MAX_RETRIES": "1"}):
            with self.subTest(extra), self.assertRaises(ConfigError):
                load_settings(env=self.ENV | extra).validate()
        load_settings(env=self.ENV | {"LLM_TIMEOUT_SECONDS": "30"}).validate()

    def test_invalid_number_error_names_variable_not_value(self):
        with self.assertRaises(ConfigError) as ctx:
            load_settings(env=self.ENV | {"LLM_MAX_OUTPUT_TOKENS": "lots-" + SECRET})
        self.assertIn("LLM_MAX_OUTPUT_TOKENS", str(ctx.exception))
        self.assertNotIn(SECRET, str(ctx.exception))

    def test_blank_key_is_rejected(self):
        with self.assertRaises(ConfigError):
            load_settings(env=self.ENV | {"OPENAI_API_KEY": "   "}).validate()

    def test_defaults_match_the_dataclass(self):
        s = load_settings(env=self.ENV)
        self.assertEqual(s, LLMSettings(provider="openai", model="gpt-4o", openai_api_key=SECRET))


if __name__ == "__main__":
    unittest.main()
