import os
import re
import xml.etree.ElementTree as ET
import xml.parsers.expat
from typing import Optional, List
from .models import DiffResult, FunctionNode

class LineTrackerBuilder(ET.TreeBuilder):
    """
    底层拦截器：在构建抽象语法树时，直接对接 expat 引擎，实时截取并作为隐藏属性注入真实行号
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.expat_parser = None
    
    def start(self, tag, attrs):
        elem = super().start(tag, attrs)
        if self.expat_parser:
            try:
                elem.set('__sourceline__', str(self.expat_parser.CurrentLineNumber))
            except Exception:
                pass
        return elem
        
    def comment(self, data):
        try:
            elem = super().comment(data)
            if self.expat_parser and elem is not None:
                try:
                    elem.set('__sourceline__', str(self.expat_parser.CurrentLineNumber))
                except Exception:
                    pass
            return elem
        except AttributeError:
            pass

class XMLAnalyzer:
    def __init__(self, excludes: Optional[List[str]] = None):
        self.excludes = excludes or []

    def _is_excluded(self, path: str) -> bool:
        if not self.excludes:
            return False
        parts = os.path.normpath(path).split(os.sep)
        return any(ex in parts for ex in self.excludes)

    def _get_xml_files(self, directory: str) -> dict:
        xml_files = {}
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.xml'):
                    full_path = os.path.join(root, file)
                    if not self._is_excluded(full_path):
                        rel_path = os.path.relpath(full_path, directory)
                        xml_files[rel_path] = full_path
        return xml_files

    def _parse_xml_with_comments(self, file_path: str):
        """加载 XML：解决 GBK 编码、提取行号、并容错处理“根节点外部存在的注释”"""
        try:
            content = None
            for enc in ['utf-8', 'gbk', 'gb2312', 'gb18030', 'utf-16']:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if not content:
                return ET.parse(file_path).getroot()

            # 移除 BOM 并剥离 XML 声明头
            if content.startswith('\ufeff'):
                content = content[1:]
            content = re.sub(r'<\?xml[^>]*\?>', '', content, count=1).strip()
            
            def _parse_content(text):
                if hasattr(ET.TreeBuilder, 'insert_comments'):
                    builder = LineTrackerBuilder(insert_comments=True)
                else:
                    builder = LineTrackerBuilder()
                    
                parser = xml.parsers.expat.ParserCreate()
                builder.expat_parser = parser
                
                parser.StartElementHandler = builder.start
                parser.EndElementHandler = builder.end
                parser.CharacterDataHandler = builder.data
                if hasattr(builder, 'comment'):
                    parser.CommentHandler = builder.comment
                    
                parser.Parse(text, True)
                return builder.close()

            try:
                return _parse_content(content)
            except xml.parsers.expat.ExpatError:
                wrapped = f"<VirtualRoot>{content}</VirtualRoot>"
                dummy = _parse_content(wrapped)
                for child in dummy:
                    if self._get_tag_str(child.tag) not in ("Comment", "VirtualRoot"):
                        return child
                return dummy
        except Exception as e:
            print(f"[XMLAnalyzer] 解析出错 {file_path}: {e}")
            return None

    def _get_tag_str(self, tag) -> str:
        if callable(tag) or str(tag) == "<built-in function Comment>":
            return "Comment"
        return str(tag)

    def _get_node_path_name(self, element: ET.Element) -> str:
        """为 GUI 下拉列表生成极致具体的展示名（智能提取关键特征属性）"""
        tag = self._get_tag_str(element.tag)
        if tag == "Comment":
            return "Comment"
        
        for attr in ['ID', 'Name', 'PT', 'Addr', 'SysIp', 'Online']:
            val = element.get(attr)
            if val:
                return f"{tag}[@{attr}='{val}']"
        return tag

    def _element_to_local_string(self, element: ET.Element) -> str:
        if element is None:
            return ""
        tag_str = self._get_tag_str(element.tag)
        if tag_str == "Comment":
            return f"<!-- {element.text} -->"
        
        attrs = ""
        if hasattr(element, 'attrib') and element.attrib:
            filtered_attrs = {k: v for k, v in element.attrib.items() if k != '__sourceline__'}
            if filtered_attrs:
                sorted_attrs = sorted(filtered_attrs.items())
                attrs = " " + " ".join(f'{k}="{v}"' for k, v in sorted_attrs)
            
        res = f"<{tag_str}{attrs}>"
        text = (element.text or "").strip()
        if text:
            res += f"\n{text}\n</{tag_str}>"
        return res

    def _get_element_key(self, element: ET.Element) -> Optional[str]:
        tag_str = self._get_tag_str(element.tag)
        if tag_str == "Comment" or not hasattr(element, 'get'):
            return None
        id_val = element.get("ID") or element.get("Name") or element.get("PT")
        if id_val:
            return f"{tag_str}_{id_val}"
        return None

    def _create_node(self, node: ET.Element, path: str, filepath: str, content: str = "") -> FunctionNode:
        line = 0
        if hasattr(node, 'get'):
            try:
                line = int(node.get('__sourceline__', 0))
            except Exception:
                pass
                
        name = f"[L{line}] {path}" if line else path
        return FunctionNode(
            name=name,
            start_line=line,
            end_line=line,
            content=content,
            file_path=filepath,
            kind='element',
            ast_root=None
        )

    def _compare_trees(self, old_node: ET.Element, new_node: ET.Element, path: str, result: DiffResult, file_rel_path: str):
        changes = []
        old_tag = self._get_tag_str(old_node.tag)
        new_tag = self._get_tag_str(new_node.tag)
        
        line_old, line_new = 0, 0
        if hasattr(old_node, 'get'):
            try: line_old = int(old_node.get('__sourceline__', 0))
            except: pass
        if hasattr(new_node, 'get'):
            try: line_new = int(new_node.get('__sourceline__', 0))
            except: pass
            
        line_str = f"L{line_old}->L{line_new}" if line_old and line_new else "-"
        
        # 将行号和完整路径拼装成清晰的节点描述，直接投递给 GUI
        node_display = f"[L{line_new}] {path}" if line_new else path

        if old_tag == "Comment" and new_tag == "Comment":
            if old_node.text != new_node.text:
                detail = f'[注释内容] "{old_node.text}" -> "{new_node.text}"'
                changes.append({
                    "action": "修改",
                    "node": node_display,
                    "type": "Comment", 
                    "lines": line_str,
                    "content": detail,
                    "old_line": str(line_old), "new_line": str(line_new), "text": detail
                })
        else:
            old_attrib = {k: v for k, v in (old_node.attrib if hasattr(old_node, 'attrib') else {}).items() if k != '__sourceline__'}
            new_attrib = {k: v for k, v in (new_node.attrib if hasattr(new_node, 'attrib') else {}).items() if k != '__sourceline__'}
            all_keys = set(old_attrib.keys()) | set(new_attrib.keys())
            
            for k in sorted(all_keys):
                old_v = old_attrib.get(k)
                new_v = new_attrib.get(k)
                if old_v != new_v:
                    # 将具体的属性变化硬编码到 detail 中，确保界面 100% 渲染出来
                    if old_v is None:
                        action, detail = "新增", f'[属性 {k}] = "{new_v}"'
                    elif new_v is None:
                        action, detail = "删除", f'[属性 {k}] = "{old_v}"'
                    else:
                        action, detail = "修改", f'[属性 {k}] "{old_v}" -> "{new_v}"'
                    
                    changes.append({
                        "action": action,
                        "node": node_display,
                        "type": "Attribute",
                        "lines": line_str,
                        "content": detail,
                        "old_line": str(line_old), "new_line": str(line_new), "text": detail
                    })
                        
            old_text = (old_node.text or "").strip()
            new_text = (new_node.text or "").strip()
            if old_text != new_text:
                detail = f'[节点文本] "{old_text}" -> "{new_text}"'
                changes.append({
                    "action": "修改",
                    "node": node_display,
                    "type": "Text",
                    "lines": line_str,
                    "content": detail,
                    "old_line": str(line_old), "new_line": str(line_new), "text": detail
                })
                
        if changes:
            old_content = self._element_to_local_string(old_node)
            new_content = self._element_to_local_string(new_node)
            
            lines_add, lines_del = 1, 1
            
            old_fn = self._create_node(old_node, path, file_rel_path, old_content)
            new_fn = self._create_node(new_node, path, file_rel_path, new_content)
            
            mod_tuple = (old_fn, new_fn, lines_add, lines_del, len(changes), 0, 0, 0, changes)
            result.modified_func_details.append(mod_tuple)
            result.modified_functions += 1
            result.lines_added += lines_add
            result.lines_deleted += lines_del
            result.ast_nodes_modified += 1
            result.ast_lines_modified += 1

        old_children = list(old_node)
        new_children = list(new_node)
        
        old_matched, new_matched = set(), set()
        
        for i, oc in enumerate(old_children):
            k = self._get_element_key(oc)
            if k:
                for j, nc in enumerate(new_children):
                    if j not in new_matched and self._get_element_key(nc) == k:
                        self._compare_trees(oc, nc, f"{path}/{self._get_node_path_name(nc)}", result, file_rel_path)
                        old_matched.add(i)
                        new_matched.add(j)
                        break
                        
        old_rem, new_rem = {}, {}
        for i, oc in enumerate(old_children):
            if i not in old_matched:
                old_rem.setdefault(self._get_tag_str(oc.tag), []).append((i, oc))
        for j, nc in enumerate(new_children):
            if j not in new_matched:
                new_rem.setdefault(self._get_tag_str(nc.tag), []).append((j, nc))
                
        all_tags = set(old_rem.keys()) | set(new_rem.keys())
        for tag in all_tags:
            o_list = old_rem.get(tag, [])
            n_list = new_rem.get(tag, [])
            max_len = max(len(o_list), len(n_list))
            
            for idx in range(max_len):
                if idx < len(o_list) and idx < len(n_list):
                    nc = n_list[idx][1]
                    child_path = f"{path}/{self._get_node_path_name(nc)}"
                    self._compare_trees(o_list[idx][1], nc, child_path, result, file_rel_path)
                elif idx < len(o_list):
                    oc = o_list[idx][1]
                    child_path = f"{path}/{self._get_node_path_name(oc)}"
                    sig = self._element_to_local_string(oc)
                    result.deleted_func_details.append(self._create_node(oc, child_path, file_rel_path, sig))
                    result.deleted_functions += 1
                    result.ast_nodes_deleted += 1
                    result.ast_lines_deleted += 1
                else:
                    nc = n_list[idx][1]
                    child_path = f"{path}/{self._get_node_path_name(nc)}"
                    sig = self._element_to_local_string(nc)
                    result.added_func_details.append(self._create_node(nc, child_path, file_rel_path, sig))
                    result.added_functions += 1
                    result.ast_nodes_added += 1
                    result.ast_lines_added += 1

    def compare_single_xml(self, old_file: str, new_file: str, file_rel_path: str, result: DiffResult):
        root_old = self._parse_xml_with_comments(old_file)
        root_new = self._parse_xml_with_comments(new_file)

        if root_old is None and root_new is None:
            return
        elif root_old is None and root_new is not None:
            sig = self._element_to_local_string(root_new)
            result.added_func_details.append(self._create_node(root_new, f"/{self._get_tag_str(root_new.tag)}", file_rel_path, sig))
            result.added_functions += 1
            result.ast_nodes_added += 1
            result.ast_lines_added += 1
        elif root_old is not None and root_new is None:
            sig = self._element_to_local_string(root_old)
            result.deleted_func_details.append(self._create_node(root_old, f"/{self._get_tag_str(root_old.tag)}", file_rel_path, sig))
            result.deleted_functions += 1
            result.ast_nodes_deleted += 1
            result.ast_lines_deleted += 1
        else:
            self._compare_trees(root_old, root_new, f"/{self._get_node_path_name(root_new)}", result, file_rel_path)

    def compare_directories(self, old_path: str, new_path: str) -> DiffResult:
        result = DiffResult()
        old_files = self._get_xml_files(old_path)
        new_files = self._get_xml_files(new_path)
        
        all_rel_paths = set(old_files.keys()) | set(new_files.keys())
        for rel_path in all_rel_paths:
            old_f = old_files.get(rel_path)
            new_f = new_files.get(rel_path)
            
            if old_f and not new_f:
                fn = FunctionNode(name=f"[文件删除] {rel_path}", start_line=0, end_line=0, content="", file_path=rel_path, kind='element')
                result.deleted_func_details.append(fn)
                result.deleted_functions += 1
            elif not old_f and new_f:
                fn = FunctionNode(name=f"[文件新增] {rel_path}", start_line=0, end_line=0, content="", file_path=rel_path, kind='element')
                result.added_func_details.append(fn)
                result.added_functions += 1
            else:
                self.compare_single_xml(old_f, new_f, rel_path, result)
        return result