#!/usr/bin/env python3
"""
修复 usd_assets 中文件名和引用的非法字符问题
- OBJ 文件名: original-N.obj -> original_N.obj
- MTL 文件名: original-N.mtl -> original_N.mtl
- 更新 OBJ 中的 mtllib 引用
- 更新 URDF 中的 mesh filename 引用
"""

import os
import re
import shutil
from pathlib import Path

DEFAULT_ROOT_DIR = "/new_world/cockatiel/urdf_xml_usd_convert/usd_assets"


def find_files_with_hyphen(directory, extensions=None):
    """查找所有含 '-' 的指定类型文件"""
    files = []
    for root, dirs, filenames in os.walk(directory):
        for fn in filenames:
            if extensions:
                if any(fn.endswith(ext) for ext in extensions):
                    if '-' in fn:
                        files.append(os.path.join(root, fn))
            else:
                if '-' in fn:
                    files.append(os.path.join(root, fn))
    return sorted(files)


def rename_file(path, dry_run=False):
    """重命名文件，将 - 替换为 _"""
    dirname = os.path.dirname(path)
    basename = os.path.basename(path)
    new_basename = basename.replace('-', '_')
    new_path = os.path.join(dirname, new_basename)

    if path == new_path:
        return False

    if dry_run:
        print(f"[DRY-RUN] Rename: {basename} -> {new_basename}")
    else:
        os.rename(path, new_path)
        print(f"[OK] Renamed: {basename} -> {new_basename}")
    return True


def update_obj_mtllib_references(directory, dry_run=False):
    """更新 OBJ 文件中的 mtllib 引用"""
    count = 0
    for root, dirs, filenames in os.walk(directory):
        for fn in filenames:
            if fn.endswith('.obj'):
                path = os.path.join(root, fn)
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                new_content = re.sub(
                    r'(mtllib\s+)(original|new)-(\d+\.mtl)',
                    r'\1\2_\3',
                    content,
                )

                if new_content != content:
                    if dry_run:
                        print(f"[DRY-RUN] Update mtllib in: {fn}")
                    else:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"[OK] Updated mtllib in: {fn}")
                    count += 1
    return count


def update_urdf_mesh_references(directory, dry_run=False):
    """更新 URDF 文件中的 mesh filename 引用"""
    count = 0
    for root, dirs, filenames in os.walk(directory):
        for fn in filenames:
            if fn.endswith('.urdf'):
                path = os.path.join(root, fn)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()

                new_content = re.sub(
                    r'(filename="[^"]*?(?:textured_objs|objs)/)(original|new)-(\d+\.obj")',
                    r'\1\2_\3',
                    content,
                )

                if new_content != content:
                    if dry_run:
                        print(f"[DRY-RUN] Update mesh refs in: {fn}")
                    else:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"[OK] Updated mesh refs in: {fn}")
                    count += 1
    return count


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Fix asset file names and references')
    parser.add_argument('--dry-run', action='store_true', help='Only show what would be changed')
    parser.add_argument(
        '--root',
        default=DEFAULT_ROOT_DIR,
        help='Root directory containing asset folders (default: usd_assets in repo)',
    )
    args = parser.parse_args()

    mode = "[DRY-RUN] " if args.dry_run else ""

    root_dir = os.path.abspath(args.root)
    if not os.path.isdir(root_dir):
        raise SystemExit(f"Root directory not found: {root_dir}")

    print(f"{mode}Root: {root_dir}")

    print(f"{mode}=== Phase 1: Rename OBJ files ===")
    obj_files = find_files_with_hyphen(root_dir, ['.obj'])
    print(f"Found {len(obj_files)} OBJ files with '-' in name")
    renamed_objs = 0
    for path in obj_files:
        if rename_file(path, dry_run=args.dry_run):
            renamed_objs += 1

    print(f"\n{mode}=== Phase 2: Rename MTL files ===")
    mtl_files = find_files_with_hyphen(root_dir, ['.mtl'])
    print(f"Found {len(mtl_files)} MTL files with '-' in name")
    renamed_mtls = 0
    for path in mtl_files:
        if rename_file(path, dry_run=args.dry_run):
            renamed_mtls += 1

    print(f"\n{mode}=== Phase 3: Update OBJ mtllib references ===")
    updated_objs = update_obj_mtllib_references(root_dir, dry_run=args.dry_run)

    print(f"\n{mode}=== Phase 4: Update URDF mesh references ===")
    updated_urdfs = update_urdf_mesh_references(root_dir, dry_run=args.dry_run)

    print(f"\n{mode}=== Summary ===")
    print(f"OBJ files renamed: {renamed_objs}")
    print(f"MTL files renamed: {renamed_mtls}")
    print(f"OBJ files updated: {updated_objs}")
    print(f"URDF files updated: {updated_urdfs}")

    if not args.dry_run:
        print("\n=== Verification ===")
        remaining_obj = find_files_with_hyphen(root_dir, ['.obj'])
        remaining_mtl = find_files_with_hyphen(root_dir, ['.mtl'])
        print(f"Remaining OBJ with '-': {len(remaining_obj)}")
        print(f"Remaining MTL with '-': {len(remaining_mtl)}")

        # Check for remaining broken references
        broken_refs = []
        for root, dirs, filenames in os.walk(root_dir):
            for fn in filenames:
                if fn.endswith('.obj'):
                    path = os.path.join(root, fn)
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if 'original-' in content or 'new-' in content:
                            broken_refs.append(f"OBJ: {path}")
                elif fn.endswith('.urdf'):
                    path = os.path.join(root, fn)
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'original-' in content or 'new-' in content:
                            broken_refs.append(f"URDF: {path}")

        if broken_refs:
            print(f"WARNING: {len(broken_refs)} files still have broken references:")
            for ref in broken_refs[:10]:
                print(f"  - {ref}")
        else:
            print("All references updated successfully!")


if __name__ == "__main__":
    main()
