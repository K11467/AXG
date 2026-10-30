"""Audit actual manifests, predictions, visual prototypes and learned graph files."""
import json
from pathlib import Path
import numpy as np
from result_summary import load_matching_results, binary_metrics, graph_action_rows

if __name__ == '__main__':
    work = Path('output/local7b')
    base = json.loads((work / 'baseline_requests.json').read_text())
    truth = json.loads((work / 'evaluation_labels.json').read_text())
    labels = {k: v['has_errors'] for k, v in truth.items()}
    audit = {'runs': {}, 'summaries': {}, 'prototypes': {}, 'graphs': {}}
    for suffix in ['', '_8f']:
        br = json.loads((work / f'baseline_requests{suffix}.json').read_text())
        gr = json.loads((work / f'axg_requests{suffix}.json').read_text())
        b = load_matching_results(work / f'baseline_results{suffix}', br)
        g = load_matching_results(work / f'axg_results{suffix}', gr)
        assert len(b) == len(br) == len(base) and len(g) == len(gr) > 0
        assert all(v['parse_ok'] for v in [*b.values(), *g.values()])
        rows = graph_action_rows(gr, g, base)
        bm = binary_metrics(labels, {k: v['is_error'] for k, v in b.items()})
        gm = binary_metrics(labels, {k: v['is_error'] for k, v in rows.items()})
        assert bm['complete'] and gm['complete']
        audit['runs'][suffix or '_3f'] = {
            'baseline_count': len(b), 'graph_count': len(g),
            'graph_drops': sum(v.get('prediction_source', '').startswith('AXG graph drop') for v in g.values()),
            'baseline_metrics': bm, 'graph_metrics': gm,
            'peak_allocated_gib': max(v['peak_allocated_gib'] for v in [*b.values(), *g.values()]),
            'hit_token_limit': sum(v['hit_token_limit'] for v in [*b.values(), *g.values()])}
    root = Path('output/CaptainCook4D/spicedhotchocolate')
    for f in (root / 'summarized_subactions_5_clust').glob('*/output.json'):
        names = [x['summarized_subaction'] for x in json.loads(f.read_text()).values()]
        assert names
        audit['summaries'][f.parent.name] = names
    assert len(audit['summaries']) == 7
    for action, names in audit['summaries'].items():
        for folder in ['v_subaction_features_5_clust', 'v_subaction_prog_features_5_clust']:
            files = list((root / folder / action).glob('*.npy'))
            assert len(files) == len(names), f'Stale/missing prototypes: {folder}/{action}'
            for f in files:
                a = np.load(f)
                assert a.shape == (256,) and np.isfinite(a).all() and np.linalg.norm(a) > 0
                audit['prototypes'][str(f)] = {'shape': list(a.shape), 'norm': float(np.linalg.norm(a))}
        f = root / 'axg_5_clust' / f'{action}.json'
        paths = json.loads(f.read_text())
        assert paths
        for edges in paths:
            assert edges and edges[0][0] == 0 and edges[-1][1] == len(names) + 1
            assert all(a[1] == b[0] for a, b in zip(edges, edges[1:]))
        audit['graphs'][action] = paths
    target = work / 'comparison_3f_8f.json'
    target.write_text(json.dumps(audit, indent=2), encoding='utf-8')
    print(json.dumps({'runs': audit['runs'], 'summary_counts': {k: len(v) for k, v in audit['summaries'].items()},
                      'prototype_arrays': len(audit['prototypes']), 'graphs': len(audit['graphs'])}, indent=2))
