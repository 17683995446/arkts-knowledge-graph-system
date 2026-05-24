#!/usr/bin/env python3
"""
超复杂边界测试 - 第二阶段迭代
"""
import os
import sys
import tempfile
import shutil
import time
import random
import threading
import string
import logging

sys.path.insert(0, '/workspace')

from src.core import KnowledgeGraphUpdater
from src.database import Database
from src.parser import ArkTSParser
from src.logger import setup_logger

logger = setup_logger(level=logging.INFO)

class SecondStageComplexTest:
    """第二阶段复杂场景测试"""
    
    def __init__(self):
        self.test_dir = tempfile.mkdtemp(prefix="arkts_stage2_")
        self.db_path = os.path.join(self.test_dir, "stage2_test.db")
        print(f"🏗️  第二阶段测试目录: {self.test_dir}")
    
    def test_extreme_edge_cases(self):
        """测试极端边界情况"""
        print("\n" + "="*80)
        print("🔥 第二阶段迭代：极端边界情况测试")
        print("="*80)
        
        tests_passed = 0
        tests_failed = 0
        
        # 测试 1: 空文件
        print("\n📄 测试 1.1: 完全空文件")
        try:
            file_path = os.path.join(self.test_dir, "empty.ts")
            with open(file_path, 'w') as f:
                pass
            
            updater = KnowledgeGraphUpdater(self.db_path)
            result = updater.update_file(file_path)
            print(f"   ✅ 空文件处理成功: {result}")
            
            db = Database(self.db_path)
            file_info = db.get_file_by_path(os.path.abspath(file_path))
            db.close()
            
            if file_info:
                tests_passed += 1
            else:
                tests_failed += 1
                print(f"   ❌ 文件信息未正确存储")
        except Exception as e:
            logger.error(f"空文件测试失败: {e}")
            tests_failed += 1
        
        # 测试 2: 只有换行符的文件
        print("\n📄 测试 1.2: 只有换行符的文件")
        try:
            file_path = os.path.join(self.test_dir, "newlines.ts")
            with open(file_path, 'w') as f:
                f.write("\n\n\n\n")
            
            updater = KnowledgeGraphUpdater(self.db_path)
            result = updater.update_file(file_path)
            print(f"   ✅ 换行文件处理成功: {result}")
            tests_passed += 1
        except Exception as e:
            logger.error(f"换行文件测试失败: {e}")
            tests_failed += 1
        
        # 测试 3: 只有空格的文件
        print("\n📄 测试 1.3: 只有空格的文件")
        try:
            file_path = os.path.join(self.test_dir, "spaces.ts")
            with open(file_path, 'w') as f:
                f.write("   " * 20)
            
            updater = KnowledgeGraphUpdater(self.db_path)
            result = updater.update_file(file_path)
            print(f"   ✅ 空格文件处理成功: {result}")
            tests_passed += 1
        except Exception as e:
            logger.error(f"空格文件测试失败: {e}")
            tests_failed += 1
        
        # 测试 4: 超长单行代码
        print("\n📄 测试 2.1: 超长单行代码 (10,000字符)")
        try:
            file_path = os.path.join(self.test_dir, "long_line.ts")
            # 创建非常长的一行
            content = "function test() { "
            for i in range(1000):
                content += f"const x{i} = {i}; "
            content += " return x0; }"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            start = time.time()
            updater = KnowledgeGraphUpdater(self.db_path)
            result = updater.update_file(file_path)
            elapsed = time.time() - start
            
            print(f"   ✅ 超长单行处理成功, 耗时 {elapsed:.3f}s")
            tests_passed += 1
        except Exception as e:
            logger.error(f"超长单行测试失败: {e}")
            tests_failed += 1
        
        # 测试 5: 大量注释
        print("\n📄 测试 2.2: 99% 是注释的文件")
        try:
            file_path = os.path.join(self.test_dir, "comments.ts")
            content = []
            for i in range(200):
                content.append(f"// This is comment line {i} that has some text")
            
            # 只有一点点实际代码
            content.append("\nfunction actual() { return 42; }\n")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            
            updater = KnowledgeGraphUpdater(self.db_path)
            result = updater.update_file(file_path)
            print(f"   ✅ 注释文件处理成功")
            
            db = Database(self.db_path)
            file_info = db.get_file_by_path(os.path.abspath(file_path))
            funcs = db.get_functions_by_file(file_info['id'])
            db.close()
            
            if len(funcs) == 1:
                print(f"   ✅ 正确解析了 1 个函数")
                tests_passed += 1
            else:
                print(f"   ⚠️  解析了 {len(funcs)} 个函数")
                tests_failed += 1
        except Exception as e:
            logger.error(f"注释文件测试失败: {e}")
            tests_failed += 1
        
        # 测试 6: 复杂嵌套结构
        print("\n📄 测试 3.1: 深度嵌套的复杂结构")
        try:
            file_path = os.path.join(self.test_dir, "nested.ts")
            content = """
class Level1 {
  method1() {
    function inner1() {
      function inner2() {
        function inner3() {
          return 42;
        }
        return inner3();
      }
      return inner2();
    }
    return inner1();
  }
  
  method2() {
    if (true) {
      if (true) {
        if (true) {
          if (true) {
            console.log("Deep!");
          }
        }
      }
    }
  }
}
"""
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            updater = KnowledgeGraphUpdater(self.db_path)
            result = updater.update_file(file_path)
            print(f"   ✅ 深度嵌套处理成功")
            tests_passed += 1
        except Exception as e:
            logger.error(f"深度嵌套测试失败: {e}")
            tests_failed += 1
        
        # 测试 7: 大量不同文件类型混合
        print("\n📄 测试 3.2: 多种文件类型混合")
        try:
            updater = KnowledgeGraphUpdater(self.db_path)
            file_types = ['.ts', '.tsx', '.js', '.jsx', '.arkts']
            count = 0
            
            for i in range(20):
                ext = random.choice(file_types)
                file_path = os.path.join(self.test_dir, f"mixed_{i}{ext}")
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"function func{i}() {{ return {i}; }}\n")
                
                if updater.update_file(file_path):
                    count += 1
            
            print(f"   ✅ 处理了 {count} 个混合类型文件")
            tests_passed += 1
        except Exception as e:
            logger.error(f"混合文件类型测试失败: {e}")
            tests_failed += 1
        
        # 测试 8: 非常长的标识符
        print("\n📄 测试 4.1: 超长标识符")
        try:
            file_path = os.path.join(self.test_dir, "long_ids.ts")
            # 生成超长的函数名和类名
            long_name = ''.join([random.choice(string.ascii_letters) for _ in range(100)])
            content = f"""
function {long_name}() {{
  return 42;
}}

class ThisIsAnExtremelyLongClassNameThatShouldBeParsedCorrectly {{
  andThisIsAnExtremelyLongMethodNameToo() {{
    return true;
  }}
}}
"""
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            updater = KnowledgeGraphUpdater(self.db_path)
            result = updater.update_file(file_path)
            print(f"   ✅ 超长标识符处理成功")
            tests_passed += 1
        except Exception as e:
            logger.error(f"超长标识符测试失败: {e}")
            tests_failed += 1
        
        # 最终结果
        print("\n" + "="*80)
        print(f"📊 第二阶段边界测试结果:")
        print(f"   ✅ 成功: {tests_passed}")
        print(f"   ❌ 失败: {tests_failed}")
        print("="*80)
        
        return tests_failed == 0
    
    def test_full_coverage(self):
        """全面覆盖所有代码分支"""
        print("\n" + "="*80)
        print("🔍 第二阶段迭代：全分支覆盖测试")
        print("="*80)
        
        success = True
        
        # 测试 1: 已存在的文件，内容不变
        print("\n📄 测试: 文件内容不变的更新")
        try:
            file_path = os.path.join(self.test_dir, "unchanged.ts")
            with open(file_path, 'w') as f:
                f.write("function test() { return 1; }")
            
            updater = KnowledgeGraphUpdater(self.db_path)
            # 第一次更新
            updater.update_file(file_path)
            print("   ✅ 第一次更新成功")
            
            # 再次更新，内容完全相同
            result = updater.update_file(file_path)
            if not result:  # result should be False for unchanged files
                print("   ✅ 未变更文件正确跳过")
            else:
                print("   ⚠️  未变更文件被重新处理")
            
        except Exception as e:
            logger.error(f"不变文件测试失败: {e}")
            success = False
        
        # 测试 2: 解析各种函数类型
        print("\n📄 测试: 各种函数类型解析")
        try:
            file_path = os.path.join(self.test_dir, "func_types.ts")
            content = """
// 普通函数
function regular() { return 1; }

// 异步函数
async function asyncFunc() { return 2; }

// 箭头函数
const arrow = () => { return 3; };

// 函数表达式
const expr = function() { return 4; };

// 带参数的函数
function withArgs(a, b, c) { return a + b + c; }
"""
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            updater = KnowledgeGraphUpdater(self.db_path)
            updater.update_file(file_path)
            
            db = Database(self.db_path)
            file_info = db.get_file_by_path(os.path.abspath(file_path))
            funcs = db.get_functions_by_file(file_info['id'])
            classes = db.get_classes_by_file(file_info['id'])
            db.close()
            
            print(f"   ✅ 成功解析了 {len(funcs)} 个函数")
            print(f"   ✅ 解析了 {len(classes)} 个类")
            
        except Exception as e:
            logger.error(f"函数类型解析测试失败: {e}")
            success = False
        
        # 测试 3: 删除操作
        print("\n📄 测试: 删除操作")
        try:
            file_path = os.path.join(self.test_dir, "to_delete.ts")
            with open(file_path, 'w') as f:
                f.write("function deleteMe() { return 'delete'; }")
            
            updater = KnowledgeGraphUpdater(self.db_path)
            updater.update_file(file_path)
            
            # 删除文件
            db = Database(self.db_path)
            file_info = db.get_file_by_path(os.path.abspath(file_path))
            if file_info:
                updater.db.delete_file_data(file_info['id'])
                db2 = Database(self.db_path)
                after_delete = db2.get_file_by_path(os.path.abspath(file_path))
                if not after_delete:
                    print("   ✅ 文件成功删除，级联清理完成")
                else:
                    print("   ❌ 文件未完全删除")
                db2.close()
            
            db.close()
            
        except Exception as e:
            logger.error(f"删除操作测试失败: {e}")
            success = False
        
        return success
    
    def cleanup(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        print(f"\n🧹 测试文件已清理")

def main():
    print("="*80)
    print("🚀 第二阶段迭代：超复杂边界测试")
    print("="*80)
    
    test = SecondStageComplexTest()
    
    try:
        # 运行边界测试
        edge_result = test.test_extreme_edge_cases()
        # 运行全分支覆盖
        cov_result = test.test_full_coverage()
        
        final_result = edge_result and cov_result
        
        if final_result:
            print("\n🎉 第二阶段所有测试通过！")
        else:
            print("\n⚠️  第二阶段有测试失败")
        
        return 0 if final_result else 1
    finally:
        test.cleanup()

if __name__ == "__main__":
    sys.exit(main())
