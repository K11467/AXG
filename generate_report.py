"""Build an evidence-based report from completed predictions, never placeholders."""
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from result_summary import binary_metrics, graph_action_rows, load_matching_results as load_results

ROOT = Path(__file__).resolve().parent
WORK = ROOT / 'output/local7b'


def link(path, title=None):
    path = Path(path).resolve()
    return f'[{title or path.name}](<{path.as_posix()}>)'


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    run_path = WORK / 'run_provenance.json'
    run = json.loads(run_path.read_text(encoding='utf-8-sig')) if run_path.exists() else {}
    separate_text = run.get('summary_model') == 'Qwen/Qwen2.5-7B-Instruct'
    summary_model = run.get('summary_model', 'Qwen/Qwen2.5-VL-7B-Instruct（纯文本模式）')
    status_log = ROOT / run.get('status_log', 'logs/graph-status.log')
    first_run = WORK / 'first_vl_text_run'
    first_report = WORK / 'first_vl_text_report.md'
    resource_path = ROOT / 'logs/resource-report.json'
    resources = json.loads(resource_path.read_text()) if resource_path.exists() else {}
    base_requests_path = WORK / 'baseline_requests.json'
    base_requests = json.loads(base_requests_path.read_text(encoding='utf-8')) if base_requests_path.exists() else []
    graph_requests_path = WORK / 'axg_requests.json'
    graph_requests = json.loads(graph_requests_path.read_text(encoding='utf-8')) if graph_requests_path.exists() else []
    baseline = load_results(WORK / 'baseline_results', base_requests)
    graph = load_results(WORK / 'axg_results', graph_requests)
    caption_requests_path = WORK / 'caption_requests.json'
    caption_requests = json.loads(caption_requests_path.read_text(encoding='utf-8')) if caption_requests_path.exists() else []
    captions = load_results(WORK / 'caption_results', caption_requests)
    truth_path = WORK / 'evaluation_labels.json'
    truth = json.loads(truth_path.read_text(encoding='utf-8')) if truth_path.exists() else {}
    feature_provenance_path = WORK / 'official_layout_provenance.json'
    feature_provenance = (json.loads(feature_provenance_path.read_text(encoding='utf-8'))
                          if feature_provenance_path.exists() else {})
    backend = feature_provenance.get('feature_backend', '')
    visual_metadata = {p.stem: json.loads(p.read_text(encoding='utf-8'))
                       for p in (WORK / 'egovlp_features').glob('*.json')
                       if '.smoke' not in p.name and p.with_suffix('.npy').exists()}
    if backend.startswith('EgoVLP') or (not backend and visual_metadata):
        feature_difference = ('使用公开 EgoVLP 的 Ego4D 预训练 TimeSformer 和学习到的256维视觉投影，实际输入视频帧。'
                              '仍未确认与 AXG 作者使用完全相同的权重和抽帧窗口，且数据为1fps。')
    elif backend:
        feature_difference = ('特征适配使用 SentenceBERT 帧描述编码和固定随机投影，不是原论文视觉特征。'
                              '投影不使用测试标签。')
    else:
        feature_difference = '特征阶段尚未完成；优先验证公开 EgoVLP 视觉特征路线，语义特征仅作为显式备选。'
    lines = ['# AXG-Reasoner 7B 本机实验记录', '',
             f'报告生成：{datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds")}', '',
             '**实验范围：公开数据适配的小样本实验，不是论文原版配置或完整测试集指标复现。**', '',
             '设备为 RTX 5090 Laptop 24GB。模型为官方 Qwen2.5-VL-7B-Instruct，BF16，Windows 原生 Transformers/SDPA 后端。', '',
             f'当前构图摘要模型：{summary_model}。模型来源与版本记录：' + (link(run_path) if run_path.exists() else '第一轮复用视觉模型的文本能力。'), '',
             '训练/构图数据：CaptainCook4D Spiced Hot Chocolate 正常视频 8_25、8_3；独立测试视频 8_50。',
             '原始官方标注和 ProMQA 导出的公开 360p/1fps 帧用于本实验。负时间戳的缺失步骤不作为可观察片段推理。', '',
             '## 实际运行状态', '',
             f'- 已保存基线片段结果：{len(baseline)}。',
             f'- 已保存帧描述：{len(captions)}/{len(caption_requests)}；布局转换实际保留 {sum(v["captions"] for v in feature_provenance.get("stats", {}).values())} 条（重叠时间只保留一个动作）。',
             f'- 已保存图对齐子动作结果：{len(graph)}。',
             f'- 已提取真实视觉特征：{sum(m["shape"][0] for m in visual_metadata.values())} 帧；记录为 {dict((k,m["shape"]) for k,m in visual_metadata.items())}。',
             '- 环境版本：' + link(ROOT / 'logs/environment-freeze.txt'),
             '- GPU 实测日志：' + link(ROOT / 'logs/gpu-check.log'),
             '- 串联执行日志：' + link(ROOT / 'logs/bootstrap-status.log') + '；' + link(status_log), '',
             '## GT 动作段基线结果', '']
    if resources:
        insert_at = lines.index('## GT 动作段基线结果')
        lines[insert_at:insert_at] = ['## 本机资源记录', '',
            f'系统：{resources["platform"]}；Python {resources["python"]}；可见物理内存 {resources["host_ram_bytes"] / 2**30:.2f} GiB。',
            f'GPU与驱动：{resources["gpu_query"]}。已完成实验的PyTorch最高峰值分配为 {max(resources["first_run_peak_pytorch_allocated_gib"], resources.get("current_run_peak_pytorch_allocated_gib", 0)):.2f} GiB；这不含桌面、驱动和其他进程占用。',
            '实测资源：' + link(resource_path) + '；原始输入文件的观察SHA256：' + link(ROOT / 'logs/input-sha256.json') + '（并非作者独立公布的校验值）。', '']
        if 'current_run_peak_pytorch_allocated_gib' in resources:
            at = lines.index('## GT 动作段基线结果')
            lines[at:at] = [
                f'工程目录逻辑文件大小 {resources["workspace_logical_bytes"] / 2**30:.2f} GiB，共享模型/轮子缓存 {resources["cache_logical_bytes"] / 2**30:.2f} GiB；未计其他系统缓存。',
                f'1109条帧描述实际推理合计 {resources["caption_inference"]["total_inference_seconds"] / 60:.1f} 分钟。论文训练和评估使用H100，见 ' + link(ROOT / 'data/papers/axg-reasoner.pdf', '论文PDF') + '。', '']
    labels = {k: v['has_errors'] for k, v in truth.items()}
    summary = binary_metrics(labels, {k: x['is_error'] for k, x in baseline.items() if x.get('parse_ok')})
    if summary['complete']:
        summary.update({'scope': 'Five observed GT action segments from one public test recording; not paper benchmark',
                        'error_threshold': 'correctness_score <= 0.5'})
        (WORK / 'baseline_small_sample_metrics.json').write_text(json.dumps(summary, indent=2))
        lines += [f'本视频 {summary["n"]} 个已观察动作段：TP={summary["tp"]}、FP={summary["fp"]}、FN={summary["fn"]}、TN={summary["tn"]}；错误类 F1={summary["error_f1"]:.3f}，正常类 F1={summary["normal_f1"]:.3f}，两类平均={summary["macro_f1"]:.3f}。',
                  '这是五个片段的诊断统计，不能与论文全任务平均成绩直接比较。', '']
        if len({v['correctness_score'] for v in baseline.values()}) == 1:
            lines += ['**基线对全部片段给出了相同评分，没有区分正常与错误；错误类 F1 需要结合正常类 F1 和误报数阅读。**', '']
    else:
        lines += ['基线尚未全部完成或存在输出解析失败，暂不报告汇总分数。', '']
    for value in sorted(baseline.values(), key=lambda x: x['request']['case']['start_time']):
        case = value['request']['case']
        gt = truth.get(value['id'], {})
        score = value.get('correctness_score')
        score_text = f'{score:.3f}' if score is not None else '解析失败'
        gt_text = '错误' if gt.get('has_errors') is True else '正常' if gt.get('has_errors') is False else '未知'
        predicted = '错误' if value.get('is_error') else '正常' if value.get('is_error') is False else '未知'
        annotation = gt.get('annotation') or {}
        gt_notes = '; '.join(f"{item.get('tag', '')}: {item.get('description', '')}"
                             for item in annotation.get('errors', []))
        lines += [f'### {case["start_time"]:.1f}–{case["end_time"]:.1f} 秒：{case["action"]}', '',
                  f'标注：{gt_text}；预测：{predicted}；正确性评分：{score_text}。', '',
                  ('标注说明（仅事后对照，未输入模型）：' + gt_notes) if gt_notes else
                  '该片段无已标注错误。' if gt.get('has_errors') is False else '未提供具体标注说明。', '',
                  value['raw_response'], '',
                  f'运行耗时 {value["elapsed_seconds"]:.1f} 秒，PyTorch 峰值分配显存 {value["peak_allocated_gib"]:.2f} GiB。',
                  link(value['_path'], '原始结果与完整提示'), '']
    if baseline:
        import matplotlib
        matplotlib.use('Agg')
        from matplotlib import pyplot as plt
        from PIL import Image
        ordered = sorted(baseline.values(), key=lambda x: x['request']['case']['start_time'])
        fig, axes = plt.subplots(len(ordered), 3, figsize=(15, 3.3 * len(ordered)), squeeze=False)
        for row, item in enumerate(ordered):
            for col, ax in enumerate(axes[row]):
                ax.axis('off')
                if col < len(item['frames']):
                    ax.imshow(Image.open(item['frames'][col]))
                    ax.set_title(f'{item["id"]} / frame {Path(item["frames"][col]).stem}', fontsize=9)
        fig.tight_layout()
        picture = WORK / 'baseline_frames.png'
        fig.savefig(picture, dpi=130)
        plt.close(fig)
        lines += ['## 推理实际采样帧', '', f'![实际采样帧]({picture.as_posix()})', '']
    lines += ['## 图对齐后的错误推理', '']
    graph_summary = {'complete': False}
    if graph_requests:
        rows = graph_action_rows(graph_requests, graph, base_requests)
        graph_summary = binary_metrics(labels, {k: row['is_error'] for k, row in rows.items()})
        if graph_summary['complete']:
            graph_summary['scope'] = 'One public test recording, observed GT action segments; not paper benchmark'
            (WORK / 'graph_small_sample_metrics.json').write_text(json.dumps(graph_summary, indent=2))
            lines += [f'按动作聚合子动作预测：错误类 F1={graph_summary["error_f1"]:.3f}，正常类 F1={graph_summary["normal_f1"]:.3f}，两类平均={graph_summary["macro_f1"]:.3f}。', '']
        else:
            lines += ['图推理尚有缺失或无保留子动作，暂不报告完整分数。', '']
        lines += ['| 动作时间（秒） | 真实标注 | 图推理 | 保留子动作数 |', '|---|---|---|---|']
        for req in base_requests:
            row, case = rows[req['id']], req['case']
            prediction = '错误' if row['is_error'] else '正常' if row['is_error'] is False else '未知/未完成'
            gt = '错误' if labels.get(req['id']) is True else '正常' if labels.get(req['id']) is False else '未知'
            lines.append(f'| {case["start_time"]:.1f}–{case["end_time"]:.1f} | {gt} | {prediction} | {len(row["request_ids"])} |')
        lines += ['', '子动作结果（完整提示、原始输出和采样帧见各JSON）：', '']
        for value in sorted(graph.values(), key=lambda x: x['request']['case']['start_time']):
            case = value['request']['case']
            origin = '图丢弃规则' if case.get('subaction') == 'BG' else '7B正确性评分'
            explanation = value['reason'].replace('\n', ' ')
            lines += [f'- {case["start_time"]:.1f}–{case["end_time"]:.1f} 秒，{case.get("subaction")}；错误分数 {value["error_score"]:.3f}（{origin}）。{explanation}',
                      '  ' + link(value['_path'], '完整子动作结果')]
        lines += ['', '图丢弃片段的错误分数由算法固定为1；这不表示VLM独立给出了100%错误置信度。', '']
        official_dir = ROOT / 'output/CaptainCook4D/spicedhotchocolate/error_reasoning_5_clust_gt_3f'
        timeline, timeline_input = official_dir / 'vis_ed/8_50.png', official_dir / '8_50.json'
        if timeline.exists() and timeline_input.exists() and timeline.stat().st_mtime >= timeline_input.stat().st_mtime:
            lines += ['### 当前3帧图结果的官方时间线', '',
                      '从上到下为GT动作分割、GT错误标签和图推理错误标签。数据为1fps，横轴索引近似秒；背景在官方脚本中按Normal显示。', '',
                      f'![官方时间线]({timeline.as_posix()})', '']
    else:
        lines += ['尚未产生图对齐推理请求；不把基线输出当作AXG图流程结果。', '']
    comparisons = {}
    base8_path, graph8_path = WORK / 'baseline_requests_8f.json', WORK / 'axg_requests_8f.json'
    if base8_path.exists() and graph8_path.exists():
        base8_requests = json.loads(base8_path.read_text(encoding='utf-8'))
        graph8_requests = json.loads(graph8_path.read_text(encoding='utf-8'))
        base8 = load_results(WORK / 'baseline_results_8f', base8_requests)
        graph8 = load_results(WORK / 'axg_results_8f', graph8_requests)
        base8_metrics = binary_metrics(labels, {k: v['is_error'] for k, v in base8.items() if v.get('parse_ok')})
        graph8_rows = graph_action_rows(graph8_requests, graph8, base_requests)
        graph8_metrics = binary_metrics(labels, {k: v['is_error'] for k, v in graph8_rows.items()})
        comparisons = {'3帧基线': summary, '3帧图推理': graph_summary,
                       '8帧基线': base8_metrics, '8帧图推理': graph8_metrics}
        if all(v['complete'] for v in comparisons.values()):
            (WORK / 'comparison_metrics.json').write_text(json.dumps(comparisons, indent=2), encoding='utf-8')
            lines += ['## 3帧与8帧对照', '',
                      '| 配置 | TP/FP/FN/TN | 错误 F1 | 正常 F1 | 两类平均 |', '|---|---|---|---|---|']
            for name, m in comparisons.items():
                lines.append(f'| {name} | {m["tp"]}/{m["fp"]}/{m["fn"]}/{m["tn"]} | {m["error_f1"]:.3f} | {m["normal_f1"]:.3f} | {m["macro_f1"]:.3f} |')
            direction = '提高了' if graph8_metrics['macro_f1'] > graph_summary['macro_f1'] else '未提高'
            lines += ['', '同一张学习得到的图和同5个测试动作，仅改变采样帧数。每段最多取8张实际可用的1fps帧，奇数帧由处理器补齐末帧；完整输入保存在逐请求JSON中。',
                      f'本样本中增加帧数{direction}图推理平均F1；样本只有一个视频，不能推出总体优劣。',
                      link(WORK / 'comparison_metrics.json', '对照指标') + '；' + link(WORK / 'comparison_3f_8f.json', '图、原型和运行审计'), '']
            missed = [r['case']['action'] for r in base_requests
                      if labels.get(r['id']) is True and graph8_rows[r['id']]['is_error'] is False]
            if missed:
                lines += ['8帧图推理漏检的动作：' + '；'.join(missed) + '。视觉上看见一个动作不等于识别其流程顺序。', '']
            for req in base_requests:
                row = graph8_rows[req['id']]
                if labels.get(req['id']) is False and row['is_error'] is True:
                    errors = [graph8[k] for k in row['request_ids'] if graph8[k]['is_error']]
                    if errors and all(v['request']['case'].get('subaction') == 'BG' for v in errors):
                        lines += ['8帧正常动作“' + req['case']['action'] + '”的错误判定全部来自BG丢弃规则；已匹配动作的评分正常，仍被any-error聚合为错误。', '']
            first_metrics_path = first_run / 'comparison_metrics.json'
            if separate_text and first_metrics_path.exists():
                first_metrics = json.loads(first_metrics_path.read_text(encoding='utf-8'))
                lines += ['### 摘要模型对照', '',
                          '| 摘要模型 | 3帧图平均F1 | 8帧图平均F1 |', '|---|---|---|',
                          f'| 第一轮：VL7B纯文本 | {first_metrics["3帧图推理"]["macro_f1"]:.3f} | {first_metrics["8帧图推理"]["macro_f1"]:.3f} |',
                          f'| 当前轮：独立文本7B | {graph_summary["macro_f1"]:.3f} | {graph8_metrics["macro_f1"]:.3f} |', '',
                          '两轮使用相同caption、视觉特征、数据和VLM；文本摘要改变后，子动作、图及对齐可能改变。', '']
    diagnostic_path = WORK / 'diagnostic_requests.json'
    if diagnostic_path.exists():
        diagnostic_requests = json.loads(diagnostic_path.read_text(encoding='utf-8'))
        diagnostic = load_results(WORK / 'diagnostic_results', diagnostic_requests)
        lines += ['## 输入与评分诊断', '', '两个正常片段来自训练视频，仅用于诊断，未加入上述测试指标；另有一张不提供动作标签的图片。', '']
        for req in diagnostic_requests:
            value = diagnostic.get(req['id'])
            if value:
                lines += [f'- {req["id"]}：' + value['raw_response'].replace('\n', ' '),
                          '  ' + link(value['_path'], '诊断原始输出')]
        lines += ['', '无动作提示的图片被识别为倒液体，正常加糖得到1.0、正常加奶得到0.5。输入链路能传递视觉信息，但评分校准和动作完整性判断不稳定。', '']
    if graph_summary['complete']:
        lines += ['## 效果判断与问题', '',
                  f'本机运行链路已跑通。当前3帧图推理TP={graph_summary["tp"]}/FP={graph_summary["fp"]}/FN={graph_summary["fn"]}/TN={graph_summary["tn"]}，正常类F1={graph_summary["normal_f1"]:.3f}。应同时阅读正常类指标与误报数，不能只看错误类F1。',
                  '五个已观察动作不足以核对论文整体效果。顺序错误的解释可能变成“未看见动作完成”，与标注错误类型不一致；当前只保存和检查解释，没有计算论文的错误解释评分。', '']
        summary_root = ROOT / 'output/CaptainCook4D/spicedhotchocolate/summarized_subactions_5_clust'
        learned = {p.parent.name: [v['summarized_subaction'] for v in json.loads(p.read_text()).values()]
                   for p in sorted(summary_root.glob('*/output.json'))}
        lines += ['初始K=5，经过摘要和过滤后实际保留的子动作如下：', '',
                  '| 动作 | 数量 | 摘要 |', '|---|---|---|']
        for action, names in learned.items():
            clean_names = '; '.join(names).replace('|', '/').replace('\n', ' ')
            lines.append(f'| {action} | {len(names)} | {clean_names} |')
        lines += ['', '摘要检查原始日志：' + link(ROOT / ('logs/text7b-summaries.log' if separate_text else 'logs/official-summaries.log')) + '。', '']
        if first_run.exists():
            lines += ['第一轮复用VL7B做文本摘要时，七类动作各只保留一个子动作，加热动作误保留“washing a mug”，按钮操作被错误排除。第一轮正常加热段又被图丢弃规则判错，8帧解释还编造了杯子封口要求。这些是第一轮观察，不能直接当作当前轮结论；生成解释本身不构成错误存在的证据。',
                      '第一轮完整报告与原始结果：' + link(first_report if first_report.exists() else first_run / 'REPRO_REPORT.md') + '；' + link(first_run / 'snapshot_sha256.json', '快照校验清单') + '。', '']
        second_report = WORK / 'separate_text7b_report.md'
        if second_report.exists():
            lines += ['独立文本7B轮的完整历史报告与原始产物：' + link(second_report) + '；' + link(WORK / 'separate_text7b_run/snapshot_sha256.json', '该轮快照校验清单') + '。', '']
        excluded_path = WORK / 'axg_excluded_short_segments.json'
        if excluded_path.exists():
            excluded = json.loads(excluded_path.read_text())
            lines += [f'按论文最短2秒规则排除了 {len(excluded)} 个子片段，清单：' + link(excluded_path) + '。公开1fps采样可能遗漏短暂错误。', '']
            if excluded:
                lines += ['被排除片段的帧时间（秒）：' + '; '.join(str(x['caption_timestamps_seconds']) for x in excluded) + '。', '']
    lines += ['## 图流程与论文差异', '',
              ('1. 32B视觉模型改为Qwen2.5-VL-7B，32B文本摘要模型改为独立Qwen2.5-7B-Instruct。官方文本模型来源：[Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct)。' if separate_text else '1. 当前将32B视觉/文本模型改为同一官方7B VL模型，文本摘要阶段以纯文本方式使用；独立文本7B是另一个可重放配置。'),
              '2. 作者专用 10fps 数据、Ego4D 视觉特征、帧描述、清洗字典和划分尚未取得；使用公开 1fps 帧，自行生成帧描述。',
              '3. ' + feature_difference,
              ('4. 已实际调用原版子动作/对象聚类、子动作摘要与检查、原型计算、图构建和 graph_utils.py 动态规划；各阶段日志保存在 logs/。' if graph_summary['complete'] else '4. 图流程尚未完成，不能把基线输出当作图流程复现。'),
              '5. 当前任务 K=5，依据论文正文。小样本允许路径频数为1；原代码默认频数阈值2保留。对齐片段阈值也为稀疏帧描述调整。',
              '6. 标注动作时间重叠时采用最近开始的动作，适配到原代码单标签时间线；与作者预处理可能不同。',
              '7. 图中被丢弃的片段按原方法直接视为错误，文字解释由7B生成；这不是模型独立给出的错误分数。',
              '8. 所有错误说明与 has_errors 只在评估侧使用；运行请求不包含这些真值。', '',
              '9. 主流程最多采样3帧，与仓库默认值及补充材料S1的消融配置一致；另跑最多8帧对照。正文主结果的 Qwen 实验使用8帧。',
              '10. 将官方评估脚本的错误分数边界从 >0.5 修正为 >=0.5，与论文 correctness<=0.5 和保存的预测保持一致。', '',
              '11. 正文定义每隔6帧生成描述（10fps时约0.6秒）。本轮对公开1fps帧逐帧生成描述，仍存在时间分辨率差异；推理前按秒排除短于2秒的子动作。', '',
              '12. 修复构图脚本的等待背景过滤：原代码先去掉句号，再与带句号字符串比较，导致过滤失效。此处按规范化后的文本判断；对齐动态规划继续调用原版实现。', '',
              '13. 官方可视化的旧Matplotlib get_cmap接口替换为等价的colormaps.resampled；仅影响绘图兼容性，不改变评分。', '',
              '14. 重放任一图流水线时更新摘要模型来源并重建两种帧数的结果；原型重建仅清理超过当前摘要数量的旧数字命名npy，避免两轮产物混用。', '',
              '## 可重复运行', '',
              '以下命令重放本机已有数据和模型缓存；PowerShell工作目录为 C:\\Dev\\AXG-Reasoner：', '',
              '```powershell', r'.\overnight_bootstrap.ps1',
              (r'.\text7b_pipeline.ps1' if separate_text else r'.\graph_pipeline.ps1'),
              r'.\.venv\Scripts\python.exe evaluate_error_detection.py --dataset CaptainCook4D --task spicedhotchocolate --tas_backbone gt --vis',
              r'.\.venv\Scripts\python.exe generate_report.py', '```', '',
              '独立文本7B对照由 download_text7b.py 下载固定版本，text7b_pipeline.ps1 等待完整校验后运行；第一轮复用VL文本能力的流程保留在 graph_pipeline.ps1。两种图流水线应串行运行。', '',
              '重放已保存的8帧对照输入：', '', '```powershell',
              r'.\.venv\Scripts\python.exe local_inference.py --manifest output/local7b/baseline_requests_8f.json --output output/local7b/baseline_results_8f',
              r'.\.venv\Scripts\python.exe local_inference.py --manifest output/local7b/axg_requests_8f.json --output output/local7b/axg_results_8f', '```', '',
              '完整后台安装与基线/帧描述流程见 overnight_bootstrap.ps1。重复运行会复用匹配的逐请求结果。图流程应在帧描述完成后执行。', '',
              '依赖已固定在 ' + link(ROOT / 'requirements-local7b.txt') + '；在 Python 3.12 的新虚拟环境中可用以下命令安装。模型、公开帧和视觉检查点仍需按 PUBLIC_DATA_RESEARCH.md 取得并放到本次使用的路径。', '',
              '```powershell', r'.\.venv\Scripts\python.exe -m pip install -r requirements-local7b.txt', '```', '',
              '## 下一步与限制', '',
              '需要作者专用数据才能核对论文原版预处理和完整指标；未发送申请邮件。当前样本数很小，可能漏掉细微洒落、顺序错误或缺失步骤。请以保存的实际输出为准。', '']
    if comparisons and all(v['complete'] for v in comparisons.values()):
        two_rounds = separate_text and (first_run / 'comparison_metrics.json').exists()
        completed_scope = '两轮公开数据图流程均已跑通。' if two_rounds else '当前公开数据图流程已跑通。'
        quick = ['## 结果速览', '',
                 completed_scope + f'当前3帧图平均F1={graph_summary["macro_f1"]:.3f}，8帧={graph8_metrics["macro_f1"]:.3f}；正常类F1分别为{graph_summary["normal_f1"]:.3f}/{graph8_metrics["normal_f1"]:.3f}。仅5个已观察测试动作，不是论文完整测试集成绩。', '']
        if two_rounds:
            same_metrics = all(comparisons[name][k] == first_metrics[name][k]
                               for name in ['3帧图推理', '8帧图推理'] for k in ['tp', 'fp', 'fn', 'tn'])
            result_note = '本样本检测指标没有改变。' if same_metrics else '检测指标的变化见摘要模型对照表。'
            first_count = sum(len(json.loads(p.read_text())) for p in (first_run / 'official/summarized_subactions_5_clust').glob('*/output.json'))
            quick += [f'独立文本7B摘要最终保留 {sum(map(len, learned.values()))} 个子动作；第一轮为{first_count}个。' + result_note + '两轮聚类一致性记录：' + link(ROOT / 'logs/cluster-control-audit.json') + '。', '']
        at = lines.index('## 实际运行状态')
        lines[at:at] = quick
    report = ROOT / 'REPRO_REPORT.md'
    report.write_text('\n'.join(lines), encoding='utf-8')
    print(report)


if __name__ == '__main__':
    main()
