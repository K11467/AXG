# AXG-Reasoner 7B 本机实验记录

报告生成：2026-10-30T07:08:08+08:00

**实验范围：公开数据适配的小样本实验，不是论文原版配置或完整测试集指标复现。**

设备为 RTX 5090 Laptop 24GB。模型为官方 Qwen2.5-VL-7B-Instruct，BF16，Windows 原生 Transformers/SDPA 后端。

当前构图摘要模型：Qwen/Qwen2.5-7B-Instruct。模型来源与版本记录：[run_provenance.json](<C:/Dev/AXG-Reasoner/output/local7b/run_provenance.json>)

训练/构图数据：CaptainCook4D Spiced Hot Chocolate 正常视频 8_25、8_3；独立测试视频 8_50。
原始官方标注和 ProMQA 导出的公开 360p/1fps 帧用于本实验。负时间戳的缺失步骤不作为可观察片段推理。

## 结果速览

两轮公开数据图流程均已跑通。当前3帧图平均F1=0.444，8帧=0.375；正常类F1分别为0.000/0.000。仅5个已观察测试动作，不是论文完整测试集成绩。

独立文本7B摘要最终保留 12 个子动作；第一轮为7个。本样本检测指标没有改变。两轮聚类一致性记录：[cluster-control-audit.json](<C:/Dev/AXG-Reasoner/logs/cluster-control-audit.json>)。

## 实际运行状态

- 已保存基线片段结果：5。
- 已保存帧描述：1109/1109；布局转换实际保留 1054 条（重叠时间只保留一个动作）。
- 已保存图对齐子动作结果：10。
- 已提取真实视觉特征：1128 帧；记录为 {'8_25': [443, 256], '8_3': [422, 256], '8_50': [263, 256]}。
- 环境版本：[environment-freeze.txt](<C:/Dev/AXG-Reasoner/logs/environment-freeze.txt>)
- GPU 实测日志：[gpu-check.log](<C:/Dev/AXG-Reasoner/logs/gpu-check.log>)
- 串联执行日志：[bootstrap-status.log](<C:/Dev/AXG-Reasoner/logs/bootstrap-status.log>)；[text7b-status.log](<C:/Dev/AXG-Reasoner/logs/text7b-status.log>)

## 本机资源记录

系统：Windows-11-10.0.26200-SP0；Python 3.12.14；可见物理内存 63.38 GiB。
GPU与驱动：NVIDIA GeForce RTX 5090 Laptop GPU, 24463 MiB, 616.92。已完成实验的PyTorch最高峰值分配为 16.02 GiB；这不含桌面、驱动和其他进程占用。
实测资源：[resource-report.json](<C:/Dev/AXG-Reasoner/logs/resource-report.json>)；原始输入文件的观察SHA256：[input-sha256.json](<C:/Dev/AXG-Reasoner/logs/input-sha256.json>)（并非作者独立公布的校验值）。

工程目录逻辑文件大小 5.39 GiB，共享模型/轮子缓存 34.54 GiB；未计其他系统缓存。
1109条帧描述实际推理合计 37.4 分钟。论文训练和评估使用H100，见 [论文PDF](<C:/Dev/AXG-Reasoner/data/papers/axg-reasoner.pdf>)。

## GT 动作段基线结果

本视频 5 个已观察动作段：TP=4、FP=1、FN=0、TN=0；错误类 F1=0.889，正常类 F1=0.000，两类平均=0.444。
这是五个片段的诊断统计，不能与论文全任务平均成绩直接比较。

**基线对全部片段给出了相同评分，没有区分正常与错误；错误类 F1 需要结合正常类 F1 和误报数阅读。**

### 0.7–69.3 秒：Add 1 teaspoon of white sugar to the mug

标注：错误；预测：错误；正确性评分：0.500。

标注说明（仅事后对照，未输入模型）：Order Error: Step performed before adding milk and microwaving it

