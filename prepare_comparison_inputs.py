"""Recreate the up-to-eight-frame comparison manifests from current graph inputs."""
import copy
import json
from pathlib import Path
from local_inputs import sample_frames

if __name__ == '__main__':
    work = Path('output/local7b')
    for stem in ['baseline_requests', 'axg_requests']:
        requests = copy.deepcopy(json.loads((work / f'{stem}.json').read_text(encoding='utf-8')))
        for request in requests:
            case = request['case']
            case['frames'] = sample_frames(Path('data/public_cook4d/frames') / case['recording_id'],
                                           case['start_time'], case['end_time'], count=8)
            if not case['frames'] or not all(Path(f).is_file() for f in case['frames']):
                raise ValueError(f'Missing real comparison frames: {request["id"]}')
        (work / f'{stem}_8f.json').write_text(json.dumps(requests, indent=2), encoding='utf-8')
        print(f'{stem}: {len(requests)} requests; frames={[len(r["case"]["frames"]) for r in requests]}')
