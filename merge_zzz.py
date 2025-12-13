#!/usr/bin/env python3
"""
merge_zzz.py - 合并指定路径下所有 *_zzz.json 文件中的列表，生成新的 xxx_zzz.json 文件。

用法:
    python merge_zzz.py <路径>

参数:
    <路径>         包含 *_zzz.json 文件的目录（递归搜索）

描述:
    遍历给定路径（包括子目录）下所有文件名匹配 *_zzz.json 的文件。
    每个文件的根元素必须是列表，将所有列表合并为一个新列表。
    输出文件名为 <路径最后一个文件夹名>_zzz.json，保存在当前工作目录。
    例如：路径为 raw/滋孽卡牌EA阶段JSON文件1.1/领域，则输出 领域_zzz.json。
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Any


def find_zzz_files(root_path: str) -> List[str]:
    """递归查找所有 *_zzz.json 文件"""
    zzz_files = []
    for dirpath, _, filenames in os.walk(root_path):
        for filename in filenames:
            if filename.endswith('_zzz.json'):
                zzz_files.append(os.path.join(dirpath, filename))
    return zzz_files


def load_json_list(filepath: str) -> List[Any]:
    """加载 JSON 文件，确保根元素是列表，返回该列表"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ValueError(f"文件 {filepath} 不是有效的 JSON: {e}")
    if not isinstance(data, list):
        raise ValueError(f"文件 {filepath} 的根元素不是列表（实际类型: {type(data).__name__}）")
    return data


def merge_zzz_files(filepaths: List[str]) -> List[Any]:
    """合并多个 JSON 文件中的列表"""
    merged = []
    for fp in filepaths:
        try:
            lst = load_json_list(fp)
            merged.extend(lst)
            print(f"已加载 {fp}，包含 {len(lst)} 条记录")
        except ValueError as e:
            print(f"警告: 跳过文件 {fp}: {e}", file=sys.stderr)
    return merged


def get_output_path(input_path: str) -> Path:
    """
    根据输入路径确定输出文件路径。
    输出文件位于输入路径的父目录下，文件名为 <输入路径的最后一个文件夹名>_zzz.json。
    """
    p = Path(input_path).resolve()
    # 如果输入路径是文件，则取其所在目录作为输入目录
    if p.is_file():
        input_dir = p.parent
    else:
        input_dir = p
    # 输入目录的父目录
    parent_dir = input_dir.parent
    # 输入目录的文件夹名
    folder_name = input_dir.name
    # 如果输入目录是根目录（例如 '/' 或 'C:\'），则父目录就是自身，此时输出到当前目录
    if parent_dir == input_dir:
        parent_dir = Path.cwd()
    output_path = parent_dir / f"{folder_name}_zzz.json"
    return output_path


def main():
    parser = argparse.ArgumentParser(description="合并指定路径下所有 *_zzz.json 文件中的列表")
    parser.add_argument('path', help='包含 *_zzz.json 文件的目录路径')
    args = parser.parse_args()

    if not os.path.exists(args.path):
        print(f"错误: 路径不存在: {args.path}", file=sys.stderr)
        sys.exit(1)

    # 查找文件
    zzz_files = find_zzz_files(args.path)
    if not zzz_files:
        print(f"警告: 在 {args.path} 下未找到 *_zzz.json 文件", file=sys.stderr)
        sys.exit(0)

    print(f"找到 {len(zzz_files)} 个 *_zzz.json 文件:")
    for f in zzz_files:
        print(f"  {f}")

    # 合并
    merged_list = merge_zzz_files(zzz_files)
    print(f"合并后总计 {len(merged_list)} 条记录")

    # 确定输出文件路径
    output_path = get_output_path(args.path)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged_list, f, ensure_ascii=False, indent=2)
    print(f"结果已保存到 {output_path}")


if __name__ == '__main__':
    main()