import os
import re
from abc import ABC, abstractmethod
from typing import List, Dict

import tree_sitter_c as tsc
import tree_sitter_cpp as tscpp
import tree_sitter_xml as tsxml
from tree_sitter import Language, Parser
import charset_normalizer

from .models import FunctionNode, ASTNode

class BaseASTParser(ABC):
    """
    Abstract base class for language-specific AST parsers.
    """
    
    def __init__(self):
        self._language = self._init_language()
        self._parser = Parser(self._language)
        
    @abstractmethod
    def _init_language(self) -> Language:
        """Initialize and return the tree-sitter Language object."""
        pass
        
    @abstractmethod
    def _extract_functions(self, root_node, source_bytes: bytes, file_path: str, encoding: str = 'utf-8') -> List[FunctionNode]:
        """Traverse the AST and extract function nodes."""
        pass
        
    def _detect_encoding(self, source_bytes: bytes) -> str:
        """Heuristic to detect the correct encoding."""
        try:
            source_bytes.decode('utf-8')
            return 'utf-8'
        except UnicodeDecodeError:
            pass
            
        try:
            source_bytes.decode('gb18030')
            return 'gb18030'
        except UnicodeDecodeError:
            pass
            
        detected = charset_normalizer.detect(source_bytes)
        return detected.get('encoding') or 'utf-8'
        
    def parse_file(self, file_path: str) -> List[FunctionNode]:
        """
        Parse a given source file and return all extracted FunctionNodes.
        """
        try:
            with open(file_path, 'rb') as f:
                source_bytes = f.read()
            encoding = self._detect_encoding(source_bytes)
            tree = self._parser.parse(source_bytes)
            return self._extract_functions(tree.root_node, source_bytes, file_path, encoding)
        except Exception as e:
            print(f"Error parsing file {file_path}: {e}")
            return []

def _normalize_signature(signature_bytes: bytes, encoding: str = 'utf-8') -> str:
    """Helper to convert bytes to a normalized string signature."""
    s = signature_bytes.decode(encoding, errors='replace')
    # Replace multiple whitespaces/newlines with a single space
    s = re.sub(r'\s+', ' ', s).strip()
    return s

class CBaseParser(BaseASTParser):
    """Base parser logic for C/C++ family of languages."""
    
    def _extract_functions(self, root_node, source_bytes: bytes, file_path: str, encoding: str = 'utf-8') -> List[FunctionNode]:
        functions = []
        
        def _build_ast_tree(ts_node) -> ASTNode:
            node_text = source_bytes[ts_node.start_byte:ts_node.end_byte].decode(encoding, errors='replace')
            children = [_build_ast_tree(c) for c in ts_node.children]
            return ASTNode(
                type=ts_node.type,
                text=node_text,
                start_line=ts_node.start_point.row + 1,
                end_line=ts_node.end_point.row + 1,
                children=children
            )

        def _extract_decl_name(node, source_bytes: bytes) -> str:
            """Extract the variable/object name from a declaration node."""
            for child in node.children:
                if child.type == 'init_declarator':
                    for cc in child.children:
                        if cc.type == 'identifier':
                            return source_bytes[cc.start_byte:cc.end_byte].decode(encoding, errors='replace')
                if child.type == 'identifier':
                    return source_bytes[child.start_byte:child.end_byte].decode(encoding, errors='replace')
            # Fallback
            return _normalize_signature(source_bytes[node.start_byte:node.end_byte], encoding)

        def walk(node, inside_class=False, inside_function=False):
            if node.type == 'function_definition':
                # --- Function extraction (original logic) ---
                signature_node = None
                body_node = None
                
                for child in node.children:
                    if child.type == 'compound_statement':
                        body_node = child
                    elif child.type not in ('compound_statement', 'comment'):
                        signature_node = child
                
                sig_text = "unknown_function"
                if signature_node:
                    for c in node.children:
                        if c.type == 'function_declarator':
                            sig_text = _normalize_signature(source_bytes[c.start_byte:c.end_byte], encoding)
                            break
                        elif c.type == 'pointer_declarator':
                            for cc in c.children:
                                if cc.type == 'function_declarator':
                                    sig_text = _normalize_signature(source_bytes[cc.start_byte:cc.end_byte], encoding)
                                    break
                
                if sig_text == "unknown_function" and body_node:
                    head_bytes = source_bytes[node.start_byte:body_node.start_byte]
                    sig_text = _normalize_signature(head_bytes, encoding)
                
                start_line = node.start_point.row + 1
                end_line = node.end_point.row + 1
                content = source_bytes[node.start_byte:node.end_byte].decode(encoding, errors='replace')
                
                ast_root = _build_ast_tree(node)

                functions.append(FunctionNode(
                    name=sig_text,
                    start_line=start_line,
                    end_line=end_line,
                    content=content,
                    file_path=file_path,
                    kind='function',
                    ast_root=ast_root
                ))

            elif node.type == 'declaration' and not inside_class and not inside_function:
                # --- Top-level (global) variable/object declaration ---
                # Skip if it contains a function_declarator (forward declarations)
                has_func_decl = any(
                    c.type == 'function_declarator' or
                    any(cc.type == 'function_declarator' for cc in getattr(c, 'children', []))
                    for c in node.children
                )
                if not has_func_decl:
                    decl_name = _extract_decl_name(node, source_bytes)
                    content = source_bytes[node.start_byte:node.end_byte].decode(encoding, errors='replace')
                    ast_root = _build_ast_tree(node)
                    functions.append(FunctionNode(
                        name=f"[变量] {decl_name}",
                        start_line=node.start_point.row + 1,
                        end_line=node.end_point.row + 1,
                        content=content,
                        file_path=file_path,
                        kind='variable',
                        ast_root=ast_root
                    ))

            elif node.type == 'field_declaration' and inside_class:
                # --- Class/struct member variable ---
                decl_name = _extract_decl_name(node, source_bytes)
                content = source_bytes[node.start_byte:node.end_byte].decode(encoding, errors='replace')
                ast_root = _build_ast_tree(node)
                functions.append(FunctionNode(
                    name=f"[成员] {decl_name}",
                    start_line=node.start_point.row + 1,
                    end_line=node.end_point.row + 1,
                    content=content,
                    file_path=file_path,
                    kind='class_field',
                    ast_root=ast_root
                ))

            # Recurse — mark class/struct context
            for child in node.children:
                if node.type in ('class_specifier', 'struct_specifier'):
                    walk(child, inside_class=True, inside_function=inside_function)
                elif node.type == 'function_definition':
                    walk(child, inside_class=inside_class, inside_function=True)
                else:
                    walk(child, inside_class=inside_class, inside_function=inside_function)
                
        walk(root_node)
        return functions

class CParser(CBaseParser):
    def _init_language(self) -> Language:
        return Language(tsc.language())

class CppParser(CBaseParser):
    def _init_language(self) -> Language:
        return Language(tscpp.language())


class ParserFactory:
    """Factory to return the appropriate parser based on file extension."""
    
    _parsers = {}
    
    @classmethod
    def get_parser(cls, file_path: str) -> BaseASTParser:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ('.c', '.h'):
            if 'c' not in cls._parsers:
                cls._parsers['c'] = CParser()
            return cls._parsers['c']
        elif ext in ('.cpp', '.cxx', '.cc', '.hpp', '.hxx'):
            if 'cpp' not in cls._parsers:
                cls._parsers['cpp'] = CppParser()
            return cls._parsers['cpp']
        else:
            raise ValueError(f"Unsupported file extension: {ext}")
