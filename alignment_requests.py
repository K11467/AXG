"""Bridge upstream graph alignment and the local Transformers backend."""
import argparse
import copy
import json
from pathlib import Path

from local_inputs import make_case, sample_frames, subaction_interval
from result_summary import load_matching_results

WORK = Path('output/local7b')
ALIGNED = Path('output/CaptainCook4D/spicedhotchocolate/data_for_vlm_5_clust_gt')


def prepare():
    requests = []
    excluded = []
    provenance = json.loads((WORK / 'data_provenance.json').read_text())
    stride = provenance['caption_stride_seconds']
    for path in sorted(ALIGNED.glob('*.json')):
        data = json.loads(path.read_text())
        previous = []
        for ai, action in enumerate(data['action']):
            for si, sub in enumerate(action['subactions']):
                indices = sub['caption_idx']
                ticks = [int(Path(action['caption_paths'][i].replace('\\', '/')).stem) for i in indices]
                interval = subaction_interval(ticks, action['start_end'][1], caption_stride=stride)
                if interval is None:
                    excluded.append({'alignment_file': str(path), 'action_index': ai,
                                     'subaction_index': si, 'reason': 'duration below paper minimum of 2 seconds',
                                     'caption_timestamps_seconds': ticks})
                    continue
                start, end = interval
                frames = sample_frames(Path('data/public_cook4d/frames') / path.stem, start, end)
                case = make_case(path.stem, {'description': action['name'], 'start_time': start,
                                             'end_time': end}, frames, previous, subaction=sub['name'])
                requests.append({'id': f'{path.stem}_a{ai}_s{si}', 'kind': 'reason', 'case': case,
                                 'parent_action': {'name': action['name'], 'start_end': action['start_end']},
                                 'alignment_file': str(path), 'action_index': ai, 'subaction_index': si})
            previous.append(action['name'])
    (WORK / 'axg_requests.json').write_text(json.dumps(requests, indent=2), encoding='utf-8')
    (WORK / 'axg_excluded_short_segments.json').write_text(json.dumps(excluded, indent=2), encoding='utf-8')
    if not requests:
        raise ValueError('No graph-aligned subaction requests produced; inspect saved exclusions')
    print(f'Prepared {len(requests)} learned-graph subaction requests')


def export():
    requests = json.loads((WORK / 'axg_requests.json').read_text())
    results = load_matching_results(WORK / 'axg_results', requests)
    documents = {str(p): json.loads(p.read_text()) for p in ALIGNED.glob('*.json')}
    for req in requests:
        result = results.get(req['id'])
        if not result or not result.get('parse_ok'):
            raise ValueError(f'Missing/invalid graph inference result: {req["id"]}')
        sub = documents[req['alignment_file']]['action'][req['action_index']]['subactions'][req['subaction_index']]
        sub.update({'is_error': result['is_error'], 'error_score': result['error_score'],
                    'reasoning': result['reason'], 'local_result_id': req['id'],
                    'prediction_source': result.get('prediction_source', 'VLM correctness score')})
    output = Path('output/CaptainCook4D/spicedhotchocolate/error_reasoning_5_clust_gt_3f')
    output.mkdir(parents=True, exist_ok=True)
    for name, doc in documents.items():
        for ai, action in enumerate(doc['action']):
            retained = {r['subaction_index'] for r in requests
                        if r['alignment_file'] == name and r['action_index'] == ai}
            action['subactions'] = [s for si, s in enumerate(action['subactions']) if si in retained]
        # An empty subaction list is no evidence, not a correct classification.
        if any(not action['subactions'] for action in doc['action']):
            raise ValueError('An action has no retained subactions: do not default missing evidence to normal')
        doc['local_adaptation'] = json.loads((WORK / 'official_layout_provenance.json').read_text())
        (output / Path(name).name).write_text(json.dumps(doc, indent=2), encoding='utf-8')
    print('Exported all parsed graph results to official evaluation layout')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['prepare', 'export'])
    args = parser.parse_args()
    prepare() if args.mode == 'prepare' else export()
