import tempfile
import unittest
from pathlib import Path

from local_inputs import parse_response, sample_frames, build_prompt, make_case, subaction_interval


class LocalInputsTests(unittest.TestCase):
    def test_parser_does_not_invent_a_correct_prediction_on_failure(self):
        self.assertEqual(parse_response('Score: 0.25\nReason: Chocolate spills.'),
                         {'correctness_score': 0.25, 'error_score': 0.75,
                          'is_error': True, 'reason': 'Chocolate spills.', 'parse_ok': True})
        for text in ('No score available.', 'Score: 2\nReason: yes', 'Score: nan\nReason: no'):
            result = parse_response(text)
            self.assertFalse(result['parse_ok'])
            self.assertIsNone(result['is_error'])

    def test_short_segment_samples_available_real_frames_in_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            for n in (1, 2, 3, 10):
                (p / f'{n}.png').touch()
            frames = sample_frames(p, 0, 3, count=3, fps=1, first_index=1)
            self.assertEqual([Path(x).name for x in frames], ['1.png', '2.png', '3.png'])
            self.assertEqual(sample_frames(p, 8, 9, count=3, fps=1, first_index=1), [])

    def test_model_input_uses_action_names_but_never_error_labels(self):
        step = {'description': 'Add-Add 2 pieces of chocolate to the mug',
                'start_time': 1.0, 'end_time': 4.0, 'has_errors': True,
                'errors': ['SECRET_GROUND_TRUTH']}
        case = make_case('8_50', step, ['1.png', '2.png'], ['Fill milk'])
        self.assertNotIn('has_errors', case)
        self.assertNotIn('errors', case)
        prompt = build_prompt(case)
        self.assertNotIn('SECRET_GROUND_TRUTH', prompt)
        self.assertIn('Add 2 pieces', prompt)
        self.assertIn('Fill milk', prompt)

    def test_missing_step_is_not_fabricated_as_observed_clip(self):
        with self.assertRaises(ValueError):
            make_case('8_50', {'description': 'mix', 'start_time': -1, 'end_time': -1}, [], [])

    def test_graph_drops_use_the_official_error_description_prompt(self):
        prompt = build_prompt({'task': 'tea', 'action': 'stir', 'subaction': 'BG'})
        self.assertIn('it seems like you are making a mistake', prompt)
        self.assertNotIn('Score:', prompt)

    def test_normalized_hyphenated_action_is_not_truncated(self):
        step = {'description': 'Fill a microwave-safe mug with milk', 'start_time': 1, 'end_time': 2}
        self.assertEqual(make_case('v', step, ['1.png'], [])['action'], step['description'])

    def test_subaction_duration_uses_real_seconds_and_clamps_action_end(self):
        self.assertIsNone(subaction_interval([10], 20, caption_stride=1))
        self.assertEqual(subaction_interval([10, 11], 20, caption_stride=1), (10, 12))
        self.assertIsNone(subaction_interval([18, 19], 19.5, caption_stride=1))
        self.assertEqual(subaction_interval([10], 20, caption_stride=3), (10, 13))


if __name__ == '__main__':
    unittest.main()
