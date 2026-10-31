"""Measure retrieval ablations and unchanged answer scoring; no model/Pod lifecycle.

Keep runtime addresses and raw operational logs out of published reports.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import time
import unicodedata

import numpy as np

from gagnvist.answering.language import guess_language
from gagnvist.answering.pipeline import Pipeline
from gagnvist.config import load_settings
from gagnvist.evaluate import evaluate, read_questions
from gagnvist.models.client import Endpoint, ModelClient
from gagnvist.search.hybrid import HybridRetriever, RetrievalConfig, query_parts
from gagnvist.search.table_index import TableIndex
from gagnvist.search.vector_search import VectorIndex


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ranks(codes, question):
    return [next((n+1 for n, code in enumerate(codes) if code in part.accepted), None)
            for part in question.parts]


def metrics(rows):
    def group(values):
        output = {'questions': len(values)}
        for k in [1, 5, 10, 100]:
            hit = lambda r: r is not None and r <= k
            fractions = [sum(hit(r) for r in v['part_ranks']) / len(v['part_ranks']) for v in values]
            parts = sum(len(v['part_ranks']) for v in values)
            output[f'recall@{k}'] = {
                'macro_part_recall': float(np.mean(fractions)) if values else None,
                'micro_part_recall': sum(sum(hit(r) for r in v['part_ranks']) for v in values)/parts if parts else None,
                'any_part': sum(any(hit(r) for r in v['part_ranks']) for v in values),
                'all_parts': sum(all(hit(r) for r in v['part_ranks']) for v in values),
            }
        for field in ['seconds', 'cpu_seconds']:
            output[field] = {f'p{p}': float(np.percentile([v[field] for v in values], p)) if values else None for p in [50,95]}
        return output
    return {'overall': group(rows), 'by_language': {l: group([r for r in rows if r['language']==l]) for l in ['is','en']},
            'by_level': {level: group([r for r in rows if r['level']==level]) for level in ['easy','medium','hard']},
            'by_language_and_level': {l: {level: group([r for r in rows if r['language']==l and r['level']==level]) for level in ['easy','medium','hard']} for l in ['is','en']}}


class CachedClient:
    def __init__(self, live, questions, vectors):
        self.live = live
        self.cache = {unicodedata.normalize('NFC', q.question): np.load(vectors/(q.id+'.npy')).reshape(1,-1) for q in questions}
        self.api_seconds = 0.
        self.api_calls = 0

    def embed(self, texts):
        result = []
        for text in texts:
            if text not in self.cache:
                started = time.perf_counter()
                self.cache[text] = self.live.embed([text])
                self.api_seconds += time.perf_counter()-started
                self.api_calls += 1
            result.append(self.cache[text][0])
        return np.array(result, dtype=np.float32)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--vectors', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--answers', action='store_true')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    repo = args.repo.resolve()
    os.environ.update(GAGNVIST_CHAT_MODEL='qwen2.5-7b', GAGNVIST_CHAT_URL='http://127.0.0.1:8000/v1', GAGNVIST_CHAT_KEY='local-only', GAGNVIST_EMBEDDINGS_MODEL='bge-m3', GAGNVIST_EMBEDDINGS_URL='http://127.0.0.1:18001/v1', GAGNVIST_EMBEDDINGS_KEY='local-only')
    settings = load_settings(repo/'gagnvist.toml')
    questions = read_questions(repo/'questions/examples.jsonl')
    baseline = json.loads(args.baseline.read_text())
    assert len(questions)==60
    assert sha(repo/'questions/examples.jsonl')==baseline['question_file_sha256']
    tables = TableIndex(settings.table_database)
    entries = {e.folder:e for e in tables.entries()}
    db = sqlite3.connect(settings.table_database.as_uri()+'?mode=ro', uri=True)
    periods = {}
    for folder, dimension, first, last in db.execute('SELECT c.folder,c.dimension_code,MIN(c.code),MAX(c.code) FROM categories c JOIN dimensions d ON c.folder=d.folder AND c.dimension_code=d.code WHERE d.is_time=1 GROUP BY c.folder,c.dimension_code'):
        periods.setdefault(folder,[]).append({'dimension':dimension,'lexical_min_code':first,'lexical_max_code':last,'used_for_ranking':False})
    db.close()
    index = VectorIndex.load(settings.search.index)
    live = ModelClient(Endpoint(settings.models.chat_url,'local-only',settings.models.chat),Endpoint(settings.models.embeddings_url,'local-only',settings.models.embeddings))
    client = CachedClient(live, questions, args.vectors)
    configs = {
        'dense_top5': RetrievalConfig(mode='dense',candidate_limit=5,decompose=False),
        'dense_top100': RetrievalConfig(mode='dense',decompose=False),
        'lexical': RetrievalConfig(mode='lexical',decompose=False),
        'hybrid': RetrievalConfig(decompose=False),
        'hybrid_subqueries': settings.retrieval,
    }
    ablations = {}
    with (args.out/'retrieval-cases.jsonl').open('x') as trace:
        for name, config in configs.items():
            started = time.perf_counter(); retriever = HybridRetriever(index, config)
            init_seconds = time.perf_counter()-started
            rows=[]
            for q in questions:
                question = unicodedata.normalize('NFC',q.question)
                api_before = client.api_seconds
                started = time.perf_counter()
                matches = retriever.search(question,guess_language(question),client)
                seconds = time.perf_counter()-started
                used_api = client.api_seconds-api_before
                candidates=[]
                for rank, m in enumerate(matches,1):
                    e=entries[m.card.folder]
                    candidates.append({'rank':rank,'folder':e.folder,'table_code':e.table_code,'language':e.language,'score':m.score,'signals':[asdict(s) for s in m.signals], 'api_url':e.api_url,'data_path':'data/'+e.folder+'/data.px','period_metadata':periods.get(e.folder,[])})
                row={'stage':name,'id':q.id,'language':q.language,'level':q.level,'part_ranks':ranks([c['table_code'] for c in candidates],q),'seconds':seconds,'cpu_seconds':max(0,seconds-used_api),'embedding_api_seconds':used_api,'queries':query_parts(question,config.max_subqueries) if config.decompose else [question],'candidates':candidates}
                rows.append(row)
                trace.write(json.dumps(row,ensure_ascii=False)+'\n');trace.flush()
            ablations[name]={'config':asdict(config),'index_build_seconds':init_seconds,'metrics':metrics(rows),'rows_without_candidates':sum(not r['candidates'] for r in rows)}
            print(json.dumps({'stage':name,**ablations[name]['metrics']['overall']},ensure_ascii=False),flush=True)
    live.close(); tables.close()
    version = subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    changed = subprocess.check_output(['git','-C',str(repo),'status','--porcelain'],text=True).strip()
    source_paths=['src/gagnvist/search/hybrid.py','src/gagnvist/search/vector_search.py','src/gagnvist/config.py','src/gagnvist/answering/pipeline.py','gagnvist.toml']
    output={'tested_commit':version,'working_tree_status':changed,'source_sha256':{p:sha(repo/p) for p in source_paths},'question_sha256':sha(repo/'questions/examples.jsonl'),'evaluator_sha256':sha(repo/'src/gagnvist/evaluate.py'),'index_sha256':sha(settings.search.index/'vectors.npy'),'data_archive_sha256':settings.data.sha256,'scoring_identity':'official accepted table codes; full folders retained, ambiguous codes not certified as exact semantic matches','ablations':ablations,'new_embedding_calls':client.api_calls,'new_embedding_seconds':client.api_seconds,'latency_note':'retrieval timing excludes index construction; cpu_seconds subtracts uncached model API time. Full-question vectors replay verified Gate-0 embeddings; subqueries use live BGE then cache. Not cold end-to-end timings.'}
    (args.out/'retrieval-summary.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    if args.answers:
        rows=[]
        def callback(o):
            a=o.answer
            row={'id':o.question.id,'language':o.question.language,'level':o.question.level,'question':o.question.question,'correct':o.correct,'verdict':o.verdict,'numbers_right':o.numbers_right,'right_table':o.right_table,'seconds':o.seconds,'answer':a.text if a else None,'why':o.why if not o.correct else '', 'error':o.error,'source':a.source if a else None,'table_folders':[t.folder for t in a.tables] if a else [],'table_codes':o.tables_used,'unsupported':a.unsupported if a else [],'notes':a.notes if a else [],'facts':[f.text for f in a.facts] if a else [],'candidates':[{'folder':m.card.folder,'score':m.score,'signals':[asdict(s) for s in m.signals]} for m in a.candidates] if a else []}
            rows.append(row)
            with (args.out/'answers-progress.jsonl').open('a') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
            print(json.dumps({'n':len(rows),'id':row['id'],'verdict':row['verdict'],'seconds':row['seconds'],'error':row['error']}),flush=True)
            if row['error'] and any(s in row['error'].lower() for s in ['cannot reach','connection to','out of memory','within 120 s','answered 500']):
                raise RuntimeError('Service failure: '+row['error'])
        with Pipeline.from_settings(settings) as pipeline:
            evaluate(pipeline,questions,on_outcome=callback)
        def answer_group(group):
            return {'total':len(group),'right':sum(r['correct'] for r in group),'WRONG':sum(r['verdict']=='WRONG' for r in group),'other_table':sum(r['verdict']=='other table' for r in group),'error':sum(bool(r['error']) for r in group),'unsupported_rows':sum(bool(r['unsupported']) for r in group),'unsupported_count':sum(len(r['unsupported']) for r in group),'p50_seconds':float(np.percentile([r['seconds'] for r in group],50)) if group else None,'p95_seconds':float(np.percentile([r['seconds'] for r in group],95)) if group else None}
        groups={l:{level:answer_group([r for r in rows if r['language']==l and r['level']==level]) for level in ['easy','medium','hard']} for l in ['is','en']}
        regressions=[]
        for l in groups:
            for level in groups[l]:
                old=sum(r['correct'] for r in baseline['results'] if r['language']==l and r['level']==level)
                new=groups[l][level]['right']
                regressions.append({'language':l,'level':level,'baseline_right':old,'after_right':new,'delta':new-old,'regression_exceeds_one':new-old < -1})
        answer_report={'tested_commit':version,'source_sha256':output['source_sha256'],'question_sha256':output['question_sha256'],'evaluator_sha256':output['evaluator_sha256'],'config':asdict(settings.retrieval),'overall':answer_group(rows),'by_language_and_level':groups,'regressions':regressions,'regression_gate_pass':not any(r['regression_exceeds_one'] for r in regressions),'hard_scope':'No extra_tables implementation; retrieval decomposition is not multi-table answering.','cases':rows}
        (args.out/'answers-summary.json').write_text(json.dumps(answer_report,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({'answers':answer_report['overall'],'regression_gate_pass':answer_report['regression_gate_pass']}),flush=True)


if __name__=='__main__':main()
