---
name: koubo-video-pipeline
description: 黄耀贤（台湾老黄）口播短视频生产线。将「选题→写稿→真声配音→讲解型渲染→数字人开场」串成可复用流程，默认产出「数字人真人开场+讲解型正文」4:3 成片。Trigger on 口播视频 / 短视频 / 数字人口播 / 老黄口播 / 讲解型视频 / 出片 / 跑一条口播 / 生鲜超市口播 等明确要做口播类视频的请求。
agent_created: true
---

# 口播视频生产线（数字人开场版）

## 目的
把黄耀贤（台湾老黄，零售与超市设计 35 年）的口播短视频，从选题到成片串成可复用流程。
默认产出：**Wan2.2 S2V 数字人真人开场（6~8s，口型对齐 Hook 句）+ 讲解型 slides 正文**，4:3（1440×1080）主推规格，含 AIGC 合规三件套。

## 硬约束（不可违背）
- **配音音色**：一律用真声模型 `1014894cb377471987e8ace757b39f42`（睿智成熟男声），绝不用库里公共声线（建国等），除非用户点名。
- **语速**：`--speed-scale 1.2` 硬编码默认（用户实测确认的最终节奏）+ 逐句内容变速（已在 `fish_tts_ts.py` 内置，按疑问/感叹/强调词/推进词/长短句定速）。
- **合规红线**：不出现绝对化用语（最/第一/唯一/绝对）；数据用「行业经验口径 [需验证]」「我见过的大多」；不贬低同行、不承诺爆单。
- **出镜照**：固定用 `H:\开发国内设计网站项目\口播出镜照_老黄_9x16.jpg`（1080×1920，已合成）。
- **合规三件套**：GB45438 AIGC 隐式元数据（build_template 已写）+ 画面「AI 配音演示」角标 + 右下角常驻「AI 配音演示·内容由本人讲解」。

## 依赖与环境
> **本 skill 是生产线编排层**：它串联本机已有的工程脚本，**自身不含视频/AI 模型权重**。clone 到别的机器后，需按本机实际路径调整下方「脚本绝对路径」。

**Python 包**：`pip install -r requirements.txt`（仅 `requests==2.34.2`）；torch / ComfyUI / Fish Audio / 火山方舟均为本地运行时环境，不通过 pip 直装。

- **Python**：`C:\Users\15051\AppData\Local\Programs\Python\Python311\python.exe`（cp311，torch 2.9+cu128 支持 RTX 4070）
- **ComfyUI（S2V 用）**：端口 8189。启动：`cd /h/comfy-flux/ComfyUI && H:/comfy-flux/venv/Scripts/python.exe main.py --port 8189 --lowvram`（约 54s 起；**后台进程会被会话中断杀掉，重跑前先 curl 探测，掉了就重启**）
- **脚本绝对路径**：
  - 写稿：`H:\开发国内设计网站项目\ark_call.py`（doubao 端点 `ep-20261102162305-6nmml`）
  - 配音+词级时间戳：`H:\fish-audio-voiceover\fish_tts_ts.py`
  - 配音变体（无时间戳）：`H:\fish-audio-voiceover\fish_voiceover.py`
  - 查重：`H:\daijia-short-video\topic_guard.py`
  - 渲染：`H:\daijia-short-video\build_template.py`
  - S2V 开场生成：`H:\comfy-flux\gen_hook_s2v.py`
  - 拼装：`H:\daijia-short-video\build_with_hook.py`
  - 选题台账：`H:\daijia-short-video\topics.json`
  - 视觉质检：`python /h/tools/vision.py <帧> --ask "..."`
- **代理坑**：所有外部 API（ark/fish）走脚本内置清代理；ComfyUI 是本地 127.0.0.1，curl 时设 `proxies={"http":None}` 或 `--noproxy 127.0.0.1`。

## 触发后执行 SOP（5+1 步）

### Step 0 · 环境自检
```
curl -s --max-time 3 http://127.0.0.1:8189/system_stats   # 空=ComfyUI 掉线，按依赖启动
```
缺出镜照/真声 ID 时停下问用户（这两个已固化，正常不缺）。

### Step 1 · 选题查重（必跑，硬性规则 6）
```
cd /h/daijia-short-video && python topic_guard.py "<选题关键词 如:果切台 高毛利 堆头 损耗>"
```
- **PASS** → 继续。
- **REWORK** → 看是否与已出片（V001 熟食区三坑 / I004 果切台等）撞角度。若本稿是台账里注册的角度且补充了图纸级新数据（尺寸/温度/层数等），可放行，并在 `topics.json` 该条记 `guard_note`；否则停下跟用户确认换角度。

