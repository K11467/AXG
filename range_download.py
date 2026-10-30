"""Bounded, resumable HTTP range download with final SHA256 verification."""
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.request


def chunk_ranges(size, chunk_size):
    return [(start, min(size - 1, start + chunk_size - 1)) for start in range(0, size, chunk_size)]


def validate_chunk(status, content_range, body, start, end, total):
    expected = f'bytes {start}-{end}/{total}'
    if status != 206 or content_range != expected or len(body) != end - start + 1:
        raise ValueError(f'Invalid range response: status={status}, range={content_range}, size={len(body)}, expected={expected}')


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fp:
        for b in iter(lambda: fp.read(8 * 1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def collect_chunks(items, fetch, store, workers):
    """Keep a bounded queue; preserve successes even when another task fails."""
    iterator = iter(items)
    failed = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        pending = {}
        def refill():
            while len(pending) < 2 * workers:
                item = next(iterator, None)
                if item is None:
                    break
                pending[pool.submit(fetch, item)] = item
        refill()
        while pending:
            done, _ = concurrent.futures.wait(pending, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                item = pending.pop(future)
                try:
                    result = future.result()
                except Exception as exc:
                    failed.append(item)
                    print(f'CHUNK_FAILED part {item[0]}: {type(exc).__name__}: {str(exc)[:160]}', flush=True)
                else:
                    store(result)
            refill()
    return failed


def download(url, destination, workers=6, chunk_size=1024 * 1024, sha256=None):
    dest = Path(destination)
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={'Range': 'bytes=0-0'})
    with urllib.request.urlopen(req, timeout=60) as resp:
        header = resp.headers.get('Content-Range', '')
        size = int(header.split('/')[-1])
        validate_chunk(resp.status, header, resp.read(), 0, 0, size)
    if dest.exists() and dest.stat().st_size == size and (not sha256 or digest(dest) == sha256):
        print(f'Already verified {dest.name}', flush=True)
        return
    partial = dest.with_name(dest.name + '.download')
    state_path = dest.with_name(dest.name + '.ranges.json')
    parts = chunk_ranges(size, chunk_size)
    completed = set()
    if state_path.exists() and partial.exists():
        state = json.loads(state_path.read_text())
        if state['size'] == size and state['chunk_size'] == chunk_size and partial.stat().st_size == size:
            completed = set(state['completed'])
    def fetch(item):
        i, (start, end) = item
        for attempt in range(5):
            try:
                req = urllib.request.Request(url, headers={'Range': f'bytes={start}-{end}'})
                with urllib.request.urlopen(req, timeout=90) as resp:
                    body = resp.read()
                    validate_chunk(resp.status, resp.headers.get('Content-Range'), body, start, end, size)
                return i, start, body
            except Exception as exc:
                if attempt == 4:
                    raise
                print(f'Retry {dest.name} part {i}: {type(exc).__name__}', flush=True)
                time.sleep(min(2 ** attempt, 8))
    print(f'Downloading {dest.name}: {size} bytes, {len(completed)}/{len(parts)} completed', flush=True)
    with open(partial, 'r+b' if partial.exists() else 'w+b') as fp:
        fp.truncate(size)
        remaining = [(i, p) for i, p in enumerate(parts) if i not in completed]
        def store(result):
            i, start, body = result
            fp.seek(start)
            fp.write(body)
            fp.flush()
            os.fsync(fp.fileno())
            completed.add(i)
            tmp_state = state_path.with_suffix('.tmp')
            tmp_state.write_text(json.dumps({'size': size, 'chunk_size': chunk_size, 'completed': sorted(completed)}))
            tmp_state.replace(state_path)
            if len(completed) % 20 == 0 or len(completed) == len(parts):
                print(f'{dest.name}: {len(completed)}/{len(parts)} chunks ({100 * len(completed)/len(parts):.1f}%)', flush=True)
        for sweep in range(3):
            remaining = collect_chunks(remaining, fetch, store, workers)
            if not remaining:
                break
            print(f'{dest.name}: retry sweep {sweep + 1}, {len(remaining)} failed chunks; other completed chunks saved', flush=True)
        if remaining:
            raise RuntimeError(f'{len(remaining)} chunks failed after bounded retry sweeps: {[x[0] for x in remaining[:20]]}; rerun to resume saved chunks')
    actual = digest(partial)
    if sha256 and actual != sha256:
        raise ValueError(f'SHA256 mismatch for {dest.name}: {actual}')
    partial.replace(dest)
    state_path.unlink(missing_ok=True)
    print(f'COMPLETE {dest.name} sha256={actual}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('destination')
    parser.add_argument('--workers', type=int, default=6)
    parser.add_argument('--sha256')
    args = parser.parse_args()
    download(args.url, args.destination, workers=args.workers, sha256=args.sha256)
