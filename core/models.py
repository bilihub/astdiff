from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Any

@dataclass
class ASTNode:
    """A purely Python-serializable abstract syntax tree node representation."""
    type: str               # The grammar Type of the node (e.g. 'if_statement')
    text: str               # The raw source code string for this node/leaf (if applicable)
    start_line: int = 0     # 1-indexed start line in source file
    end_line: int = 0       # 1-indexed end line in source file
    children: List['ASTNode'] = field(default_factory=list)

@dataclass
class FunctionNode:
    """Represents a code element (function, variable, etc.) extracted from source code."""
    name: str          # Name or signature
    start_line: int    # 1-indexed start line
    end_line: int      # 1-indexed end line
    content: str       # Raw source code
    file_path: str     # Path to the file containing the node
    kind: str = 'function'  # 'function', 'variable', 'class_field'
    ast_root: Optional[ASTNode] = None


@dataclass
class DiffResult:
    """Stores the result of the diff process."""
    added_functions: int = 0
    deleted_functions: int = 0
    modified_functions: int = 0
    
    # Line modifications within the modified functions
    lines_added: int = 0
    lines_deleted: int = 0
    # A modified line can be interpreted as a deletion followed by an addition in unified diffs.
    
    # Pure AST-level modifications (if activated)
    ast_nodes_added: int = 0
    ast_nodes_deleted: int = 0
    ast_nodes_modified: int = 0
    
    # AST-level line counts (lines covered by changed AST nodes)
    ast_lines_added: int = 0
    ast_lines_deleted: int = 0
    ast_lines_modified: int = 0
    
    # Detailed tracking
    added_func_details: List[FunctionNode] = field(default_factory=list)
    deleted_func_details: List[FunctionNode] = field(default_factory=list)
    # Tuple of (old_node, new_node, added_lines, deleted_lines)
    modified_func_details: List[Tuple[FunctionNode, FunctionNode, int, int]] = field(default_factory=list)
