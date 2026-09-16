"""为 static/ 下已存在的图片补齐 WebP 衍生档（幂等，可重复执行）。

背景：图片衍生档（@1024 / @400）是后加的能力，只对「之后上传」的图片生效。
历史图片没有衍生档，前端若按约定请求衍生档就会 404 —— 本脚本负责一次性补齐。

安全性：
- 只**新增**衍生档文件，不修改、不删除任何原图；
- 已有衍生档的跳过（幂等，可反复执行）；
- 跳过 SVG / GIF，与上传链路的判断共用 needs_derivatives()，不会出现规则漂移；
- 默认 dry-run，只有显式加 --apply 才真正写盘。

用法（在 blog-api/ 目录下）：
    ../.venv/Scripts/python.exe scripts/backfill_image_derivatives.py           # 预览计划
    ../.venv/Scripts/python.exe scripts/backfill_image_derivatives.py --apply   # 实际生成
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

# 允许从 blog-api/ 根目录直接运行本脚本
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings  # noqa: E402
from app.services.image_service import (  # noqa: E402
    DERIVATIVE_EXT,
    DERIVATIVE_SPECS,
    is_derivative_name,
    needs_derivatives,
)


def list_main_images(root: Path) -> list[Path]:
    """列出所有需要衍生档的主图（排除衍生档自身与 svg/gif）。"""
    out: list[Path] = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if is_derivative_name(p.name):
            continue
        # 头像在上游已用 PIL 裁切压缩，不生成衍生档（与 store_image 调用方保持一致）
        if p.relative_to(root).parts[:1] == ("avatar",):
            continue
        if not needs_derivatives(p):
            continue
        out.append(p)
    return out


def missing_specs(main: Path) -> list[tuple[str, int]]:
    """该主图缺失的衍生档规格。"""
    return [
        (suffix, box)
        for suffix, box in DERIVATIVE_SPECS
        if not main.with_name(f"{main.stem}{suffix}.{DERIVATIVE_EXT}").is_file()
    ]


def run(apply: bool) -> int:
    root = settings.static_path
    if not root.is_dir():
        print(f"static 目录不存在：{root}")
        return 1

    try:
        from PIL import Image, ImageOps
    except ImportError:
        print("缺少 Pillow，无法生成衍生档。请先安装：pip install Pillow")
        return 1

    mains = list_main_images(root)
    pending: list[tuple[Path, list[tuple[str, int]]]] = []
    for main_path in mains:
        todo = missing_specs(main_path)
        if todo:
            pending.append((main_path, todo))

    total_files = sum(len(todo) for _, todo in pending)
    print(f"扫描根目录 : {root}")
    print(f"主图总数   : {len(mains)}")
    print(f"已有完整档 : {len(mains) - len(pending)}")
    print(f"待补齐主图 : {len(pending)}（共 {total_files} 个衍生档文件）")

    if not pending:
        print("\n无需处理，所有图片都已有衍生档。")
        return 0

    if not apply:
        print("\n预览（未写盘）。以下为前 10 项：")
        for main_path, todo in pending[:10]:
            rel = main_path.relative_to(root).as_posix()
            names = ", ".join(f"{main_path.stem}{s}.{DERIVATIVE_EXT}" for s, _ in todo)
            print(f"  {rel}  ->  {names}")
        if len(pending) > 10:
            print(f"  … 其余 {len(pending) - 10} 项")
        print("\n加 --apply 执行写入。")
        return 0

    created = 0
    failed = 0
    for main_path, todo in pending:
        try:
            data = main_path.read_bytes()
            with Image.open(io.BytesIO(data)) as im:
                im = ImageOps.exif_transpose(im)
                for suffix, box in todo:
                    out = im.copy()
                    out.thumbnail((box, box), Image.LANCZOS)
                    if out.mode not in ("RGB", "RGBA"):
                        out = out.convert("RGB")
                    out.save(
                        main_path.with_name(f"{main_path.stem}{suffix}.{DERIVATIVE_EXT}"),
                        "WEBP",
                        quality=80,
                        method=5,
                    )
                    created += 1
            print(f"  ok {main_path.relative_to(root).as_posix()}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  ! 失败 {main_path.relative_to(root).as_posix()}: {exc}")

    print(f"\n完成：生成 {created} 个衍生档，失败 {failed} 个")
    return 0 if failed == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="为历史图片补齐 WebP 衍生档")
    ap.add_argument("--apply", action="store_true", help="真正写入磁盘（默认只预览）")
    args = ap.parse_args()
    return run(args.apply)


if __name__ == "__main__":
    raise SystemExit(main())
