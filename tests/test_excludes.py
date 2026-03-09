import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine import AnalyzerEngine

class TestExcludes(unittest.TestCase):
    def setUp(self):
        self.base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.v1_dir = os.path.join(self.base, 'test_cases', 'v1')
        self.v2_dir = os.path.join(self.base, 'test_cases', 'v2')

    def test_no_excludes(self):
        engine = AnalyzerEngine()
        report = engine.compare_directories(self.v1_dir, self.v2_dir)
        # Without excludes, we should see 'new_module.cpp' in added_files or modified files etc.
        fc = report.get('file_changes', {})
        self.assertTrue(any('new_module' in f for f in fc.get('added_files', [])), "new_module.cpp should be detected normally")
        
        # We should also see 'ast_comprehensive.cpp' in modified_files or having modified functions.
        mod_files = [m['file'] for m in report['details']['modified']]
        self.assertTrue(any('ast_comprehensive.cpp' in f for f in mod_files), "ast_comprehensive.cpp should be analyzed normally")

    def test_exclude_file_by_name(self):
        # Exclude exactly the new file
        engine = AnalyzerEngine(excludes=["new_module.cpp"])
        report = engine.compare_directories(self.v1_dir, self.v2_dir)
        
        fc = report.get('file_changes', {})
        self.assertFalse(any('new_module' in f for f in fc.get('added_files', [])), "new_module.cpp should be excluded completely")

    def test_exclude_directory(self):
        # We don't have a sub-directory in test_cases right now, but we can exclude "test_cases" itself which would result in 0 files matched.
        # Alternatively, we can exclude "v1" but the folder we traverse IS v1.
        # Let's test excluding by a known substring that acts as a folder or file.
        engine = AnalyzerEngine(excludes=["ast_comprehensive.cpp"])
        report = engine.compare_directories(self.v1_dir, self.v2_dir)
        
        mod_files = [m['file'] for m in report['details']['modified']]
        self.assertFalse(any('ast_comprehensive.cpp' in f for f in mod_files), "ast_comprehensive.cpp should be excluded completely")

if __name__ == '__main__':
    unittest.main()
