"""Convert generated captions to the official scripts' file layout.

Adaptation: 1fps public frames and sparse captions; prefer real public EgoVLP
Ego4D-pretrained TimeSformer features. Caption projection is explicit fallback.
"""
import json
import argparse
from pathlib import Path
import re

import numpy as np
from sentence_transformers import SentenceTransformer
from result_summary import load_matching_results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--feature-backend', choices=['egovlp', 'caption'], default='egovlp',
                        help='Prefer real Ego4D-pretrained TimeSformer features; caption is an explicit fallback')
    args = parser.parse_args()
    source = Path('data/public_cook4d')
    work = Path('output/local7b')
    data = Path('data/CaptainCook4D/spicedhotchocolate')
    output = Path('output/CaptainCook4D/spicedhotchocolate')
    for p in [data / 'labels_10fps', data / 'action_object_state',
              data / 'vc_v_features_10fps', output / 'vc_v_features_10fps']:
        p.mkdir(parents=True, exist_ok=True)
    provenance = json.loads((work / 'data_provenance.json').read_text(encoding='utf-8'))
    annotation = json.loads((source / 'complete_step_annotations.json').read_text())
    requests = json.loads((work / 'caption_requests.json').read_text(encoding='utf-8'))
    results = load_matching_results(work / 'caption_results', requests)
    missing = [r['id'] for r in requests if r['id'] not in results]
    if missing:
        raise RuntimeError(f'{len(missing)} caption requests not yet completed')
    raw_names = [s['description'].split('-', 1)[-1].strip()
                 for s in annotation[provenance['train'][0]]['steps']]
    actions = {'BG': '0', **{name: str(i + 1) for i, name in enumerate(raw_names)}}
    cleaning = {name: re.sub(r'[<>:"/\\|?*]', ' ', name.replace('1/5', 'one fifth')).strip()
                for name in raw_names}
    Path('data/CaptainCook4D/action2idx.json').write_text(json.dumps({'spicedhotchocolate': actions}, indent=2))
    Path('data/clean_action_dict.json').write_text(json.dumps(cleaning, indent=2))
    (data / 'training.txt').write_text('\n'.join(provenance['train']) + '\n')
    (data / 'test.txt').write_text('\n'.join(provenance['test']) + '\n')
    if args.feature_backend == 'egovlp':
        from extract_egovlp_features import extract
        extract(provenance['train'] + provenance['test'])
        feature_backend = 'EgoVLP_PT_BEST: Ego4D-pretrained TimeSformer and learned 256D visual projection'
    else:
        sentence_model = SentenceTransformer('C:/Dev/axg-cache/all-MiniLM-L6-v2', device='cuda')
        projection = np.random.default_rng(0).standard_normal((384, 256)).astype(np.float32) / np.sqrt(256)
        np.save(work / 'caption_feature_projection.npy', projection)
        feature_backend = 'all-MiniLM-L6-v2 captions, fixed seed-0 384-to-256 projection, L2 normalized'
    stats = {}
    for vid in provenance['train'] + provenance['test']:
        steps = sorted((s for s in annotation[vid]['steps'] if s['start_time'] >= 0), key=lambda s: s['start_time'])
        num_frames = max(int(p.stem) for p in (source / 'frames' / vid).glob('*.png'))
        frame_labels, frame_step_ids, overlap_count = [], [], 0
        for t in range(num_frames):
            candidates = [s for s in steps if s['start_time'] <= t < s['end_time']]
            overlap_count += int(len(candidates) > 1)
            step = candidates[-1] if candidates else None
            name = step['description'].split('-', 1)[-1].strip() if step else 'BG'
            # Error flag is used only for later evaluation; no descriptions enter captions/features.
            tag = 'Error' if step and step['has_errors'] else 'Normal'
            frame_labels.append(f'{name}|{tag}|\n')
            frame_step_ids.append(step['step_id'] if step else None)
        (data / 'labels_10fps' / f'{vid}.txt').write_text(''.join(frame_labels))
        rows = [r for r in requests if r['recording_id'] == vid and
                r['timestamp'] < num_frames and frame_step_ids[r['timestamp']] == r['step_id']]
        captions = []
        directory = data / 'action_object_state' / vid
        directory.mkdir(parents=True, exist_ok=True)
        for req in rows:
            text = ' '.join(results[req['id']]['raw_response'].lower().split()).strip()
            if not text:
                raise ValueError(f'Empty caption {req["id"]}')
            if not text.endswith('.'):
                text += '.'
            (directory / f'{req["timestamp"]:06d}.txt').write_text(text, encoding='utf-8')
            captions.append(text.split('.')[0])
        if args.feature_backend == 'egovlp':
            features = np.load(work / 'egovlp_features' / f'{vid}.npy')
            if features.shape != (num_frames, 256) or not np.isfinite(features).all():
                raise ValueError(f'Invalid real visual feature array for {vid}')
        else:
            embedding = sentence_model.encode(captions, normalize_embeddings=True)
            embedding = (embedding @ projection).astype(np.float32)
            embedding /= np.maximum(np.linalg.norm(embedding, axis=1, keepdims=True), 1e-12)
            features = np.zeros((num_frames, 256), dtype=np.float32)
            for req, emb in zip(rows, embedding):
                features[req['timestamp']] = emb
        for directory in [data / 'vc_v_features_10fps', output / 'vc_v_features_10fps']:
            np.save(directory / f'{vid}_360p.npy', features)
        stats[vid] = {'frames': num_frames, 'captions': len(rows), 'overlapping_annotation_seconds': overlap_count}
    (work / 'official_layout_provenance.json').write_text(json.dumps({
        'warning': 'Directory suffixes retained for upstream compatibility; data is 1fps, not 10fps.',
        'feature_backend': feature_backend,
        'overlap_policy': 'most recently started annotated action at each integer second',
        'stats': stats, 'train': provenance['train'], 'test': provenance['test']}, indent=2))
    print(json.dumps(stats), flush=True)


if __name__ == '__main__':
    main()
