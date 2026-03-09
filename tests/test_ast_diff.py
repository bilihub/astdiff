import os
import sys
import unittest

# Ensure the core module is discoverable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.parser import ParserFactory
from core.ast_diff import ASTDiffer
from core.engine import AnalyzerEngine

class TestASTDiffEngine(unittest.TestCase):
    def setUp(self):
        # Setup paths to the test files
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.v1_sample = os.path.join(self.base_dir, 'test_cases', 'v1', 'ast_sample.cpp')
        self.v2_sample = os.path.join(self.base_dir, 'test_cases', 'v2', 'ast_sample.cpp')
        
    def test_ast_diff_comprehensive(self):
        engine = AnalyzerEngine(use_ast_diff=True)
        report = engine.compare_files(self.v1_sample, self.v2_sample)
        metrics = report['metrics']
        ast_metrics = report['ast_metrics']
        
        # calculate_discount signature changed (float->double), so old is deleted, new is added.
        # However, with smart signature matching, it is now considered modified!
        
        # Now let's test the modified functions behavior
        modified_funcs_names = [m['name'] for m in report['details']['modified']]
        
        self.assertIn("calculate_discount", "".join(modified_funcs_names), "calculate_discount should be flagged as modified due to signature change")
        
        # 1. Negative Assertions: Functions that should NOT be in the modified list 
        # because they only had formatting or non-logical reordering changes
        # is_valid_user: only formatting/brace differences. Should be ignored.
        self.assertNotIn("is_valid_user", "".join(modified_funcs_names), "is_valid_user should be fully ignored due to purely formatting diff")
        # reorder_test: statements were strictly swapped without structural modification. Should be ignored.
        self.assertNotIn("reorder_test", "".join(modified_funcs_names), "reorder_test should be fully ignored due to structural AST tolerance")
        
        # 2. Positive Assertions: Functions that DID have actual logical changes
        # check_ast: body changed (a*b -> a/b)
        self.assertIn("check_ast", "".join(modified_funcs_names), "check_ast should be flagged as modified")
        # sum_array: body changed (`<` to `<=`)
        self.assertIn("sum_array", "".join(modified_funcs_names), "sum_array should be flagged as modified")
        # process_data: variable renamed (temp_val -> initial_value, res -> result)
        self.assertIn("process_data", "".join(modified_funcs_names), "process_data should be flagged as modified")
        
        # 3. Class Methods Assertions
        # Calculator::subtract: only brace formatting. Should be ignored.
        self.assertNotIn("subtract", "".join(modified_funcs_names), "subtract method in Calculator should be ignored due to only formatting changes")
        # Calculator::add: logic changed (a+b -> b+a)
        self.assertIn("add", "".join(modified_funcs_names), "add method in Calculator should be flagged as modified")
        
        # 4. Template Function Assertions
        # find_max: logic changed (> to >=)
        self.assertIn("find_max", "".join(modified_funcs_names), "find_max template should be flagged as modified")
        
        # We manually check the output validity via running the AST difference engine.
        print("AST Testing ran successfully. Node metrics collected:")
        print(f"Nodes Added: {ast_metrics['ast_nodes_added']}")
        print(f"Nodes Deleted: {ast_metrics['ast_nodes_deleted']}")
        print(f"Nodes Modified: {ast_metrics['ast_nodes_modified']}")

if __name__ == '__main__':
    unittest.main()
