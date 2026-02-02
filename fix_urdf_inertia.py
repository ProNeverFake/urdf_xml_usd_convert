#!/usr/bin/env python3
"""
为 URDF 中缺少惯性属性的辅助链接添加虚拟惯性
"""

import os
import re
from pathlib import Path

DEFAULT_ROOT_DIR = "/new_world/cockatiel/urdf_xml_usd_convert/usd_assets"

INERTIAL_BLOCK = """	<inertial>
			<origin xyz="0 0 0"/>
			<mass value="1e-6"/>
			<inertia ixx="1e-10" ixy="0" ixz="0" iyy="1e-10" iyz="0" izz="1e-10"/>
		</inertial>"""

def fix_urdf_file(path):
    """修复单个 URDF 文件"""
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    original_lines = lines.copy()
    modified = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        # 匹配 <link name="link_X_helper"/>
        if stripped.startswith('<link name="link_') and stripped.endswith('/>'):
            # 提取 link 名称
            match = re.search(r'name="([^"]+)"', stripped)
            if match:
                link_name = match.group(1)
                indent = line[:len(line) - len(line.lstrip())]

                new_lines = [
                    f'{indent}<link name="{link_name}">\n',
                    f'{indent}{INERTIAL_BLOCK}\n',
                    f'{indent}</link>\n'
                ]
                lines[i:i+1] = new_lines
                modified = True

    if modified:
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

    return modified


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fix missing inertials in URDF helper links")
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

    urdf_files = []
    for item in root_dir.iterdir():
        if item.is_dir():
            urdf_path = item / "mobility.urdf"
            if urdf_path.exists():
                urdf_files.append(urdf_path)

    print(f"找到 {len(urdf_files)} 个 URDF 文件")

    fixed = 0
    for urdf_path in urdf_files:
        if fix_urdf_file(urdf_path):
            print(f"[FIXED] {urdf_path.name}")
            fixed += 1

    print(f"\n=== 统计 ===")
    print(f"已修复: {fixed}/{len(urdf_files)}")


if __name__ == "__main__":
    main()
