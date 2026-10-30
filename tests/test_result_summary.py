import unittest
import json
import tempfile
from pathlib import Path
from result_summary import binary_metrics, graph_action_rows, load_matching_results
from generate_report import load_results


class ResultSummaryTests(unittest.TestCase):
    def test_incomplete_predictions_do_not_get_a_perfect_score(self):
        result = binary_metrics({'a': True, 'b': False}, {'a': True})
        self.assertFalse(result['complete'])
        self.assertNotIn('macro_f1', result)
        result = binary_metrics({'a': True, 'b': False}, {'a': True, 'b': False})
        self.assertTrue(result['complete'])
        self.assertEqual((result['tp'], result['tn'], result['macro_f1']), (1, 1, 1.0))

    def test_all_normal_prediction_exposes_false_negative(self):
        result = binary_metrics({'a': True, 'b': False}, {'a': False, 'b': False})
        self.assertEqual((result['tp'], result['fp'], result['fn'], result['tn']), (0, 0, 1, 1))
        self.assertAlmostEqual(result['macro_f1'], 1 / 3)

    def test_graph_any_error_aggregation_requires_all_expected_results(self):
        base = [{'id': 'actionA', 'case': {'recording_id': 'v', 'start_time': .5, 'end_time': 10.2}},
                {'id': 'actionB', 'case': {'recording_id': 'v', 'start_time': 10.2, 'end_time': 20.5}}]
        reqs = [{'id': 's1', 'case': {'recording_id': 'v'}, 'parent_action': {'start_end': [1, 11]}},
                {'id': 's2', 'case': {'recording_id': 'v'}, 'parent_action': {'start_end': [1, 11]}},
                {'id': 's3', 'case': {'recording_id': 'v'}, 'parent_action': {'start_end': [11, 21]}}]
        predictions = {'s1': {'parse_ok': True, 'is_error': False, 'error_score': .1},
                       's2': {'parse_ok': True, 'is_error': True, 'error_score': 1},
                       's3': {'parse_ok': True, 'is_error': False, 'error_score': .1}}
        rows = graph_action_rows(reqs, predictions, base)
        self.assertTrue(rows['actionA']['is_error'])
        self.assertFalse(rows['actionB']['is_error'])
        del predictions['s2']
        rows = graph_action_rows(reqs, predictions, base)
        self.assertIsNone(rows['actionA']['is_error'])
        self.assertFalse(rows['actionA']['complete'])

    def test_report_ignores_stale_inputs_even_with_same_request_id(self):
        req = {'id': 'a', 'kind': 'reason', 'case': {'frames': ['real.png']}}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            good = {'id': 'a', 'status': 'ok', 'parse_ok': True, 'request': req}
            stale = {**good, 'request': {**req, 'case': {'frames': ['old.png']}}}
            (root / 'good.json').write_text(json.dumps(good))
            (root / 'stale.json').write_text(json.dumps(stale))
            result = load_results(root, [req])
            self.assertEqual(result['a']['request']['case']['frames'], ['real.png'])

    def test_shared_caption_and_graph_loader_rejects_changed_prompts(self):
        for kind in ['caption', 'reason']:
            req = {'id': 'stable', 'kind': kind, 'prompt': 'current prompt'}
            old = {**req, 'prompt': 'old prompt'}
            with tempfile.TemporaryDirectory() as tmp:
                p = Path(tmp)
                (p / 'old.json').write_text(json.dumps({'id': 'stable', 'kind': kind, 'status': 'ok',
                                                      'parse_ok': True, 'request': old}))
                self.assertEqual(load_matching_results(p, [req]), {})
