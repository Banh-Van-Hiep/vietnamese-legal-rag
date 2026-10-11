import unittest
from team2_rag.llm.service import LLMService
from team2_rag.llm.fake import FakeLLMProvider
from team2_rag.llm.errors import LLMBadOutputError, LLMTimeoutError
from team2_rag.tests.helpers import GOOD_TEXT, CONTEXT, QUESTION

class ServiceTests(unittest.TestCase):
    def test_fake_provider_works_offline(self):
        p=FakeLLMProvider([GOOD_TEXT]); r=LLMService(p).ask(QUESTION,CONTEXT)
        self.assertEqual(r.output.status,"answered")
        self.assertEqual(r.retries,0)
    def test_bad_output_is_not_retried(self):
        p=FakeLLMProvider(["bad json",GOOD_TEXT]); svc=LLMService(p)
        with self.assertRaises(LLMBadOutputError): svc.ask(QUESTION,CONTEXT)
        self.assertEqual(len(p.calls),1)
    def test_timeout_is_not_retried_by_default(self):
        p=FakeLLMProvider([LLMTimeoutError("timeout"),GOOD_TEXT]); svc=LLMService(p)
        with self.assertRaises(LLMTimeoutError): svc.ask(QUESTION,CONTEXT)
        self.assertEqual(len(p.calls),1)
    def test_history_and_original_question_reach_prompt(self):
        p=FakeLLMProvider([GOOD_TEXT]); LLMService(p).ask("Câu đã diễn giải",CONTEXT,[{"role":"user","content":"Câu trước"}],original_question=QUESTION)
        user=p.calls[0][0].user
        self.assertIn(QUESTION,user); self.assertIn("Câu đã diễn giải",user); self.assertIn("Câu trước",user)

if __name__ == "__main__": unittest.main()
