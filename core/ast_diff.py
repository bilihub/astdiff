from typing import List, Tuple, Dict, Any
from .models import ASTNode, FunctionNode, DiffResult
from .analyzer import CodeAnalyzer

class ASTDiffer:
    """
    Engine for structurally comparing two pure Python ASTNode trees.
    Count differences at the semantic AST level instead of text lines.
    Uses a robust global mapping approach (similar to GumTree) to properly
    handle nested code block changes (wrappers/unwrappers/shifts) without shifting match offsets.
    """
    
    def __init__(self):
        self.mapping = {}
        self.reverse_mapping = {}

    def _nodes_are_identical(self, node1: ASTNode, node2: ASTNode) -> bool:
        """
        Recursively check if two AST trees are exactly identical.
        """
        if node1.type != node2.type:
            return False
        if len(node1.children) != len(node2.children):
            return False
        if len(node1.children) == 0:
            if node1.text != node2.text:
                return False
                
        for c1, c2 in zip(node1.children, node2.children):
            if not self._nodes_are_identical(c1, c2):
                return False
        return True

    @staticmethod
    def _line_range_set(node: ASTNode) -> set:
        """Return the set of source line numbers a node spans."""
        return set(range(node.start_line, node.end_line + 1)) if node.start_line > 0 else {0}

    def _get_descendants(self, node: ASTNode) -> List[ASTNode]:
        res = [node]
        for c in node.children:
            res.extend(self._get_descendants(c))
        return res

    def _compute_mapping(self, old_root: ASTNode, new_root: ASTNode):
        """Build a global mapping of matching AST nodes between old and new trees."""
        self.mapping.clear()
        self.reverse_mapping.clear()
        
        old_nodes = self._get_descendants(old_root)
        new_nodes = self._get_descendants(new_root)
        
        def get_size(n: ASTNode) -> int:
            return sum(1 for _ in self._get_descendants(n))
            
        # 1. Exact matches (Top-down greedy by size)
        old_nodes.sort(key=get_size, reverse=True)
        new_nodes.sort(key=get_size, reverse=True)
        
        for old_n in old_nodes:
            if id(old_n) in self.mapping:
                continue
            for new_n in new_nodes:
                if id(new_n) in self.reverse_mapping:
                    continue
                if old_n.type == new_n.type and self._nodes_are_identical(old_n, new_n):
                    old_sub = self._get_descendants(old_n)
                    new_sub = self._get_descendants(new_n)
                    for o, n in zip(old_sub, new_sub):
                        self.mapping[id(o)] = n
                        self.reverse_mapping[id(n)] = o
                    break
                    
        # 2. Structure-only exact matches 
        def _structure_identical(n1: ASTNode, n2: ASTNode) -> bool:
            if n1.type != n2.type: return False
            if len(n1.children) != len(n2.children): return False
            for c1, c2 in zip(n1.children, n2.children):
                if not _structure_identical(c1, c2): return False
            return True
            
        for old_n in old_nodes:
            if id(old_n) in self.mapping:
                continue
            if get_size(old_n) < 3:
                continue
            for new_n in new_nodes:
                if id(new_n) in self.reverse_mapping:
                    continue
                if _structure_identical(old_n, new_n):
                    import difflib
                    ratio = difflib.SequenceMatcher(None, old_n.text.strip(), new_n.text.strip()).ratio()
                    text_len = max(len(old_n.text.strip()), len(new_n.text.strip()))
                    min_ratio = 0.8 if text_len < 20 else 0.45
                    if ratio >= min_ratio:
                        old_sub = self._get_descendants(old_n)
                        new_sub = self._get_descendants(new_n)
                        for o, n in zip(old_sub, new_sub):
                            if id(o) not in self.mapping and id(n) not in self.reverse_mapping:
                                self.mapping[id(o)] = n
                                self.reverse_mapping[id(n)] = o
                        break

        # 3. Fuzzy matches for LEAF nodes or extremely simple nodes only
        import difflib
        for old_n in old_nodes:
            if id(old_n) in self.mapping:
                continue
            if len(old_n.children) > 1:
                continue
                
            best_new = None
            best_score = -1.0
            for new_n in new_nodes:
                if id(new_n) in self.reverse_mapping:
                    continue
                if old_n.type == new_n.type and len(new_n.children) <= 1:
                    score = difflib.SequenceMatcher(None, old_n.text.strip(), new_n.text.strip()).ratio()
                    if score >= 0.8 and score > best_score:
                        best_score = score
                        best_new = new_n
            
            if best_new and best_score >= 0.8:
                # Map them independently
                self.mapping[id(old_n)] = best_new
                self.reverse_mapping[id(best_new)] = old_n
                if len(old_n.children) == 1 and len(best_new.children) == 1:
                    oc = old_n.children[0]
                    nc = best_new.children[0]
                    if id(oc) not in self.mapping and id(nc) not in self.reverse_mapping:
                        self.mapping[id(oc)] = nc
                        self.reverse_mapping[id(nc)] = oc
                        
        # 4. Bottom-up match for inner/branch nodes
        # Process from smallest to largest
        old_nodes_asc = sorted(old_nodes, key=get_size)
        new_nodes_asc = sorted(new_nodes, key=get_size)
        
        for old_n in old_nodes_asc:
            if id(old_n) in self.mapping:
                continue
                
            old_desc_ids = {id(d) for d in self._get_descendants(old_n) if id(d) != id(old_n)}
            
            best_new = None
            best_ratio = -1.0
            for new_n in new_nodes_asc:
                if id(new_n) in self.reverse_mapping:
                    continue
                if old_n.type != new_n.type:
                    continue
                
                new_desc_ids = {id(d) for d in self._get_descendants(new_n) if id(d) != id(new_n)}
                
                # Check how many descendants match mapped ones
                mapped_old = sum(1 for od_id in old_desc_ids if od_id in self.mapping and id(self.mapping[od_id]) in new_desc_ids)
                
                denom = max(len(old_desc_ids), len(new_desc_ids))
                if denom == 0:
                    continue
                    
                ratio = mapped_old / denom
                if ratio > 0.4 and ratio > best_ratio:
                    best_ratio = ratio
                    best_new = new_n
            
            if best_new:
                self.mapping[id(old_n)] = best_new
                self.reverse_mapping[id(best_new)] = old_n
                        
    def diff_ast(self, old_node: ASTNode, new_node: ASTNode) -> Tuple[int, int, int, set, set, set]:
        """
        Compare two AST nodes via global mapping reporting:
        (nodes_added, nodes_deleted, nodes_modified,
         lines_added_set, lines_deleted_set, lines_modified_set)
        """
        self._compute_mapping(old_node, new_node)
        
        added = 0
        deleted = 0
        modified = 0
        raw_lines_add = set()
        raw_lines_del = set()
        lines_mod = set()
        
        mapped_old_lines = set()
        mapped_new_lines = set()
        
        old_nodes = self._get_descendants(old_node)
        new_nodes = self._get_descendants(new_node)
        
        for old_n in old_nodes:
            if id(old_n) not in self.mapping:
                deleted += 1
                raw_lines_del |= self._line_range_set(old_n)
            else:
                new_n = self.mapping[id(old_n)]
                mapped_old_lines |= self._line_range_set(old_n)
                # If mapped but basically different
                is_leaf_changed = (len(old_n.children) == 0 and len(new_n.children) == 0 and old_n.text.strip() != new_n.text.strip())
                is_branch_changed = (len(old_n.children) > 0 and len(old_n.children) != len(new_n.children))
                
                if is_leaf_changed or is_branch_changed:
                    modified += 1
                
                # Only inflate lines_mod for changed leaves, branches are covered by their internal unmapped children
                if is_leaf_changed:
                    lines_mod |= self._line_range_set(old_n) | self._line_range_set(new_n)
                    
        for new_n in new_nodes:
            if id(new_n) not in self.reverse_mapping:
                added += 1
                raw_lines_add |= self._line_range_set(new_n)
            else:
                mapped_new_lines |= self._line_range_set(new_n)
                
        # Exclude perfectly mapped overlaps from raw additions/deletions to prevent wrapper bloat
        lines_add = raw_lines_add - mapped_new_lines
        lines_del = raw_lines_del - mapped_old_lines
        
        # If a line has both mapped and unmapped parts, it's effectively a modified line
        lines_mod |= (raw_lines_add & mapped_new_lines)
        lines_mod |= (raw_lines_del & mapped_old_lines)
        
        # Also clean up lines_mod overlaps so a line isn't counted as both added and modified
        lines_add -= lines_mod
        lines_del -= lines_mod
        
        return added, deleted, modified, lines_add, lines_del, lines_mod
    def _find_naming_context(self, node: ASTNode, parent_map: Dict[int, ASTNode]) -> str:
        """Find a descriptive name for the node based on its ancestors."""
        curr = node
        visited = set()
        while curr and id(curr) not in visited:
            visited.add(id(curr))
            # Language-specific heuristics
            # For XML: find the nearest element parent and get its tag name + identifying attributes
            if curr.type == 'element':
                tag_name = ""
                ident = ""
                for child in curr.children:
                    if child.type in ('STag', 'EmptyElemTag'):
                        for gc in child.children:
                            if gc.type == 'Name':
                                tag_name = gc.text.strip()
                            elif gc.type == 'Attribute':
                                # Look for Name or ID
                                attr_name = ""
                                attr_val = ""
                                for ac in gc.children:
                                    if ac.type == 'Name': attr_name = ac.text.strip()
                                    if ac.type == 'AttValue': attr_val = ac.text.strip()
                                if attr_name.lower() in ('name', 'id'):
                                    ident = f"{attr_name}={attr_val}"
                if tag_name:
                    res = f"<{tag_name}>"
                    if ident: res += f" ({ident})"
                    return res
            
            # For C++/Javaish: find functions or classes
            if curr.type in ('function_definition', 'class_specifier', 'method_declaration'):
                # Try to find an identifier
                for child in curr.children:
                    if child.type in ('identifier', 'field_identifier'):
                        return f"{curr.type.split('_')[0]}: {child.text}"

            curr = parent_map.get(id(curr))
        return ""

    def collect_change_details(self, old_root: ASTNode, new_root: ASTNode, depth: int = 0) -> List[Dict[str, Any]]:
        """
        Produce a human-readable list of top-most changes using the global mapping.
        """
        if depth == 0:
            self._compute_mapping(old_root, new_root)
        
        changes = []
        old_nodes = self._get_descendants(old_root)
        new_nodes = self._get_descendants(new_root)
        
        # Build parent mappings
        parent_map_old = {}
        def build_parent_map(n, pm):
            for c in n.children:
                pm[id(c)] = n
                build_parent_map(c, pm)
        build_parent_map(old_root, parent_map_old)
        
        parent_map_new = {}
        build_parent_map(new_root, parent_map_new)
        
        # 1. Deleted
        for old_n in old_nodes:
            if id(old_n) not in self.mapping:
                curr_p = parent_map_old.get(id(old_n))
                is_top_unmapped = True
                while curr_p is not None:
                    if id(curr_p) not in self.mapping:
                        is_top_unmapped = False
                        break
                    curr_p = parent_map_old.get(id(curr_p))
                    
                if is_top_unmapped:
                    report_n = old_n
                    while report_n.type == 'compound_statement':
                        meaningful = [c for c in report_n.children if c.type not in ('{', '}')]
                        if len(meaningful) == 1:
                            report_n = meaningful[0]
                        else:
                            break
                    
                    context = self._find_naming_context(report_n, parent_map_old)
                    changes.append({
                        'type': 'deleted',
                        'old_line': f"L{report_n.start_line}-L{report_n.end_line}",
                        'new_line': '-',
                        'node_type': report_n.type,
                        'context': context,
                        'old_text': report_n.text.strip(),
                        'new_text': '',
                    })
                    
        # 2. Added
        for new_n in new_nodes:
            if id(new_n) not in self.reverse_mapping:
                curr_p = parent_map_new.get(id(new_n))
                is_top_unmapped = True
                while curr_p is not None:
                    if id(curr_p) not in self.reverse_mapping:
                        is_top_unmapped = False
                        break
                    curr_p = parent_map_new.get(id(curr_p))
                    
                if is_top_unmapped:
                    report_n = new_n
                    while report_n.type == 'compound_statement':
                        meaningful = [c for c in report_n.children if c.type not in ('{', '}')]
                        if len(meaningful) == 1:
                            report_n = meaningful[0]
                        else:
                            break
                    
                    context = self._find_naming_context(report_n, parent_map_new)
                    changes.append({
                        'type': 'added',
                        'old_line': '-',
                        'new_line': f"L{report_n.start_line}-L{report_n.end_line}",
                        'node_type': report_n.type,
                        'context': context,
                        'old_text': '',
                        'new_text': report_n.text.strip(),
                    })
                    
        # 3. Modified
        for old_n in old_nodes:
            if id(old_n) in self.mapping:
                new_n = self.mapping[id(old_n)]
                if len(old_n.children) == 0 and len(new_n.children) == 0:
                    ot, nt = old_n.text.strip(), new_n.text.strip()
                    if ot != nt:
                        context = self._find_naming_context(old_n, parent_map_old)
                        changes.append({
                            'type': 'modified',
                            'old_line': f"L{old_n.start_line}",
                            'new_line': f"L{new_n.start_line}",
                            'node_type': f"{old_n.type}",
                            'context': context,
                            'old_text': ot,
                            'new_text': nt,
                        })

        filtered_changes = []
        import re
        for c in changes:
            if c['type'] in ('added', 'deleted'):
                if not re.search('[a-zA-Z]', str(c.get('node_type', ''))):
                    continue
            filtered_changes.append(c)

        return filtered_changes

    def analyze_functions_ast(self, old_funcs: List[FunctionNode], new_funcs: List[FunctionNode]) -> DiffResult:
        """
        Compare old and new function lists using pure AST deep diff.
        """
        # First use basic analyzer logic to classify functions
        result = CodeAnalyzer().analyze_functions(old_funcs, new_funcs)
        
        # Then, for all that were deemed 'modified' by text, we compute AST diff instead of line diff
        # We'll reset the line diff logic metrics
        result.lines_added = 0
        result.lines_deleted = 0
        
        # Reset and recreate details properly for AST
        modified_func_details_ast = []
        
        # Process completely added functions
        for f in result.added_func_details:
            if getattr(f, 'ast_root', None):
                nodes = self._get_descendants(f.ast_root)
                result.ast_nodes_added += len(nodes)
                result.ast_lines_added += len(self._line_range_set(f.ast_root))

        # Process completely deleted functions
        for f in result.deleted_func_details:
            if getattr(f, 'ast_root', None):
                nodes = self._get_descendants(f.ast_root)
                result.ast_nodes_deleted += len(nodes)
                result.ast_lines_deleted += len(self._line_range_set(f.ast_root))
                
        for old_f, new_f, _, _ in result.modified_func_details:
            if old_f.ast_root and new_f.ast_root:
                ast_add, ast_del, ast_mod, la_set, ld_set, lm_set = self.diff_ast(old_f.ast_root, new_f.ast_root)
                
                if ast_add == 0 and ast_del == 0 and ast_mod == 0:
                    result.modified_functions -= 1
                    continue
                    
                result.ast_nodes_added += ast_add
                result.ast_nodes_deleted += ast_del
                result.ast_nodes_modified += ast_mod
                result.ast_lines_added += len(la_set)
                result.ast_lines_deleted += len(ld_set)
                result.ast_lines_modified += len(lm_set)
                
                change_details = self.collect_change_details(old_f.ast_root, new_f.ast_root)
                
                modified_func_details_ast.append((old_f, new_f, ast_add, ast_del, ast_mod,
                                                   len(la_set), len(ld_set), len(lm_set), change_details))
            else:
                modified_func_details_ast.append((old_f, new_f, 0, 0, 0, 0, 0, 0, []))
                
        result.modified_func_details = modified_func_details_ast
        return result
