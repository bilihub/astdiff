import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.engine import AnalyzerEngine

def test_xml_ast_diff():
    old_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../test_cases/v1/sample.xml'))
    new_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../test_cases/v2/sample.xml'))
    
    engine = AnalyzerEngine(use_ast_diff=True)
    report = engine.compare_files(old_file, new_file)
    
    metrics = report.get('metrics', {})
    ast_metrics = report.get('ast_metrics', {})
    
    print(f"Metrics (Files/Funcs equivalent):")
    print(f"Added nodes: {metrics.get('added_functions')}")
    print(f"Deleted nodes: {metrics.get('deleted_functions')}")
    print(f"Modified nodes: {metrics.get('modified_functions')}")
    
    print(f"\nAST Metrics:")
    print(f"AST Added: {ast_metrics.get('ast_nodes_added')}")
    print(f"AST Deleted: {ast_metrics.get('ast_nodes_deleted')}")
    print(f"AST Modified: {ast_metrics.get('ast_nodes_modified')}")
    
    print("\nDetails:")
    for mod in report.get('details', {}).get('modified', []):
        print(f"Modified '{mod['name']}' - AST Changes: {mod['ast_nodes_modified']}")
        for adr in mod['ast_change_details']:
            print(f"  {adr['type']} {adr['node_type']} (L{adr['old_line']} -> L{adr['new_line']})")

if __name__ == '__main__':
    test_xml_ast_diff()
