import argparse
import json
import os
import sys
import difflib
import io

from core.api import compare_code
from core.standardization import StandardizationCalculator
from core.models import DiffResult

class MyCustomStandardization(StandardizationCalculator):
    def calculate(self, diff_result: DiffResult) -> float:
        total_changes = diff_result.added_functions + diff_result.modified_functions
        if total_changes == 0:
            return 1.0
        if diff_result.lines_deleted > 0:
            ratio = (diff_result.lines_added / diff_result.lines_deleted)
            return min(ratio, 1.0)
        return 1.0

def _group_by_file(items, key='file'):
    """将列表按文件路径分组，返回 {file_path: [items]} 有序字典"""
    from collections import OrderedDict
    groups = OrderedDict()
    for item in items:
        fp = item.get(key, '未知文件') if isinstance(item, dict) else '未知文件'
        fp = os.path.basename(fp)
        groups.setdefault(fp, []).append(item)
    return groups

def _format_text(text, max_len=60):
    if not text:
        return ""
    clean = " ".join(text.split())
    if len(clean) > max_len:
        return clean[:max_len-3] + "..."
    return clean

def _print_change_detail(cd, indent="       "):
    """打印单条 AST 变化详情"""
    ct = cd['type']
    old_t = _format_text(cd.get('old_text', ''))
    new_t = _format_text(cd.get('new_text', ''))
    context = f"[{cd['context']}] " if cd.get('context') else ""
    
    if ct == 'modified':
        print(f"{indent}修改 {context}<{cd['node_type']}> 旧{cd['old_line']}→新{cd['new_line']}:  「{old_t}」→「{new_t}」")
    elif ct == 'added':
        print(f"{indent}新增 {context}<{cd['node_type']}> 新{cd['new_line']}:  「{new_t}」")
    elif ct == 'deleted':
        print(f"{indent}删除 {context}<{cd['node_type']}> 旧{cd['old_line']}:  「{old_t}」")
    elif ct == 'replaced':
        print(f"{indent}替换 {context}<{cd['node_type']}> 旧{cd['old_line']}→新{cd['new_line']}:  「{old_t}」→「{new_t}」")

def _print_modified_func(m, args, indent="   "):
    """打印一个修改函数的详情"""
    if args.ast_diff:
        print(f"{indent}~ {m['name']}  (节点变更: {m.get('ast_nodes_modified', 0)})")
        if not args.brief:
            for cd in m.get('ast_change_details', []):
                _print_change_detail(cd, indent + "      ")
    else:
        print(f"{indent}~ {m['name']}  (+{m['lines_added']} / -{m['lines_deleted']})")

def _print_show_diff(m, args, indent="     "):
    """打印 unified diff（仅非 AST 模式）"""
    if not args.show_diff or args.ast_diff:
        return
    if args.ignore_formatting:
        old_lines = [line.strip() + '\n' for line in m['old_content'].splitlines() if line.strip()]
        new_lines = [line.strip() + '\n' for line in m['new_content'].splitlines() if line.strip()]
    else:
        old_lines = m['old_content'].splitlines(keepends=True)
        new_lines = m['new_content'].splitlines(keepends=True)
    diff = difflib.unified_diff(old_lines, new_lines, fromfile=f"旧/{m['name']}", tofile=f"新/{m['name']}", n=3)
    print(f"{indent}{'─'*44}")
    for line in diff:
        clean = line.rstrip('\n')
        if clean.startswith('+') and not clean.startswith('+++'):
            print(f"{indent}+ {clean[1:]}")
        elif clean.startswith('-') and not clean.startswith('---'):
            print(f"{indent}- {clean[1:]}")
        elif clean.startswith('@@'):
            print(f"{indent}{clean}")
        else:
            print(f"{indent}  {clean}")
    print(f"{indent}{'─'*44}")