### Step 2 · 写稿（豆包，带人设+情绪标签+合规）
调 `ark_call.py --model doubao`，prompt 必须含：
- 人设：「黄耀贤，台湾老黄，零售与超市设计 35 年（1991 家乐福→TESCO 全国采购总监→2008 自创设计公司）」
- 选题角度（锁定，避开已讲过的：胖东来、湿区隔离、生熟动线、面积配比）
- 格式：每段一行、段首情绪标签 `[happy][excited][serious][whisper][emphasis]`；结构 Hook（反常识开头）→ 论据 → 图纸级细节 3 条（具体尺寸/位置/数字）→ 金句 → CTA（评论区留「图纸」）；字数 180–210 字（语速 1.2× 约 50–55s）
- 合规红线（见上）
- **长稿请求偶尔被会话 SIGTERM** → 用 `--prompt-file` + 后台跑：`python ark_call.py --model doubao --max-tokens 1200 --prompt-file prompt.txt > raw.txt 2>&1 &`，再读 raw.txt
- 压缩到目标字数后存 `H:\daijia-short-video\scripts_<选题>.txt`
- **⏸ 暂停点**：把稿子给用户过目，确认角度/合规无误再进配音。

### Step 3 · 真声配音 + 词级时间戳（出视频必须走这个）
```
cd /h/fish-audio-voiceover && python fish_tts_ts.py \
  --script "H:/daijia-short-video/scripts_<选题>.txt" \
  --voice-id 1014894cb377471987e8ace757b39f42 \
  --speed-scale 1.2 \
  --out "H:/daijia-short-video/vo_<选题>.wav" \
  --manifest "H:/daijia-short-video/vo_<选题>.json"
```
产出 `.wav` + `.json`（segments 分段 + words 词级时间轴，逐句 segment 已对齐）。

### Step 4 · slides 渲染（讲解型正文）
写 `H:\daijia-short-video\template\slides_<选题>_4x3.json`，**版式坑**（实测踩过）：
- hero 页 `subtitle` 锚点要覆盖前 2 句，保证首页 ≥4s（否则首页被压成 0.x 秒）
- **stat 页**标签/小注勿过长，否则被右侧人物栏裁断 → 缩短 label/note
- **bullets 页不显示 image 字段**（模板不支持）→ 效果图挪进 `grid` 页凑 2×2
- **cta 页标题用单行**，两行会被按钮遮挡
- 实拍图用绝对路径（如 `I:/Desktop/大买家/...` 或 `assets/实拍-20261102/...`）
```
cd /h/daijia-short-video && python build_template.py \
  --template template/template_4x3.json \
  --slides template/slides_<选题>_4x3.json \
  --manifest vo_<选题>.json \
  --out "<选题>_4x3_真声.mp4"
```

### Step 5 · 数字人开场（S2V）+ 拼装
1. 取 manifest 第 1 段 `end` 作为 Hook 时长 `HOOK_SEC`（I004 实测 6.162s）。
2. `gen_hook_s2v.py` 内部已切前 `HOOK_SEC` 秒配音→97 帧@16fps→480×832→输出 `ComfyUI/output/hook_s2v_00001-audio.mp4`。如要通用，改脚本 `HOOK_SEC` 为读 manifest 或加 `--hook-sec` 参数。
3. **⏸ 暂停点**：抽帧 `ffmpeg -ss 3 -i hook_s2v...mp4 -frames:v 1 f.png` → `python /h/tools/vision.py f.png --ask "有无扭曲变形/质量打分"` 确认无变形（合格线 7+ 分）。
4. 拼装：`cd /h/daijia-short-video && python build_with_hook.py`（数字人段放大补暗边成 4:3 → drawtext 叠 hero 标题/姓名/AI 角标 → 正文取现有成片 `HOOK_SEC` 之后 → 整条音频用 `vo_<选题>.wav` 全长对齐）。
5. 成品：`H:\daijia-short-video\out\<选题>_4x3_真声_数字人开场.mp4`

### Step 6 · 收尾质检 + 台账
- 抽帧查关键页（首/中/尾）有无文字溢出、遮挡、变形。
- `topics.json` 该条 `status` 改 `produced`，记 `video` 路径与 `produced_at`。
- **建议发布前过 lingyi 违禁词预检（簇4）**，成片仅作管线验证不可直接发（除非 REWORK 已凭新数据放行）。

## 关键暂停点汇总
1. Step 2 写稿后：稿子给用户过目（角度/合规）
2. Step 5 S2V 渲染后：视觉质检数字人画质
3. 任何排版遮挡（stat/cta 页）：修 slides 重渲

## 已知短板（下次迭代）
- 数字人段原生 480p 放大到 1080 偏软 → 待 SeedVR2 超分（仓库已排）。
- ComfyUI 后台进程会被会话中断杀掉 → 重跑先探测重启。
- `gen_hook_s2v.py` / `build_with_hook.py` 已参数化：`--hook-sec` / `--manifest`（自动读第1段 end）/ `--title1 --title2` / `--out` / `--body` / `--audio`，换选题直接传参无需改码。
- 长稿豆包请求偶发 SIGTERM → 用 prompt-file 后台规避（已验证）。

## 维护
- 新增选题角度 → 先登记 `topics.json`（防查重撞车）。
- 脚本路径/真声 ID/出镜照变更 → 同步改本文件「硬约束」「依赖」两节。
- 接 auto-skill-dispatch：触发词见 description，视频类请求会被自动路由到本 skill。
