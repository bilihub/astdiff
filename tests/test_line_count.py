"""
行数统计精确性测试套件
使用小型可控测试文件，人工计算预期值，验证 AST 行数统计精确性
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine import AnalyzerEngine


class TestLineCountAccuracy(unittest.TestCase):
    """使用 line_count_test.cpp v1/v2 验证行数统计精确性"""

    def setUp(self):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        v1 = os.path.join(base, 'test_cases', 'v1', 'line_count_test.cpp')
        v2 = os.path.join(base, 'test_cases', 'v2', 'line_count_test.cpp')
        engine = AnalyzerEngine(use_ast_diff=True)
        self.report = engine.compare_files(v1, v2)
        self.metrics = self.report['metrics']
        self.ast = self.report['ast_metrics']
        self.added = [a['name'] for a in self.report['details']['added']]
        self.deleted = [d['name'] for d in self.report['details']['deleted']]
        self.modified = [m['name'] for m in self.report['details']['modified']]

    # ==========================================================
    # 函数/变量级别计数
    # ==========================================================

    def test_func_c_deleted(self):
        """func_c 仅存在于 v1，应出现在删除列表"""
        self.assertTrue(any('func_c' in n for n in self.deleted))

    def test_func_g_added(self):
        """func_g 仅存在于 v2，应出现在新增列表"""
        self.assertTrue(any('func_g' in n for n in self.added))

    def test_func_a_not_modified(self):
        """func_a 完全不变，不应出现在任何变动列表"""
        all_names = ' '.join(self.added + self.deleted + self.modified)
        self.assertNotIn('func_a', all_names)

    def test_func_b_modified(self):
        """func_b 仅改了一个常量 100->200，应在修改列表"""
        self.assertTrue(any('func_b' in n for n in self.modified))

    def test_func_d_modified(self):
        """func_d 改了两行操作 +1/+2 -> *10/*20，应在修改列表"""
        self.assertTrue(any('func_d' in n for n in self.modified))

    def test_g_config_modified(self):
        """全局变量 g_config 从 10 改为 99，应在修改列表"""
        self.assertTrue(any('g_config' in n for n in self.modified))

    def test_g_version_not_modified(self):
        """全局变量 g_version 未变，不应出现在变动列表"""
        all_names = ' '.join(self.added + self.deleted + self.modified)
        self.assertNotIn('g_version', all_names)

    # ==========================================================
    # AST 行数精确性断言
    # ==========================================================

    def test_ast_lines_modified_positive(self):
        """修改了 func_b(1处), func_d(2处), g_config(1处)，行数应 > 0"""
        self.assertGreater(self.ast['ast_lines_modified'], 0)

    def test_ast_lines_modified_upper_bound(self):
        """
        v1 文件约30行, v2 约33行。
        变更行数不应超过两文件行数之和。
        """
        max_possible = 30 + 33
        self.assertLessEqual(self.ast['ast_lines_modified'], max_possible,
                             "变更行数不应超过两文件行数之和")

    def test_total_change_lines_not_exceed_file(self):
        """新增行+删除行+修改行的总和应在合理范围内"""
        total = (self.ast['ast_lines_added'] +
                 self.ast['ast_lines_deleted'] +
                 self.ast['ast_lines_modified'])
        # 两个文件加一起约63行，变更总行不应超过这个数
        self.assertLessEqual(total, 63,
                             "行数变动总量不应超过新旧文件总行数")

    def test_no_negative_ast_lines(self):
        """所有 AST 行数度量不应为负数"""
        for key in ('ast_lines_added', 'ast_lines_deleted', 'ast_lines_modified'):
            self.assertGreaterEqual(self.ast[key], 0, f"{key} 不应为负数")


class TestLineCountAccuracyDirectory(unittest.TestCase):
    """目录模式下行数统计精确性"""

    def setUp(self):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        v1_dir = os.path.join(base, 'test_cases', 'v1')
        v2_dir = os.path.join(base, 'test_cases', 'v2')
        engine = AnalyzerEngine(use_ast_diff=True)
        self.report = engine.compare_directories(v1_dir, v2_dir)
        self.ast = self.report['ast_metrics']

    def test_dir_total_lines_reasonable(self):
        """目录模式下变更行数应在合理范围"""
        total = (self.ast['ast_lines_added'] +
                 self.ast['ast_lines_deleted'] +
                 self.ast['ast_lines_modified'])
        # 所有测试文件加一起约400行，不应超过
        self.assertLessEqual(total, 400,
                             "目录模式行数变动不应远超所有文件总行数")
        self.assertGreater(total, 0, "应有行数变更")

    def test_dir_lines_per_metric_non_negative(self):
        """目录模式下各项行数度量不应为负"""
        for key in ('ast_lines_added', 'ast_lines_deleted', 'ast_lines_modified'):
            self.assertGreaterEqual(self.ast[key], 0, f"{key} 不应为负数")

    def test_dir_added_lines_covers_new_file(self):
        """v2 有 new_module.cpp 新文件，应有新增行"""
        # new_module.cpp 有 func (约3行内容)，至少应有一些新增
        self.assertGreater(self.ast['ast_lines_added'], 0,
                           "新文件中的函数应贡献新增行数")

    def test_file_changes_detected(self):
        """应检测到新增/删除的文件"""
        fc = self.report.get('file_changes', {})
        added_files = fc.get('added_files', [])
        # new_module.cpp 应在新增文件列表中
        self.assertTrue(any('new_module' in f for f in added_files),
                        "new_module.cpp 应被检测为新增文件")


class TestLineCountEdgeCases(unittest.TestCase):
    """行数统计边界情况"""

    def setUp(self):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.engine = AnalyzerEngine(use_ast_diff=True)
        self.base = base

    def test_identical_files_zero_lines(self):
        """相同文件对比，所有行数应为0"""
        v1 = os.path.join(self.base, 'test_cases', 'v1', 'line_count_test.cpp')
        r = self.engine.compare_files(v1, v1)
        ast = r['ast_metrics']
        self.assertEqual(ast['ast_lines_added'], 0, "相同文件不应有新增行")
        self.assertEqual(ast['ast_lines_deleted'], 0, "相同文件不应有删除行")
        self.assertEqual(ast['ast_lines_modified'], 0, "相同文件不应有修改行")
        self.assertEqual(r['metrics']['added_functions'], 0)
        self.assertEqual(r['metrics']['deleted_functions'], 0)
        self.assertEqual(r['metrics']['modified_functions'], 0)


if __name__ == '__main__':
    unittest.main()
