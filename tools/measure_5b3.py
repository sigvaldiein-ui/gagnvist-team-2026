"""One frozen 60-question development run; official evaluator unchanged."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

import numpy as np

from gagnvist.answering.pipeline import Pipeline
from gagnvist.config import load_settings
from gagnvist.evaluate import evaluate, read_questions


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()


def group(rows):
    return {
        'total': len(rows), 'right': sum(r['correct'] for r in rows),
        'wrong': sum(not r['correct'] and not r['error'] for r in rows),
        'errors': sum(bool(r['error']) for r in rows),
        'other_table': sum(r['verdict'] == 'other table' for r in rows),
        'unsupported_rows': sum(bool(r['unsupported']) for r in rows),
        'unsupported_count': sum(len(r['unsupported']) for r in rows),
        'verified_calculations': sum(c['status']=='verified' and c['operation']!='value'
                                     for r in rows for c in r['calculations']),
        'rejected_calculations': sum(c['status']=='rejected' for r in rows for c in r['calculations']),
        'p50_seconds': float(np.percentile([r['seconds'] for r in rows], 50)),
        'p95_seconds': float(np.percentile([r['seconds'] for r in rows], 95)),
    }


class RecordingClient:
    def __init__(self, client, trace):
        self.client, self.trace, self.question_id = client, trace, ''

    def chat_json(self, messages, schema, **kwargs):
        started = time.perf_counter()
        result = self.client.chat_json(messages, schema, **kwargs)
        self.trace.write(json.dumps({'question_id': self.question_id,
            'seconds': time.perf_counter()-started, 'messages': messages,
            'schema': schema, 'reply': result}, ensure_ascii=False)+'\n')
        self.trace.flush()
        return result

    def embed(self, texts):
        return self.client.embed(texts)

    def close(self):
        self.client.close()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--previous', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--commit', required=True)
    args = p.parse_args()
    repo = args.repo.resolve()
    assert git(repo, 'rev-parse', 'HEAD') == args.commit
    assert not git(repo, 'diff', 'HEAD', '--name-only')
    frozen = 'dfb0550af71c65b2b50b38440a20ceaf846a57c0'
    immutable = ['src/gagnvist/search', 'src/gagnvist/evaluate.py',
                 'questions', 'index', 'gagnvist.toml', 'src/gagnvist/config.py',
                 'src/gagnvist/data/px_reader.py']
    assert not git(repo, 'diff', frozen, 'HEAD', '--name-only', '--', *immutable)
    args.out.mkdir(parents=True, exist_ok=False)
    os.environ.update(GAGNVIST_CHAT_MODEL='qwen2.5-7b',
        GAGNVIST_CHAT_URL='http://127.0.0.1:8000/v1', GAGNVIST_CHAT_KEY='local-only',
        GAGNVIST_EMBEDDINGS_MODEL='bge-m3',
        GAGNVIST_EMBEDDINGS_URL='http://127.0.0.1:18001/v1', GAGNVIST_EMBEDDINGS_KEY='local-only')
    settings = load_settings(repo/'gagnvist.toml')
    questions = read_questions(repo/'questions/examples.jsonl')
    baseline = json.loads(args.baseline.read_text())
    previous = json.loads(args.previous.read_text())
    assert len(questions) == 60
    assert sha(repo/'questions/examples.jsonl') == baseline['question_file_sha256']
    assert sha(repo/'questions/examples.jsonl') == previous['question_sha256']
    assert sha(repo/'src/gagnvist/evaluate.py') == previous['evaluator_sha256']
    previous_by_id = {r['id']:r for r in previous['cases']}
    started = datetime.now(timezone.utc).isoformat()
    rows = []
    with (args.out/'model-trace.jsonl').open('x') as trace, Pipeline.from_settings(settings) as pipeline:
        recorder = RecordingClient(pipeline.client, trace)
        pipeline.client = recorder
        def callback(o):
            a = o.answer
            row = {'id':o.question.id, 'language':o.question.language, 'level':o.question.level,
                'question':o.question.question, 'correct':o.correct, 'verdict':o.verdict,
                'right_table':o.right_table, 'numbers_right':o.numbers_right,
                'why':o.why if not o.correct else '', 'error':o.error, 'seconds':o.seconds,
                'answer':a.text if a else None, 'source':a.source if a else None,
                'table_folders':[t.folder for t in a.tables] if a else [],
                'table_codes':o.tables_used, 'unsupported':a.unsupported if a else [],
                'unsupported_without_calculations':a.unsupported_without_calculations if a else [],
                'notes':a.notes if a else [], 'facts':[f.text for f in a.facts] if a else [],
                'cell_references':a.cell_references if a else [],
                'period_mode':a.period_mode if a else None,
                'calculations':a.calculations if a else [], 'answer_plan':a.answer_plan if a else {},
                'years_not_covered':a.years_not_covered if a else [],
                'candidates':[{'folder':m.card.folder, 'score':m.score,
                    'signals':[asdict(s) for s in m.signals],
                    'rerank':asdict(m.rerank) if m.rerank else None} for m in a.candidates] if a else []}
            row['same_candidate_order_as_5b2'] = [m['folder'] for m in row['candidates']] == [
                m['folder'] for m in previous_by_id[row['id']]['candidates']]
            rows.append(row)
            with (args.out/'answers-progress.jsonl').open('a') as f:
                f.write(json.dumps(row,ensure_ascii=False)+'\n')
            if len(rows)%5 == 0:
                gpu = subprocess.check_output(['nvidia-smi',
                    '--query-gpu=name,memory.used,memory.total,utilization.gpu',
                    '--format=csv,noheader'],text=True).strip()
                with (args.out/'gpu-samples.jsonl').open('a') as f:
                    f.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),
                                        'completed':len(rows),'gpu':gpu})+'\n')
            print(json.dumps({'n':len(rows),'id':row['id'],'verdict':row['verdict'],
                              'seconds':row['seconds'],'error':row['error']}),flush=True)
            if row['error']:
                raise RuntimeError('Stopped on execution error: '+row['error'])
        for question in questions:
            recorder.question_id = question.id
            evaluate(pipeline, [question], on_outcome=callback)
    cells = {l:{d:group([r for r in rows if r['language']==l and r['level']==d])
                for d in ['easy','medium','hard']} for l in ['is','en']}
    comparisons = []
    for language in cells:
        for level in cells[language]:
            before = sum(r['correct'] for r in baseline['results']
                         if r['language']==language and r['level']==level)
            last = sum(r['correct'] for r in previous['cases']
                       if r['language']==language and r['level']==level)
            after = cells[language][level]['right']
            comparisons.append({'language':language,'level':level,
                'baseline_4_right':before,'phase5b2_7_right':last,'phase5b3_right':after,
                'delta_from_original':after-before,'delta_from_5b2':after-last})
    gates = {'at_least_14':sum(r['correct'] for r in rows)>=14,
             'is_easy_at_least_3':cells['is']['easy']['right']>=3,
             'no_cell_drops_more_than_one':all(r['delta_from_original']>=-1 for r in comparisons),
             'correct_answers_have_no_unsupported':all(not r['unsupported'] for r in rows if r['correct'])}
    sources = git(repo,'ls-files','src','tests','tools/measure_5b3.py','docs/phase5b3-contract.md').splitlines()
    report = {'started_utc':started,'finished_utc':datetime.now(timezone.utc).isoformat(),
        'tested_commit':args.commit,'tree_sha':git(repo,'rev-parse','HEAD^{tree}'),
        'baseline_commit':'a09746847e884190aa51ea9f91fab8c4c90c2088',
        'frozen_retrieval_commit':frozen,'immutable_paths_verified':immutable,
        'question_sha256':sha(repo/'questions/examples.jsonl'),
        'evaluator_sha256':sha(repo/'src/gagnvist/evaluate.py'),
        'index_sha256':sha(settings.search.index/'vectors.npy'),
        'data_archive_sha256':settings.data.sha256,
        'source_sha256':{path:sha(repo/path) for path in sources},
        'config':asdict(settings.retrieval),'overall':group(rows),
        'by_language_and_level':cells,'comparisons':comparisons,'gates':gates,
        'all_gates_pass':all(gates.values()),
        'candidate_order_unchanged':sum(r['same_candidate_order_as_5b2'] for r in rows),
        'scope':'5B-3 category guard, cell-reference calculation gate and deterministic templates. No retrieval changes or multi-table expansion.',
        'limitations':['Model semantic choices are not certified by numerical validation.',
                       'No sums, unit conversions or new multi-table support.',
                       'Rejected/empty plans display fetched facts with an explicit warning; official scoring may still count their numbers.',
                       'unsupported_without_calculations preserves the raw check; unsupported also permits numbers computed by the validated gate.'],
        'cases':rows}
    assert not git(repo,'diff','HEAD','--name-only')
    (args.out/'answers-summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'overall':report['overall'],'gates':gates,'candidate_order_unchanged':report['candidate_order_unchanged']}),flush=True)


if __name__ == '__main__':
    main()