Score: 0.5
Reason: The image shows a hand holding a bag of sugar, but there is no mug or sugar being added to a mug visible. The action of adding sugar to a mug is not depicted in the image.

运行耗时 20.9 秒，PyTorch 峰值分配显存 15.66 GiB。
[原始结果与完整提示](<C:/Dev/AXG-Reasoner/output/local7b/baseline_results/8_50_0.663_69.335_9b688468a5e1.json>)

### 69.3–92.3 秒：Fill a microwave-safe mug with skimmed milk

标注：错误；预测：错误；正确性评分：0.500。

标注说明（仅事后对照，未输入模型）：Order Error: Step performed after adding sugar

Score: 0.5
Reason: The image shows a hand reaching into a refrigerator, which suggests the action of retrieving an ingredient, but it does not depict the step of filling a microwave-safe mug with skimmed milk. The action in the image is not directly related to the current step in the recipe.

运行耗时 5.5 秒，PyTorch 峰值分配显存 15.66 GiB。
[原始结果与完整提示](<C:/Dev/AXG-Reasoner/output/local7b/baseline_results/8_50_69.335_92.281_4f7876c1032c.json>)

### 96.1–159.8 秒：Microwave the contents of the mug for 1 minute

标注：错误；预测：错误；正确性评分：0.500。

标注说明（仅事后对照，未输入模型）：Order Error: Step performed after adding sugar

Score: 0.5
Reason: The image shows a microwave, but there is no mug with the contents of the spiced hot chocolate inside it. The action of microwaving the contents of the mug for 1 minute cannot be performed as there is no mug with the required contents.

运行耗时 5.3 秒，PyTorch 峰值分配显存 15.67 GiB。
[原始结果与完整提示](<C:/Dev/AXG-Reasoner/output/local7b/baseline_results/8_50_96.078_159.797_45e00ff7e9ef.json>)

### 163.3–185.9 秒：Add 2 pieces of chocolate to the mug

标注：错误；预测：错误；正确性评分：0.500。

标注说明（仅事后对照，未输入模型）：Technique Error: Spill while adding chocolate

Score: 0.5

Reason: The image shows a hand reaching towards a cabinet, but there is no visible mug or chocolate pieces in the image. The action of adding chocolate to the mug cannot be confirmed as the mug is not in the frame, and there is no indication of chocolate pieces being added. Therefore, the score is 0.5, indicating that the action is partially correct but cannot be fully verified from the given image.

运行耗时 7.8 秒，PyTorch 峰值分配显存 15.67 GiB。
[原始结果与完整提示](<C:/Dev/AXG-Reasoner/output/local7b/baseline_results/8_50_163.264_185.879_bc0ed36fd214.json>)

### 186.4–251.7 秒：Heat the contents of the mug for 1 minute and serve

标注：正常；预测：错误；正确性评分：0.500。

该片段无已标注错误。

Score: 0.5

Reason: The image shows a microwave, which is the correct appliance to heat the contents of the mug. However, the image does not show the mug being placed inside the microwave, nor does it show the mug being removed after heating. Therefore, the action of heating the contents of the mug for 1 minute and serving cannot be fully confirmed as completed based on the provided image.

运行耗时 7.3 秒，PyTorch 峰值分配显存 15.68 GiB。
[原始结果与完整提示](<C:/Dev/AXG-Reasoner/output/local7b/baseline_results/8_50_186.375_251.745_33e9f121eb3b.json>)

## 推理实际采样帧

![实际采样帧](C:/Dev/AXG-Reasoner/output/local7b/baseline_frames.png)

## 图对齐后的错误推理

按动作聚合子动作预测：错误类 F1=0.889，正常类 F1=0.000，两类平均=0.444。

| 动作时间（秒） | 真实标注 | 图推理 | 保留子动作数 |
|---|---|---|---|
| 0.7–69.3 | 错误 | 错误 | 2 |
| 69.3–92.3 | 错误 | 错误 | 1 |
| 96.1–159.8 | 错误 | 错误 | 3 |
| 163.3–185.9 | 错误 | 错误 | 1 |
| 186.4–251.7 | 正常 | 错误 | 3 |

