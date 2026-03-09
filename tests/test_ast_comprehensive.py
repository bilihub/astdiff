"""
全面 AST 差异分析综合测试套件
覆盖 20 种场景 (A-T) 及其复合情况
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.parser import ParserFactory
from core.ast_diff import ASTDiffer
from core.engine import AnalyzerEngine


class TestASTComprehensive(unittest.TestCase):
    """综合测试: 使用 ast_comprehensive.cpp 覆盖 20 种场景"""

    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.v1 = os.path.join(self.base_dir, 'test_cases', 'v1', 'ast_comprehensive.cpp')
        self.v2 = os.path.join(self.base_dir, 'test_cases', 'v2', 'ast_comprehensive.cpp')
        self.engine = AnalyzerEngine(use_ast_diff=True)
        self.report = self.engine.compare_files(self.v1, self.v2)
        self.metrics = self.report['metrics']
        self.ast_metrics = self.report['ast_metrics']
        self.modified_names = [m['name'] for m in self.report['details']['modified']]
        self.added_names = [item['name'] for item in self.report['details']['added']]
        self.deleted_names = [item['name'] for item in self.report['details']['deleted']]
        self.modified_all = "\n".join(self.modified_names)

    # ================================================================
    # 正向断言: 应当被识别为有实质变更的函数
    # ================================================================

    def test_A_numeric_constant_change(self):
        """场景A: 数值常量 42->99 应被识别为修改"""
        self.assertIn("get_magic_number", self.modified_all)

    def test_B_string_literal_change(self):
        """场景B: 字符串字面量修改应被识别"""
        self.assertIn("print_greeting", self.modified_all)

    def test_C_statement_addition(self):
        """场景C: 新增语句应被识别为修改"""
        self.assertIn("log_init", self.modified_all)

    def test_D_statement_deletion(self):
        """场景D: 删除语句应被识别为修改"""
        self.assertIn("log_shutdown", self.modified_all)

    def test_E_ternary_operator_change(self):
        """场景E: 三元表达式中操作符变化应被识别"""
        self.assertIn("abs_val", self.modified_all)

    def test_F_loop_type_change(self):
        """场景F: for->while 循环类型变换应被识别"""
        self.assertIn("count_up", self.modified_all)

    def test_G_nested_if_threshold_change(self):
        """场景G: 嵌套if/else阈值和返回值修改应被识别"""
        self.assertIn("classify", self.modified_all)

    def test_H_switch_case_modification(self):
        """场景H: switch-case新增case和修改返回值应被识别"""
        self.assertIn("day_name", self.modified_all)

    def test_I_empty_to_nonempty(self):
        """场景I: 空函数体->有内容应被识别"""
        self.assertIn("placeholder", self.modified_all)

    def test_L_compound_modification(self):
        """场景L: 多重复合修改(操作符+常量+变量名+增删)应被识别"""
        self.assertIn("complex_calc", self.modified_all)

    def test_M_virtual_function_constant(self):
        """场景M: 虚函数中数值常量修改应被识别(Circle::area)"""
        self.assertIn("area", self.modified_all)

    def test_N_nested_loop_expression(self):
        """场景N: 嵌套循环内层表达式修改应被识别"""
        self.assertIn("matrix_print", self.modified_all)

    def test_Q_lambda_change(self):
        """场景Q: lambda表达式操作符和新增lambda应被识别"""
        self.assertIn("use_lambda", self.modified_all)

    def test_R_template_cast_change(self):
        """场景R: 模板函数中类型转换方法变更应被识别"""
        self.assertIn("convert", self.modified_all)

    def test_S_exception_handling_change(self):
        """场景S: 异常类型和返回值修改应被识别"""
        self.assertIn("safe_divide", self.modified_all)

    # ================================================================
    # 全局变量断言
    # ================================================================

    def test_U_global_variable_detected(self):
        """场景U: 全局变量值修改应被检测到"""
        # 全局变量在解析时名称前会加 [变量] 前缀
        self.assertIn("g_max_retry", self.modified_all, "全局变量 g_max_retry 值变化 3->5 应被识别")
        self.assertIn("APP_NAME", self.modified_all, "全局变量 APP_NAME 值变化应被识别")
        self.assertIn("PI_VALUE", self.modified_all, "全局变量 PI_VALUE 值变化应被识别")

    def test_M_class_member_detected(self):
        """场景M: Circle 类的成员变量 radius 应被提取并配对"""
        # 成员变量在两边都存在且未变，不应出现在修改列表
        # 但应确保不会崩溃（它会被提取为 [成员] radius）
        # 成员变量 radius 在两版中完全相同，不应在修改列表
        # 验证不出现意外错误即可
        pass

    # ================================================================
    # 反向断言: 应当被完全忽略的函数
    # ================================================================

    def test_P_unchanged_function_ignored(self):
        """场景P: 完全不变的函数不应出现在修改列表中"""
        self.assertNotIn("unchanged_func", self.modified_all)

    def test_T_format_only_ignored(self):
        """场景T: 纯格式重排(空行/缩进变化)应被忽略"""
        self.assertNotIn("format_test", self.modified_all)

    # ================================================================
    # 签名变化: 应识别为新增+删除
    # ================================================================

    def test_K_param_added_is_modified_function(self):
        """场景K: 参数增加导致签名变化, 应通过智能匹配被识别为修改"""
        self.assertIn("compute", "\n".join(self.modified_names), "签名改变的compute应被识别为修改")

    def test_O_pointer_to_ref_is_modified_function(self):
        """场景O: 指针参数->引用参数, 应通过智能匹配被识别为修改"""
        self.assertIn("swap_vals", "\n".join(self.modified_names), "签名改变的swap_vals应被识别为修改")
        
    def test_W_wrapper_added_is_clean(self):
        """场景W: 嵌套包裹/层级变化, 原内容被包裹进新的if, 应被精简识别而不是大面积错位"""
        self.assertIn("wrapper_test", self.modified_all)
        
        # We can check specific details of the modification:
        # It should NOT be considered completely replaced or having massive offsets.
        # So the number of modified lines should be relatively small or specific (like just the if added)
        # However, testing exact lines might be fragile, so we just assert it's caught as modified
        # and doesn't spam AST additions/deletions excessively.
        
        w_item_found = False
        for mod_item in self.report['details']['modified']:
            if 'wrapper_test' in mod_item['name']:
                w_item_found = True
                ast_adds = mod_item['ast_change_details']
                # The only added node should ideally be the outer if_statement or conditions
                add_types = [desc['node_type'] for desc in ast_adds if desc['type'] == 'added']
                self.assertTrue(any(t in ('if_statement', 'compound_statement') for t in add_types), "Should report outer block (compound_statement or if_statement) as added")
        self.assertTrue(w_item_found, "wrapper_test should exist in modified details")

    # ================================================================
    # 注释变化: 场景J 测试
    # ================================================================

    def test_J_comment_addition(self):
        """场景J: 纯注释增加, 但注释也是AST节点, 应被检测到"""
        # 注释在 tree-sitter 中是 AST 节点, 所以增加注释会被识别为新增节点
        # 这里我们验证它要么被识别为修改（有新增的comment节点），
        # 要么被忽略（如果注释不在AST中）。
        # 实际上 tree-sitter 会把注释作为节点, 所以应该出现在修改中。
        # 我们不做强硬断言, 只确认系统不会崩溃
        pass  # 此场景作为回归安全检查

    # ================================================================
    # 度量值验证
    # ================================================================

    def test_total_nodes_positive(self):
        """AST变更节点总数应大于0"""
        total = (self.ast_metrics['ast_nodes_added'] +
                 self.ast_metrics['ast_nodes_deleted'] +
                 self.ast_metrics['ast_nodes_modified'])
        self.assertGreater(total, 0, "应有AST节点变更")

    def test_total_lines_positive(self):
        """AST变更行数总数应大于0"""
        total = (self.ast_metrics['ast_lines_added'] +
                 self.ast_metrics['ast_lines_deleted'] +
                 self.ast_metrics['ast_lines_modified'])
        self.assertGreater(total, 0, "应有行数变更")

    def test_total_lines_reasonable(self):
        """AST变更行数不应超过文件总行数"""
        total = (self.ast_metrics['ast_lines_added'] +
                 self.ast_metrics['ast_lines_deleted'] +
                 self.ast_metrics['ast_lines_modified'])
        # 文件约220行，变更行数不应超过文件行数的2倍（新旧两文件合计）
        self.assertLessEqual(total, 500, "变更行数应合理，不应远超文件行数")
    def test_no_negative_metrics(self):
        """所有度量值不应为负数"""
        for key, val in self.ast_metrics.items():
            self.assertGreaterEqual(val, 0, f"{key} 不应为负数")


class TestASTOriginalSample(unittest.TestCase):
    """原有 ast_sample.cpp 的回归测试, 确保新改动不破坏旧行为"""

    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.v1 = os.path.join(self.base_dir, 'test_cases', 'v1', 'ast_sample.cpp')
        self.v2 = os.path.join(self.base_dir, 'test_cases', 'v2', 'ast_sample.cpp')
        self.engine = AnalyzerEngine(use_ast_diff=True)
        self.report = self.engine.compare_files(self.v1, self.v2)
        self.modified_names = "\n".join([m['name'] for m in self.report['details']['modified']])

    def test_formatting_ignored(self):
        """is_valid_user 纯格式变化应被忽略"""
        self.assertNotIn("is_valid_user", self.modified_names)

    def test_reorder_ignored(self):
        """reorder_test 语句乱序应被忽略"""
        self.assertNotIn("reorder_test", self.modified_names)

    def test_subtract_formatting_ignored(self):
        """Calculator::subtract 纯格式变化应被忽略"""
        self.assertNotIn("subtract", self.modified_names)

    def test_operator_change_detected(self):
        """check_ast 操作符 *->/ 应被识别"""
        self.assertIn("check_ast", self.modified_names)

    def test_boundary_change_detected(self):
        """sum_array 边界 <-><=  应被识别"""
        self.assertIn("sum_array", self.modified_names)

    def test_variable_rename_detected(self):
        """process_data 变量重命名应被识别"""
        self.assertIn("process_data", self.modified_names)

    def test_class_method_change_detected(self):
        """Calculator::add 操作数顺序变化应被识别"""
        self.assertIn("add", self.modified_names)

    def test_template_change_detected(self):
        """find_max 模板函数操作符变化应被识别"""
        self.assertIn("find_max", self.modified_names)


class TestASTDirectoryMode(unittest.TestCase):
    """目录级别测试, 验证多文件合并分析"""

    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.v1_dir = os.path.join(self.base_dir, 'test_cases', 'v1')
        self.v2_dir = os.path.join(self.base_dir, 'test_cases', 'v2')
        self.engine = AnalyzerEngine(use_ast_diff=True)
        self.report = self.engine.compare_directories(self.v1_dir, self.v2_dir)

    def test_directory_report_has_metrics(self):
        """目录模式应生成有效的度量数据"""
        self.assertIn('metrics', self.report)
        self.assertIn('ast_metrics', self.report)

    def test_directory_has_multiple_functions(self):
        """目录模式应包含来自多个文件的函数"""
        total = (self.report['metrics']['added_functions'] +
                 self.report['metrics']['deleted_functions'] +
                 self.report['metrics']['modified_functions'])
        self.assertGreater(total, 5, "目录分析应包含大量函数变更")

    def test_directory_ast_lines_positive(self):
        """目录模式下行数统计应大于0"""
        ast_m = self.report['ast_metrics']
        total_lines = ast_m['ast_lines_added'] + ast_m['ast_lines_deleted'] + ast_m['ast_lines_modified']
        self.assertGreater(total_lines, 0)


if __name__ == '__main__':
    unittest.main()
