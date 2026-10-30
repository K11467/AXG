import unittest
from local_inference import cache_is_valid


class InferenceResumeTests(unittest.TestCase):
    def test_generated_but_unparsed_response_is_not_cached_success(self):
        self.assertFalse(cache_is_valid({'status': 'ok', 'kind': 'reason', 'parse_ok': False}))
        self.assertFalse(cache_is_valid({'status': 'parse_error', 'kind': 'reason', 'parse_ok': False}))
        self.assertTrue(cache_is_valid({'status': 'ok', 'kind': 'reason', 'parse_ok': True}))
        self.assertTrue(cache_is_valid({'status': 'ok', 'kind': 'caption'}))