子动作结果（完整提示、原始输出和采样帧见各JSON）：

- 1.0–17.0 秒，BG；错误分数 1.000（图丢弃规则）。The mistake being made is that the action of adding 1 teaspoon of white sugar to the mug is not being performed, as the image shows a cabinet with various food items, not a mug or sugar being added.
  [完整子动作结果](<C:/Dev/AXG-Reasoner/output/local7b/axg_results/8_50_a0_s0_d485bf819efe.json>)
- 17.0–70.0 秒，The person is holding a spoon and a container of white sugar.；错误分数 0.500（7B正确性评分）。The image shows a hand holding a spoon and a container of white sugar, which is consistent with the action of adding sugar to a mug. However, the image does not show the sugar being added to the mug, which is a crucial part of the action. Therefore, the score is 0.5, indicating that the action is partially correct but not fully completed.
  [完整子动作结果](<C:/Dev/AXG-Reasoner/output/local7b/axg_results/8_50_a0_s1_9e60f766555f.json>)
- 70.0–93.0 秒，The person is pouring milk from a carton into a microwave-safe mug.；错误分数 0.500（7B正确性评分）。The image shows a hand reaching into a refrigerator, which suggests the person is retrieving an ingredient, likely milk, for the spiced hot chocolate. However, the image does not show the milk being poured into a microwave-safe mug, which is the next step in the process. Therefore, the score is 0.5, indicating that the action is partially correct but not fully completed.
  [完整子动作结果](<C:/Dev/AXG-Reasoner/output/local7b/axg_results/8_50_a1_s0_34a2de29270f.json>)
- 97.0–104.0 秒，The person is placing the mug into the microwave.；错误分数 0.500（7B正确性评分）。The image shows a kitchen counter with a laptop, a sink, and a microwave, but there is no mug or microwave activity visible. Therefore, it is not possible to determine if the mug is being placed into the microwave based on the provided image.
  [完整子动作结果](<C:/Dev/AXG-Reasoner/output/local7b/axg_results/8_50_a2_s0_43b004520de6.json>)
- 104.0–153.0 秒，BG；错误分数 1.000（图丢弃规则）。The mistake being made is that the microwave-safe mug is not yet filled with the correct amount of skimmed milk before being microwaved.
  [完整子动作结果](<C:/Dev/AXG-Reasoner/output/local7b/axg_results/8_50_a2_s1_017fde366d07.json>)
- 153.0–160.0 秒，The person is pressing the buttons on the microwave.；错误分数 0.200（7B正确性评分）。The image shows a microwave with a digital display and buttons, which is the correct appliance for microwaving. The person's hand is positioned near the microwave, suggesting they are about to press the buttons. However, the image does not show the actual pressing of the buttons, which is the specific action being described. The score of 0.8 indicates that the action is partially correct, as the person is in the process of using the microwave, but the pressing of the buttons is not yet visible.
  [完整子动作结果](<C:/Dev/AXG-Reasoner/output/local7b/axg_results/8_50_a2_s2_43c9e9bfdba6.json>)
- 164.0–185.0 秒，BG；错误分数 1.000（图丢弃规则）。You are mistakenly adding chocolate pieces to the counter instead of the mug, which is a step in the process of making spiced hot chocolate.
  [完整子动作结果](<C:/Dev/AXG-Reasoner/output/local7b/axg_results/8_50_a3_s0_c47bb3796141.json>)
- 187.0–197.0 秒，The person is placing the mug into the microwave.；错误分数 0.500（7B正确性评分）。The image shows the person holding the mug and the microwave door open, but the mug is not yet inside the microwave. The action of placing the mug into the microwave has not been completed.
  [完整子动作结果](<C:/Dev/AXG-Reasoner/output/local7b/axg_results/8_50_a4_s0_0e636a5c9b6c.json>)
