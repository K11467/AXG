# AXG-Reasoner 7B 本机复现进度

## 授权和目标
用户授权从零自主搭建环境、做技术决策、使用少量代理，2026-10-30 早晨查看结果。优先 Qwen2.5-VL-7B-Instruct，真实视频的小规模结果；不可把替代演示或7B结果声称为原论文复现指标。不购买资源、不发邮件、不上传私人文件。

## 已知环境
- Windows；RTX 5090 Laptop 24463 MiB，系统内存约64GB，C盘空余787GiB。
- WSL 未安装；命令行 python 是商店占位符。可用引导 Python：C:\Users\20961\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe（3.12.14）。只用它创建独立环境，不修改应用自带依赖。
- 交流电已连接，交流自动睡眠为0（禁用），没有改变电源设置。
- 官方仓库基线 a4389ec；无 requirements 或测试套件。
- 自动化 axg-reasoner ACTIVE，每30分钟在本聊天继续。

## 执行方案
1. 创建独立 .venv，安装支持Blackwell的CUDA PyTorch及Transformers路线，避免WSL安装/重启。验证GPU矩阵运算。
2. 下载官方Qwen2.5-VL-7B模型，限制分辨率、batch=1、逐模型加载，优先BF16；必要时量化但记录。
3. 研究官方数据公开入口。优先EgoPER tea，核实帧/特征/标签/描述/字典/划分及AXG是否齐全；不足则记录具体缺项，尝试公开真实数据的清晰标注替代演示。
4. 配置路径和后端，保留官方核心算法；如可获取完整数据，构图、GT动作分段对齐、推理与评估；否则优先完成模型真实推理并逐项补齐可公开获取的流程。
5. 输出中文报告、模型输出JSON、样例帧、环境版本和可重复命令。不要伪造运行结果。

