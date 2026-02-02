#!/usr/bin/env python3
"""
批量修复 usd_assets 中所有 mobility.xml 文件的路径
将绝对路径转换为相对路径
"""

import os
import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from change_format.fix_xml import update_mjcf_file_paths_auto

DEFAULT_ROOT_DIR = "/new_world/cockatiel/urdf_xml_usd_convert/usd_assets"


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fix XML mesh paths in batch")
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

    xml_files = []
    for item in root_dir.iterdir():
        if item.is_dir():
            xml_path = item / "mobility.xml"
            if xml_path.exists():
                xml_files.append(xml_path)

    print(f"找到 {len(xml_files)} 个 XML 文件")

    success = 0
    skipped = 0
    failed = 0

    for i, xml_path in enumerate(xml_files, 1):
        print(f"[{i}/{len(xml_files)}] 处理: {xml_path.parent.name}/mobility.xml", end=" ... ")

        try:
            result = update_mjcf_file_paths_auto(str(xml_path), str(xml_path))
            if "未在文件中找到任何包含 '/objs/' 的 mesh 路径" in result:
                print("跳过（无 objs 路径）")
                skipped += 1
            else:
                print("完成")
                success += 1
        except Exception as e:
            print(f"失败: {e}")
            failed += 1

    print(f"\n=== 统计 ===")
    print(f"成功: {success}")
    print(f"跳过: {skipped}")
    print(f"失败: {failed}")


if __name__ == "__main__":
    main()
