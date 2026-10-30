"""Report-only aggregation: missing evidence never becomes a normal prediction."""
import json


def load_matching_results(directory, requests=None):
    """Read successful results only when their saved inputs match this run."""
    values = {}
    expected = {r['id']: r for r in requests} if requests is not None else None
    for path in sorted(directory.glob('*.json'), key=lambda p: p.stat().st_mtime):
        value = json.loads(path.read_text(encoding='utf-8'))
        if value.get('status') != 'ok':
            continue
        if expected is not None:
            wanted = dict(expected.get(value['id'], {}))
            actual = dict(value.get('request', {}))
            wanted.pop('strict_output', None)
            actual.pop('strict_output', None)
            if not wanted or wanted != actual:
                continue
        value['_path'] = path
        values[value['id']] = value
    return values


def binary_metrics(labels, predictions):
    valid = {k: predictions[k] for k in labels if isinstance(predictions.get(k), bool)}
    info = {'complete': bool(labels) and len(valid) == len(labels),
            'expected': len(labels), 'valid': len(valid),
            'missing': sorted(set(labels) - set(valid))}
    if not info['complete']:
        return info
    tp = sum(valid[k] and labels[k] for k in labels)
    fp = sum(valid[k] and not labels[k] for k in labels)
    fn = sum(not valid[k] and labels[k] for k in labels)
    tn = sum(not valid[k] and not labels[k] for k in labels)
    error_f1 = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0
    normal_f1 = 2 * tn / (2 * tn + fp + fn) if 2 * tn + fp + fn else 0
    return {**info, 'n': len(labels), 'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn,
            'error_f1': error_f1, 'normal_f1': normal_f1,
            'macro_f1': (error_f1 + normal_f1) / 2}


def graph_action_rows(requests, predictions, baseline_requests):
    rows = {r['id']: {'request_ids': [], 'complete': False, 'is_error': None, 'error_score': None}
            for r in baseline_requests}
    for req in requests:
        start, end = req['parent_action']['start_end']
        candidates = []
        for base in baseline_requests:
            case = base['case']
            overlap = min(end, case['end_time']) - max(start, case['start_time'])
            if case['recording_id'] == req['case']['recording_id'] and overlap > 0:
                candidates.append((overlap, base['id']))
        if not candidates:
            raise ValueError(f'No GT action interval matches graph request {req["id"]}')
        key = max(candidates)[1]
        rows[key]['request_ids'].append(req['id'])
    for row in rows.values():
        values = [predictions.get(k) for k in row['request_ids']]
        row['complete'] = bool(values) and all(v and v.get('parse_ok') and
                                              isinstance(v.get('is_error'), bool) for v in values)
        if row['complete']:
            row['is_error'] = any(v['is_error'] for v in values)
            row['error_score'] = max(v['error_score'] for v in values)
    return rows
