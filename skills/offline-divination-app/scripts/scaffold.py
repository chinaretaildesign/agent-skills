#!/usr/bin/env python3
"""生成一个可离线运行的占卜 App 最小骨架。

用法:
    python scaffold.py ./my-divination
    python scaffold.py ./my-divination --title "合作占卜"
    python scaffold.py ./my-divination --force      # 目标非空时也写入

产出:
    index.html                                  入口（双击即可运行）
    assets/css/style.css                        样式（含暗色与减少动效）
    assets/js/data/tarot.js                     22 张大阿尔卡纳（骨架版）
    assets/js/data/spreads.js                   2 套牌阵
    assets/js/engine/divination.js              抽牌 + 解读 + 评分
    assets/js/app.js                            界面交互

骨架只是起点：按 references/tarot-engine.md 补全 78 张、按
references/bazi-wuxing.md 接入五行合参、按 references/packaging.md 打包成 App。
"""

import argparse
import shutil
import sys
from pathlib import Path

PLACEHOLDER = "__APP_TITLE__"


def main():
    ap = argparse.ArgumentParser(
        description="生成离线占卜 App 的最小可运行骨架",
        epilog="生成后可直接双击 index.html 预览，再跑 check_offline.py 体检",
    )
    ap.add_argument("target", help="要生成到的目录（不存在会自动创建）")
    ap.add_argument("--title", default="合作占卜", help="应用名称，默认「合作占卜」")
    ap.add_argument("--force", action="store_true",
                    help="目标目录非空时仍然写入（会覆盖同名文件）")
    args = ap.parse_args()

    target = Path(args.target).expanduser().resolve()
    template = Path(__file__).resolve().parent.parent / "assets" / "scaffold"

    if not template.is_dir():
        print(f"模板目录缺失: {template}", file=sys.stderr)
        return 1

    if target.exists() and any(target.iterdir()) and not args.force:
        print(f"目标目录非空: {target}", file=sys.stderr)
        print("为安全起见不覆盖已有文件。确认要写入请加 --force", file=sys.stderr)
        return 2

    target.mkdir(parents=True, exist_ok=True)

    created = []
    for src in sorted(template.rglob("*")):
        if not src.is_file():
            continue
        rel = src.relative_to(template)
        dst = target / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if rel.suffix.lower() in (".html", ".htm"):
            text = src.read_text(encoding="utf-8").replace(PLACEHOLDER, args.title)
            dst.write_text(text, encoding="utf-8")
        else:
            shutil.copyfile(src, dst)
        created.append(rel.as_posix())

    print(f"\n已生成骨架: {target}")
    print(f"应用名称: {args.title}")
    print(f"文件 {len(created)} 个:")
    for rel in created:
        print(f"  + {rel}")

    print("\n下一步:")
    print("  1. 双击 index.html 预览（无需服务器，断网可用）")
    print("  2. python check_offline.py " + str(target) + "   # 体检")
    print("  3. 按 references/ 补全 78 张牌库、五行合参、原生打包")
    return 0


if __name__ == "__main__":
    sys.exit(main())
