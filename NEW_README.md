# usd_assets 转换流程总结

## 概述

本项目用于将符合相同目录结构的资产批量转换为 IsaacLab 可用的 USDA 格式。

已验证可用的输入目录示例：
- `usd_assets/`（29 个资产）
- `/new_world/cockatiel/ASSETS/PM_RAW/Box`（26 个资产，见下方记录）

### 输入数据
- 目录结构：`{ROOT}/{asset_id}/`
- 核心文件：
  - `mobility.urdf` - URDF 机器人描述文件
  - `textured_objs/*.obj` - 3D 模型文件
  - `textured_objs/*.mtl` - 材质文件
  - `meta.json` - 元数据
  - `result.json` - 物体层级结构

### 输出数据
- `mobility.usda` - IsaacLab 可直接使用的 USD 格式文件

---

## 完整转换流程（7 步）

### Step 1: 清理与备份
```bash
# 指定要处理的根目录
ROOT=/path/to/assets

# 创建备份
cp -r "$ROOT" "${ROOT}_backup"

# 删除点云采样数据
find "$ROOT" -name "point_sample" -type d -exec rm -rf {} +
```

### Step 2: 几何修复
**脚本**: `change_format/geom_fixing.py`

**功能**:
- 修复 OBJ 文件语法错误
- 处理顶点数过少的情况（<4 顶点时构建四面体）
- 为几何添加微小扰动（1e-4 随机噪声）避免数值问题
- 修复退化轴的厚度

**命令**:
```bash
python change_format/geom_fixing.py "$ROOT"
```

**输出**: 若检测到问题，会生成 `.obj.bak` 备份文件

---

### Step 3: 文件重命名
**脚本**: `fix_asset_names.py` (新建)

**功能**:
- 重命名 `original-N.obj` → `original_N.obj`
- 重命名 `original-N.mtl` → `original_N.mtl`

**命令**:
```bash
python fix_asset_names.py --root "$ROOT"
```

---

### Step 4: 引用修复
**脚本**: `fix_asset_names.py`

**功能**:
- 更新 OBJ 文件中的 `mtllib` 引用
- 更新 URDF 文件中的 `mesh filename` 引用
- 修复特殊资产（如 3398）中的 `new-X.obj` 引用

**命令**:
```bash
python fix_asset_names.py --root "$ROOT"
```

**验证**:
```bash
# 检查剩余含 '-' 的文件
find "$ROOT" -name "*[-]*" -type f | wc -l  # 应为 0

# 检查损坏的引用
rg "filename=\\\"[^\\\"]*-" "$ROOT" -g "*.urdf"  # 应无输出
rg "mtllib\\s+[^\\s]*-" "$ROOT" -g "*.obj"      # 应无输出
```

---

### Step 5: URDF → XML
**脚本**: `fix_urdf_inertia.py` + `convert_urdf_to_xml.py` (新建)

**依赖**: `urdf2mjcf` (conda env: usdtoolbox)

**功能**:
- 为辅助链接 (`link_X_helper`) 添加惯性属性
- 调用 `urdf2mjcf` 转换

**命令**:
```bash
python fix_urdf_inertia.py --root "$ROOT"
conda run -n usdtoolbox python convert_urdf_to_xml.py --root "$ROOT"
```

**修复内容**:
```xml
# 修复前
<link name="link_0_helper"/>

# 修复后
<link name="link_0_helper">
    <inertial>
        <origin xyz="0 0 0"/>
        <mass value="1e-6"/>
        <inertia ixx="1e-10" ixy="0" ixz="0" iyy="1e-10" iyz="0" izz="1e-10"/>
    </inertial>
</link>
```

---

### Step 6: XML 路径修复
**脚本**: `fix_xml_batch.py` (新建)

**功能**:
- 将绝对路径转为相对路径
- 修复 `file="/new_world/cockatiel/.../textured_objs/..."` → `file="textured_objs/..."`

**命令**:
```bash
python fix_xml_batch.py --root "$ROOT"
```

**关键修改** (`change_format/fix_xml.py`):
```python
# 支持 textured_objs 目录
m = re.search(r'file="([^"]*/textured_objs/)([^"]+)"', content)
if not m:
    m = re.search(r'file="([^"]*/objs/)([^"]+)"', content)
```

---

### Step 7: XML → USDA
**脚本**: `convert_xml_to_usda.py` (新建)

**依赖**: `teleillusion` conda 环境 (IsaacLab)

**功能**:
- 批量将 XML 转换为 USDA
- 单次 IsaacLab 会话中处理所有文件

