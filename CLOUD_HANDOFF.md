# H20 云端 Codex 接手说明

## 目标与当前状态

用户已选择论文原版 **Qwen2.5-VL-32B-Instruct + Qwen2.5-32B-Instruct**。
优先单张 H20，必要时使用第二张已可用 H20；两个模型分阶段运行。
模型使用固定的官方指令权重，训练阶段学习子动作图，不是微调大模型。

当前代码已在 Windows / RTX 5090 Laptop 24GB / 7B 上完成两轮真实实验，
25项测试通过。**Linux/H20/32B 尚未在本机验证**，云端接手者负责迁移和实测。
本仓库配置文件是交接规格，现有脚本不会自动读取它。

## 最快的执行顺序

1. 读取本文件、`AGENTS.md`、`configs/paper32b-h20.json`。先检查GPU/驱动、
   Python、PyTorch、磁盘、作者数据是否可用，并记录到新的云端运行目录。
2. 复用供应商已有CUDA/PyTorch或vLLM镜像与模型缓存。缺模型时在服务器直接
   下载固定revision；不要经GitHub搬运模型、Windows `.venv` 或数十GB缓存。
3. 保留原有已验证修复，参数化下述本机路径。先做一段32B真实图像推理和少量
   文本摘要的显存/耗时测试，再运行一个**完整任务的作者train/test划分**。
4. 优先完成Hot Chocolate的GT动作段流程并核对Table S10；数据/结果通过后扩展
   其余论文任务。预测TAS和错误解释评分还需要对应标注/模型/权重，单独记录。
5. 每阶段保存命令、模型版本、stdout/stderr、退出码、原始输出、峰值显存与指标。
   使用tmux或进程管理器保持运行、断点续跑，保留不同配置独立目录。

## 硬件和模型

- NVIDIA资料列常见H20为96GB；以服务器 `nvidia-smi` 的实际可用容量为准。
- 两套32B权重文件合计约134GB量级，数据和临时文件另算。磁盘先测量，不宣称
  固定容量能容纳全部作者数据。
- BF16优先、batch=1预检、两个大模型串行加载，避免同时驻留GPU。
- 官方VLM脚本已有单卡H100配置：context8192、memory utilization0.9。
  这可作为H20预检起点，不是已验证的H20性能保证。
- 如果单卡确实OOM，先检查残留进程和KV缓存设置。必要时同机双卡使用
  vLLM `tensor_parallel_size=2`；不能只增加第二张卡而保持TP=1。
- 原始HF Transformers单卡runner没有实现多卡分片；需要双卡时使用明确的
  vLLM TP或经过验证的模型分片，不要启动两份完整模型冒充张量并行。

固定模型来源与revision见JSON。不要将“32B权重约64GB”误当成64B参数模型。

## 依赖与环境

`requirements-local7b.txt` 是本机完整版本快照；`requirements-linux-core.txt`
列出跨平台核心API版本，**不强制覆盖云镜像已有torch/torchvision**。

建议Python3.12隔离环境。先验证CUDA PyTorch可用并执行一次BF16矩阵乘法；
没有CUDA PyTorch时，按当前驱动选择官方wheel。原本机验证版本为
torch2.11.0+cu128 / torchvision0.26.0+cu128，但云端必须自行实测并保存freeze。

```bash
python --version
nvidia-smi
python -m pip install -r requirements-linux-core.txt
python -m pip check
python -m unittest discover -s tests
```

论文VLM入口用vLLM。优先选择已支持Qwen2.5-VL的稳定镜像，记录镜像digest和
版本；vLLM会绑定torch等依赖，建议与图构建环境分开，避免破坏已工作的环境。
`local_inference.py --model /absolute/model/path` 可用于Transformers路径的
独立预检，但仅凭该预检不能宣称完成论文原版vLLM全流程。

下载示例（模型在服务器下载，CACHE指向实际有空间的持久盘）：

```bash
export AXG_CACHE_DIR=/workspace/axg-cache
hf download Qwen/Qwen2.5-VL-32B-Instruct --revision 7cfb30d71a1f4f49a57592323337a4a4727301da --local-dir "$AXG_CACHE_DIR/Qwen2.5-VL-32B-Instruct"
hf download Qwen/Qwen2.5-32B-Instruct --revision 5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd --local-dir "$AXG_CACHE_DIR/Qwen2.5-32B-Instruct"
```