def print_report(report, args):
    metrics = report['metrics']
    total_funcs = metrics['added_functions'] + metrics['deleted_functions'] + metrics['modified_functions']
    is_dir = report.get('type') == 'directory'

    if args.ast_diff:
        ast_m = report.get('ast_metrics', {})
        total_lines = ast_m.get('ast_lines_added', 0) + ast_m.get('ast_lines_deleted', 0) + ast_m.get('ast_lines_modified', 0)
    else:
        total_lines = metrics['lines_added_in_mod'] + metrics['lines_deleted_in_mod']

    target_type = '目录' if is_dir else '文件'
    W = 56
    print("=" * W)
    print(f" 代码差异分析报告 | 目标: {report['target']} ({target_type})")
    print("=" * W)
    print(f" 变动项: {total_funcs}  |  变动行数: {total_lines}  |  标准化率: {report['design_standardization_rate']:.4f}")
    print("-" * W)

    mode_label = "语法树(AST)度量" if args.ast_diff else "函数与代码行度量"
    print(f" [{mode_label}]")
    print(f"   新增: {metrics['added_functions']}    删除: {metrics['deleted_functions']}    修改: {metrics['modified_functions']}")

    if args.ast_diff:
        am = report.get('ast_metrics', {})
        print(f"   新增节点: {am.get('ast_nodes_added', 0)}    删除节点: {am.get('ast_nodes_deleted', 0)}    变更节点: {am.get('ast_nodes_modified', 0)}")
        print(f"   新增行数: {am.get('ast_lines_added', 0)}    删除行数: {am.get('ast_lines_deleted', 0)}    变更行数: {am.get('ast_lines_modified', 0)}")
    else:
        print(f"   新增行: {metrics['lines_added_in_mod']}    删除行: {metrics['lines_deleted_in_mod']}")
    print("=" * W)

    details = report['details']

    if is_dir:
        # ========== 目录模式: 先展示文件级增删 ==========
        file_changes = report.get('file_changes', {})
        added_files_list = file_changes.get('added_files', [])
        deleted_files_list = file_changes.get('deleted_files', [])

        if added_files_list:
            print(" [新增文件]")
            for f in added_files_list:
                print(f"   📄 + {f}")
        if deleted_files_list:
            print(" [删除文件]")
            for f in deleted_files_list:
                print(f"   📄 - {f}")
        if added_files_list or deleted_files_list:
            print("-" * W)

        # ========== 按文件分组输出变动详情 ==========
        added_groups = _group_by_file(details['added'])
        deleted_groups = _group_by_file(details['deleted'])
        modified_groups = _group_by_file(details['modified'])

        all_files = list(dict.fromkeys(
            list(added_groups.keys()) +
            list(deleted_groups.keys()) +
            list(modified_groups.keys())
        ))

        for fname in all_files:
            file_added = added_groups.get(fname, [])
            file_deleted = deleted_groups.get(fname, [])
            file_modified = modified_groups.get(fname, [])
            file_total = len(file_added) + len(file_deleted) + len(file_modified)

            print(f" 📄 {fname}  ({file_total} 项变动)")

            if file_added:
                for item in file_added:
                    print(f"   + {item['name']}")

            if file_deleted:
                for item in file_deleted:
                    print(f"   - {item['name']}")

            if file_modified:
                for m in file_modified:
                    _print_modified_func(m, args, indent="   ")
                    _print_show_diff(m, args, indent="     ")

            print()
    else:
        # ========== 文件模式: 平铺输出 ==========
        if details['added']:
            print(" [新增]")
            for item in details['added']:
                print(f"   + {item['name']}")
        if details['deleted']:
            print(" [删除]")
            for item in details['deleted']:
                print(f"   - {item['name']}")
        if details['modified']:
            print(" [修改]")
            for m in details['modified']:
                _print_modified_func(m, args)
                _print_show_diff(m, args)

    print("=" * W)


def main():
    parser = argparse.ArgumentParser(description="AST-based Code Evolution & Standardization Rate Analyzer")
    parser.add_argument("old_file", help="旧版本路径（文件或目录）")
    parser.add_argument("new_file", help="新版本路径（文件或目录）")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")
    parser.add_argument("--show-diff", action="store_true", help="显示 unified diff（非 AST 模式）")
    parser.add_argument("--ignore-formatting", action="store_true", help="忽略空白和空行变化")
    parser.add_argument("--ast-diff", action="store_true", help="启用深度语法树对比")
    parser.add_argument("--brief", action="store_true", help="简洁模式：仅显示摘要和变动列表，不显示逐条变动详情")
    parser.add_argument("-e", "--exclude", nargs="*", default=[], help="要排除的文件或文件夹名称列表")

    args = parser.parse_args()

    # For Windows console properly displaying CJK characters
    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    try:
        report = compare_code(
            old_path=args.old_file,
            new_path=args.new_file,
            use_ast_diff=args.ast_diff,
            ignore_formatting=args.ignore_formatting,
            excludes=args.exclude,
            stn_calculator=MyCustomStandardization()
        )

        if args.format == "json":
            print(json.dumps(report, indent=4, ensure_ascii=False))
        else:
            print_report(report, args)

    except Exception as e:
        print(f"分析出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
