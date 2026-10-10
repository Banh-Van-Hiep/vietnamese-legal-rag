import json, unittest
from team2_rag.llm.output_parser import parse_llm_output
from team2_rag.llm.errors import LLMBadOutputError
from team2_rag.tests.helpers import GOOD_TEXT, good_output

class ParserTests(unittest.TestCase):
    def test_valid_answered(self):
        out = parse_llm_output(GOOD_TEXT)
        self.assertEqual(out.status, "answered")
        self.assertEqual(out.citations[0].citation_id, "C1")
    def test_valid_insufficient(self):
        out = parse_llm_output(json.dumps({"status":"insufficient_context","answer":"Chưa đủ căn cứ.","citations":[]}, ensure_ascii=False))
        self.assertEqual(out.citations, ())
    def test_old_ref_schema_is_rejected(self):
        x = {"status":"answered","answer":"A [1].","citations":[{"ref":1,"chunk_id":"x"}]}
        with self.assertRaises(LLMBadOutputError): parse_llm_output(json.dumps(x))
    def test_extra_field_is_rejected(self):
        x = good_output(); x["extra"] = 1
        with self.assertRaises(LLMBadOutputError): parse_llm_output(json.dumps(x))
    def test_invalid_marker_is_rejected(self):
        with self.assertRaises(LLMBadOutputError): parse_llm_output(json.dumps(good_output("A [C2]."), ensure_ascii=False))
    def test_no_fence_repair(self):
        with self.assertRaises(LLMBadOutputError): parse_llm_output("```json\n" + GOOD_TEXT + "\n```")

if __name__ == "__main__": unittest.main()
