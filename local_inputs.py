"""Model-independent inputs for the local public-data experiment.

Ground-truth error annotations stay outside model requests. Times use seconds.
"""
import math
import re
from pathlib import Path


def parse_response(text):
    match = re.search(r'\bScore\s*:\s*([0-9]+(?:\.[0-9]+)?|\.[0-9]+)\b', text, re.I)
    reason = re.search(r'\bReason\s*:\s*(.+)', text, re.I | re.S)
    score = float(match.group(1)) if match else None
    valid = score is not None and 0 <= score <= 1 and reason is not None
    return {'correctness_score': score if valid else None,
            'error_score': 1 - score if valid else None,
            'is_error': score <= 0.5 if valid else None,
            'reason': reason.group(1).strip() if reason else text.strip(),
            'parse_ok': valid}


def sample_frames(directory, start, end, count=3, fps=1, first_index=1):
    """Sample midpoints of available bins, respecting export's first-frame index."""
    if start < 0 or end <= start or count <= 0:
        return []
    files = []
    for p in Path(directory).iterdir():
        if p.suffix.lower() not in {'.png', '.jpg', '.jpeg'} or not p.stem.isdigit():
            continue
        t = (int(p.stem) - first_index) / fps
        if start <= t < end:
            files.append((t, p))
    files.sort()
    n = min(count, len(files))
    return [str(files[min(math.floor((i + .5) * len(files) / n), len(files) - 1)][1].resolve())
            for i in range(n)]


def make_case(recording_id, step, frames, previous_actions, subaction=None):
    start, end = step['start_time'], step['end_time']
    if start < 0 or end <= start or not frames:
        raise ValueError('Expected an observed segment with real frames and nonnegative timestamps')
    description = step['description'].strip()
    prefix, separator, remainder = description.partition('-')
    if separator and len(prefix.strip().split()) == 1 and remainder.strip().lower().startswith(prefix.strip().lower()):
        description = remainder.strip()
    return {'id': f'{recording_id}_{start:.3f}_{end:.3f}', 'recording_id': recording_id,
            'task': 'Spiced Hot Chocolate', 'action': description,
            'subaction': subaction, 'start_time': start, 'end_time': end,
            'frames': list(frames), 'previous_actions': list(previous_actions)}


def subaction_interval(frame_seconds, action_end, caption_stride, min_seconds=2):
    if not frame_seconds or caption_stride <= 0:
        raise ValueError('Expected real caption timestamps and a positive stride')
    start = min(frame_seconds)
    end = min(max(frame_seconds) + caption_stride, action_end)
    return (start, end) if end - start >= min_seconds else None


def build_prompt(case):
    text = "You are trying to do '%s'\nYou have finished the following steps:\n" % case['task']
    text += '\n'.join(case.get('previous_actions', [])) + '\n'
    if case.get('subaction') == 'BG':
        return text + ("Now you are trying to do an action '%s' and it seems like you are making a mistake.\n"
                       "Given a sequence of images for '%s', use one sentence to describe what mistake you are making."
                       % (case['action'], case['action']))
    if case.get('subaction'):
        text += "Now you are trying to do an subaction '%s' of an action '%s'.\n" % (case['subaction'], case['action'])
        target = case['subaction']
    else:
        text += "Now you are trying to do an action '%s'.\n" % case['action']
        target = case['action']
    return text + ("Given a sequence of images for '%s', output a score to show the correctness of the action and your reason. "
                   "The score ranges from 0 to 1. Higher score indicates the action shown by those images is more correct. "
                   "The output format: Score: x\nReason: y" % target)
