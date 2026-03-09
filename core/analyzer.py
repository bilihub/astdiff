import difflib
from typing import List, Dict

from .models import FunctionNode, DiffResult

class CodeAnalyzer:
    """
    Core engine that compares two sets of AST-extracted FunctionNodes
    and computes the difference at both function and line levels.
    """
    
    def __init__(self):
        pass
        
    def analyze_functions(self, old_funcs: List[FunctionNode], new_funcs: List[FunctionNode], ignore_formatting: bool = False) -> DiffResult:
        """
        Compare old and new function lists to produce a DiffResult.
        Functions are matched by their name/signature.
        """
        result = DiffResult()
        # Helper for matching
        def normalize_sig(s: str) -> str:
            return "".join(s.split())
            
        def get_base_name(s: str) -> str:
            return s.split('(')[0].strip()

        old_map: Dict[str, FunctionNode] = {f.name: f for f in old_funcs}
        new_map: Dict[str, FunctionNode] = {f.name: f for f in new_funcs}
        
        old_remaining = list(old_map.keys())
        new_remaining = list(new_map.keys())
        
        matched_pairs = [] # List of (old_name, new_name)
        
        # 1. Exact Name Match
        for name in list(old_remaining):
            if name in new_remaining:
                matched_pairs.append((name, name))
                old_remaining.remove(name)
                new_remaining.remove(name)
                
        # 2. Normalized Signature Match (ignoring spaces)
        new_norm_map = {normalize_sig(name): name for name in new_remaining}
        for old_name in list(old_remaining):
            norm_old = normalize_sig(old_name)
            if norm_old in new_norm_map:
                new_name = new_norm_map[norm_old]
                matched_pairs.append((old_name, new_name))
                old_remaining.remove(old_name)
                new_remaining.remove(new_name)
                del new_norm_map[norm_old]
                
        # 3. Base Name Match (if unique in remaining)
        old_base_counts = {}
        for name in old_remaining:
            base = get_base_name(name)
            old_base_counts[base] = old_base_counts.get(base, 0) + 1
            
        new_base_counts = {}
        new_base_map = {}
        for name in new_remaining:
            base = get_base_name(name)
            new_base_counts[base] = new_base_counts.get(base, 0) + 1
            new_base_map[base] = name
            
        for old_name in list(old_remaining):
            base = get_base_name(old_name)
            if old_base_counts.get(base) == 1 and new_base_counts.get(base) == 1:
                new_name = new_base_map[base]
                matched_pairs.append((old_name, new_name))
                old_remaining.remove(old_name)
                new_remaining.remove(new_name)

        # Added functions
        result.added_functions = len(new_remaining)
        for name in new_remaining:
            f = new_map[name]
            result.added_func_details.append(f)
            result.lines_added += f.end_line - f.start_line + 1
            
        # Deleted functions
        result.deleted_functions = len(old_remaining)
        for name in old_remaining:
            f = old_map[name]
            result.deleted_func_details.append(f)
            result.lines_deleted += f.end_line - f.start_line + 1
            
        # Potentially modified functions
        for old_name, new_name in matched_pairs:
            old_f = old_map[old_name]
            new_f = new_map[new_name]
            # Fast check: skip if identical (taking formatting into account if requested)
            if ignore_formatting:
                old_clean = [line.strip() for line in old_f.content.splitlines() if line.strip()]
                new_clean = [line.strip() for line in new_f.content.splitlines() if line.strip()]
                if old_clean == new_clean and old_name == new_name:
                    continue
            else:
                if old_f.content == new_f.content and old_name == new_name:
                    continue
                
            # Otherwise, analyze line differences
            added_lines, deleted_lines = self._calculate_line_diff(old_f.content, new_f.content, ignore_formatting)
            
            # If signature changed, it's considered a modification even if line diff is 0 internally
            sig_changed = (old_name != new_name)
            if added_lines > 0 or deleted_lines > 0 or sig_changed:
                result.modified_functions += 1
                result.lines_added += added_lines
                result.lines_deleted += deleted_lines
                result.modified_func_details.append((old_f, new_f, added_lines, deleted_lines))
                
        return result

    def _calculate_line_diff(self, old_content: str, new_content: str, ignore_formatting: bool) -> tuple[int, int]:
        """
        Compare two strings using unified diff and count actual line additions and deletions.
        """
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()
        
        if ignore_formatting:
            old_lines = [line.strip() for line in old_lines if line.strip()]
            new_lines = [line.strip() for line in new_lines if line.strip()]
        
        added = 0
        deleted = 0
        
        # Keepends is false in splitlines(), which is fine for ndiff/unified_diff
        # Use ndiff for accurate single-line change tracking
        for diff_line in difflib.ndiff(old_lines, new_lines):
            if diff_line.startswith('+ '):
                added += 1
            elif diff_line.startswith('- '):
                deleted += 1
                
        return added, deleted
