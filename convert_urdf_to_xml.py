#!/usr/bin/env python3
"""
将 usd_assets 中所有 mobility.urdf 转换为 XML 格式
使用 urdf2mjcf 工具
"""

import os
import subprocess
from pathlib import Path

DEFAULT_ROOT_DIR = "/new_world/cockatiel/urdf_xml_usd_convert/usd_assets"


def convert_urdf_to_xml(urdf_path):
    """将 URDF 转换为 XML"""
    dir_path = os.path.dirname(urdf_path)
    urdf_name = os.path.basename(urdf_path)
    xml_name = urdf_name.replace('.urdf', '.xml')

    # 切换到模型目录执行转换
    cmd = ['urdf2mjcf', urdf_name, xml_name]

    try:
        result = subprocess.run(
            cmd,
            cwd=dir_path,
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            return True, f"成功: {urdf_name} -> {xml_name}"
        else:
            return False, f"失败: {urdf_name}\n  stderr: {result.stderr}"
    except subprocess.TimeoutExpired:
        return False, f"超时: {urdf_name}"
    except Exception as e:
        return False, f"错误: {urdf_name}, {e}"


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Batch convert URDF to XML using urdf2mjcf")
    parser.add_argument(
        "--root",
        default=DEFAULT_ROOT_DIR,
        help="Root directory containing asset folders (default: usd_assets in repo)",
    )
    args = parser.parse_args()

    root_dir = Path(args.root).resolve()
    if not root_dir.is_dir():
        raise SystemExit(f"Root directory not found: {root_dir}")

    print(f"Root: {root_dir}")

    # 查找所有 mobility.urdf 文件
    urdf_files = []
    for item in root_dir.iterdir():
        if item.is_dir():
            urdf_path = item / "mobility.urdf"
            if urdf_path.exists():
                urdf_files.append(urdf_path)

    print(f"找到 {len(urdf_files)} 个 URDF 文件")

    success = 0
    failed = 0

    for i, urdf_path in enumerate(urdf_files, 1):
        print(f"[{i}/{len(urdf_files)}] ", end="")
        ok, msg = convert_urdf_to_xml(urdf_path)
        print(msg)
        if ok:
            success += 1
        else:
            failed += 1

    print(f"\n=== 统计 ===")
    print(f"成功: {success}")
    print(f"失败: {failed}")


if __name__ == "__main__":
    main()
