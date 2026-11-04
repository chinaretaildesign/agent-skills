#!/usr/bin/env python3
# 数字人开场版拼装（通用版）：
#   0-HOOK_SEC   = S2V 数字人段（480x832 → 放大补暗边成 4:3 + 叠 hero 标题/姓名/AI 角标）
#   HOOK_SEC-末尾 = 讲解型 slides 正文（build_template 产出的成片直接复用）
# 音频一条到底（全长 wav），开头 HOOK_SEC 的声音就是数字人说的 Hook 句
import subprocess, json, argparse
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--hook", default="H:/comfy-flux/ComfyUI/output/hook_s2v_00001-audio.mp4")
ap.add_argument("--body", default="H:/daijia-short-video/out/果切台_堆头逻辑_4x3_真声.mp4")
ap.add_argument("--audio", default="H:/daijia-short-video/vo_fruitcut.wav")
ap.add_argument("--manifest", default=None, help="用于自动取 Hook 时长")
ap.add_argument("--hook-sec", type=float, default=None, help="数字人段时长；默认读 manifest 第1段 end")
ap.add_argument("--out", default="H:/daijia-short-video/out/果切台_堆头逻辑_4x3_真声_数字人开场.mp4")
ap.add_argument("--title1", default="果切台", help="开场大标题第一行")
ap.add_argument("--title2", default="不是切水果的档口", help="开场大标题第二行")
args = ap.parse_args()

HOOK_SEC = args.hook_sec
if HOOK_SEC is None and args.manifest:
    mf = json.load(open(args.manifest, encoding="utf-8"))
    HOOK_SEC = round(mf["segments"][0]["end"], 3)
elif HOOK_SEC is None:
    HOOK_SEC = 6.162
print(f"[0] Hook 时长 = {HOOK_SEC}s")

WORK = Path("H:/daijia-short-video/out/_hookwork")
WORK.mkdir(parents=True, exist_ok=True)
HOOK, BODY, AUDIO, OUT = Path(args.hook), Path(args.body), Path(args.audio), Path(args.out)
W, H = 1440, 1080

def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print("[ffmpeg err]", (r.stderr or "")[-600:])
        raise SystemExit("ffmpeg failed")

# 1) 数字人段：480x832 → 放大到高 1080，左右补暗边成 4:3
run(["ffmpeg", "-y", "-i", str(HOOK), "-t", f"{HOOK_SEC:.3f}",
     "-vf", ("scale=-2:1080:flags=lanczos,"
            "pad=1440:1080:(ow-iw)/2:(oh-ih)/2:color=0x12151E"),
     "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
     "-pix_fmt", "yuv420p", "-r", "30", "-video_track_timescale", "90000",
     str(WORK / "hook_base.mp4")])

# 2) 开场叠字：hero 标题（两行）+ 姓名 + 头衔 + AI 角标
t1, t2 = args.title1, args.title2
run(["ffmpeg", "-y", "-i", str(WORK / "hook_base.mp4"),
     "-vf", (
       f"drawtext=fontfile='C\\:/Windows/Fonts/msyhbd.ttc':"
       f"text='{t1}':fontcolor=0xFFD640:fontsize=104:"
       f"x=(w-text_w)/2:y=120,"
       f"drawtext=fontfile='C\\:/Windows/Fonts/msyhbd.ttc':"
       f"text='{t2}':fontcolor=0xFFD640:fontsize=104:"
       f"x=(w-text_w)/2:y=250,"
       "drawtext=fontfile='C\\:/Windows/Fonts/msyh.ttc':"
       "text='黄耀贤 · 台湾老黄 · 零售与超市设计 35 年':fontcolor=0xF5F7FA:fontsize=40:"
       "x=(w-text_w)/2:y=920,"
       "drawbox=x=64:y=44:w=234:h=60:color=black@0.55:t=fill,"
       "drawtext=fontfile='C\\:/Windows/Fonts/msyhbd.ttc':"
       "text='AI 配音演示':fontcolor=white:fontsize=38:x=86:y=56"
     ),
     "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
     "-pix_fmt", "yuv420p", "-r", "30", str(WORK / "hook_titled.mp4")])

# 3) 正文：现有成片跳过前 HOOK_SEC 秒（正文页面从第 2 段配音开始）
BODY_SEC = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", str(BODY)], capture_output=True, text=True).stdout.strip())
run(["ffmpeg", "-y", "-ss", f"{HOOK_SEC:.3f}", "-i", str(BODY),
     "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
     "-pix_fmt", "yuv420p", "-r", "30", "-an", str(WORK / "body_part.mp4")])

# 4) 拼接：hook + body
lst = WORK / "vlist.txt"
lst.write_text("file 'hook_titled.mp4'\nfile 'body_part.mp4'\n", encoding="utf-8")
run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
     "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
     "-pix_fmt", "yuv420p", "-r", "30", "-an", str(WORK / "video_all.mp4")], cwd=WORK)

# 5) 合成整条音频（全长 wav，开头 HOOK_SEC 即数字人说的 Hook 句）
run(["ffmpeg", "-y", "-i", str(WORK / "video_all.mp4"), "-i", str(AUDIO),
     "-map", "0:v", "-map", "1:a", "-c:v", "copy",
     "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-shortest",
     "-movflags", "+faststart", str(OUT)])

d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "csv=p=0", str(OUT)], capture_output=True, text=True).stdout.strip()
print(f"[done] {OUT}  {d}s")
