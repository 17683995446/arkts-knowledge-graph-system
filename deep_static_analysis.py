#!/usr/bin/env python3
"""
深度代码走读与静态分析工具
"""
import os
import sys
import re
from pathlib import Path

class DeepCodeAnalyzer:
    """深度代码分析器"""
    
    def __init__(self, code_dir="/workspace/src"):
        self.code_dir = Path(code_dir)
        self.analysis_result = {}
    
    def analyze_file(self, file_path: Path):
        """分析单个文件"""
        print(f"\n{'='*80}")
        print(f"📄 深度分析: {file_path.name}")
        print(f"{'='*80}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
            result = {
                "file_name": file_path.name,
                "line_count": len(lines),
                "functions": [],
                "classes": [],
                "imports": [],
                "if_statements": 0,
                "for_loops": 0,
                "while_loops": 0,
                "try_except": 0,
                "potential_issues": []
            }
            
            # 提取函数定义
            func_pattern = r"def\s+(\w+)\s*\("
            functions = re.findall(func_pattern, content)
            result["functions"] = functions
            
            # 提取类定义
            class_pattern = r"class\s+(\w+)"
            classes = re.findall(class_pattern, content)
            result["classes"] = classes
            
            # 提取导入
            import_pattern = r"^(from|import)\s+(.+)$"
            imports = re.findall(import_pattern, content, re.MULTILINE)
            result["imports"] = imports
            
            # 统计控制流
            result["if_statements"] = content.count("if ")
            result["for_loops"] = content.count("for ")
            result["while_loops"] = content.count("while ")
            result["try_except"] = content.count("try:")
            
            # 分析潜在问题
            self._analyze_potential_issues(lines, result)
            
            self.analysis_result[file_path.name] = result
            
            # 打印分析结果
            self._print_analysis(result)
            
            return result
            
        except Exception as e:
            print(f"❌ 分析失败: {e}")
            return None
    
    def _analyze_potential_issues(self, lines, result):
        """分析潜在问题"""
        for i, line in enumerate(lines, 1):
            # 查找硬编码的路径
            if any(x in line for x in ["/tmp", "/etc", "/root", "C:\\"]):
                result["potential_issues"].append(
                    (i, "潜在硬编码路径", line.strip())
                )
            
            # 查找未处理的异常
            if "except:" in line and not any(x in line for x in ["Exception", "Error"]):
                result["potential_issues"].append(
                    (i, "裸 except，可能掩盖问题", line.strip())
                )
            
            # 查找过长的行
            if len(line) > 120:
                result["potential_issues"].append(
                    (i, "代码过长（>120字符）", line.strip()[:80] + "...")
                )
            
            # 查找魔法数字
            if re.search(r"\b\d+\b", line):
                # 简单检查，可能有误报
                pass
    
    def _print_analysis(self, result):
        """打印分析结果"""
        print(f"\n📊 基本信息:")
        print(f"   - 行数: {result['line_count']}")
        print(f"   - 函数数: {len(result['functions'])}")
        print(f"   - 类数: {len(result['classes'])}")
        
        if result['functions']:
            print(f"\n🔧 函数列表:")
            for func in result['functions'][:10]:  # 最多显示10个
                print(f"   - {func}")
            if len(result['functions']) > 10:
                print(f"   ... 还有 {len(result['functions'])-10} 个")
        
        print(f"\n🔀 控制流统计:")
        print(f"   - if 语句: {result['if_statements']}")
        print(f"   - for 循环: {result['for_loops']}")
        print(f"   - while 循环: {result['while_loops']}")
        print(f"   - try-except: {result['try_except']}")
        
        if result['potential_issues']:
            print(f"\n⚠️  发现 {len(result['potential_issues'])} 个潜在问题:")
            for issue in result['potential_issues'][:10]:
                print(f"   第 {issue[0]} 行: {issue[1]}")
                print(f"      {issue[2]}")
            if len(result['potential_issues']) > 10:
                print(f"   ... 还有 {len(result['potential_issues'])-10} 个")
        
        print(f"\n✅ {result['file_name']} 分析完成")
    
    def run_full_analysis(self):
        """运行完整分析"""
        print("="*80)
        print("🔍 深度代码走读与静态分析")
        print("="*80)
        
        files_to_analyze = [
            self.code_dir / "database" / "database.py",
            self.code_dir / "parser" / "arkts_parser.py",
            self.code_dir / "core.py",
            self.code_dir / "logger.py"
        ]
        
        all_results = {}
        
        for file_path in files_to_analyze:
            if file_path.exists():
                result = self.analyze_file(file_path)
                if result:
                    all_results[file_path.name] = result
        
        print(f"\n{'='*80}")
        print("📈 静态分析汇总")
        print(f"{'='*80}")
        
        total_lines = 0
        total_functions = 0
        total_classes = 0
        total_issues = 0
        
        for file_name, result in all_results.items():
            total_lines += result["line_count"]
            total_functions += len(result["functions"])
            total_classes += len(result["classes"])
            total_issues += len(result["potential_issues"])
        
        print(f"\n📊 总体统计:")
        print(f"   - 分析文件: {len(all_results)}")
        print(f"   - 总代码行数: {total_lines}")
        print(f"   - 总函数数: {total_functions}")
        print(f"   - 总类数: {total_classes}")
        print(f"   - 潜在问题: {total_issues}")
        
        return all_results

def main():
    print("="*80)
    print("🔍 深度代码走读与静态分析启动")
    print("="*80)
    
    analyzer = DeepCodeAnalyzer()
    results = analyzer.run_full_analysis()
    
    print("\n✅ 深度静态分析完成！")
    return 0

if __name__ == "__main__":
    sys.exit(main())