- 198.0–249.0 秒，BG；错误分数 1.000（图丢弃规则）。You are making a mistake by trying to heat the contents of the mug in the microwave while the mug is still on the counter, which is not the correct sequence for preparing the spiced hot chocolate.
  [完整子动作结果](<C:/Dev/AXG-Reasoner/output/local7b/axg_results/8_50_a4_s1_344854d532ed.json>)
- 249.0–252.0 秒，The person is pressing the buttons on the microwave.；错误分数 0.000（7B正确性评分）。The image shows a person's hand pressing buttons on a microwave, which is the correct action to heat the contents of the mug for 1 minute. The presence of the microwave and the hand interacting with it directly supports the action described.
  [完整子动作结果](<C:/Dev/AXG-Reasoner/output/local7b/axg_results/8_50_a4_s2_6d5e3d55ccd7.json>)

图丢弃片段的错误分数由算法固定为1；这不表示VLM独立给出了100%错误置信度。

### 当前3帧图结果的官方时间线

从上到下为GT动作分割、GT错误标签和图推理错误标签。数据为1fps，横轴索引近似秒；背景在官方脚本中按Normal显示。

![官方时间线](C:/Dev/AXG-Reasoner/output/CaptainCook4D/spicedhotchocolate/error_reasoning_5_clust_gt_3f/vis_ed/8_50.png)

## 3帧与8帧对照

| 配置 | TP/FP/FN/TN | 错误 F1 | 正常 F1 | 两类平均 |
|---|---|---|---|---|
| 3帧基线 | 4/1/0/0 | 0.889 | 0.000 | 0.444 |
| 3帧图推理 | 4/1/0/0 | 0.889 | 0.000 | 0.444 |
| 8帧基线 | 4/1/0/0 | 0.889 | 0.000 | 0.444 |
| 8帧图推理 | 3/1/1/0 | 0.750 | 0.000 | 0.375 |

同一张学习得到的图和同5个测试动作，仅改变采样帧数。每段最多取8张实际可用的1fps帧，奇数帧由处理器补齐末帧；完整输入保存在逐请求JSON中。
本样本中增加帧数未提高图推理平均F1；样本只有一个视频，不能推出总体优劣。
[对照指标](<C:/Dev/AXG-Reasoner/output/local7b/comparison_metrics.json>)；[图、原型和运行审计](<C:/Dev/AXG-Reasoner/output/local7b/comparison_3f_8f.json>)

8帧图推理漏检的动作：Fill a microwave-safe mug with skimmed milk。视觉上看见一个动作不等于识别其流程顺序。

8帧正常动作“Heat the contents of the mug for 1 minute and serve”的错误判定全部来自BG丢弃规则；已匹配动作的评分正常，仍被any-error聚合为错误。

### 摘要模型对照

| 摘要模型 | 3帧图平均F1 | 8帧图平均F1 |
|---|---|---|
| 第一轮：VL7B纯文本 | 0.444 | 0.375 |
| 当前轮：独立文本7B | 0.444 | 0.375 |

两轮使用相同caption、视觉特征、数据和VLM；文本摘要改变后，子动作、图及对齐可能改变。

## 输入与评分诊断

两个正常片段来自训练视频，仅用于诊断，未加入上述测试指标；另有一张不提供动作标签的图片。

- normal_control_8_25_6.090_72.181：Score: 0.5 Reason: The image shows a person pouring milk into a mug, which is a step in the process of making spiced hot chocolate. However, the image does not clearly show the mug being placed in a microwave-safe container, which is a necessary step before heating the milk. The score is low because the image does not fully capture the action of filling the mug with milk and placing it in a microwave-safe container.
  [诊断原始输出](<C:/Dev/AXG-Reasoner/output/local7b/diagnostic_results/normal_control_8_25_6.090_72.181_e31bd0e10a57.json>)
