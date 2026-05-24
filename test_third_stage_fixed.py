#!/usr/bin/env python3
"""
第三阶段迭代修正版：每个测试使用独立数据库
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
from typing import List

sys.path.insert(0, '/workspace')

from src.core import KnowledgeGraphUpdater
from src.database import Database
from src.parser import ArkTSParser
from src.logger import setup_logger

logger = setup_logger(level=logging.INFO)

class ThirdStageFixedTest:
    """第三阶段修正测试类"""
    
    def __init__(self):
        self.base_dir = tempfile.mkdtemp(prefix="arkts_stage3_fixed_")
        print(f"🏗️  第三阶段修正版测试目录: {self.base_dir}")
    
    def get_test_dir(self, test_name: str):
        """为每个测试创建独立目录"""
        test_dir = os.path.join(self.base_dir, test_name)
        os.makedirs(test_dir, exist_ok=True)
        return test_dir
    
    def generate_massive_file(self, directory: str, num_functions: int = 500, num_classes: int = 200):
        """生成超大文件"""
        file_path = os.path.join(directory, "massive.ts")
        content_parts = []
        
        for i in range(100):
            content_parts.append(f"const CONSTANT_{i} = {random.randint(0, 10000)};")
        
        for i in range(num_functions):
            func_name = f"function_{i}_{''.join(random.choices(string.ascii_letters, k=5))}"
            content_parts.append(f"function {func_name}() {{")
            content_parts.append(f"  return {i};")
            content_parts.append("}")
        
        for i in range(num_classes):
            class_name = f"Class_{i}_{''.join(random.choices(string.ascii_uppercase, k=1))}{''.join(random.choices(string.ascii_letters, k=4))}"
            content_parts.append(f"class {class_name} {{")
            for j in range(random.randint(2, 5)):
                method_name = f"method_{j}"
                content_parts.append(f"  {method_name}() {{")
                content_parts.append(f"    return '{class_name}_{method_name}';")
                content_parts.append("  }")
            content_parts.append("}")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content_parts))
        
        return file_path
    
    def test_massive_single_file(self):
        """测试处理单个超大文件"""
        print("\n" + "="*80)
        print("🚀 第三阶段：单个超大文件压力测试")
        print("="*80)
        
        test_dir = self.get_test_dir("massive")
        db_path = os.path.join(test_dir, "massive.db")
        
        try:
            print("📄 正在生成 500 函数 + 200 类 的超大文件...")
            file_path = self.generate_massive_file(test_dir, 500, 200)
            
            file_size = os.path.getsize(file_path)
            print(f"   📊 生成文件大小: {file_size / 1024:.1f} KB")
            
            start_time = time.time()
            updater = KnowledgeGraphUpdater(db_path)
            result = updater.update_file(file_path)
            elapsed = time.time() - start_time
            
            print(f"   ⏱️  处理时间: {elapsed:.3f} 秒")
            print(f"   ✅ 处理结果: {result}")
            
            db = Database(db_path)
            file_info = db.get_file_by_path(os.path.abspath(file_path))
            
            if file_info:
                functions = db.get_functions_by_file(file_info['id'])
                classes = db.get_classes_by_file(file_info['id'])
                
                print(f"   📈 成功解析 {len(functions)} 个函数")
                print(f"   📈 成功解析 {len(classes)} 个类")
                
                if len(functions) > 0 and len(classes) > 0:
                    print("   ✅ 超大文件测试通过！")
                    db.close()
                    updater.close()
                    return True
                else:
                    print("   ❌ 解析内容不足")
                    db.close()
                    updater.close()
                    return False
            else:
                print("   ❌ 文件信息未找到")
                db.close()
                updater.close()
                return False
            
        except Exception as e:
            logger.error(f"超大文件测试失败: {e}", exc_info=True)
            return False
    
    def test_rapid_crud_operations(self):
        """测试快速的CRUD操作"""
        print("\n" + "="*80)
        print("🔄 第三阶段：快速CRUD操作测试")
        print("="*80)
        
        test_dir = self.get_test_dir("crud")
        db_path = os.path.join(test_dir, "crud.db")
        
        try:
            updater = KnowledgeGraphUpdater(db_path)
            operations_count = 0
            success_count = 0
            start_time = time.time()
            
            for i in range(100):
                file_path = os.path.join(test_dir, f"crud_{i:03d}.ts")
                
                with open(file_path, 'w') as f:
                    f.write(f"function crudFunc{i}() {{ return {i}; }}")
                
                if updater.update_file(file_path):
                    success_count += 1
                operations_count += 1
                
                if i % 2 == 0:
                    time.sleep(0.001)
                    with open(file_path, 'w') as f:
                        f.write(f"function crudFunc{i}() {{ return {i + 1000}; }}")
                    if updater.update_file(file_path):
                        success_count += 1
                    operations_count += 1
            
            for i in range(0, 100, 3):
                file_path = os.path.join(test_dir, f"crud_{i:03d}.ts")
                if os.path.exists(file_path):
                    db = Database(db_path)
                    file_info = db.get_file_by_path(os.path.abspath(file_path))
                    db.close()
                    if file_info:
                        updater.db.delete_file_data(file_info['id'])
                        os.remove(file_path)
                        success_count += 1
                        operations_count += 1
            
            elapsed = time.time() - start_time
            print(f"   ⏱️  总耗时: {elapsed:.3f} 秒")
            print(f"   📊 总操作: {operations_count}")
            print(f"   ✅ 成功: {success_count}")
            print(f"   💨 平均速度: {operations_count / elapsed:.1f} 操作/秒")
            
            db = Database(db_path)
            all_files = db.get_all_files()
            db.close()
            
            print(f"   📂 最终数据库中有 {len(all_files)} 个文件")
            
            updater.close()
            return operations_count == success_count
            
        except Exception as e:
            logger.error(f"CRUD测试失败: {e}", exc_info=True)
            return False
    
    def test_branch_coverage_complete(self):
        """完全的分支覆盖测试"""
        print("\n" + "="*80)
        print("🔍 第三阶段：完整分支覆盖测试")
        print("="*80)
        
        test_dir = self.get_test_dir("branch")
        db_path = os.path.join(test_dir, "branch.db")
        
        try:
            updater = KnowledgeGraphUpdater(db_path)
            
            print("\n   📋 测试 1: 完全正常的文件")
            normal_file = os.path.join(test_dir, "normal.ts")
            with open(normal_file, 'w') as f:
                f.write("""
