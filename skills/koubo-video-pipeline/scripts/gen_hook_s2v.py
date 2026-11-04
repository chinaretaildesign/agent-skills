#!/usr/bin/env python3
# Wan2.2 S2V 数字人开场段生成（口播第1句，口型对齐配音前 N 秒）
# 输入：个人.jpg（出镜照，需放 ComfyUI/input）+ hook_audio.wav（前 N 秒配音）
# 输出：ComfyUI/output/<prefix>_00001-audio.mp4（480x832，含音轨）
import requests, json, time, sys, subprocess, argparse
from pathlib import Path

BASE = "http://127.0.0.1:8189"
s = requests.Session()
s.proxies = {"http": None, "https": None}
requests.packages.urllib3.disable_warnings()

ap = argparse.ArgumentParser()
ap.add_argument("--audio", default="H:/daijia-short-video/vo_fruitcut.wav", help="全长配音 wav")
ap.add_argument("--manifest", default="H:/daijia-short-video/vo_fruitcut.json", help="对应词级时间戳 json")
ap.add_argument("--hook-sec", type=float, default=None, help="开场时长；默认读 manifest 第1段 end")
ap.add_argument("--out-prefix", default="hook_s2v")
ap.add_argument("--seed", type=int, default=42)
args = ap.parse_args()

# Hook 时长：默认取 manifest 第1段 end（口播第1段即 Hook 句）
HOOK_SEC = args.hook_sec
if HOOK_SEC is None:
    mf = json.load(open(args.manifest, encoding="utf-8"))
    HOOK_SEC = round(mf["segments"][0]["end"], 3)
print(f"[0] Hook 时长 = {HOOK_SEC}s")

src = Path(args.audio)
hook = Path("H:/comfy-flux/ComfyUI/input/hook_audio.wav")
subprocess.run(["ffmpeg", "-y", "-i", str(src), "-t", f"{HOOK_SEC:.3f}",
                "-c:a", "pcm_s16le", "-ar", "16000", "-ac", "1", str(hook)],
               check=True, capture_output=True)
print(f"[1] hook 音频已切出 {HOOK_SEC}s")

# 帧数：16fps，取 8n+1 覆盖音频
LENGTH = 8 * round(HOOK_SEC * 16 / 8) + 1
POS = ("a middle-aged East Asian man speaking naturally to the camera, "
       "subtle head movement, professional attire, bright even lighting, "
       "sharp focus, realistic skin texture, talking head video")
NEG = "色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量"
W, H = 480, 832

prompt = {
    "1": {"class_type": "LoadImage", "inputs": {"image": "个人.jpg"}},
    "2": {"class_type": "LoadAudio", "inputs": {"audio": "hook_audio.wav"}},
    "3": {"class_type": "CLIPLoader", "inputs": {"clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "type": "wan", "device": "default"}},
    "4": {"class_type": "VAELoader", "inputs": {"vae_name": "wan_2.1_vae_fp8_e4m3fn.safetensors"}},
    "5": {"class_type": "UNETLoader", "inputs": {"unet_name": "wan2.2_s2v_14B_fp8_scaled.safetensors", "weight_dtype": "default"}},
    "6": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["5", 0], "lora_name": "Wan22\\wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors", "strength_model": 1.0}},
    "7": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["6", 0], "shift": 8.0}},
    "8": {"class_type": "AudioEncoderLoader", "inputs": {"audio_encoder_name": "wav2vec2_large_english_fp16.safetensors"}},
    "9": {"class_type": "AudioEncoderEncode", "inputs": {"audio_encoder": ["8", 0], "audio": ["2", 0]}},
    "10": {"class_type": "CLIPTextEncode", "inputs": {"text": POS, "clip": ["3", 0]}},
    "11": {"class_type": "CLIPTextEncode", "inputs": {"text": NEG, "clip": ["3", 0]}},
    "12": {"class_type": "WanSoundImageToVideo", "inputs": {
        "positive": ["10", 0], "negative": ["11", 0], "vae": ["4", 0],
        "width": W, "height": H, "length": LENGTH, "batch_size": 1,
        "audio_encoder_output": ["9", 0], "ref_image": ["1", 0]}},
    "13": {"class_type": "KSampler", "inputs": {
        "model": ["7", 0], "positive": ["12", 0], "negative": ["12", 1], "latent_image": ["12", 2],
        "seed": args.seed, "steps": 4, "cfg": 1.0, "sampler_name": "uni_pc", "scheduler": "simple", "denoise": 1.0}},
    "14": {"class_type": "VAEDecode", "inputs": {"samples": ["13", 0], "vae": ["4", 0]}},
    "15": {"class_type": "VHS_VideoCombine", "inputs": {
        "images": ["14", 0], "audio": ["2", 0], "frame_rate": 16, "loop_count": 0,
        "filename_prefix": args.out_prefix, "format": "video/h264-mp4", "pingpong": False, "save_output": True}},
}

print("[2] 提交 S2V 任务 ...")
r = s.post(f"{BASE}/prompt", json={"prompt": prompt, "client_id": "hook_gen"}, timeout=30)
if r.status_code != 200:
    print("[!] 提交失败:", r.status_code, r.text[:500]); sys.exit(1)
pid = r.json()["prompt_id"]
print(f"[+] prompt_id = {pid}")
start = time.time()
while True:
    try:
        h = s.get(f"{BASE}/history/{pid}", timeout=10).json()
    except Exception:
        h = {}
    if pid in h:
        for nid, o in h[pid].get("outputs", {}).items():
            for g in o.get("gifs", []):
                print(f"[+] 输出: {g['filename']} (subfolder={g.get('subfolder','')})")
                print(f"[done] 用时 {int(time.time()-start)}s")
                sys.exit(0)
        print("[!] 完成但无视频输出"); sys.exit(3)
    el = int(time.time() - start)
    if el % 60 == 0:
        print(f"    ... {el}s")
    time.sleep(10)
    if el > 3600:
        print("[!] 超时"); sys.exit(2)
