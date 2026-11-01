#!/usr/bin/env python3
"""离线合规体检：检查一个占卜类 Web/App 项目是否真的能断网运行。

用法:
    python check_offline.py <项目目录>
    python check_offline.py <项目目录> --max-kb 5120
    python check_offline.py <项目目录> --json

检查项:
    1. 入口文件是否存在（index.html）
    2. HTML/CSS/JS 中的远程资源引用（CDN、远程字体、fetch 远程接口）
    3. 绝对路径资源引用（打包后会 404）
    4. 产物目录混入 node_modules / .git / 测试文件
    5. AGPL / GPL 依赖（闭源分发风险）
    6. <script> 引用的本地 vendor 文件是否真的存在
    7. 产物体积

退出码: 0 = 无 ERROR；1 = 存在 ERROR。WARN 不影响退出码。
仅做只读检查，不修改任何文件。
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", "dist", "build", ".idea", ".vscode",
             "__pycache__", "coverage", ".pytest_cache"}

TEXT_EXT = {".html", ".htm", ".js", ".mjs", ".css", ".json", ".svg"}

CDN_HINTS = ("unpkg.com", "jsdelivr.net", "cdnjs.cloudflare.com",
             "fonts.googleapis.com", "fonts.gstatic.com", "googletagmanager.com",
             "ajax.googleapis.com", "bootstrapcdn.com")

RE_HTML_REMOTE = re.compile(r'(?:src|href)\s*=\s*["\'](https?://[^"\']+)["\']', re.I)
RE_CSS_REMOTE = re.compile(r'url\(\s*["\']?(https?://[^)"\']+)', re.I)
RE_JS_FETCH = re.compile(r'(?:fetch|importScripts)\s*\(\s*["\'`](https?://[^"\'`]+)', re.I)
RE_JS_IMPORT = re.compile(r'from\s+["\'](https?://[^"\']+)["\']', re.I)
RE_ABS_PATH = re.compile(r'(?:src|href)\s*=\s*["\']/(?!/)[^"\']*["\']', re.I)
RE_SCRIPT_SRC = re.compile(r'<script[^>]+src\s*=\s*["\']([^"\']+)["\']', re.I)

COPYLEFT = ("agpl", "gpl-3", "gpl-2", "gplv3", "gplv2", "sspl", "cc-by-nc")

TEST_PATTERNS = ("smoke.js", "test.js", "spec.js", ".test.", ".spec.")


class Report:
    def __init__(self):
        self.errors = []
        self.warns = []
        self.infos = []

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warns.append(msg)

    def info(self, msg):
        self.infos.append(msg)

    def dump(self, as_json=False):
        if as_json:
            print(json.dumps({
                "ok": not self.errors,
                "errors": self.errors,
                "warnings": self.warns,
                "info": self.infos,
            }, ensure_ascii=False, indent=2))
            return
        print(f"\n=== 离线体检: {self.target} ===")
        if self.infos:
            print("\n[信息]")
            for m in self.infos:
                print(f"  - {m}")
        if self.warns:
            print(f"\n[警告 {len(self.warns)}]")
            for m in self.warns:
                print(f"  ! {m}")
        if self.errors:
            print(f"\n[错误 {len(self.errors)}]")
            for m in self.errors:
                print(f"  x {m}")
            print("\n结论: 未通过，修复错误后再打包。")
        else:
            print("\n结论: 通过，可断网运行。" if not self.warns
                  else "\n结论: 通过（有警告，建议逐条确认）。")


def iter_text_files(root, report):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in TEXT_EXT:
            yield path


def check_entry(root, report):
    for name in ("index.html", "index.htm"):
        if (root / name).exists():
            report.info(f"入口文件存在: {name}")
            return True
    report.error("找不到入口文件 index.html（确认目录是项目根目录或构建产物目录）")
    return False


def check_remote_refs(root, report):
    for path in iter_text_files(root, report):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = path.relative_to(root)
        hits = []
        if path.suffix.lower() in (".html", ".htm"):
            hits += RE_HTML_REMOTE.findall(text)
        if path.suffix.lower() == ".css":
            hits += RE_CSS_REMOTE.findall(text)
        if path.suffix.lower() in (".js", ".mjs"):
            hits += RE_JS_FETCH.findall(text)
            hits += RE_JS_IMPORT.findall(text)
        for url in hits:
            if any(d in url for d in CDN_HINTS):
                report.error(f"引用了 CDN 资源（断网必挂）: {rel} -> {url}")
            else:
                report.warn(f"存在远程引用（确认是否可选）: {rel} -> {url}")


def check_abs_paths(root, report):
    for path in iter_text_files(root, report):
        if path.suffix.lower() not in (".html", ".htm"):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in RE_ABS_PATH.finditer(text):
            report.error(
                f"绝对路径引用（App 内会 404）: "
                f"{path.relative_to(root)} -> {m.group(0)[:80]}"
            )


def check_vendor_scripts(root, report):
    for path in iter_text_files(root, report):
        if path.suffix.lower() not in (".html", ".htm"):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for src in RE_SCRIPT_SRC.findall(text):
            # 远程引用与绝对路径各有专门检查项，这里只管本地相对路径
            if src.startswith(("http://", "https://", "//", "/", "data:")):
                continue
            target = (path.parent / src).resolve()
            if not target.exists():
                report.error(f"脚本文件不存在: {src}（在 {path.relative_to(root)} 中被引用）")


def check_artifacts(root, report):
    if (root / "node_modules").exists():
        report.warn("目录内有 node_modules：打包时应排除（体积暴涨且含源码副本）")
    gitdir = root / ".git"
    if gitdir.exists():
        report.warn("目录内有 .git：构建产物应排除")
    strays = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        name = path.name.lower()
        if any(p in name for p in TEST_PATTERNS):
            strays.append(str(path.relative_to(root)))
    if strays:
        report.warn(f"产物中混入测试文件 {len(strays)} 个: {', '.join(strays[:3])}")


def check_size(root, report, max_kb):
    total = 0
    count = 0
    for path in root.rglob("*"):
        if path.is_file() and not any(p in SKIP_DIRS for p in path.parts):
            total += path.stat().st_size
            count += 1
    kb = total / 1024
    report.info(f"文件 {count} 个，合计 {kb:.1f} KB")
    if kb > max_kb:
        report.warn(f"产物体积 {kb:.0f} KB 超过阈值 {max_kb} KB，首屏加载会变慢")


def check_licenses(root, report):
    pkg = root / "package.json"
    if not pkg.exists():
        report.info("未找到 package.json，跳过依赖许可证检查")
        return
    try:
        data = json.loads(pkg.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        report.warn("package.json 解析失败，跳过依赖许可证检查")
        return
    deps = list(data.get("dependencies", {}).keys())
    if not deps:
        report.info("package.json 无 dependencies")
        return
    node_modules = root / "node_modules"
    checked = 0
    for name in deps:
        meta = node_modules / name / "package.json"
        if not meta.exists():
            report.warn(f"依赖 {name} 未安装，无法核查许可证")
            continue
        try:
            m = json.loads(meta.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            report.warn(f"依赖 {name} 的 package.json 解析失败")
            continue
        checked += 1
        lic = m.get("license") or m.get("licenses") or "UNKNOWN"
        lic_str = lic if isinstance(lic, str) else json.dumps(lic, ensure_ascii=False)
        low = lic_str.lower()
        if any(c in low for c in COPYLEFT):
            report.error(
                f"依赖 {name} 的许可证为 {lic_str}：闭源分发前必须更换或隔离"
            )
        elif low in ("unknown", ""):
            report.warn(f"依赖 {name} 许可证未知，需人工确认")
        else:
            report.info(f"依赖 {name} 许可证: {lic_str}")
    report.info(f"已核查 {checked}/{len(deps)} 个直接依赖")


def main():
    ap = argparse.ArgumentParser(
        description="离线合规体检：确认项目能断网运行、无许可证风险",
        epilog="示例: python check_offline.py ./my-app",
    )
    ap.add_argument("target", help="项目根目录或构建产物目录")
    ap.add_argument("--max-kb", type=int, default=5120,
                    help="产物体积上限（KB），默认 5120")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    args = ap.parse_args()

    root = Path(args.target).expanduser().resolve()
    if not root.is_dir():
        print(f"目录不存在: {root}", file=sys.stderr)
        return 1

    report = Report()
    report.target = str(root)

    if check_entry(root, report):
        check_remote_refs(root, report)
        check_abs_paths(root, report)
        check_vendor_scripts(root, report)
        check_artifacts(root, report)
        check_licenses(root, report)
        check_size(root, report, args.max_kb)
    else:
        # 目录可能选错（比如选到了上级），仍给出体积信息便于判断
        check_size(root, report, args.max_kb)

    report.dump(as_json=args.json)
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
