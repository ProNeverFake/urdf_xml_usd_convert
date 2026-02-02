#!/usr/bin/env python3
"""
批量将 usd_assets 中所有 mobility.xml 转换为 USDA 格式
使用 IsaacLab SimulationApp
"""

import argparse
import os
from pathlib import Path

from isaacsim import SimulationApp

DEFAULT_ROOT_DIR = "/new_world/cockatiel/urdf_xml_usd_convert/usd_assets"


def main():
    parser = argparse.ArgumentParser(description="Batch convert MJCF/XML to USD")
    parser.add_argument("--fix-base", action="store_true", default=False, help="Fix base")
    parser.add_argument("--headless", action="store_true", default=True, help="Run headless")
    parser.add_argument(
        "--root",
        default=DEFAULT_ROOT_DIR,
        help="Root directory containing asset folders (default: usd_assets in repo)",
    )
    args, _ = parser.parse_known_args()

    root_dir = Path(args.root).resolve()
    if not root_dir.is_dir():
        raise SystemExit(f"Root directory not found: {root_dir}")

    print(f"Root: {root_dir}")

    simulation_app = SimulationApp({"headless": args.headless})

    print("Isaac Sim 已启动\n")

    from isaaclab.sim.converters import MjcfConverter, MjcfConverterCfg
    from isaaclab.utils.assets import check_file_path

    xml_files = []
    for item in root_dir.iterdir():
        if item.is_dir():
            xml_path = item / "mobility.xml"
            if xml_path.exists():
                xml_files.append(xml_path)

    print(f"找到 {len(xml_files)} 个 XML 文件\n")

    success = 0
    failed = 0

    for i, xml_path in enumerate(xml_files, 1):
        asset_name = xml_path.parent.name
        usda_path = xml_path.parent / f"{asset_name}.usda"

        print(f"[{i}/{len(xml_files)}] 处理: {asset_name}")

        try:
            mjcf_path = str(xml_path)
            usda_path = xml_path.parent / "mobility.usda"

            dest_path = str(usda_path)

            if not check_file_path(mjcf_path):
                print(f"  无效文件路径: {mjcf_path}")
                failed += 1
                continue

            mjcf_converter_cfg = MjcfConverterCfg(
                asset_path=mjcf_path,
                usd_dir=os.path.dirname(dest_path),
                usd_file_name=os.path.basename(dest_path),
                fix_base=args.fix_base,
                import_sites=False,
                force_usd_conversion=True,
                make_instanceable=False,
            )

            print(f"  Input: {xml_path.name}")
            print(f"  Output: {usda_path.name}")

            mjcf_converter = MjcfConverter(mjcf_converter_cfg)
            print(f"  Generated: {os.path.basename(mjcf_converter.usd_path)}")
            success += 1

        except Exception as e:
            print(f"  失败: {e}")
            failed += 1

    print(f"\n=== 统计 ===")
    print(f"成功: {success}")
    print(f"失败: {failed}")

    simulation_app.close()
    print("\n完成")


if __name__ == "__main__":
    main()
