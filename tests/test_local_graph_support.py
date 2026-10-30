import unittest
from local_graph_support import select_action_paths, split_frame_ref, is_error_score
import local_graph_support
import tempfile
from pathlib import Path


class LocalGraphSupportTests(unittest.TestCase):
    def test_rebuilding_fewer_prototypes_removes_previous_run_surplus(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / '1.npy').write_bytes(b'previous prototype one')
            (root / '2.npy').write_bytes(b'previous prototype two')
            local_graph_support.prune_stale_prototypes(root, 1)
            self.assertTrue((root / '1.npy').exists())
            self.assertFalse((root / '2.npy').exists())

    def test_prototype_cleanup_refuses_unknown_files_and_empty_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / '1.npy').write_bytes(b'previous prototype')
            (root / 'custom.npy').write_bytes(b'user file')
            with self.assertRaises(ValueError):
                local_graph_support.prune_stale_prototypes(root, 1)
            with self.assertRaises(ValueError):
                local_graph_support.prune_stale_prototypes(root, 0)
            self.assertTrue((root / '1.npy').exists())
            self.assertTrue((root / 'custom.npy').exists())

    def test_background_filter_ignores_sentence_punctuation(self):
        for text in ['the person is waiting.', 'the person is waiting', ' The person  is waiting. ']:
            self.assertTrue(local_graph_support.is_background_caption(text))
        self.assertFalse(local_graph_support.is_background_caption('the person is pouring milk.'))

    def test_windows_frame_reference(self):
        self.assertEqual(split_frame_ref('8_25\\000003.png'), ('8_25', '000003.png'))
        self.assertEqual(split_frame_ref('8_25/000003.png'), ('8_25', '000003.png'))

    def test_singleton_paths_require_explicit_small_sample_setting(self):
        paths = {(1, 2): 1, (2, 1): 1}
        self.assertEqual(select_action_paths(paths, 2, 2), [])
        self.assertEqual(select_action_paths(paths, 2, 2, min_count=1),
                         [[[0, 1], [1, 2], [2, 3]], [[0, 2], [2, 1], [1, 3]]])

    def test_default_retains_repeated_frequent_paths(self):
        self.assertEqual(select_action_paths({(1, 2): 4, (2,): 1}, 5, 2),
                         [[[0, 1], [1, 2], [2, 3]]])

    def test_error_boundary_includes_half(self):
        self.assertTrue(is_error_score(0.5))
        self.assertFalse(is_error_score(0.4999))


if __name__ == '__main__':
    unittest.main()
