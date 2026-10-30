# Public data investigation (2026-10-29, Asia/Shanghai)

## Decision

EgoPER tea cannot currently be obtained fully unattended from the official instructions: both original EgoPER recordings and the AXG-specific processed data require an email request. No public download URL for the author's cleaned action dictionary, dense captions, AXGs or subaction features was found in the official repositories. Do not claim the official-data reproduction succeeded without them.

The most useful overnight fallback is **CaptainCook4D Spiced Hot Chocolate**, an actual task used in the AXG paper, using public dataset annotations and ProMQA's public 360p frame export. This is a **7B public-data adaptation/demo**, not reproduction of the paper's exact preprocessing, split, AXG, features or reported scores.

## Official access evidence

- AXG official README: https://github.com/robert80203/AXG-Reasoner#preparation
  - Requests institutional email to lee.shih@northeastern.edu.
  - Expected data: frames_10fps, vc_v_features_10fps, labels_10fps, action_object_state, action2idx.json, clean_action_dict.json, training.txt and test.txt.
  - AXG and subaction intermediates are generated under output; repository tree contains code and figures, no released output/checkpoints.
- GTG2Vid README: https://github.com/robert80203/GTG2Vid#download-datasets
  - Processed annotations, features, splits and pretrained GTG2Vid weights require the same author request.
- EgoPER README: https://github.com/robert80203/EgoPER_official#preparation
  - Original recordings/annotations require email; links are issued with a two-week expiry.
  - Original annotations include temporal step labels and object boxes, but are not bundled with the code. No official archive byte size is given, so cannot estimate exact download.

## Working public fallback

Primary dataset author sources:

- Dataset project: https://captaincook4d.github.io/captain-cook/
- Annotation repository: https://github.com/CaptainCook4D/annotations
- Complete step labels (about 1.6MB): https://raw.githubusercontent.com/CaptainCook4D/annotations/main/annotation_json/complete_step_annotations.json
- Error descriptions (about 2.0MB): https://raw.githubusercontent.com/CaptainCook4D/annotations/main/annotation_json/error_annotations.json
- Task graph: https://raw.githubusercontent.com/CaptainCook4D/annotations/main/task_graphs/spicedhotchocolate.json
- Metadata: https://raw.githubusercontent.com/CaptainCook4D/annotations/main/metadata/video_information.csv
- Official downloader: https://github.com/CaptainCook4D/downloader

The official downloader obtains Box URLs from metadata/download_links.json. HEAD against recording 8_50's official 360p Box URL returned **404** on this investigation. Therefore do not spend the night repeatedly retrying that URL.

Public frame export maintained by the **ProMQA paper authors**:

- Code and provenance: https://github.com/kimihiroh/promqa-cooking#data
- Dataset: https://huggingface.co/datasets/kimihiroh/promqa-cooking-frames
- Frame sampling code: https://github.com/kimihiroh/promqa-cooking/blob/main/src/benchmark/sample_frame.py
- License stated by exporter: Apache 2.0, following CaptainCook4D.
- Sampling is **1fps**, naming `%d.png`; verify zip internal paths and start-index conventions before matching timestamps. It is not AXG's 10fps export.

Suggested recording pair:

| Recording | Task | Label status | Archive bytes | Direct download |
|---|---|---|---:|---|
| 8_25 | Spiced Hot Chocolate | 0 error steps | 104186387 | https://huggingface.co/datasets/kimihiroh/promqa-cooking-frames/resolve/main/8_25.zip |
| 8_50 | Spiced Hot Chocolate | 6 error steps including missing steps | 81620289 | https://huggingface.co/datasets/kimihiroh/promqa-cooking-frames/resolve/main/8_50.zip |
| 8_3 | Spiced Hot Chocolate | inspect labels before selecting | 139283302 | https://huggingface.co/datasets/kimihiroh/promqa-cooking-frames/resolve/main/8_3.zip |

HEAD for the 8_50 HF URL returned **200**, Content-Length **81620289**, application/zip. Metadata is directly accessible via PowerShell Invoke-RestMethod (web tool rejects the HF API URL): `https://huggingface.co/api/datasets/kimihiroh/promqa-cooking-frames/tree/main?recursive=false`.

### Concrete 8_50 annotated cases

- 0.663–69.335s: adding sugar before milk/microwaving (order error).
- 69.335–92.281s: filling milk after sugar (order error).
- 96.078–159.797s: microwaving after adding sugar (order error).
- 163.264–185.879s: adding chocolate with spilling (technique error).
- 186.375–251.745s: final heating/serving, marked normal.
- Mixing and adding cinnamon have start/end = -1 and are missing-step annotations. **Do not sample negative timestamps or claim clip-level detection of a missing step without temporal context.**

For a first visual correctness demo, normal vs spilling-chocolate clips are easier to interpret than order errors, which require preceding context. Keep all GT error descriptions outside inference prompts; use them only for evaluation/reporting. The normal recipe instructions may be provided as task context. Do not use erroneous GT descriptions as generated subaction labels.

## Smallest honest experiment

1. Download the normal/error pair (~186MB compressed total), annotations and normal recipe task graph.
2. Inspect timestamps/frames; select a few normal and erroneous observed intervals, and sample three ordered frames per interval.
3. Run Qwen2.5-VL-7B with the official AXG reasoning prompt style. Save raw generation, prompt, frame filenames/timestamps, correctness score and explanation.
4. If automatic AXG construction is not feasible without author preprocessing, label the result **GT action-segment reasoning baseline/public-data demo**, not full AXG. A manually supplied recipe graph also is not the paper's automatically learned AXG.
5. Only claim an AXG pipeline when normal-training-derived subactions/features/graph and the official graph-to-video matching code have actually been executed. Keep train and test recording IDs disjoint.

## Additional tiny diagnostic assets

The dataset's website repository includes public 1.5–2.5MB video montages at `https://raw.githubusercontent.com/CaptainCook4D/captain-cook/main/static/videos/error_categories/`, including `technique_error_2.mp4`, `preparation_error.mp4` and `measurement_error.mp4`. These combine normal/error snippets, so they are useful for decode/model smoke tests but should not be treated as independent labeled evaluation recordings.

No large downloads were started during this investigation. Only this research document was written.