import { A, B } from 'module';

function testFunc() {
  return 42;
}

class TestClass {
  method1() { return true; }
  method2() { return false; }
}
""")
            result1 = updater.update_file(normal_file)
            print(f"      ✅ 结果: {result1}")
            
            print("\n   📋 测试 2: 不存在的文件")
            non_existent = os.path.join(test_dir, "does_not_exist.ts")
            result2 = updater.update_file(non_existent)
            print(f"      ✅ 结果: {result2} (预期: False)")
            
            print("\n   📋 测试 3: 复杂嵌套类")
            nested_file = os.path.join(test_dir, "nested_classes.ts")
            with open(nested_file, 'w') as f:
                f.write("""
class Outer {
  outerMethod() {
    return 'outer';
  }
}

class Inner1 extends Outer {
  innerMethod1() {
    return 'inner1';
  }
}

class Inner2 extends Outer {
  innerMethod2() {
    return 'inner2';
  }
}
""")
            result3 = updater.update_file(nested_file)
            print(f"      ✅ 结果: {result3}")
            
            print("\n   📋 测试 4: 各种导入语句")
            import_file = os.path.join(test_dir, "imports.ts")
            with open(import_file, 'w') as f:
                f.write("""
import Default from 'module-a';
import { Named, Another as Alias } from 'module-b';
import * as All from 'module-c';
import 'module-d';
import type { TypeA } from 'type-module';
""")
            result4 = updater.update_file(import_file)
            print(f"      ✅ 结果: {result4}")
            
            print("\n   📋 测试 5: 特殊字符编码")
            unicode_file = os.path.join(test_dir, "unicode_test.ts")
            with open(unicode_file, 'w', encoding='utf-8') as f:
                f.write("""
