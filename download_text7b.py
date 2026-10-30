"""Pinned official text-only 7B checkpoint for the second overnight comparison."""
import json
from pathlib import Path
import urllib.request
from range_download import download

REPO = 'Qwen/Qwen2.5-7B-Instruct'
REVISION = 'a09a35458c702b33eeacc393d103063234e8bc28'
DEST = Path('C:/Dev/axg-cache/Qwen2.5-7B-Instruct')

if __name__ == '__main__':
    DEST.mkdir(parents=True, exist_ok=True)
    entries = json.load(urllib.request.urlopen(f'https://huggingface.co/api/models/{REPO}/tree/{REVISION}', timeout=60))
    entries.sort(key=lambda x: (x['path'].endswith('.safetensors'), x['path']))
    for entry in entries:
        name = entry['path']
        if entry['type'] != 'file' or not name.endswith(('.json', '.txt', '.safetensors', '.jinja')):
            continue
        url = f'https://huggingface.co/{REPO}/resolve/{REVISION}/{name}'
        dest = DEST / name
        expected_hash = entry.get('lfs', {}).get('oid')
        if name.endswith('.safetensors') and not expected_hash:
            raise ValueError(f'Missing published weight hash: {name}')
        if entry['size'] > 1024 * 1024:
            download(url, dest, workers=6, sha256=expected_hash)
        elif not dest.exists() or dest.stat().st_size != entry['size']:
            urllib.request.urlretrieve(url, dest)
            if dest.stat().st_size != entry['size']:
                raise ValueError(f'Incorrect size: {name}')
            print(f'Saved {name}', flush=True)
    marker = DEST / 'download_provenance.json'
    tmp = marker.with_suffix('.tmp')
    tmp.write_text(json.dumps({'repo': REPO, 'revision': REVISION, 'files': entries}, indent=2))
    tmp.replace(marker)
    print('ALL TEXT 7B FILES VERIFIED', flush=True)