- normal_control_8_3_229.507_284.502：Score: 1 Reason: The image shows the person holding a bag of Imperial Sugar, which is a brand of white sugar. This aligns with the step of adding 1 teaspoon of white sugar to the mug. The action is correctly represented in the image.
  [诊断原始输出](<C:/Dev/AXG-Reasoner/output/local7b/diagnostic_results/normal_control_8_3_229.507_284.502_55775c4b372b.json>)
- unconditioned_milk_frame82：A person is pouring a liquid from a bottle into a metal cup on a kitchen counter.
  [诊断原始输出](<C:/Dev/AXG-Reasoner/output/local7b/diagnostic_results/unconditioned_milk_frame82_4036a332d442.json>)

无动作提示的图片被识别为倒液体，正常加糖得到1.0、正常加奶得到0.5。输入链路能传递视觉信息，但评分校准和动作完整性判断不稳定。

## 效果判断与问题

本机运行链路已跑通。当前3帧图推理TP=4/FP=1/FN=0/TN=0，正常类F1=0.000。应同时阅读正常类指标与误报数，不能只看错误类F1。
五个已观察动作不足以核对论文整体效果。顺序错误的解释可能变成“未看见动作完成”，与标注错误类型不一致；当前只保存和检查解释，没有计算论文的错误解释评分。

初始K=5，经过摘要和过滤后实际保留的子动作如下：

| 动作 | 数量 | 摘要 |
|---|---|---|
| Add 1 teaspoon of white sugar to the mug | 2 | The person is holding a spoon and a container of white sugar.; The person is holding a spoon and a mug. |
| Add 2 pieces of chocolate to the mug | 1 | The person is adding chocolate to the mug. |
| Add one fifth teaspoon cinnamon to the mug | 2 | The person is scooping cinnamon from the container with the spoon.; The person is adding cinnamon to the mug. |
| Fill a microwave-safe mug with skimmed milk | 1 | The person is pouring milk from a carton into a microwave-safe mug. |
| Heat the contents of the mug for 1 minute and serve | 3 | The person is washing a mug.; The person is placing the mug into the microwave.; The person is pressing the buttons on the microwave. |
| Microwave the contents of the mug for 1 minute | 2 | The person is placing the mug into the microwave.; The person is pressing the buttons on the microwave. |
| Mix the contents of the mug | 1 | The person is stirring the contents of the mug. |

摘要检查原始日志：[text7b-summaries.log](<C:/Dev/AXG-Reasoner/logs/text7b-summaries.log>)。

第一轮复用VL7B做文本摘要时，七类动作各只保留一个子动作，加热动作误保留“washing a mug”，按钮操作被错误排除。第一轮正常加热段又被图丢弃规则判错，8帧解释还编造了杯子封口要求。这些是第一轮观察，不能直接当作当前轮结论；生成解释本身不构成错误存在的证据。
第一轮完整报告与原始结果：[first_vl_text_report.md](<C:/Dev/AXG-Reasoner/output/local7b/first_vl_text_report.md>)；[快照校验清单](<C:/Dev/AXG-Reasoner/output/local7b/first_vl_text_run/snapshot_sha256.json>)。

独立文本7B轮的完整历史报告与原始产物：[separate_text7b_report.md](<C:/Dev/AXG-Reasoner/output/local7b/separate_text7b_report.md>)；[该轮快照校验清单](<C:/Dev/AXG-Reasoner/output/local7b/separate_text7b_run/snapshot_sha256.json>)。

按论文最短2秒规则排除了 1 个子片段，清单：[axg_excluded_short_segments.json](<C:/Dev/AXG-Reasoner/output/local7b/axg_excluded_short_segments.json>)。公开1fps采样可能遗漏短暂错误。

被排除片段的帧时间（秒）：[185]。

## 图流程与论文差异

