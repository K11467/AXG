"""Extract real 256D EgoVLP TimeSformer visual features from public frames.

Uses the authors' video_transformer.py and public EgoVLP_PT_BEST checkpoint.
This is a closer visual-backbone adaptation, not proof of the exact AXG author
checkpoint or original 10fps preprocessing. No error annotations are inputs.
"""
import argparse
import importlib.util
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import time


def frame_window(index, frame_count, window_size):
    if not 0 <= index < frame_count or window_size <= 0:
        raise ValueError('Expected an existing frame and positive window size')
    start = index - (window_size - 1) // 2
    return [max(0, min(frame_count - 1, start + i)) for i in range(window_size)]


def partition_weights(state):
    state = {k.removeprefix('module.'): v for k, v in state.items()}
    video = {k.removeprefix('video_model.'): v for k, v in state.items() if k.startswith('video_model.')}
    projection = {k.removeprefix('vid_proj.'): v for k, v in state.items() if k.startswith('vid_proj.')}
    if 'temporal_embed' not in video or not {'0.weight', '0.bias'} <= projection.keys():
        raise ValueError('Pretrained video encoder or learned 256D projection missing')
    return video, projection


class _CheckpointConfig:
    """Inert metadata container; never executes the archived training config."""
    pass


def load_visual_model(checkpoint, source):
    import torch
    spec = importlib.util.spec_from_file_location('egovlp_video_transformer', source / 'model/video_transformer.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # pickletools probe confirmed these are the only nonstandard metadata types.
    # The original ConfigParser is deliberately not imported or executed; Linux
    # PosixPath metadata maps to a pure path on Windows. Keep weights_only=True.
    with torch.serialization.safe_globals([(_CheckpointConfig, 'parse_config.ConfigParser'),
                                            argparse.Namespace, (PurePosixPath, 'pathlib.PosixPath')]):
        stored = torch.load(checkpoint, map_location='cpu', weights_only=True)
    video_state, projection_state = partition_weights(stored['state_dict'])
    num_frames = int(video_state['temporal_embed'].shape[1])
    video = module.SpaceTimeTransformer(num_frames=num_frames, num_classes=0,
                                        time_init='zeros', attention_style='frozen-in-time')
    video.load_state_dict(video_state, strict=True)
    projection = torch.nn.Sequential(torch.nn.Linear(768, 256))
    projection.load_state_dict(projection_state, strict=True)
    model = torch.nn.Sequential(video, projection).eval().cuda()
    del stored, video_state, projection_state
    return model, num_frames


def extract(recordings, checkpoint=Path('C:/Dev/axg-cache/egovlp.pth'),
            source=Path('C:/Dev/axg-cache/EgoVLP'), limit=None, batch_size=4):
    import numpy as np
    import torch
    from PIL import Image
    from torchvision import transforms
    if not checkpoint.exists():
        raise FileNotFoundError('Public EgoVLP checkpoint is still downloading')
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA required for visual feature extraction')
    torch.set_num_threads(8)
    model, window_size = load_visual_model(checkpoint, source)
    transform = transforms.Compose([transforms.ToTensor(), transforms.Resize(256),
                                    transforms.CenterCrop(256), transforms.Resize(224),
                                    transforms.Normalize((.485, .456, .406), (.229, .224, .225))])
    dest = Path('output/local7b/egovlp_features')
    dest.mkdir(parents=True, exist_ok=True)
    commit = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    with checkpoint.open('rb') as fp:
        checkpoint_sha256 = hashlib.file_digest(fp, 'sha256').hexdigest()
    for recording in recordings:
        started = time.perf_counter()
        directory = Path('data/public_cook4d/frames') / recording
        paths = sorted(directory.glob('*.png'), key=lambda p: int(p.stem))
        if [int(p.stem) for p in paths] != list(range(1, len(paths) + 1)):
            raise ValueError(f'{recording}: frame indices must be contiguous and 1-based')
        count = len(paths) if limit is None else min(limit, len(paths))
        suffix = '.npy' if limit is None else f'.smoke{count}.npy'
        target = dest / f'{recording}{suffix}'
        metadata_path = target.with_suffix('.json')
        if target.exists() and metadata_path.exists():
            cached = np.load(target)
            metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
            if (cached.shape == (count, 256) and np.isfinite(cached).all()
                    and metadata.get('checkpoint_sha256') == checkpoint_sha256
                    and metadata.get('source_commit') == commit):
                print(f'Existing complete visual features: {target}', flush=True)
                continue
        images = [transform(Image.open(p).convert('RGB')) for p in paths]
        output = []
        with torch.inference_mode():
            for start in range(0, count, batch_size):
                indices = range(start, min(start + batch_size, count))
                clips = torch.stack([torch.stack([images[i] for i in frame_window(t, len(paths), window_size)])
                                     for t in indices]).cuda()
                features = model(clips)
                if features.shape[1] != 256 or not features.isfinite().all():
                    raise ValueError('Invalid pretrained visual features')
                output.append(features.cpu().numpy())
                if start % 100 == 0:
                    print(f'{recording}: {start}/{count} visual windows', flush=True)
        array = np.concatenate(output).astype(np.float32)
        if np.any(np.linalg.norm(array, axis=1) <= 1e-10):
            raise ValueError('Zero visual feature vector')
        tmp = target.with_suffix('.tmp.npy')
        np.save(tmp, array)
        tmp.replace(target)
        meta = {'backbone': 'EgoVLP_PT_BEST TimeSformer + learned 768-to-256 projection',
                'source': 'https://github.com/showlab/EgoVLP', 'source_commit': commit,
                'checkpoint': str(checkpoint), 'official_public_file_id': '1-cP3Gcg0NGDcMZalgJ_615BQdbFIbcj7',
                'checkpoint_sha256': checkpoint_sha256,
                'weights_only': True, 'strict_video_and_projection_loading': True,
                'window_frames': window_size, 'source_fps': 1, 'sampling': 'centered neighboring 1fps frames, boundary clamping',
                'transform': 'official test transform: Resize256, CenterCrop256, Resize224, ImageNet normalization',
                'shape': list(array.shape), 'seconds': time.perf_counter() - started,
                'warning': 'Public Ego4D pretrained checkpoint; AXG exact visual checkpoint/window and 10fps preprocessing not confirmed'}
        target.with_suffix('.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
        print(f'VISUAL FEATURES SAVED {target} {array.shape} {meta["seconds"]:.1f}s', flush=True)
    del model
    torch.cuda.empty_cache()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--recordings', nargs='+', default=['8_25', '8_3', '8_50'])
    parser.add_argument('--limit', type=int)
    parser.add_argument('--batch-size', type=int, default=4)
    args = parser.parse_args()
    extract(args.recordings, limit=args.limit, batch_size=args.batch_size)