可复用供应商/官方镜像缓存以节省下载；换来源时记录来源与文件校验，不静默换模型。

## 数据是完整复现的前提

官方README要求申请labels、splits、逐帧caption等文件。完整目录包括
`frames_10fps`、`vc_v_features_10fps`、`labels_10fps`、`action_object_state`、
`action2idx.json`、`clean_action_dict.json`、`training.txt`、`test.txt`。
已有作者预计算caption/特征时优先复用，并记录来源，不重复生成同一产物。

本机实际用过的只有公开1fps Hot Chocolate：训练8_25/8_3、测试8_50；
详细来源在 `PUBLIC_DATA_RESEARCH.md`。它只适合独立smoke profile。
**不能把1fps目录改名当成10fps，不能把三个视频称为完整任务划分。**
原始输入/模型/输出因体积原因不在Git源码包中，GitHub不会自动提供它们。

缺作者数据时：继续完成硬件、依赖、模型与公开样例预检，输出缺失文件清单；
完整论文指标需要补齐数据后才能开始计算。不要替用户发送申请邮件。

## 云端必须处理的现有路径与配置

- `.ps1` 是Windows历史运行入口，不作为Linux入口；用Bash/Python编排原版阶段。
- `download_models.py` / `download_text7b.py` 固定为旧7B下载，不用于32B模型。
- `local_inference.py` 支持 `--model`，默认仍是Windows7B缓存路径，必须覆盖。
- `extract_egovlp_features.py` 的checkpoint/source默认路径和
  `prepare_official_layout.py` 的SentenceBERT路径需配置到云端缓存；
  作者特征已提供时不需要该公开EgoVLP替代路线。
- `AXG_SENTENCE_MODEL` 已受聚类/原型/图脚本支持，可指向本地MiniLM目录。
  `AXG_CACHE_DIR` 当前仅为交接约定，尚未接入所有旧脚本。
- `vllm/run_axg-reasoner.py` 的 `MODEL_PATH`、`frame_dir`、TP配置需参数化。
  入口在 `vllm/` 目录运行，作者原始路径 `/data/shihpo` 必须改为实际数据根目录。
- `clust_config.json` 还有多个任务为10；论文主配置是K=5。逐任务核对/设置，
  不把本机仅Hot Chocolate已改为5的配置直接当作所有任务已对齐。
- 本机 `--min-path-count 1`、min-action-captions1/min-bg-captions2是稀疏
  两视频适配。作者全量数据运行应核对并恢复原版默认，记录每项选择。
- **不要在作者数据目录运行 `prepare_public_data.py` / `prepare_official_layout.py`**，
  后者会重写本机三视频实验的字典和划分。不要复用7B摘要/图作为32B主结果。
- 使用新工作目录/输出目录和新请求manifest，不能携带本机C盘绝对帧路径及PID文件。

## 原版阶段与成功标准

按顺序运行：generate_subactions_objects → summarize_subactions（独立文本32B）
→ generate_subaction_features → build_axg → axg2vid →
vllm/run_axg-reasoner（视觉32B、numf8）→ evaluate_error_detection →
错误解释评估。GT路径先验收，再推进有预测TAS的实验。

成功需要真实GPU输出、完整split、每动作非空图/原型、正确样本数、指标及图像，
不是仅安装成功或有PID文件。错误解释的LLM评价模型也使用独立文本32B。
保留原始评分和解释；不要按测试标签调阈值、改提示词或挑选子动作。

本机已验证修复：完整请求匹配缓存、解析失败不当正常、correctness<=0.5、
等待背景文本规范化、旧数字原型清理、两轮来源及3/8帧结果一致性、Matplotlib接口。
如果选择撤销某项以复刻上游bug，应单独对照并记录，不能混淆结果。

最终交付：环境freeze、GPU/模型版本、数据/划分来源、精确命令、全量结果、
失败样本、指标、与论文差异和中文结论。原本机报告仅作历史：`REPRO_REPORT.md`。
