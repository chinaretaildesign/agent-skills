#!/usr/bin/env python3
"""agent-skills 上架自检：提交前必跑，全部通过才可交付。

用法：
    python scripts/validate_skill.py skills/<skill-name>

检查项：
  1. 目录名规范（小写字母/数字/连字符）
  2. SKILL.md 存在且 frontmatter 含 name / description / agent_created
  3. description 是否写清「做什么」+「什么场景触发」（长度下限提示）
  4. 敏感信息扫描（密钥、令牌、内网地址等）
  5. SKILL.md 篇幅（建议 < 5k 词，超出提示下沉到 references/）
  6. 官方校验器 package_skill.py（能找到就跑，找不到仅提示）

退出码：0 = 全部通过；1 = 有 error。
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

SENSITIVE_PATTERNS = [
    (r"sk-[A-Za-z0-9]{20,}", "疑似 OpenAI API Key"),
    (r"ghp_[A-Za-z0-9]{30,}", "GitHub 个人访问令牌"),
    (r"gho_[A-Za-z0-9]{30,}", "GitHub OAuth 令牌"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key"),
    (r"-----BEGIN (RSA |OPENSSH |EC |PRIVATE )?PRIVATE KEY-----", "私钥内容"),
    (r"\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "内网 IP"),
    (r"\b192\.168\.\d{1,3}\.\d{1,3}\b", "内网 IP"),
    (r"https?://[\w.-]*(corp|internal|intranet|oa|erp)[\w.-]*", "疑似内网地址"),
]

# 官方校验器候选位置（不同机器安装路径可能不同）
PACKAGER_CANDIDATES = [
    "F:/Workbuddy/resources/app.asar.unpacked/resources/plugins/"
    "workbuddy-builtin/skills/skill-creator/scripts/package_skill.py",
    "F:/Workbuddy/resources/app.asar.unpacked/resources/plugins/"
    "workbuddy-builtin/skills/skill-creator/scripts/quick_validate.py",
]


def find_packager():
    import os
    env = os.environ.get("SKILL_PACKAGER")
    if env and Path(env).exists():
        return Path(env)
    for c in PACKAGER_CANDIDATES:
        if Path(c).exists():
            return Path(c)
    return None


def parse_frontmatter(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.DOTALL)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        kv = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
        if kv:
            fm[kv.group(1).strip()] = kv.group(2).strip()
    return fm


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    skill_dir = Path(sys.argv[1])
    errors, warnings = [], []

    # 1. 目录名
    if not skill_dir.is_dir():
        print(f"[ERROR] 目录不存在：{skill_dir}")
        return 1
    if not NAME_RE.match(skill_dir.name):
        errors.append(
            f"目录名 '{skill_dir.name}' 不规范：只能用小写字母、数字、连字符"
        )

    # 2. SKILL.md 与 frontmatter
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        print(f"[ERROR] 缺少 SKILL.md：{skill_dir / 'SKILL.md'}")
        return 1

    text = skill_md.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)
    if fm is None:
        errors.append("SKILL.md 缺少 YAML frontmatter（文件开头需为 --- 包围的块）")
    else:
        for field in ("name", "description"):
            if not fm.get(field):
                errors.append(f"frontmatter 缺少必填字段：{field}")
        if "agent_created" not in fm:
            errors.append("frontmatter 缺少 agent_created 字段（应设为 true）")
        elif fm["agent_created"].lower() not in ("true", "yes"):
            warnings.append(f"agent_created = {fm['agent_created']}，建议设为 true")
        if fm.get("name") and fm["name"] != skill_dir.name:
            errors.append(
                f"frontmatter name '{fm['name']}' 与目录名 '{skill_dir.name}' 不一致"
            )
        desc = fm.get("description", "")
        if 0 < len(desc) < 30:
            warnings.append(
                f"description 仅 {len(desc)} 字，可能过短，"
                "建议写清「做什么」+「什么场景下触发」"
            )

    # 3. 敏感信息
    for path in skill_dir.rglob("*"):
        if not path.is_file() or path.suffix.lower() in {
            ".png", ".jpg", ".jpeg", ".gif", ".mp4", ".zip", ".woff", ".woff2"
        }:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for pattern, label in SENSITIVE_PATTERNS:
            if re.search(pattern, content):
                errors.append(f"疑似敏感信息（{label}）：{path.relative_to(skill_dir)}")
                break

    # 4. 篇幅
    body = text.split("---", 2)[-1] if fm else text
    words = len(body.split())
    cn_chars = len(re.findall(r"[\u4e00-\u9fff]", body))
    size = words + cn_chars
    if size > 5000:
        warnings.append(
            f"SKILL.md 篇幅约 {size} 词/字（>5000），建议把细节下沉到 references/"
        )

    # 5. 官方校验器
    packager = find_packager()
    if packager:
        try:
            with tempfile.TemporaryDirectory() as tmp:
                r = subprocess.run(
                    [sys.executable, str(packager), str(skill_dir), tmp],
                    capture_output=True, text=True, timeout=120,
                )
            if r.returncode == 0:
                print(f"[OK] 官方校验器通过（{packager.name}）")
            else:
                errors.append(
                    f"官方校验器未通过：{(r.stdout + r.stderr).strip()[:300]}"
                )
        except Exception as e:  # noqa: BLE001
            warnings.append(f"官方校验器执行异常：{e}")
    else:
        warnings.append(
            "未找到官方校验器 package_skill.py；"
            "可用环境变量 SKILL_PACKAGER 指定路径"
        )

    # 输出
    print(f"\n=== 自检结果：{skill_dir.name} ===")
    if errors:
        print(f"errors ({len(errors)}):")
        for e in errors:
            print(f"  ✗ {e}")
    if warnings:
        print(f"warnings ({len(warnings)}):")
        for w in warnings:
            print(f"  ! {w}")
    if not errors and not warnings:
        print("全部通过，可提交 ✓")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
