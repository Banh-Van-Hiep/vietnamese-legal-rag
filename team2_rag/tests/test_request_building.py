import unittest
from team2_rag.llm.factory import create_llm_service
from team2_rag.tests.helpers import settings_for, openai_ok, gemini_ok, RecordingTransport, QUESTION, CONTEXT

class RequestTests(unittest.TestCase):
    def test_openai(self):
        t=RecordingTransport(openai_ok()); svc=create_llm_service(settings_for("openai"),transport=t); svc.ask(QUESTION,CONTEXT)
        b=t.calls[0]["body"]
        self.assertEqual(b["response_format"],{"type":"json_object"})
        self.assertIn("LEGAL_CONTEXT",b["messages"][1]["content"])
        self.assertNotIn("test-openai-key",str(b))
    def test_gemini(self):
        t=RecordingTransport(gemini_ok()); svc=create_llm_service(settings_for("gemini"),transport=t); svc.ask(QUESTION,CONTEXT)
        b=t.calls[0]["body"]
        self.assertEqual(b["generationConfig"]["responseMimeType"],"application/json")
        self.assertIn("LEGAL_CONTEXT",b["contents"][0]["parts"][0]["text"])
    def test_qwen_uses_remote_openai_compatible_api(self):
        from team2_rag.tests.helpers import openai_ok
        t=RecordingTransport(openai_ok()); svc=create_llm_service(settings_for("qwen"),transport=t); svc.ask(QUESTION,CONTEXT)
        self.assertIn("dashscope",t.calls[0]["url"])
        self.assertEqual(t.calls[0]["body"]["response_format"],{"type":"json_object"})

if __name__ == "__main__": unittest.main()
