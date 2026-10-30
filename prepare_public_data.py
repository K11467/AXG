"""Prepare separate inference and evaluation inputs from public CaptainCook4D."""
import argparse
import json
from pathlib import Path
import zipfile

from local_inputs import sample_frames, make_case


def caption_prompt(action):
    return ("You are a system that given a image, outputs the action the person is doing and the detailed state for every object the person is working with. "
            f"The person is in the process of doing '{action}'. Do not use vague verbs such as prepare, manipulate, etc. "
            "If the person's hand is not visible, outputs 'the person is waiting.' Otherwise, select one of the output formats in the following to output the action: "
            "The person is [verb] [object1]. The state of [object1] is [state1].\n"
            "The person is [verb] [object1] [prep1] [object2]. The state of [object1] is [state1]. The state of [object2] is [state2].\n"
            "The person is [verb] [object1] and [object2]. The state of [object1] is [state1]. The state of [object2] is [state2].\n"
            "The person is [verb] [object1] [prep1] [object2] [prep2] [object3]. The state of [object1] is [state1]. The state of [object2] is [state2]. The state of [object3] is [state3].")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=Path, default=Path('data/public_cook4d'))
    parser.add_argument('--output', type=Path, default=Path('output/local7b'))
    parser.add_argument('--train', nargs='+', default=['8_25', '8_3'])
    parser.add_argument('--test', nargs='+', default=['8_50'])
    parser.add_argument('--caption-stride', type=int, default=1)
    args = parser.parse_args()
    if set(args.train) & set(args.test):
        raise ValueError('Train/test recording overlap')
    args.output.mkdir(parents=True, exist_ok=True)
    frames_root = args.data / 'frames'
    for vid in args.train + args.test:
        if not (frames_root / vid).exists():
            with zipfile.ZipFile(args.data / f'{vid}.zip') as archive:
                if archive.testzip() is not None:
                    raise ValueError(f'Corrupted archive: {vid}')
                # Only the expected flat recording folder is accepted.
                for entry in archive.namelist():
                    path = Path(entry)
                    if path.is_absolute() or '..' in path.parts or path.parts[0] != vid:
                        raise ValueError(f'Unsafe zip member {entry}')
                archive.extractall(frames_root)
    labels = json.loads((args.data / 'complete_step_annotations.json').read_text())
    errors = {x['recording_id']: x for x in json.loads((args.data / 'error_annotations.json').read_text())}
    baseline, evaluation, captions = [], {}, []
    for vid in args.train + args.test:
        if vid in args.train and any(s['has_errors'] for s in labels[vid]['steps']):
            raise ValueError(f'Training recording {vid} contains annotated errors')
        previous = []
        steps = sorted((s for s in labels[vid]['steps'] if s['start_time'] >= 0), key=lambda s: s['start_time'])
        for i, step in enumerate(steps):
            directory = frames_root / vid
            frames = sample_frames(directory, step['start_time'], step['end_time'])
            case = make_case(vid, step, frames, previous)
            if vid in args.test:
                baseline.append({'id': case['id'], 'kind': 'reason', 'case': case})
                evaluation[case['id']] = {'has_errors': step['has_errors'], 'step_id': step['step_id'],
                                         'annotation': next((s for s in errors[vid]['step_annotations']
                                                             if s['step_id'] == step['step_id']), None)}
            # Captions are obtained without error annotations, for train and test.
            dense = sample_frames(directory, step['start_time'], step['end_time'],
                                  count=max(1, int((step['end_time'] - step['start_time']) / args.caption_stride)))
            for frame in dense:
                captions.append({'id': f'{vid}_step{step["step_id"]}_frame{Path(frame).stem}',
                                 'kind': 'caption', 'prompt': caption_prompt(case['action']),
                                 'frames': [frame], 'recording_id': vid, 'action': case['action'],
                                 'step_id': step['step_id'], 'frame_index': int(Path(frame).stem),
                                 'timestamp': int(Path(frame).stem) - 1,
                                 'action_start': step['start_time'], 'action_end': step['end_time'],
                                 'split': 'train' if vid in args.train else 'test'})
            previous.append(case['action'])
    for name, value in [('baseline_requests.json', baseline), ('evaluation_labels.json', evaluation),
                        ('caption_requests.json', captions),
                        ('data_provenance.json', {'train': args.train, 'test': args.test,
                          'fps': 1, 'first_frame_index': 1, 'caption_stride_seconds': args.caption_stride,
                          'frames_export': 'kimihiroh/promqa-cooking-frames',
                          'annotations': 'CaptainCook4D/annotations',
                          'deviation': 'Public-data adaptation; original AXG preprocessing and splits unavailable'})]:
        (args.output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Prepared {len(baseline)} baseline segments and {len(captions)} caption requests')


if __name__ == '__main__':
    main()
