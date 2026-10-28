# Interface references

- [Contract](../../../../../contracts/v0.1/CONTRACT.md), [schema](../../../../../contracts/v0.1/retrieval_output.schema.json): không thay đổi.
- evaluate(retriever, cases, method, groups, corpus) nhận object có retrieve(question, top_k=20).
- CLI scripts/eval_retrieval.py: --method bm25|dense|hybrid_rrf --golden PATH --groups PATH --chunks PATH --index PATH --output PATH; Dense thêm --model/--revision/--qdrant-url.
- --factory owner_module:function nhận argparse Namespace và trả retriever; đây là adapter QA, không định nghĩa factory production của Team 1.
- JSON report v1 nội bộ; exit 0 complete, 1 query/schema error, 2 setup/dependency error. Mọi lần parse argument thành công đều ghi report nếu output ghi được.
- Mixin tests/retriever_contract.py không kế thừa TestCase; concrete class khai báo retriever/method/sample_question. Hybrid có thể dùng lại.
