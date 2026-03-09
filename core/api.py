import os
from typing import Optional, List

from .engine import AnalyzerEngine
from .standardization import StandardizationCalculator

def compare_code(
    old_path: str, 
    new_path: str, 
    use_ast_diff: bool = False, 
    ignore_formatting: bool = False, 
    excludes: Optional[List[str]] = None,
    stn_calculator: Optional[StandardizationCalculator] = None
) -> dict:
    """
    Core API entrypoint to compare code differences between two versions.
    Automatically detects if the paths are directories or single files.
    
    Args:
        old_path (str): Path to the old version (file or directory).
        new_path (str): Path to the new version (file or directory).
        use_ast_diff (bool): Whether to use deep Abstract Syntax Tree comparison.
        ignore_formatting (bool): Whether to ignore whitespace and formatting changes in text diff mode.
        excludes (List[str]): List of exact directory or file names to exclude from analysis.
        stn_calculator (StandardizationCalculator): Custom algorithm to compute standardization metrics.
        
    Returns:
        dict: A comprehensive report object containing change statistics, detailed file metrics, and standardizations scores.
    """
    engine = AnalyzerEngine(
        stn_calculator=stn_calculator, 
        use_ast_diff=use_ast_diff, 
        excludes=excludes
    )
    
    if os.path.isdir(old_path) and os.path.isdir(new_path):
        report = engine.compare_directories(old_path, new_path, ignore_formatting=ignore_formatting)
    elif os.path.isfile(old_path) and os.path.isfile(new_path):
        report = engine.compare_files(old_path, new_path, ignore_formatting=ignore_formatting)
    else:
        raise ValueError("Inputs must either be both directories or both files.")
        
    return report