**命令**:
```bash
conda run -n teleillusion python convert_xml_to_usda.py --root "$ROOT"
```

---

## 遇到的问题与解决方案

### 问题 1: URDF 解析错误 (mismatched tag)
**原因**: 脚本错误地将 `<link .../>` 转换为不完整的 XML

**解决**: 重写 `fix_urdf_inertia.py`，逐行处理而非正则替换

### 问题 2: urdf2mjcf 找不到 OBJ 文件
**原因**: URDF 引用 `original-X.obj` 但文件已重命名为 `original_X.obj`

**解决**: 同步更新 URDF 中的所有 mesh 引用

### 问题 3: XML 路径检测失败
**原因**: 路径检测只匹配 `/objs/` 而实际使用 `/textured_objs/`

**解决**: 修改 `fix_xml.py` 支持 `textured_objs` 目录

### 问题 4: IsaacLab 导入错误 (Failed to open layer)
**原因**: XML 中 `file="objs/..."` 但文件实际在 `textured_objs/`

**解决**: 修复所有 XML 中的路径前缀

### 问题 5: IsaacLab 共享信号量权限错误
**报错**: `Failed to create/open shared semaphore {13/Permission denied}`

**原因**: Isaac Sim 需要创建共享信号量（常见于受限环境或沙箱）

**解决**: 在具备系统权限的环境中运行 `convert_xml_to_usda.py`

---

## 生成的脚本清单

| 脚本 | 用途 |
|------|------|
| `change_format/geom_fixing.py` | OBJ 几何与语法修复 |
| `fix_asset_names.py` | 文件重命名与引用修复 |
| `fix_urdf_inertia.py` | URDF 辅助链接惯性修复 |
| `convert_urdf_to_xml.py` | URDF → XML 批量转换 |
| `fix_xml_batch.py` | XML 路径修复 |
| `convert_xml_to_usda.py` | XML → USDA 批量转换 |

---

## 快速复跑流程

```bash
# 0. 设置根目录
ROOT=/path/to/assets

# 1. 如果有备份，从备份恢复
cp -r "${ROOT}_backup" "$ROOT"

# 2. 清理点云数据
find "$ROOT" -name "point_sample" -type d -exec rm -rf {} +

# 3. 几何修复
python change_format/geom_fixing.py "$ROOT"

# 4. 文件重命名与引用修复
python fix_asset_names.py --root "$ROOT"

# 5. URDF 预修复 + URDF → XML
python fix_urdf_inertia.py --root "$ROOT"
conda run -n usdtoolbox python convert_urdf_to_xml.py --root "$ROOT"

# 6. XML 路径修复
python fix_xml_batch.py --root "$ROOT"

# 7. XML → USDA
conda run -n teleillusion python convert_xml_to_usda.py --root "$ROOT"
```

---

## 文件结构变化

```
usd_assets/{asset_id}/
├── mobility.urdf        # 输入
├── mobility.xml         # Step 5 输出
├── mobility.usda        # Step 7 最终输出 ✓
├── textured_objs/
│   ├── original_*.obj   # 重命名后
│   └── original_*.mtl   # 重命名后
├── meta.json
└── result.json
```

---

## 注意事项

1. **备份**: 任何修改前先创建备份
2. **验证**: 每步完成后检查输出文件和引用是否正确
3. **环境**: 步骤 5 需要 `usdtoolbox`，步骤 7 需要 `teleillusion`
4. **权限**: 若遇到共享信号量权限问题，需在具备系统权限的环境运行 Step 7
5. **路径**: 确保 XML 中的 `file` 路径与实际目录结构一致

---

## /ASSETS/PM_RAW/Box 批次处理记录 (2026-02-02)

**目录**: `/new_world/cockatiel/ASSETS/PM_RAW/Box`

**统计**:
- 子目录数量: 26（含 `mobility.urdf`）
- OBJ 数量: 1239
- URDF → XML: 26/26 成功
- XML → USDA: 26/26 成功（`mobility.usda` 全部生成）

**修复与更新**:
- OBJ/MTL 文件名中的 `-` 已统一改为 `_`
- OBJ `mtllib` 引用与 URDF `mesh filename` 引用已同步更新
- XML 路径全部改为相对 `textured_objs/`

**提示**:
- Isaac Sim 转换过程中可能出现警告（例如 base 缺少 inertial/geom）
- 若出现资源复制失败的警告，建议后续扫描 XML/MTL 的贴图路径是否缺失
