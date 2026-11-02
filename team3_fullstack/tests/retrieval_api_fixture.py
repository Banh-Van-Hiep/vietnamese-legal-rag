"""Labelled HTTP fixtures only. No retrieval model or LLM is called."""
import copy
import json
import os
from pathlib import Path

from team1_data.retrieval.errors import RetrievalUnavailableError
from team2_rag.api import create_app
from team2_rag.llm.errors import LLMTimeoutError

ROOT=Path(__file__).resolve().parents[2]


def create_fixture_app():
    scenario=os.environ.get('EVALUATION_FIXTURE_SCENARIO','answered')
    sample=json.loads((ROOT/'team2_rag/data/samples/rerank_output_sample.json').read_text(encoding='utf-8'))
    row=sample['results'][0]
    fields=('chunk_id','document_id','article_id','document_title','article','clause','point','source_url')
    citation={'citation_id':'C1',**{k:row[k] for k in fields}}

    class FixturePipeline:
        def query(self,question,history=None,*,request_id=None):
            if os.environ.get('EVALUATION_FIXTURE_LOG'):
                with Path(os.environ['EVALUATION_FIXTURE_LOG']).open('a',encoding='utf-8') as stream:
                    stream.write(json.dumps({'question':question,'history':history,'request_id':request_id},ensure_ascii=False)+'\n')
            if scenario=='retrieval_unavailable':raise RetrievalUnavailableError('fixture unavailable')
            if scenario=='timeout':raise LLMTimeoutError('fixture timeout')
            if scenario=='insufficient_context':return {'status':'insufficient_context','answer':'Dữ liệu kiểm thử chưa đủ căn cứ.','citations':[]}
            return {'status':'answered','answer':'Phản hồi giả lập kiểm thử contract, không phải tư vấn pháp luật '+('[C2]' if scenario=='invalid_citation' else '[C1]'),
                    'citations':[copy.deepcopy(citation)]}

    app=create_app(pipeline=FixturePipeline())
    app.title='Team 3 evaluation HTTP fixtures — MOCK ONLY'
    @app.middleware('http')
    async def mark_mock(request,call_next):
        response=await call_next(request)
        response.headers['X-RAG-Mode']='mock'
        return response
    return app
