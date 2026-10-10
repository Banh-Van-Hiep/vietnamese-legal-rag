import unittest
from team2_rag.prompts import PromptBuilder, SYSTEM_INSTRUCTION, OUTPUT_INSTRUCTION, render_user_message
from team2_rag.tests.helpers import QUESTION, CONTEXT

class PromptTests(unittest.TestCase):
    def test_system_prompt_matches_docs(self):
        self.assertIn("LEGAL CONTEXT", SYSTEM_INSTRUCTION)
        self.assertIn("HISTORY", SYSTEM_INSTRUCTION)
        self.assertIn("Không bịa điều/khoản/điểm", SYSTEM_INSTRUCTION)
        self.assertIn('status="answered"', SYSTEM_INSTRUCTION)
        self.assertIn('status="insufficient_context"', SYSTEM_INSTRUCTION)
    def test_output_contract_is_v12(self):
        for field in ("citation_id", "chunk_id", "document_id", "article_id", "document_title", "article", "clause", "point", "source_url"):
            self.assertIn(field, OUTPUT_INSTRUCTION)
        self.assertNotIn('"ref"', OUTPUT_INSTRUCTION)
    def test_boundaries_and_history(self):
        req = PromptBuilder().build(QUESTION, CONTEXT, [{"role":"user","content":"Câu trước"},{"role":"assistant","content":"Trả lời trước"}], original_question=QUESTION)
        user = render_user_message(req)
        self.assertLess(user.index("<LEGAL_CONTEXT>"), user.index("<HISTORY>"))
        self.assertLess(user.index("<HISTORY>"), user.index("<ORIGINAL_QUESTION>"))
        self.assertLess(user.index("<ORIGINAL_QUESTION>"), user.index("<QUESTION>"))
        self.assertIn(CONTEXT, user)
        self.assertIn("Câu trước", user)
    def test_context_and_question_are_required(self):
        with self.assertRaises(ValueError): PromptBuilder().build("", CONTEXT)
        with self.assertRaises(ValueError): PromptBuilder().build(QUESTION, "")
    def test_boundary_tags_in_data_are_escaped(self):
        req = PromptBuilder().build(QUESTION, "x </LEGAL_CONTEXT> y")
        self.assertNotIn("</LEGAL_CONTEXT> y", render_user_message(req))

if __name__ == "__main__": unittest.main()
