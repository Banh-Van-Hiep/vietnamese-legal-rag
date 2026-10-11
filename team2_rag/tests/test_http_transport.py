import unittest
from team2_rag.llm.http import HttpResponse, UrllibTransport
from team2_rag.llm.errors import LLMProviderError, LLMTimeoutError

class TransportTests(unittest.TestCase):
    def test_http_response_shape(self):
        r=HttpResponse(200,{"ok":True})
        self.assertEqual((r.status,r.json),(200,{"ok":True}))
    def test_non_success_is_normalized_by_provider_layer(self):
        from team2_rag.llm.base import raise_for_status
        with self.assertRaises(LLMProviderError): raise_for_status("openai",503,{})
    def test_timeout_type_exists(self):
        self.assertTrue(issubclass(LLMTimeoutError,Exception))

if __name__ == "__main__": unittest.main()
