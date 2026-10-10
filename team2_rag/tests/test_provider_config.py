import os, unittest
from unittest.mock import patch
from team2_rag.config.settings import ConfigError, load_settings
from team2_rag.llm.factory import create_llm_service
from team2_rag.tests.helpers import settings_for, openai_ok, gemini_ok, RecordingTransport

class ConfigTests(unittest.TestCase):
    def test_defaults(self):
        s = load_settings(env={"LLM_MODEL":"m","OPENAI_API_KEY":"k"})
        self.assertEqual((s.timeout_seconds,s.max_retries,s.max_output_tokens),(30.0,0,1500))
    def test_env_overrides(self):
        s = load_settings(env={"LLM_PROVIDER":"gemini","LLM_MODEL":"g","GEMINI_API_KEY":"k","LLM_TIMEOUT_SECONDS":"20"})
        self.assertEqual((s.provider,s.model,s.timeout_seconds),("gemini","g",20.0))
    def test_missing_key(self):
        with self.assertRaises(ConfigError): load_settings(env={"LLM_PROVIDER":"openai","LLM_MODEL":"m"}).validate()
    def test_secret_not_in_repr(self):
        s = load_settings(env={"LLM_MODEL":"m","OPENAI_API_KEY":"secret"})
        self.assertNotIn("secret",repr(s))

class ProviderSwitchTests(unittest.TestCase):
    def test_common_interface(self):
        for name, response in (("openai",openai_ok()), ("gemini",gemini_ok())):
            s=settings_for(name)
            transport=RecordingTransport(response)
            svc=create_llm_service(s, transport=transport)
            self.assertEqual(svc.provider.name,name)
            self.assertEqual(svc.ask("Q", "C").output.status,"answered")

if __name__ == "__main__": unittest.main()