## 当前状态
2026-10-30 01:22 CST：GPU环境、预处理/SBERT/原版DP预检通过；公开EgoVLP严格加载及三段视频1128帧真实256维视觉特征已完成并验证。7B首分片校验完成、第二分片下载中；21项CPU测试通过，尚无7B输出。当前bootstrap PID27016、graph PID42100；具体状态以logs/*pid及实时进程为准。

## 恢复工作指南
先检查 logs/ 和进程，勿重复大下载/安装。环境路径 .venv/Scripts/python.exe；缓存放 C:/Dev/axg-cache。定时检查只在有操作价值时推进，无变化不要反复播报。完成后暂停自动化。若基础设施故障需用户操作，记录准确错误并继续其他可完成事项。

## 2026-10-29 23:53 CST 决策和实际进展
- 上一轮为 progress：创建独立环境、自动化和分支，启动下载。本轮继续实际落地。
- Ruling: EgoPER及作者专用预处理资料需邮件，改用论文同任务 CaptainCook4D Spiced Hot Chocolate 的公开1fps/360p帧；官方原视频Box抽查404，HF导出可下载。是公开数据适配，不能声称原版指标复现。
- 正常8_25、错误8_50已下载，8_50 zip CRC验证待准备脚本执行；8_25 CRC已通过，443帧1-based，1fps。8_3正常视频正在下载，避免训练/测试混用。
- 公开原始annotation与GT错误单独存储。推理请求只含任务/动作名、已执行动作和真实图像，不含has_errors或错误描述。缺失步骤(-1,-1)从片段推理排除。
- .venv已装Transformers4.57.6、科学计算依赖及qwen-vl-utils。torch尚未安装，不能声称GPU可用。
- Ruling: 完整大文件请求首字节迟滞，小范围GET实验1024B/64KB/256KB/1MB返回206，8MB约53秒；取消零进度的完整下载，使用可续传1MB分块。每块检查Content-Range/长度，模型最终比对HF LFS SHA256。
- 下载句柄：torch session41700，model48665，8_3 session53609，data session40642（8_50已完成）。下载进程均须查实后再重启。
- 隐藏后台bootstrap PID在logs/bootstrap.pid（当前3088），等待torch下载后安装CUDA/accelerate/SentenceTransformers、验证GPU；待模型和数据齐后自动执行5个基线片段，再生成训练/测试帧描述。日志logs/bootstrap-status.log。不要与其并发加载GPU模型。
- 新脚本local_inference.py保留官方提示风格，用Transformers SDPA BF16逐请求运行，原vLLM入口未修改；raw response/provenance逐请求落盘且可恢复。
- 6项unittest通过：输出失败不可判正常、分数界限、短片段真实帧采样、GT错误信息不进入模型请求、负时间戳排除、下载分块及响应校验。
- 接下来争取运行官方聚类/构图/对齐代码：原版Ego4D视觉特征不可得，考虑其注释中的caption/SBERT特征路线；若采用，标注为特征替换适配，绝不称原版特征复现。小样本路径频数阈值需单独可配置，不能假造重复训练视频。

## 2026-10-30 00:01 CST
- 三段真实视频帧全部下载并通过zip CRC：8_25正常443帧、8_3正常、8_50错误；prepare_public_data.py已实际生成5个测试动作段请求和363个帧描述请求。训练/测试ID不重叠。
- SentenceBERT模型已下载并SHA256校验（C:/Dev/axg-cache/all-MiniLM-L6-v2）；torch wheel约53%、7B首分片约25%，下载持续有真实分块进度。
- 后台bootstrap PID3088，graph pipeline PID42596；均在等待依赖。查logs/bootstrap.pid、logs/graph.pid和Win32_Process确认实际存活，不要仅凭pid文件推断。
- 新增graph_pipeline.ps1串联官方聚类、摘要/检查、原型计算、构图、对齐和错误评估；目前尚未运行成功，不可宣称完成。
- Ruling: 使用官方代码支持的caption语义特征思路，SBERT384维经seed0固定投影到256维兼容原型/进度嵌入；不是原论文Ego4D视觉特征。prepare_official_layout.py明示1fps数据仍放原版10fps命名文件夹以兼容入口；不将其称为10fps。
- Ruling: 文本摘要用同一VL7B纯文本模式，避免另下载15GB纯文本模型；记录模型差异。
- 实查clust_config对本任务默认10，与论文正文K5不同，已将spicedhotchocolate设为5。也避免全排列图指数膨胀。
- 两个训练样本路径可能只出现一次，新增--min-path-count 1显式小样本配置；默认2仍保持原版规则。对齐以--min-action-captions 0 --min-bg-captions 1适配每3秒一个帧描述，并保留真实时间索引。
- Windows路径split修复；原脚本平台依赖rm -rf清理删除，改为逐文件覆盖，保留已有实验。
- 10项unittest通过（新增路径/路径频数/BG提示验证）；主脚本compileall通过。尚无模型真实输出，不能报性能或显存实测。
- REPRO_REPORT.md由generate_report.py生成，当前明确结果0、未完成。基线一旦生成可重跑报告查看中间结果。
- 代码已提交4b4ba51（首批设置）；Git无用户身份，用单次Codex/codex@localhost署名，不改全局配置，不推送。
- torch官方预期SHA256已保存logs/torch-expected-hash.json，完整下载后请额外核对。

## 2026-10-30 00:08 CST 静态审查处理
- 同一辅助代理完成一次有界静态审查，记录STATIC_REVIEW.md，无新增代理。4项重要问题均已核查：连字符动作截断、解析失败缓存、0.5边界、旧状态日志。
- 连字符修复已通过回归；缓存只接受成功解析，失败写parse_error并明确失败，恢复可用--strict-output新提示或--retry-invalid，不伪造分数、不无限重试。
- 评估脚本两处>0.5改>=0.5，匹配论文correctness<=0.5。报告披露修正。
- 启动状态改成带run UUID和PID的原子JSON；graph只接受当前bootstrap.pid对应的状态，不读取旧文本日志判断完成。
- 当前bootstrap PID6404，graph PID39316；bootstrap-state.json证实running/waiting-for-torch。进程均已查实存活，下载也继续推进。
- 13项unittest及compileall通过。torch约74%、模型首分片约35%；没有CUDA实测或推理结果，完整目标仍未完成。
- 本轮3帧采样与仓库默认一致，但论文Qwen用8帧，已加入报告差异。

## 2026-10-30 00:18 CST 更接近论文的视觉特征路线
- 上轮为progress+verified wait：13测试修复、commit8a569bb；下载句柄41700/48665均确认live且分块增加。
- 主动调查表明公开EgoVLP使用Ego4D预训练TimeSformer+学习到的256D投影，与原论文骨干/特征维度更接近；尚不能确认AXG作者具体checkpoint。不能直接把语义特征替换当最终目标完成。
- 官方来源 https://github.com/showlab/EgoVLP；源码clone到C:/Dev/axg-cache/EgoVLP，commit928406c2d5d42b4d76421f6500e43feb61fc9d68，无AGENTS。
- 作者公开EgoVLP_PT_BEST Drive文件ID1-cP3Gcg0NGDcMZalgJ_615BQdbFIbcj7，已验证206/2171555287字节，range下载session18951（logs/download-egovlp.log），当前尚未下载完；有超时自动有界重试，不能仅因观察超时重复启动。
- pickletools安全探测data.pkl只含OrderedDict、torch tensor rebuild、parse_config.ConfigParser、argparse.Namespace、pathlib.PosixPath。extract_egovlp_features.py用weights_only=True和惰性元数据替身/纯路径允许列表加载，严格匹配video_model和vid_proj所有权重；不加载额外文本模型或ImageNet初始化。
- 视觉提取用官方SpaceTimeTransformer代码和官方test归一化；按1fps邻帧组成预训练帧数窗口（边界重复），每秒256D特征。尚待实际权重加载/图像依赖性/finite验证，不能宣称已成功。
- prepare_official_layout默认feature-backend=egovlp，会在图阶段提取真实视觉特征；caption投影保留为显式--feature-backend caption选项，若视觉路线不可行必须记录实际错误再决定，不可悄悄降级。报告动态读取实际后端。
- 15项CPU tests通过，新增真实帧窗口边界和严格权重分区校验，未有GPU结果。
- 重要下一步：torch/torchvision/accelerate安装完成且bootstrap在等7B模型时，在.venv中安装 timm>=1,<2 和 einops（不要与已有pip并发）。EgoVLP权重下载后先跑 extract_egovlp_features.py --recordings 8_25 --limit 2 做真实smoke，再全部提取。
- 当前torch下载约98%，7B首分片48%；bootstrap6404和graph39316仍活着，暂未安装torch。

## 2026-10-30 00:21 CST GPU环境实际通过
- torch完整下载，SHA256与官方index一致：7c78215c3af4f62e63f2b2e360f1722fc719b0853c7ac22666483d9810613a4c。
- 后台已成功安装torch2.11.0+cu128、torchvision0.26.0+cu128、accelerate1.15.0、SentenceTransformers5.2.0。
- logs/gpu-check.log真实输出RTX5090Laptop、CUDA12.8、架构包含sm_120、1024x1024 BF16 GPU矩阵乘积finite=True。
- bootstrap状态prepare-public-data，已进入等待7B完整权重；检查无其他pip后完成timm/einops安装（logs/install-visual-deps.log）。后续已重存pip freeze。
- 7B和EgoVLP仍在下载，无模型推理输出。下一步先验证Qwen处理器/真实视频张量编码，再等EgoVLP视觉smoke及7B加载。

## 2026-10-30 00:24 CST 运行时检查
- timm1.0.30/einops0.8.2安装完成，pip freeze已更新。
- 真实8_50视频三帧通过Qwen处理器：input_ids[1,653]、pixel_values_videos[2112,1176]，浮点张量全部finite；logs/processor-check.json。Qwen工具对帧列表返回实际fps=2.0（同仓库默认），源帧导出仍是1fps；已将实际处理器kwargs/grid/shapes写入每个推理结果，便于审计补帧和时间编码。
- 真实SBERT GPU编码3句得到[3,384] finite，倒牛奶/装牛奶相似度高于切菜；logs/sbert-check.json。
- 原版graph_utils CPU动态规划真实执行三帧链式smoke，得到pred=[0,1,2]，logs/graph-dp-smoke.json。此测试不证明真实数据图流程成功。
- 7B与EgoVLP权重仍下载，有部分网络超时/IncompleteRead有界重试，不能据此重复启动同一个下载。继续读真实ranges完成计数确认进展。

## 2026-10-30 00:28 CST 下载器故障定位与恢复
- 实查模型ranges完成数1821，文件mtime停在00:15:49，但进程仍请求2183/2362等后续块；不是仅凭超时判断停止。源码future.result异常退出as_completed后，ThreadPoolExecutor上下文等待所有已提交任务，导致新下载结果不再保存。单块1826已有4次URLError重试，故障路径可确认。
- 修复collect_chunks：队列限制为2*workers；单块失败记录并继续保存其他成功块；每个文件最多3轮失败块重试，之后明确终止并保留断点。新增回归证明一个失败块不会丢弃其他完成块，16项测试通过。
- 为部署已验证的代码修复，确认并停止旧模型11312/43480与EgoVLP30360/18728下载进程，保留全部已提交断点，旧日志保存*-before-recovery.log。不是因观察超时盲重启。
- 新句柄：7B session51564，EgoVLP session9337。模型从1821块恢复，已观察1860块（50.0%），实际进度重新增加；EgoVLP从364块恢复。bootstrap6404、graph39316继续等待，不重启。
- 暂无7B错误推理或真实EgoVLP视觉输出，保持目标active，不能宣称复现完成。

## 2026-10-30 00:36 CST 特征来源核查
- 当前轮前半为verified wait，实际model进度从2080到2400块，EgoVLP从500到660块，两下载进程及bootstrap/graph均查实live。
- 进一步核查相关GTG2Vid论文：作者实现细节称VideoCLIP(Ego4D预训练)，而AXG正文称TimeSformer并援引GTG2Vid；vc_v_features命名不能证明具体checkpoint。因此公开EgoVLP路线只可称符合所述骨干/维度的适配，不能声称恢复同一作者视觉特征。
- 原始主来源：GTG2Vid PDF https://openaccess.thecvf.com/content/ICCV2025/papers/Lee_Error_Recognition_in_Procedural_Videos_using_Generalized_Task_Graph_ICCV_2025_paper.pdf；AXG PDF和EgoVLP官方源码见前述记录。
- 已准备本地英文数据/权重/抽帧细节申请草稿docs/data-request-email.txt，含待用户填写的机构信息，没有发送邮件，也没有推断用户身份。
- 可能的后续增强：先测7B真实吞吐与显存，再决定是否将caption stride由3秒改为1秒，或补做论文8帧采样的对比。不要在没有吞吐/显存证据前盲目并发模型或扩展实验。

## 2026-10-30 00:46 CST 原论文/附录实读与采样修正
- 正文11页及补充9页从官方CVF实际下载到data/papers，pypdf提取为同目录txt。作者主页镜像SSL校验失败，未关闭验证，直接官方CVF下载成功。
- 附录S1实际报告3/8/12帧对比，故3帧是论文研究过的配置；仍不是32B论文主结果。S5/S6提示与当前生成/推理模板一致。
- 正文明确sample one every beta frame，beta6表示10fps源每0.6秒一帧，而不是6fps。为更接近论文密度，caption-stride默认改为1，对全部可用1fps帧生成描述。实际manifest已重生成：5个基线动作段、1109条caption请求，无任何推理结果需要作废。
- 对齐设置改为min-action-captions1、min-bg-captions2；alignment_requests根据真实秒及data_provenance的stride计算覆盖区间，并严格排除<2秒子动作，排除清单另存axg_excluded_short_segments.json。导出只保留实际推理过的子动作，仍拒绝将空证据动作当正常。17项tests通过，包括2秒边界与action end截断。
- PDF输出暴露Windows GBK控制台UnicodeEncodeError；为避免后续含特殊符号的模型输出使进程终止，两个后台PS入口显式设UTF8/PYTHONIOENCODING及Console.OutputEncoding。确认尚无7B权重就绪、无推理进行，重启等待中的bootstrap/graph以应用编码配置；pip已存在依赖原位复核，无大文件重复下载。当前bootstrap27016，graph42100（后者为1fps阈值配置重启），state JSON已验证新runUUID/PID。
- 7B下载session51564，EgoVLP下载session9337；00:44测首分片86.0%、EgoVLP50.2%，不是7B整体86%。下载继续有进度。

## 2026-10-30 00:52 CST 首个7B分片校验通过
- model-00001-of-00005.safetensors完整3900233256字节，SHA256=e97b877e47fde53a6c6e77aafb36e58e91ee9d95c4a3eeac6f1b5c0e6a1c986e，与HF LFS预期一致。正在下载第二分片；这不代表模型整体完成。
- EgoVLP下载1340/2071块（64.7%）；句柄51564/9337仍live。
- Qwen单图caption真实处理器也通过，inputs包含pixel_values和image_grid_thw，无None导致shape记录失败；logs/caption-processor-check.json。
- local_inference默认reason max_new_tokens从初始192对齐原仓库256，并记录hit_token_limit，便于识别解释被截断。caption仍显式112，若真实输出多次截断，需据实际输出提高上限。
- 短子动作排除清单在没有请求时也先落盘再明确失败，避免旧manifest残留误导恢复。
- 当前目标仍未完成：需要完整7B加载、真实图像推理、TimeSformer严格权重加载和实际图流程输出；已有CPU/GPU预检不等同于完成。

## 2026-10-30 01:23 CST 真实视觉编码完成及报告汇总
- 上一目标轮为progress：正文/附录核对、1fps逐帧caption计划、2秒阈值、UTF8入口和首个分片完整校验；当前轮继续实际验证，未缩小目标。
- Qwen结构在meta设备构造通过，8292166656参数，sdpa导入兼容；logs/model-architecture-check.json。只证明结构，不代表权重加载或推理完成。
- EgoVLP下载session9337实际exit0，2171555287字节，观察SHA256=e5c13b7a084331bcd3f46361b1ad66ca0088e2eeef0769529d19bb2a3a4df09d，源为作者公开Drive文件；这是观察哈希，未取得作者独立公布哈希。
- 真实GPU smoke session68408 exit0，严格加载全部video/projection权重，成功输出2x256有限特征。
- 完整视觉提取session30826 exit0：8_25=443x256/78.5s，8_3=422x256/74.2s，8_50=263x256/46.2s，总1128帧。每数组finite=True、norm最小31以上、RMS跨帧变化约1.66，非固定/零占位特征。数值核验logs/egovlp-feature-check.json；输出output/local7b/egovlp_features/*.npy及逐视频元数据json。
- 该视觉阶段在7B完整权重未就绪且无推理进程时运行，已退出，不并行占用后续7B显存。
- 新增结果汇总helper及测试：缺失预测不可产生满分；全判正常必须显示FN；图子动作any-error聚合要求对应动作全部推理已齐；旧输入即便同ID也不计入当前报告。21项tests通过。
- generate_report.py现在展示实际视觉帧数、图动作级对比和每个子动作的真实解释/JSON链接，保留图丢弃分数来源；基线及图F1都只有完整证据时才写入小样本metrics.json。当前报告明确0个7B结果，不编分数。
- alignment_requests新加parent_action时间/名字用于报告对齐到GT动作段，只进评估汇总，不加入模型prompt。
- 7B下载session51564仍需检查；01:19第二分片63.5%，完整模型未就绪。bootstrap27016/graph42100仍等待。
- 后续必须完成：7B加载/基线5段/1109帧描述/原版聚类摘要原型构图对齐/图推理和评估/实际结果审查。不能用当前视觉编码完成代替最终复现。

## 2026-10-30 01:37 CST 生成配置与报告对照
- 当前轮为verified wait+progress：确认下载22940、bootstrap27016、graph42100实际存活且第二分片持续增加，未重启活跃下载。
- 第二个7B分片已完整通过SHA，日志进入第三分片（01:35第三分片3.8%）；完整模型仍未就绪。
- 实查7B generation_config默认do_sample=True、repetition_penalty=1.05；本地早已显式关闭采样，现在进一步显式repetition_penalty=1.0以对应官方vLLM SamplingParams默认（已查官方API文档 https://docs.vllm.ai/en/latest/api/vllm/sampling_params/）。运行参数写入每条结果；签名backend升级v2，避免默认差异隐式混用。无现存推理输出受影响。
- 报告增加仅供事后对照的公开错误标注说明（Order/Technique等），与模型输入仍分离；缺标签/缺说明显示未知，不默认正常。
- 21项CPU tests通过。当前仍没有7B真实生成，不能报错误检测或解释成绩。

## 2026-10-30 01:49 CST 最终静态审查修复
- 唯一新发现：caption布局和graph导出只按ID匹配旧缓存，报告则按完整请求匹配，可能在修改prompt/时间后产生不一致。
- 已统一三个消费者为load_matching_results，必须status=ok且保存的request与当前manifest相等；只允许已记录的strict_output格式提醒差异。新增稳定ID但改变prompt的回归测试先失败后通过；全22项tests通过。
- 当前尚无7B输出，不存在已污染结果。第三分片约34%，下载活跃；bootstrap/graph仍等待，未重复启动任务。

## 2026-10-30 01:54 CST 运行手册校正与等待
- 上一轮属于progress：缓存输入一致性修复已提交7e22c55；本轮验证下载20844、bootstrap27016和graph42100活跃。第三分片47.7%，仍未进入7B生成。
- 可重复运行手册改为依次overnight_bootstrap.ps1、graph_pipeline.ps1、generate_report.py，覆盖原先命令示例遗漏的1109条caption生成及bootstrap就绪状态；不新开重复后台实例。
- 核对qwen_vl_utils的帧列表默认sample_fps=2.0，与原仓库不指定sample_fps的用法一致；这是模型帧列表时间约定，不代表公开源帧为2fps。每条结果保留实际processor_video_kwargs。保持原约定，不隐式改变处理器行为。

## 2026-10-30 02:22 CST 第三个权重完成及尾分片预取
- 本轮progress+verified wait。第三分片3864726424字节完整SHA256=111223d173e00bbee81cba1216fad28668df3476706b7fd26f4d5b50f8b3a507，与HF LFS预期一致。主下载已进入第四分片约11%。
- 为减少串行尾部等待，用现有range_download工具以3 workers预取最后一个1089994880字节分片到独立C:/Dev/axg-cache/prefetch目录，session45041（launcher644/actual43036）。不会修改主下载中的文件；只有SHA通过才Move-Item到模型目录，主下载随后仍会复核SHA并跳过。没有新GPU任务、没有新智能体。
- 02:21第五分片约79%；主下载20844/session51564存活且持续进度，bootstrap27016、graph42100继续等待。已验证所有进程，不因等待重启。
- 02:12按ranges.completed实际块数计算总下载70.9%，logs/download-progress.json；预分配.download文件长度不能作为进度。当前模型仍未就绪，未产生任何7B预测。
- 待执行：全权重校验→基线5→caption1109，早期检查动作/对象句式和token截断→原版聚类摘要原型图构建/对齐→图推理→真实评估/报告审查。

## 2026-10-30 02:28 CST 第五分片完成及8帧对照准备
- 预取session45041 exit0，第五分片1089994880字节SHA256=0c859795ad3a627a9b95bcb762e059d5b768a4a36fdd4affeff269d93fdecc67，与HF LFS预期一致，已原子移入正式模型目录。四个分片已完成，只剩第四分片约27%；bootstrap和graph仍等待完整marker。
- 为更接近正文8帧配置，已生成output/local7b/baseline_requests_8f.json：同5个动作、每段8张真实均匀采样帧，未执行，不覆盖主3f manifest。先完成3f全图流程，查看真实显存后再尝试8f对照，必须串行、不与caption或summary同时加载模型。后续结果需另存baseline_results_8f；图8f也应单独manifest/目录，不能混入3f官方导出。

## 2026-10-30 03:02 CST 完整7B加载与真实推理通过
- 本轮为progress：全部5个权重分片SHA通过，主下载session51564实际exit0，02:58日志ALL MODEL FILES VERIFIED。第四分片SHA=ef47f634fa57d46ee134edcc09f34085a47da1e16c12a2abe0d67118be6d72ed；正式模型目录已有完整download_provenance.json。
- bootstrap27016自动于02:58:11启动baseline，02:59:11切换caption；无需重启。真实7B BF16/SDPA权重加载8.2秒，PyTorch allocated15.45GiB。
- 5条真实视频baseline全部status ok、parse_ok=True、generated50~91tokens、hit_token_limit=False。冷启动首条20.90秒，后续5.35~7.78秒，PyTorch峰值15.66~15.68GiB。
- 重要效果限制：5个评分全部0.5，按论文correctness<=0.5全部判错。TP4/FP1/FN0/TN0；E-F1 .8889、N-F1 0、macro .4444。这没有区分能力，报告已明确标出，不能只报错误F1或宣称复现论文成绩。实际采样帧已目视检查，符合真实视频场景；原始推理输出完整保留。
- 帧描述首批43条审计：39条含动作+对象状态句、0空输出、0token截断，均值2.697秒；logs/caption-early-audit.json。真实描述可见pouring milk / carton open等；不因个别措辞不准改提示词迎合标签。
- 当前caption1109条正在跑，03:01约44条，实际GPU利用95%、总显存约18.7GB、温度61C，无OOM。进程actual36800（launcher39208，启动时值，后续需实查）；graph42100仍等待caption完成，不并发加载。
- REPRO_REPORT.md已重生成真实5条基线结果、macro及评分塌缩提示，output/local7b/baseline_small_sample_metrics.json已生成。当前尚无图结果，目标未完成。
- 后续：监控caption完成→原版图全流程→排查实际故障并记录→8帧对照（先baseline_requests_8f.json，同GPU串行）→审查真实图结果、保存可复用命令和差异→完成后停止heartbeat并完成goal。

## 2026-10-30 03:14 CST 依赖锁定与逐帧描述继续
- 上一轮是progress：完整权重、5条真实基线、首批caption已验证；当前实际caption PID50128（launcher12800），bootstrap27016和graph42100存活。03:13约349/1109，真实输出持续增加，无重启。
- 重新从实际运行venv捕获50项pip freeze（包含后装的timm/einops），保存logs/environment-freeze.txt；新建requirements-local7b.txt固定所有版本，torch本地wheel URI改为等价已安装版本2.11.0+cu128，并给出官方cu128索引。原wheel SHA仍保留在原始freeze及安装日志。
- 报告已补充固定依赖安装命令；模型/数据/视觉检查点仍需按公开来源放在指定缓存位置，不把requirements文件描述为包含数据的完整离线包。

## 2026-10-30 03:40 CST 帧描述完成，原版聚类及摘要运行
- 1109/1109真实caption全部成功，0空输出、0token截断；总推理2245.58秒，均值2.025秒，PyTorch峰值15.625GiB；logs/caption-full-audit.json。caption50128已正常结束，bootstrap状态ready。
- 六个官方后续模块实际import全部通过，session46077，无缺失依赖。layout于03:37:21成功；复用完整真实EgoVLP数组，未切换caption投影。实际保留caption8_25=417、8_3=397、8_50=240（重叠55秒按单标签owner过滤），帧数组仍443/422/263。
- 官方clustering03:37:33成功，七个动作均有实际输出；summary03:37:33启动，同一7B VL纯文本模式，显式do_sample=False，GPU实际生成中，当前已到第五个动作。
- 发现并修复确定性上游字符串问题：build_axg.py先caption.split('.')[0]去句号，却与BG='the person is waiting.'比较，条件总把等待当非背景。新is_background_caption规范空格/大小写/句号后判断，仅用于构图原有过滤意图；axg2vid的全时间线对齐不改。回归测试RED缺函数→实现后全23tests通过。修改发生在实际build_axg阶段启动之前，无需重算caption/cluster/summary。
- 7B摘要自检存在语义误判，例如认为从carton倒入与skimmed milk冲突、认为按微波炉按钮与微波主动作冲突。保留模型输出和原始检查逻辑，不按测试标注人工挑子动作；这属于7B替换的效果限制，后续报告应说明。
- 已为报告加入帧描述完成/布局保留数量及上述句号修复差异。当前尚无完整图结果。

## 2026-10-30 03:58 CST 第一轮全流程完成，独立文本7B对照启动
- 第一轮图流水线03:41:44真实完成：七类动作均各1条摘要、7个AXG、14个256D有限非零原型（含progress版）；3f图7个子动作，其中4个BG规则丢弃。官方evaluate输出N-F1=0/E-F1=88.9/平均44.4，与独立聚合一致。背景修复commit1ad3158实际03:40:05，早于build启动03:40:44，确实应用。
- 3f基线及图均TP4/FP1/FN0/TN0，macro .4444。8f实际完成session17016 exit0：基线仍全部.5；图TP3/FP1/FN1/TN0，macro .375（加奶视觉动作被判正常，但GT为顺序错误）。此前凭日志片段说8f图也全判错不准确，已明确更正，正式指标以完整汇总为准。所有3f/8f输出0截断；峰值8f16.016GiB PyTorch allocated。
- 诊断session52505 exit0：正常训练milk8f=.5，正常训练sugar8f=1.0，无动作标签的测试frame82图片识别为从瓶子倒液体入杯。诊断结果单独保存，不加入5段测试统计。证明不是所有输入都恒定评分或完全看不到视觉信息；评分校准、动作完成和顺序推理不稳。
- 第一轮所有官方图目录、3f/8f/诊断原始结果、请求、指标、报告及关键日志，已保存到output/local7b/first_vl_text_run；93个原始文件SHA清单snapshot_sha256.json，不再覆盖。第一次comparison审计只列基础原型7个，但official快照含两套14个实际数组；新的audit_experiment.py已在当前实际数据检查14个数组、7图并通过。
- 决策：原论文分开使用文本LLM和VLM；首轮为省下载复用VL7B纯文本，出现明确摘要误判（heat竟选washing a mug、按钮被判冲突）。不调阈值或按测试标注挑摘要，改用同系列独立Qwen2.5-7B-Instruct作摘要对照，保持VL7B、caption、视觉特征、数据与提示不变。更接近论文分工，不能预先保证改善；时间仍在原10小时窗口内。
- 官方HF模型页已核对：https://huggingface.co/Qwen/Qwen2.5-7B-Instruct 。官方API参数7615616512，固定revision a09a35458c702b33eeacc393d103063234e8bc28。download_text7b.py复用已测试的range下载/逐分片SHA验证，session96716，launcher32304/actual53384；缓存C:/Dev/axg-cache/Qwen2.5-7B-Instruct，4个权重分片约15.2GB。下载完成才原子写download_provenance。
- 新后台text7b_pipeline.ps1 PID46252，logs/text7b-state.json=waiting；native stage退出码检查/UTF8/独立runUUID+PID状态。等待新权重→layout/clustering复核→独立文本summary→原型/图/对齐→3f推理/官方评估→8f manifests与推理→audit_experiment→report；当前无GPU并发。已有第一轮快照。数据/I-O编排脚本按实际产物审计和阶段退出码验证，未做无意义的镜像单测；PS语法解析与Python编译通过。
- prepare_comparison_inputs.py已在真实请求运行，5 baseline均8帧，图7请求为8/8/8/7/8/8/8；audit_experiment.py实际通过。审计脚本首次把progress目录拼错，已经按原脚本v_subaction_prog_features_5_clust校正，属审计路径错误，非原型缺失。
- 重要待办：generate_report.py已加入第一轮3f/8f及诊断与局限，但目前部分结论仍写死第一轮（七类各1、heat washing、8f milk FN等）。在第二轮完成前，必须改为读取run_provenance（PS写UTF8 BOM，使用utf-8-sig）、当前审计与原型/指标，第一轮结论明确指向first_vl_text_run；不得把第一轮分析当第二轮。报告模型差异和重放命令需增加独立text7b_pipeline。
- 其他待办：实际资源/输入SHA审计，检查最终报告和所有语义结果、完整测试23项；完成第二轮和必要对照后停止heartbeat axg-reasoner，再完成goal。不能因第一轮已跑通就把当前尚在下载的对照宣称完成。

## 2026-10-30 04:05 CST 第二轮报告与资源审计准备
- 上一轮是progress：全图/8f/诊断完成，第一轮快照与独立text7B下载/自动流水线已建立。本轮重新验证下载53384和等待流水线46252活跃，首分片约24%；不是整体下载24%。
- generate_report现读取run_provenance.json（utf-8-sig兼容PS BOM），动态选择摘要模型、日志、复放流水线、3/8f优劣及漏检动作，并从当前summary目录生成真实数量/文本表。第一轮错误明确标为历史观察，模型切换后显示两轮图指标对照，避免沿用首轮结论。临时目录BOM元数据+未完成报告功能smoke通过，不污染实际实验；全23项tests通过。
- 本机资源记录logs/resource-report.json：Windows11、Python3.12.14、CPU Ultra9 275HX、可见RAM68050006016字节、RTX5090Laptop24463MiB、driver616.92、04:00磁盘余811692949504字节。第一轮PyTorch峰值16.016GiB不含桌面/驱动。最终仍需刷新磁盘占用及当前轮峰值，不能用预分配.download长度当已下载数据。
- 7个公开输入（3zip及4标注/metadata文件）观察SHA保存logs/input-sha256.json，明确不是独立发布哈希。93个第一轮原始快照逐个SHA复查0变化，logs/first-snapshot-audit.json。
- 创建output/local7b/first_vl_text_report.md为历史展示副本，把已复制的结果/指标链接重定向到first_vl_text_run；原始93文件和snapshot_sha256完全不改。避免旧报告指向日后覆盖的新指标。
- heartbeat axg-reasoner已保持ACTIVE/每30min，提示更新为跟踪download-text7b/text7b-state和新实际进程，不能见首轮finished就提前完成；仅重要变化通知，不新开代理。一次额度检查显示充足，不需要额外高级模型/代理。
- 待第二轮权重及自动流水线真正结束后：审查当前图/预测/官方指标、最新comparison与历史对照、解释及数据差异；检查报告语义和图像；刷新资源/完整输入验证、23项测试及重放验证；保存最终记录，停止heartbeat，完成goal。当前第二轮尚未运行，目标保持active。

## 2026-10-30 04:39 CST 独立文本首分片校验，官方时间线可视化通过
- 本轮progress+verified wait：独立文本首分片model-00001-of-00004完整SHA256=a1333e6293854747c481288ea83b348226af178dd565c49b6f9495ba1966aba7，与固定HF LFS预期一致。04:35进入第二分片；04:38约7.6%。下载53384/session96716及等待worker46252仍需后续按实际PID/句柄检查，不重启活跃下载。
- 实际运行官方evaluate_error_detection --vis发现Matplotlib3.11.2移除了cm.get_cmap，CLI明确失败。utils/utils.py四个活动调用改为等价matplotlib.colormaps['rainbow'].resampled(N)，准确保留颜色数量；第一次补丁只改到另一个绘图函数，补齐draw_pred_v2后同一CLI exit0，指标仍N0/E88.9/平均44.4。
- 已实际查看output/CaptainCook4D/spicedhotchocolate/error_reasoning_5_clust_gt_3f/vis_ed/8_50.png：上GT TAS、中GT错误、下预测，正常末段GT紫/预测红，确认误报可见。横轴是1fps索引近似秒，背景在原脚本按Normal显示。图片复制到output/local7b/first_vl_text_timeline.png，并加入历史展示副本；93原始快照不改。
- 主报告仅在官方PNG时间戳不早于对应导出JSON时显示“当前轮”时间线，避免第二轮已导出而图片仍是首轮。新text流水线默认没有--vis；最终agent必须在第二轮finished后重新运行官方evaluate --vis，再生成报告并查看图片。已补充该重放命令及绘图兼容差异。
- 当前仍只完成第一轮和报告/资源准备；第二轮权重仍下载，不能完成goal或停heartbeat。下一轮主要是真实下载等待，不要为等待创造无关实现或盲目调参；待全权重校验和text7b_pipeline完成后按前述清单审计收尾。

## 2026-10-30 05:18 CST 独立文本模型第二分片校验通过
- 本轮为verified wait：持续轮询实际下载53384/session96716及等待流水线46252，均活跃；未重启，也未为等待添加额外实验。
- 第二分片主体完成后，下载器自动补齐2个失败块，随后完整SHA校验通过并进入第三分片。全部成功块已持久化，未重复下载已完成分片。
- 第一、第二文本权重已完整，第三刚开始；当前没有第二轮GPU推理结果，不完成goal、不停止heartbeat。待第三/四及完整marker后text7b_pipeline自动继续。
- 后续收尾仍按04:39/04:05记录：真实新图3/8f与首轮对照审查，当前模型与报告语义核对，最终官方--vis及图片检查，资源/输入/测试/重放审计，保存最终结果后停止自动化并完成goal。
- 原始校验日志：COMPLETE model-00002-of-00004.safetensors sha256=f5d25a2772cb825164a2a2c0fb6d51a87e282abf21e4dd75bc5cfb3cd0ea6185

## 2026-10-30 05:56 CST 独立文本模型第三分片校验通过
- 本轮为verified wait：实际下载53384/session96716和等待流水线46252持续活跃，第三分片完整SHA通过，05:56已开始最后一个3556377672字节/3392块分片。没有重启活跃任务、没有新增实验。
- 当前文本权重3/4完成，但完整marker尚未产生，因此第二轮GPU尚未开始；第一轮及所有历史原始输出保持可查。
- 继续等待最后分片及text7b_pipeline实际完成。最终审查应再核对两轮subactions/obj_state聚类文件是否一致，支持“同一caption/特征，仅更换摘要模型”的对照；若不同需如实记录，不能只凭配置宣称一致。
- 收尾仍需当前轮官方--vis、查看新时间线和主报告、刷新资源与原始输入/快照校验、完整23项测试和重放证据，再停止heartbeat并完成goal。当前不完成。
- 原始校验日志：COMPLETE model-00003-of-00004.safetensors sha256=8efdec4c1bc12317ae1a38dc42b595ce777738a64deea3fcb8a0a91381bcdfd5

## 2026-10-30 06:56 CST 最终审查发现重放混用问题，修复验证中
- 最终独立只读审查确认本轮真实结果无Critical问题，但发现first graph_pipeline重放会沿用text7B来源/8f请求；进一步检查发现旧的较多原型2.npy/3.npy也会残留。
- 修复：first流水线每次写本轮VL-text来源、重建8f输入并推理/审计；特征生成在每个动作读取非空summary后，仅删除超出当前数量的数字命名旧npy，拒绝未知npy和越界链接。回归测试先RED，后全25项通过，PS语法通过。
- 第二轮完整原始数据/报告/官方目录已保存output/local7b/separate_text7b_run与独立SHA清单。现在实际执行修复后的first全流水线作为重放验证（会临时切换当前目录内容），成功后必须恢复第二轮快照，并重新审查报告/指标/时间线后才能完成goal。两轮原始历史均保留；当前不要因text7b-state finished就停止。

## 2026-10-30 07:07 CST 最终交付完成
- 两个7B配置均真实完成官方聚类、摘要、视觉原型、AXG、GT对齐、3/8帧VLM推理及评估；默认当前交付恢复为独立Qwen2.5-7B文本摘要 + Qwen2.5-VL-7B视觉模型。第一轮03:41完成，第二轮06:39完成；额外重放一致性验证07:00成功。
- 本任务为公开CaptainCook4D Spiced Hot Chocolate适配：正常训练8_25/8_3、测试8_50五个观察动作，作者专用10fps数据/划分/检查点尚未取得。不是论文完整benchmark或精度复现。
- 最终图3f TP4/FP1/FN0/TN0，macroF1=.4444；8f TP3/FP1/FN1/TN0，macro=.375。两轮检测指标相同、正常类F1均0；独立文本模型使摘要7→12个，但BG丢弃/any-error仍误报正常加热段。没有按GT调阈值或人工选子动作。
- 原始1109条帧描述、1128帧真实256D EgoVLP特征、3/8f基线与图输出、独立诊断全部保存。当前每种帧数10个有效图子动作，第二轮各5个新推理/5个完整请求相同的缓存复用。1个185秒单帧子片段按最短2秒规则排除，清单明确记录。
- 全25项测试通过；基线/caption/图3/图8匹配缓存重放通过；1284处实际输入帧存在；3套视觉特征副本逐元素相同、有限且有时间变化；模型9个分片下载时逐SHA核验、最终版本/尺寸复查；7个原始输入SHA未变；14份聚类字节一致。
- 原始历史快照93+128文件SHA均未变，两份历史展示报告把结果/指标/图像链接指向对应快照。最终本地报告链接检查无缺失，采样蒙太奇与当前官方时间线实际目视检查。独立只读审查的Important重放问题已修复并实际验证，见FINAL_STATIC_REVIEW.md。
- 实测RTX5090Laptop 24463MiB、Windows11、Python3.12.14、主机可见RAM63.38GiB；最高PyTorch分配16.022GiB，未包含桌面/驱动。工程约5.39GiB，共享cache约34.54GiB；帧描述推理约37.4分钟。环境50项版本固定requirements-local7b.txt，资源细表logs/resource-report.json。
- REPRO_REPORT.md为最终入口：真实分数/解释/图、模型版本、两轮对照、已知失误、与论文14项差异、复放命令和下一步。公开资料PUBLIC_DATA_RESEARCH.md，数据申请邮件仅为未发送草稿。
- heartbeat axg-reasoner已于最终审查通过后更新为PAUSED（工具确认）；没有遗留下载或GPU模型进程，无购买资源/发送邮件/私人上传。源代码保持本地local-7b-repro分支，不推送远端。