1. 32B视觉模型改为Qwen2.5-VL-7B，32B文本摘要模型改为独立Qwen2.5-7B-Instruct。官方文本模型来源：[Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct)。
2. 作者专用 10fps 数据、Ego4D 视觉特征、帧描述、清洗字典和划分尚未取得；使用公开 1fps 帧，自行生成帧描述。
3. 使用公开 EgoVLP 的 Ego4D 预训练 TimeSformer 和学习到的256维视觉投影，实际输入视频帧。仍未确认与 AXG 作者使用完全相同的权重和抽帧窗口，且数据为1fps。
4. 已实际调用原版子动作/对象聚类、子动作摘要与检查、原型计算、图构建和 graph_utils.py 动态规划；各阶段日志保存在 logs/。
5. 当前任务 K=5，依据论文正文。小样本允许路径频数为1；原代码默认频数阈值2保留。对齐片段阈值也为稀疏帧描述调整。
6. 标注动作时间重叠时采用最近开始的动作，适配到原代码单标签时间线；与作者预处理可能不同。
7. 图中被丢弃的片段按原方法直接视为错误，文字解释由7B生成；这不是模型独立给出的错误分数。
8. 所有错误说明与 has_errors 只在评估侧使用；运行请求不包含这些真值。

9. 主流程最多采样3帧，与仓库默认值及补充材料S1的消融配置一致；另跑最多8帧对照。正文主结果的 Qwen 实验使用8帧。
10. 将官方评估脚本的错误分数边界从 >0.5 修正为 >=0.5，与论文 correctness<=0.5 和保存的预测保持一致。

11. 正文定义每隔6帧生成描述（10fps时约0.6秒）。本轮对公开1fps帧逐帧生成描述，仍存在时间分辨率差异；推理前按秒排除短于2秒的子动作。

12. 修复构图脚本的等待背景过滤：原代码先去掉句号，再与带句号字符串比较，导致过滤失效。此处按规范化后的文本判断；对齐动态规划继续调用原版实现。

13. 官方可视化的旧Matplotlib get_cmap接口替换为等价的colormaps.resampled；仅影响绘图兼容性，不改变评分。

14. 重放任一图流水线时更新摘要模型来源并重建两种帧数的结果；原型重建仅清理超过当前摘要数量的旧数字命名npy，避免两轮产物混用。

## 可重复运行

以下命令重放本机已有数据和模型缓存；PowerShell工作目录为 C:\Dev\AXG-Reasoner：

```powershell
.\overnight_bootstrap.ps1
.\text7b_pipeline.ps1
.\.venv\Scripts\python.exe evaluate_error_detection.py --dataset CaptainCook4D --task spicedhotchocolate --tas_backbone gt --vis
.\.venv\Scripts\python.exe generate_report.py
```

独立文本7B对照由 download_text7b.py 下载固定版本，text7b_pipeline.ps1 等待完整校验后运行；第一轮复用VL文本能力的流程保留在 graph_pipeline.ps1。两种图流水线应串行运行。

重放已保存的8帧对照输入：

```powershell
.\.venv\Scripts\python.exe local_inference.py --manifest output/local7b/baseline_requests_8f.json --output output/local7b/baseline_results_8f
.\.venv\Scripts\python.exe local_inference.py --manifest output/local7b/axg_requests_8f.json --output output/local7b/axg_results_8f
```

完整后台安装与基线/帧描述流程见 overnight_bootstrap.ps1。重复运行会复用匹配的逐请求结果。图流程应在帧描述完成后执行。

依赖已固定在 [requirements-local7b.txt](<C:/Dev/AXG-Reasoner/requirements-local7b.txt>)；在 Python 3.12 的新虚拟环境中可用以下命令安装。模型、公开帧和视觉检查点仍需按 PUBLIC_DATA_RESEARCH.md 取得并放到本次使用的路径。

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-local7b.txt
```

## 下一步与限制

需要作者专用数据才能核对论文原版预处理和完整指标；未发送申请邮件。当前样本数很小，可能漏掉细微洒落、顺序错误或缺失步骤。请以保存的实际输出为准。
