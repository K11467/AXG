"""Download the pinned official 7B model; independent of the inference environment."""
import json
from pathlib import Path
import urllib.request
from range_download import download

REPO = 'Qwen/Qwen2.5-VL-7B-Instruct'
REVISION = 'cc594898137f460bfe9f0759e9844b3ce807cfb5'
DEST = Path('C:/Dev/axg-cache/Qwen2.5-VL-7B-Instruct')

if __name__ == '__main__':
    DEST.mkdir(parents=True, exist_ok=True)
    entries = json.load(urllib.request.urlopen(f'https://huggingface.co/api/models/{REPO}/tree/{REVISION}', timeout=60))
    # Config/tokenizer files first, then weights, for early validation.
    entries.sort(key=lambda x: (x['path'].endswith('.safetensors'), x['path']))
    for entry in entries:
        name = entry['path']
        if entry['type'] != 'file' or not name.endswith(('.json', '.txt', '.safetensors')):
            continue
        url = f'https://huggingface.co/{REPO}/resolve/{REVISION}/{name}'
        dest = DEST / name
        if entry['size'] > 1024 * 1024:
            download(url, dest, workers=6, sha256=entry.get('lfs', {}).get('oid'))
        elif not dest.exists() or dest.stat().st_size != entry['size']:
            urllib.request.urlretrieve(url, dest)
            print(f'Saved {name}', flush=True)
    (DEST / 'download_provenance.json').write_text(json.dumps({'repo': REPO, 'revision': REVISION, 'files': entries}, indent=2))
    print('ALL MODEL FILES VERIFIED', flush=True)
