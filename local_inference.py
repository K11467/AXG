"""Windows Transformers backend for AXG-style requests; no vLLM dependency.

Every request saves its prompt, frames, raw response and runtime provenance.
The original vLLM entry point is left unchanged.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time

from local_inputs import build_prompt, parse_response


def cache_is_valid(value):
    return (value.get('status') == 'ok' and
            (value.get('kind') != 'reason' or value.get('parse_ok') is True))


def request_signature(request, model, max_pixels, max_new_tokens):
    payload = {'request': request, 'model': str(model), 'max_pixels': max_pixels,
               'max_new_tokens': max_new_tokens, 'backend': 'transformers-sdpa-bf16-greedy-rp1-v2'}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--model', default='C:/Dev/axg-cache/Qwen2.5-VL-7B-Instruct')
    parser.add_argument('--max-pixels', type=int, default=384 * 28 * 28)
    parser.add_argument('--max-new-tokens', type=int, default=256)
    parser.add_argument('--limit', type=int)
    parser.add_argument('--retry-invalid', action='store_true', help='Explicitly retry a recorded parsing failure')
    parser.add_argument('--strict-output', action='store_true', help='Add a formatting reminder, saved in the actual prompt')
    args = parser.parse_args()
    requests = json.loads(args.manifest.read_text(encoding='utf-8'))
    args.output.mkdir(parents=True, exist_ok=True)
    pending = []
    for req in requests[:args.limit]:
        if args.strict_output and req.get('kind', 'reason') == 'reason':
            req = dict(req, strict_output=True)
        signature = request_signature(req, args.model, args.max_pixels, args.max_new_tokens)
        dest = args.output / f"{req['id']}_{signature[:12]}.json"
        if dest.exists():
            cached = json.loads(dest.read_text(encoding='utf-8'))
            if cache_is_valid(cached):
                continue
            if cached.get('status') == 'parse_error' and not args.retry_invalid:
                raise RuntimeError(f'Recorded invalid output {dest}; inspect raw response, then use --strict-output or --retry-invalid')
        pending.append((req, signature, dest))
    if not pending:
        print('All matching requests already completed', flush=True)
        return
    import torch
    from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration
    from qwen_vl_utils import process_vision_info
    torch.manual_seed(0)
    torch.set_num_threads(8)
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA is unavailable; refusing silently to run 7B on CPU')
    info = {'torch': torch.__version__, 'cuda': torch.version.cuda,
            'gpu': torch.cuda.get_device_name(), 'transformers': importlib.metadata.version('transformers'),
            'model': args.model, 'dtype': 'bfloat16', 'attention': 'sdpa',
            'max_pixels': args.max_pixels, 'max_new_tokens': args.max_new_tokens}
    info.update({'do_sample': False, 'repetition_penalty': 1.0})
    print(json.dumps(info), flush=True)
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        args.model, torch_dtype=torch.bfloat16, device_map='cuda',
        attn_implementation='sdpa', local_files_only=True).eval()
    processor = AutoProcessor.from_pretrained(args.model, min_pixels=128 * 28 * 28,
                                             max_pixels=args.max_pixels, local_files_only=True)
    print(f'Model loaded; pending={len(pending)}; allocated={torch.cuda.memory_allocated()/2**30:.2f} GiB', flush=True)
    parsing_failures = []
    for index, (req, signature, dest) in enumerate(pending):
        start = time.perf_counter()
        kind = req.get('kind', 'reason')
        prompt = build_prompt(req['case']) if kind == 'reason' else req['prompt']
        if req.get('strict_output') and req.get('case', {}).get('subaction') != 'BG':
            prompt += '\nReturn exactly two lines: Score: <number between 0 and 1>\nReason: <your explanation>.'
        frames = req.get('frames', req.get('case', {}).get('frames', []))
        for frame in frames:
            if not Path(frame).is_file():
                raise FileNotFoundError(frame)
        content = []
        if kind == 'caption':
            content.extend({'type': 'image', 'image': str(Path(frame).resolve()), 'max_pixels': args.max_pixels}
                           for frame in frames)
        elif frames:
            content.append({'type': 'video', 'video': [str(Path(f).resolve()) for f in frames],
                            'fps': req.get('fps', 1.0), 'max_pixels': args.max_pixels})
        content.append({'type': 'text', 'text': prompt})
        messages = [{'role': 'user', 'content': content}]
        chat = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        images, videos, video_kwargs = process_vision_info(messages, return_video_kwargs=True)
        inputs = processor(text=[chat], images=images, videos=videos, padding=True,
                           return_tensors='pt', **video_kwargs).to('cuda')
        torch.cuda.reset_peak_memory_stats()
        with torch.inference_mode():
            generated = model.generate(**inputs, max_new_tokens=args.max_new_tokens,
                                       do_sample=False, repetition_penalty=1.0, use_cache=True)
        new_ids = generated[:, inputs.input_ids.shape[1]:]
        response = processor.batch_decode(new_ids, skip_special_tokens=True,
                                          clean_up_tokenization_spaces=False)[0]
        eos_tokens = model.generation_config.eos_token_id or []
        eos_tokens = [eos_tokens] if isinstance(eos_tokens, int) else eos_tokens
        hit_token_limit = (new_ids.shape[1] >= args.max_new_tokens and
                           int(new_ids[0, -1]) not in eos_tokens)
        result = {'status': 'ok', 'id': req['id'], 'kind': kind, 'signature': signature,
                  'prompt': prompt, 'frames': frames, 'request': req, 'raw_response': response,
                  'processor_video_kwargs': video_kwargs,
                  'video_grid_thw': inputs['video_grid_thw'].tolist() if 'video_grid_thw' in inputs else None,
                  'input_shapes': {key: list(value.shape) for key, value in inputs.items()},
                  'runtime': info, 'elapsed_seconds': time.perf_counter() - start,
                  'peak_allocated_gib': torch.cuda.max_memory_allocated() / 2**30,
                  'generated_tokens': int(new_ids.shape[1])}
        result['hit_token_limit'] = bool(hit_token_limit)
        if kind == 'reason':
            if req.get('case', {}).get('subaction') == 'BG':
                result.update({'correctness_score': 0.0, 'error_score': 1.0,
                               'is_error': True, 'reason': response.strip(), 'parse_ok': True,
                               'prediction_source': 'AXG graph drop, not a VLM correctness score'})
            else:
                result.update(parse_response(response))
                if not result['parse_ok']:
                    result['status'] = 'parse_error'
                    parsing_failures.append(req['id'])
        tmp = dest.with_suffix('.tmp')
        tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        tmp.replace(dest)
        print(f"[{index+1}/{len(pending)}] {req['id']} {result['elapsed_seconds']:.1f}s: {response[:180]}", flush=True)
        del generated, new_ids, inputs
        torch.cuda.empty_cache()
    if parsing_failures:
        raise RuntimeError(f'Unparsed requests {parsing_failures}; raw outputs saved, no correctness values invented. Use --strict-output for a new documented attempt.')


if __name__ == '__main__':
    main()