// Unicode 测试文件
// 中文：这是中文
// 日文：日本語
// 韩文：한국어
// Emoji: 🌍 🚀 🔥

const chineseName = "张三";
const japaneseName = "田中";

function unicodeTest() {
  return "测试成功";
}
""")
            result5 = updater.update_file(unicode_file)
            print(f"      ✅ 结果: {result5}")
            
            updater.close()
            
            all_passed = result1 and not result2 and result3 and result4 and result5
            print("\n" + "="*80)
            print(f"   📊 分支覆盖测试: {'全部通过' if all_passed else '部分失败'}")
            
            return all_passed
            
        except Exception as e:
            logger.error(f"分支覆盖测试失败: {e}", exc_info=True)
            return False
    
    def test_data_integrity(self):
        """测试数据完整性"""
        print("\n" + "="*80)
        print("🔒 第三阶段：数据完整性测试")
        print("="*80)
        
        test_dir = self.get_test_dir("integrity")
        db_path = os.path.join(test_dir, "integrity.db")
        
        try:
            updater = KnowledgeGraphUpdater(db_path)
            
            for i in range(50):
                file_path = os.path.join(test_dir, f"integrity_{i}.ts")
                with open(file_path, 'w') as f:
                    f.write(f"function test{i}() {{ return {i}; }}\n")
                    f.write(f"\nclass Class{i} {{ method() {{ return {i}; }} }}")
                updater.update_file(file_path)
            
            db = Database(db_path)
            all_files = db.get_all_files()
            print(f"   📂 数据库中有 {len(all_files)} 个文件")
            
            all_good = True
            for file_info in all_files:
                functions = db.get_functions_by_file(file_info['id'])
                classes = db.get_classes_by_file(file_info['id'])
                
                if len(functions) != 1:
                    print(f"   ⚠️  文件 {file_info['path']}: 期望 1 个函数，但有 {len(functions)} 个")
                    all_good = False
                if len(classes) != 1:
                    print(f"   ⚠️  文件 {file_info['path']}: 期望 1 个类，但有 {len(classes)} 个")
                    all_good = False
            
            db.close()
            updater.close()
            
            if all_good:
                print("   ✅ 数据完整性验证通过！")
                return True
            else:
                print("   ❌ 数据完整性有问题！")
                return False
            
        except Exception as e:
            logger.error(f"数据完整性测试失败: {e}", exc_info=True)
            return False
    
    def run_all_tests(self):
        """运行所有第三阶段测试"""
        print("="*80)
        print("🚀 第三阶段迭代（修正版）：极端压力与优化测试")
        print("="*80)
        
        results = []
        
        results.append(("超大文件测试", self.test_massive_single_file()))
        results.append(("快速CRUD操作", self.test_rapid_crud_operations()))
        results.append(("分支覆盖测试", self.test_branch_coverage_complete()))
        results.append(("数据完整性", self.test_data_integrity()))
        
        print("\n" + "="*80)
        print("📊 第三阶段测试总结:")
        print("="*80)
        for name, result in results:
            status = "✅  通过" if result else "❌  失败"
            print(f"   {status}: {name}")
        
        all_passed = all(result for _, result in results)
        
        if all_passed:
            print("\n🎉 第三阶段所有测试通过！")
        else:
            print("\n⚠️  第三阶段有测试失败")
        
        return all_passed
    
    def cleanup(self):
        shutil.rmtree(self.base_dir, ignore_errors=True)
        print(f"\n🧹 测试文件已清理")

def main():
    print("="*80)
    print("🚀 第三阶段迭代（修正版）：极端压力与性能优化测试")
    print("="*80)
    
    test = ThirdStageFixedTest()
    
    try:
        success = test.run_all_tests()
        return 0 if success else 1
    finally:
        test.cleanup()

if __name__ == "__main__":
    sys.exit(main())
