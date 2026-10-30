"""Small portable helpers; original graph pruning is preserved by default."""
from pathlib import Path


def prune_stale_prototypes(directory, expected_count):
    """Remove only obsolete numbered outputs when rebuilding a smaller graph."""
    if expected_count < 1:
        raise ValueError('Cannot rebuild prototypes from an empty summary')
    root = Path(directory).resolve()
    files = list(root.glob('*.npy'))
    if any(not p.stem.isdecimal() or not p.resolve().is_relative_to(root) for p in files):
        raise ValueError(f'Unexpected prototype file in {root}; refusing cleanup')
    expected = {f'{i}.npy' for i in range(1, expected_count + 1)}
    for path in files:
        if path.name not in expected:
            path.unlink()


def is_background_caption(text):
    return ' '.join(text.lower().split()).rstrip('.') == 'the person is waiting'


def is_error_score(value, threshold=0.5):
    return value >= threshold


def split_frame_ref(value):
    parts = value.replace('\\', '/').split('/')
    if len(parts) != 2:
        raise ValueError(f'Expected recording/frame reference, got {value!r}')
    return tuple(parts)


def select_action_paths(path_counts, valid_count, num_clusters, min_count=2):
    if min_count < 1:
        raise ValueError('Path count must be positive')
    if not path_counts:
        return []
    result = []
    for path, count in path_counts.items():
        if path and count > valid_count / len(path_counts) - 1 and count >= min_count:
            nodes = [0, *path, num_clusters + 1]
            result.append([[a, b] for a, b in zip(nodes, nodes[1:])])
    return result
