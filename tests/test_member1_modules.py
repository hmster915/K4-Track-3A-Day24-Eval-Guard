"""Member 1 offline behavior tests; ML/API results are separate live evidence."""
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.m1_chunking import chunk_hierarchical, load_documents
from src.m2_search import HybridSearch, SearchResult, reciprocal_rank_fusion
from src.m3_rerank import CrossEncoderReranker
from src.m5_enrichment import enrich_chunks
from src.phase_a_ragas import run_ragas_50q

pytestmark = pytest.mark.student


def test_chunk_boundaries_and_provenance(tmp_path):
    text = '# Policy\n> Version: 2\n\n## Leave\n15 days per year. Carry over 5 days.\n\n## VPN\nMFA required.'
    (tmp_path / 'policy.md').write_text(text, encoding='utf-8')
    doc = load_documents(str(tmp_path))[0]
    parents, children = chunk_hierarchical(doc['text'], doc['metadata'], parent_size=40, child_size=20)
    by_id = {parent.metadata['parent_id']: parent for parent in parents}
    assert len(by_id) == len(parents)
    assert all(child.parent_id in by_id and child.text in by_id[child.parent_id].text for child in children)
    assert all(len(child.text) <= 20 for child in children)
    assert all(child.metadata['source'] == 'policy.md' for child in children)
    assert all('MFA' not in child.text for child in children if child.metadata['section'] == 'Leave')
    other, _ = chunk_hierarchical(text, {'source': 'other.md'})
    assert set(by_id).isdisjoint(p.metadata['parent_id'] for p in other)


def test_enrichment_preserves_count_order_and_raw_text():
    chunks = [{'text': '15 days.', 'metadata': {'source': 'leave.md', 'version': '2024'}},
              {'text': 'MFA required.', 'metadata': {'source': 'vpn.md'}}]
    output = enrich_chunks(chunks)
    assert len(output) == len(chunks)
    assert all(item.enriched_text.endswith(raw['text']) for item, raw in zip(output, chunks))
    assert '2024' in output[0].enriched_text and 'vpn.md' in output[1].enriched_text
    assert chunks[0]['text'] == '15 days.'


def test_fusion_promotes_shared_hits_but_preserves_different_sources():
    a = SearchResult('same', .9, {'source': 'a'}, 'bm25')
    b = SearchResult('same', .8, {'source': 'b'}, 'bm25')
    output = reciprocal_rank_fusion([[a, b], [b]], top_k=2)
    assert [r.metadata['source'] for r in output] == ['b', 'a']
    assert output[0].score == pytest.approx(1 / 62 + 1 / 61)


def test_hybrid_uses_qdrant_19_search_and_keeps_metadata(monkeypatch):
    import src.m2_search as module
    monkeypatch.setattr(module, 'segment_vietnamese', lambda text: text.lower().split())
    search = HybridSearch.__new__(HybridSearch)
    search.chunks = [{'text': 'leave', 'metadata': {'source': 'leave.md', 'chunk_index': 0}}]
    search.bm25 = SimpleNamespace(get_scores=lambda words: [2.0])
    search.encoder = SimpleNamespace(encode=Mock(return_value=SimpleNamespace(tolist=lambda: [1., 0.])))
    search.client = SimpleNamespace(search=Mock(return_value=[SimpleNamespace(
        payload={'text': 'leave', 'source': 'leave.md', 'chunk_index': 0}, score=.8)]))
    output = search.search('leave')
    assert len(output) == 1 and output[0].metadata['source'] == 'leave.md'
    assert search.client.search.call_args.kwargs['query_vector'] == [1., 0.]
    search.client.search.side_effect = RuntimeError('Qdrant unavailable')
    with pytest.raises(RuntimeError, match='Qdrant unavailable'):
        search.search('leave')


def test_rerank_uses_model_scores_and_keeps_source():
    reranker = CrossEncoderReranker.__new__(CrossEncoderReranker)
    reranker.model = SimpleNamespace(predict=Mock(return_value=[.1, .9]))
    docs = [{'text': 'A', 'metadata': {'source': 'a'}}, {'text': 'B', 'metadata': {'source': 'b'}}]
    output = reranker.rerank('Q', docs, top_k=1)
    assert output[0].text == 'B' and output[0].metadata['source'] == 'b'
    reranker.model.predict.side_effect = RuntimeError('model failed')
    with pytest.raises(RuntimeError, match='model failed'):
        reranker.rerank('Q', docs)


@pytest.mark.parametrize('measured', [[], [SimpleNamespace(
    faithfulness=float('nan'), answer_relevancy=.8, context_precision=.8, context_recall=.8)]])
def test_phase_a_rejects_missing_or_invalid_metrics(monkeypatch, measured):
    monkeypatch.setitem(sys.modules, 'src.m4_eval', SimpleNamespace(evaluate_ragas=lambda *args: {
        'per_question': measured, 'metadata': {'evaluator_models': ['actual-evaluator']}}))
    row = {'id': 1, 'distribution': 'factual', 'question': 'Q', 'answer': 'A',
           'contexts': ['C'], 'ground_truth': 'GT'}
    with pytest.raises(ValueError):
        run_ragas_50q([row])


def test_m4_passes_real_evaluator_configuration_and_preserves_scores(monkeypatch):
    from src import m4_eval as module
    monkeypatch.setattr(module, 'OPENAI_API_KEY', 'test-only')
    llm = SimpleNamespace(model_name='configured-llm')
    embedding = SimpleNamespace(model='configured-embedding')
    monkeypatch.setitem(sys.modules, 'torch', SimpleNamespace())
    monkeypatch.setitem(sys.modules, 'datasets', SimpleNamespace(Dataset=SimpleNamespace(from_dict=lambda d: d)))
    monkeypatch.setitem(sys.modules, 'langchain_openai', SimpleNamespace(
        ChatOpenAI=lambda **kw: llm, OpenAIEmbeddings=lambda **kw: embedding))
    values = {'faithfulness': .9, 'answer_relevancy': .8, 'context_precision': .7, 'context_recall': .6}
    frame = SimpleNamespace(to_dict=lambda **kw: [values])
    evaluate = Mock(return_value=SimpleNamespace(to_pandas=lambda: frame))
    monkeypatch.setitem(sys.modules, 'ragas', SimpleNamespace(evaluate=evaluate))
    monkeypatch.setitem(sys.modules, 'ragas.metrics', SimpleNamespace(**{
        name: Mock for name in ('Faithfulness', 'AnswerRelevancy', 'ContextPrecision', 'ContextRecall')}))
    monkeypatch.setitem(sys.modules, 'ragas.run_config', SimpleNamespace(RunConfig=lambda **kw: kw))
    actual = module.evaluate_ragas(['Q'], ['A'], [['C']], ['GT'])
    assert vars(actual['per_question'][0]) == values
    assert actual['metadata']['evaluator_models'] == ['configured-llm', 'configured-embedding']
    assert evaluate.call_args.kwargs['raise_exceptions'] is True
    values['faithfulness'] = float('nan')
    with pytest.raises(ValueError, match='Invalid RAGAS scores'):
        module.evaluate_ragas(['Q'], ['A'], [['C']], ['GT'])
