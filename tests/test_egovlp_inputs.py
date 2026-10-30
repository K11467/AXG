import unittest
from extract_egovlp_features import frame_window, partition_weights


class EgoVLPInputsTests(unittest.TestCase):
    def test_temporal_window_clamps_to_real_recording_frames(self):
        self.assertEqual(frame_window(0, 3, 4), [0, 0, 1, 2])
        self.assertEqual(frame_window(2, 3, 4), [1, 2, 2, 2])
        with self.assertRaises(ValueError):
            frame_window(0, 0, 4)

    def test_pretrained_video_and_projection_are_required(self):
        video, proj = partition_weights({'module.video_model.temporal_embed': 'v',
                                         'module.vid_proj.0.weight': 'w',
                                         'module.vid_proj.0.bias': 'b',
                                         'module.text_model.a': 'ignored'})
        self.assertEqual(video, {'temporal_embed': 'v'})
        self.assertEqual(proj, {'0.weight': 'w', '0.bias': 'b'})
        with self.assertRaises(ValueError):
            partition_weights({'video_model.temporal_embed': 'v'})
