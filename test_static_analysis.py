#!/usr/bin/env python3
"""
静态代码分析与问题检测
"""
import ast
import sys
import os
from typing import List, Dict, Any

class CodeAnalyzer:
    def __init__(self):
        self.issues = []
        
    def analyze_file(self, file_path: str) -> List[Dict[str, Any]]:
        print(f"\n🔍 Analyzing file: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=file_path)
            visitor = CodeIssueVisitor(file_path, self.issues)
            visitor.visit(tree)
            
            print(f"✅ Analyzed {file_path}, found {len(self.issues)} issues so far")
        except Exception as e:
            print(f"❌ Error analyzing {file_path}: {e}")
            
        return self.issues
        
    def print_report(self):
        print("\n" + "="*80)
        print("📋 STATIC CODE ANALYSIS REPORT")
        print("="*80)
        
        if not self.issues:
            print("✅ No issues found!")
            return
            
        for i, issue in enumerate(self.issues, 1):
            print(f"\n{i}. [{issue['type']}] {issue['file']}:{issue['line']}")
            print(f"   Message: {issue['message']}")
            print(f"   Code: {issue['code']}")
            
        print(f"\nTotal issues: {len(self.issues)}")
        print("="*80)

class CodeIssueVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str, issues: List[Dict[str, Any]]):
        self.file_path = file_path
        self.issues = issues
        
    def visit_ExceptHandler(self, node):
        if node.type is None:
            self._add_issue(
                "WARNING",
                node.lineno,
                "Bare exception handler - catches all exceptions",
                ast.unparse(node)
            )
        self.generic_visit(node)
        
    def visit_FunctionDef(self, node):
        if not node.body:
            self._add_issue(
                "WARNING",
                node.lineno,
                "Empty function body",
                f"def {node.name}(...):"
            )
        self.generic_visit(node)
        
    def visit_ClassDef(self, node):
        if not node.body:
            self._add_issue(
                "WARNING",
                node.lineno,
                "Empty class body",
                f"class {node.name}:"
            )
        self.generic_visit(node)
        
    def _add_issue(self, type_: str, line: int, message: str, code: str):
        self.issues.append({
            "file": self.file_path,
            "line": line,
            "type": type_,
            "message": message,
            "code": code
        })

def main():
    analyzer = CodeAnalyzer()
    
    files_to_analyze = [
        "src/database/database.py",
        "src/database/database_logged.py",
        "src/parser/arkts_parser.py",
        "src/parser/arkts_parser_logged.py",
        "src/core.py",
        "src/core_logged.py",
        "src/logger.py"
    ]
    
    for file_path in files_to_analyze:
        if os.path.exists(file_path):
            analyzer.analyze_file(file_path)
            
    analyzer.print_report()
    
if __name__ == "__main__":
    main()
