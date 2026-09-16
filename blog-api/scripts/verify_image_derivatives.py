"""验证图片衍生档的生成与删除一致性。

不依赖运行中的服务，直接调用 service 层，覆盖两个关键不变量：
1. store_image 落盘后必定生成全部衍生档；
2. delete_image_files 删除主图时必定连衍生档一起清掉（不留孤儿）。

另外全站扫描一遍 static/，报告是否存在「衍生档没有对应主图」的孤儿文件。

用法（在 blog-api/ 目录下）：
    ../.venv/Scripts/python.exe scripts/verify_image_derivatives.py
"""
from __future__ import annotations

import io
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings  # noqa: E402
from app.services.image_service import (  # noqa: E402
    DERIVATIVE_EXT,
    DERIVATIVE_SPECS,
    delete_image_files,
    derivative_paths,
    is_derivative_name,
    store_image,
)

TEST_DIR = Path("_verify_derivatives")
results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"   {detail}" if detail else ""))


def make_jpeg(width: int = 1600, height: int = 900) -> bytes:
    """造一张纯色 JPEG，避免依赖仓库里的真实图片。"""
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (width, height), (122, 165, 247)).save(buf, "JPEG", quality=92)
    return buf.getvalue()


def find_orphan_derivatives(root: Path) -> list[Path]:
    """找出没有对应主图的衍生档（真正的孤儿）。"""
    orphans: list[Path] = []
    for p in root.rglob("*"):
        if not p.is_file() or not is_derivative_name(p.name):
            continue
        stem = p.name.split("@", 1)[0]
        siblings = [
            q for q in p.parent.glob(f"{stem}.*")
            if q.is_file() and not is_derivative_name(q.name)
        ]
        if not siblings:
            orphans.append(p)
    return orphans


def main() -> int:
    root = settings.static_path
    test_dir = root / TEST_DIR

    # 测试目录必须先回到干净状态：上一轮若异常退出留下文件，会污染
    # 「目录为空」「无残留」这两项断言，造成误报（已真实踩到过）。
    if test_dir.exists():
        stale = sorted(q.name for q in test_dir.glob("*"))
        shutil.rmtree(test_dir, ignore_errors=True)
        print(f"已清理上轮残留 {len(stale)} 个文件：{', '.join(stale[:3])}"
              + ("…" if len(stale) > 3 else ""))
    print(f"static 根目录: {root}\n")

    print("[1] 生成：store_image 应产出主图 + 全部衍生档")
    url, filename = store_image(make_jpeg(), TEST_DIR, "jpg")
    main_path = test_dir / filename
    expect_derivatives = derivative_paths(main_path)

    on_disk = sorted(q.name for q in test_dir.glob("*"))
    check("主图已落盘", main_path.is_file(), main_path.name)
    check("目录内恰好 1 主图 + 2 衍生档", len(on_disk) == 3,
          f"实际 {len(on_disk)} 个: {', '.join(on_disk)}")
    for path in expect_derivatives:
        check(f"衍生档已生成 {path.name}", path.is_file())

    from PIL import Image

    for (suffix, box), path in zip(DERIVATIVE_SPECS, expect_derivatives):
        if not path.is_file():
            continue
        with Image.open(path) as im:
            w, h = im.size
            check(
                f"{suffix} 尺寸不超过 {box}px 且为 WebP",
                max(w, h) <= box and im.format == "WEBP",
                f"{w}x{h} {im.format}",
            )
        check(f"{suffix} 体积小于主图", path.stat().st_size < main_path.stat().st_size,
              f"{path.stat().st_size // 1024}KB < {main_path.stat().st_size // 1024}KB")

    print("\n[2] 命名识别：is_derivative_name 应能区分主图与衍生档")
    for path in expect_derivatives:
        check(f"识别为衍生档 {path.name}", is_derivative_name(path.name))
    check("主图不被识别为衍生档", not is_derivative_name(main_path.name), main_path.name)

    print("\n[3] 删除：delete_image_files 应同时清掉主图与全部衍生档")
    removed = delete_image_files(url)
    check("删除返回 True", bool(removed))
    check("主图已删除", not main_path.is_file())
    for path in expect_derivatives:
        check(f"衍生档已删除 {path.name}", not path.is_file())
    leftovers = [q for q in (root / TEST_DIR).glob("*") if q.is_file()] if (root / TEST_DIR).is_dir() else []
    check("测试目录内无残留文件", not leftovers,
          ("残留: " + ", ".join(q.name for q in leftovers)) if leftovers else "")

    print("\n[4] 空目录回收：日期目录整目录为空时应被清掉")
    check("测试目录已自动回收", not (root / TEST_DIR).exists())

    print("\n[5] 全站孤儿扫描：不应存在没有主图的衍生档")
    orphans = find_orphan_derivatives(root)
    check("孤儿衍生档数量为 0", not orphans,
          "" if not orphans else f"{len(orphans)} 个，例如 {orphans[0]}")
    for p in orphans[:5]:
        print(f"      ! {p.relative_to(root).as_posix()}")

    # 兜底清理：即使断言失败也不要留下测试产物
    if (root / TEST_DIR).exists():
        shutil.rmtree(root / TEST_DIR, ignore_errors=True)

    failed = [r for r in results if not r[1]]
    print(f"\n{'=' * 52}")
    print(f"通过 {len(results) - len(failed)} 项，失败 {len(failed)} 项")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
