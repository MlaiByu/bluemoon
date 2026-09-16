"""从 .env.docker.example 生成 Docker 部署用的 .env。

用法：
    python scripts/gen_docker_env.py            # 已存在则跳过
    python scripts/gen_docker_env.py --force    # 覆盖重建

被 scripts/docker-up.sh 与 scripts/docker-up.bat 共用，
避免在两个平台的脚本里各写一份随机密钥生成逻辑。
"""
from __future__ import annotations

import argparse
import re
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / ".env.docker.example"
TARGET = ROOT / ".env"

# 需要自动生成随机值的键。长度按用途选择：
#   SECRET_KEY  —— JWT 签名密钥，生产环境要求 >= 32 位
#   数据库密码  —— 仅容器网络内使用，token_urlsafe(18) 约 24 字符足够
GENERATED = {
    "SECRET_KEY": lambda: secrets.token_urlsafe(48),
    "MYSQL_PASSWORD": lambda: secrets.token_urlsafe(18),
    "MYSQL_ROOT_PASSWORD": lambda: secrets.token_urlsafe(18),
}


def fill(text: str, key: str, value: str) -> tuple[str, bool]:
    """只替换行首的 `KEY=` 赋值行，不碰注释里出现的同名文本。"""
    pattern = re.compile(rf"^{re.escape(key)}=.*$", re.MULTILINE)
    if not pattern.search(text):
        return text, False
    return pattern.sub(f"{key}={value}", text, count=1), True


def main() -> None:
    parser = argparse.ArgumentParser(description="生成 Docker 部署用的 .env")
    parser.add_argument("--force", action="store_true", help="已存在时覆盖重建")
    args = parser.parse_args()

    if not TEMPLATE.is_file():
        print(f"[错误] 找不到模板：{TEMPLATE}")
        sys.exit(1)

    if TARGET.exists() and not args.force:
        print(f"[跳过] {TARGET.name} 已存在，沿用现有配置（重建请加 --force）")
        return

    text = TEMPLATE.read_text(encoding="utf-8")
    missing: list[str] = []
    for key, gen in GENERATED.items():
        text, ok = fill(text, key, gen())
        if not ok:
            missing.append(key)

    TARGET.write_text(text, encoding="utf-8")

    print(f"[完成] 已生成 {TARGET.name}")
    for key in GENERATED:
        if key in missing:
            print(f"        [!!] 模板中未找到 {key}= 赋值行，未自动填充")
        else:
            print(f"        {key} = <已随机生成>")
    if missing:
        sys.exit(1)


if __name__ == "__main__":
    main()
