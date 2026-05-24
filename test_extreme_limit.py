#!/usr/bin/env python3
"""
极限测试：处理超大规模、超复杂、超混乱场景
测试目标：发现系统在极端场景下的潜在问题
"""
import os
import sys
import tempfile
import shutil
import time
import random
import string
import threading
import traceback
from typing import List, Dict, Any
import logging

sys.path.insert(0, '/workspace')

from src.core import KnowledgeGraphUpdater
from src.database import Database
from src.parser import ArkTSParser
from src.logger import setup_logger

logger = setup_logger(level=logging.DEBUG)

class ExtremeLimitTest:
    """极限测试类"""
    
    def __init__(self):
        self.test_dir = tempfile.mkdtemp(prefix="arkts_extreme_")
        self.db_path = os.path.join(self.test_dir, "extreme_test.db")
        self.results = []
        self.errors = []
        print(f"🏗️  极限测试目录: {self.test_dir}")
    
    def log_result(self, test_name: str, success: bool, details: str = "", time_taken: float = 0):
        """记录测试结果"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'time_taken': time_taken
        }
        self.results.append(result)
        if not success:
            self.errors.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {test_name}")
        if time_taken > 0:
            print(f"     ⏱️  耗时: {time_taken:.4f}秒")
        if details:
            print(f"     📝 详情: {details}")
    
    def generate_ultra_complex_file(self, file_path: str, complexity: int = 50):
        """生成超复杂的测试文件"""
        code_parts = []
        
        # 添加大量导入
        for i in range(random.randint(5, 20)):
            imports = random.choice(['import {', 'import '])
            if imports == 'import {':
                symbols = ', '.join(random.choice(string.ascii_letters) for _ in range(random.randint(1, 5)))
                code_parts.append(f'import {{ {symbols} }} from "@/module{i}";')
            else:
                code_parts.append(f'import Default{i} from "@/module{i}";')
        
        # 添加常量声明
        for i in range(random.randint(5, 30)):
            const_name = ''.join(random.choice(string.ascii_letters) for _ in range(8))
            value_type = random.choice(['string', 'number', 'boolean'])
            if value_type == 'string':
                value = f'"{random.choice(string.ascii_letters * 10)}"'
            elif value_type == 'number':
                value = str(random.randint(0, 10000))
            else:
                value = 'true' if random.random() > 0.5 else 'false'
            code_parts.append(f'const {const_name}: {value_type} = {value};')
        
        # 添加大量函数
        for i in range(random.randint(complexity // 2, complexity)):
            func_name = ''.join(random.choice(string.ascii_letters) for _ in range(6))
            if random.random() > 0.7:
                code_parts.append(f'async function {func_name}() {{')
            else:
                code_parts.append(f'function {func_name}() {{')
            
            code_parts.append(f'  // Function body {i}')
            for j in range(random.randint(3, 15)):
                if random.random() > 0.5:
                    var_name = ''.join(random.choice(string.ascii_letters) for _ in range(4))
                    code_parts.append(f'  const {var_name} = {random.randint(0, 100)};')
                else:
                    another_func = ''.join(random.choice(string.ascii_letters) for _ in range(5))
                    code_parts.append(f'  {another_func}();')
            code_parts.append('}')
        
        # 添加复杂类结构
        for i in range(random.randint(complexity // 3, complexity // 2)):
            class_name = ''.join(random.choice(string.ascii_uppercase) for _ in range(1)) + \
                        ''.join(random.choice(string.ascii_letters) for _ in range(5))
            code_parts.append(f'class {class_name} {{')
            
            for j in range(random.randint(2, 10)):
                method_name = ''.join(random.choice(string.ascii_letters) for _ in range(5))
                code_parts.append(f'  {method_name}() {{')
                for k in range(random.randint(2, 8)):
                    var_name = ''.join(random.choice(string.ascii_letters) for _ in range(3))
                    code_parts.append(f'    this.{var_name} = {random.randint(0, 100)};')
                code_parts.append('  }')
            
            code_parts.append('}')
        
        content = '\n'.join(code_parts)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def test_very_large_file(self):
        """测试超大型文件（10000行+）"""
        print("\n" + "="*80)
        print("📄 测试 1: 超大型文件处理")
        print("="*80)
        
        start_time = time.time()
        try:
            large_file = os.path.join(self.test_dir, "very_large_file.ts")
            code_lines = []
            
            for i in range(15000):  # 15000行
                if i % 15 == 0:
                    func_name = f'function_{i // 15}'
                    code_lines.append(f'function {func_name}() {{')
                    code_lines.append(f'  return {i};')
                    code_lines.append('}')
                elif i % 7 == 0:
                    class_name = f'Class_{i // 7}'
                    code_lines.append(f'class {class_name} {{')
                    code_lines.append('  method() {')
                    code_lines.append(f'    return {i};')
                    code_lines.append('  }')
                    code_lines.append('}')
                else:
                    code_lines.append(f'// Comment line {i}')
            
            with open(large_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(code_lines))
            
            updater = KnowledgeGraphUpdater(self.db_path)
            success = updater.update_file(large_file)
            updater.close()
            
            elapsed = time.time() - start_time
            
            if success:
                db = Database(self.db_path)
                file_info = db.get_file_by_path(os.path.abspath(large_file))
                if file_info:
                    funcs = len(db.get_functions_by_file(file_info['id']))
                    classes = len(db.get_classes_by_file(file_info['id']))
                    db.close()
                    self.log_result(
                        "超大型文件处理", 
                        True, 
                        f"解析了 {funcs} 个函数和 {classes} 个类，共 15000行",
                        elapsed
                    )
                else:
                    db.close()
                    self.log_result("超大型文件处理", False, "文件未找到", elapsed)
            else:
                self.log_result("超大型文件处理", False, "更新失败", elapsed)
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"超大型文件测试异常: {e}")
            self.log_result("超大型文件处理", False, f"异常: {str(e)}", elapsed)
    
    def test_many_small_files(self):
        """测试大量小文件（1000个文件）"""
        print("\n" + "="*80)
        print("📂 测试 2: 大量小文件处理（1000个）")
        print("="*80)
        
        start_time = time.time()
        files_created = 0
        files_processed = 0
        
        try:
            updater = KnowledgeGraphUpdater(self.db_path)
            
            for i in range(1000):
                file_path = os.path.join(self.test_dir, f"small_file_{i:04d}.ts")
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f'function smallFunc{i}() {{ return {i}; }}\n')
                files_created += 1
                
                if updater.update_file(file_path):
                    files_processed += 1
            
            updater.close()
            
            elapsed = time.time() - start_time
            self.log_result(
                "大量小文件处理", 
                files_processed == files_created, 
                f"创建 {files_created} 个，处理 {files_processed} 个",
                elapsed
            )
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"大量小文件测试异常: {e}")
            self.log_result("大量小文件处理", False, f"异常: {str(e)}", elapsed)
    
    def test_deeply_nested_directories(self):
        """测试深层嵌套目录结构"""
        print("\n" + "="*80)
        print("📁 测试 3: 深层嵌套目录结构")
        print("="*80)
        
        start_time = time.time()
        try:
            # 创建深层嵌套目录
            current_dir = self.test_dir
            nested_path = []
            for i in range(25):  # 25层嵌套
                current_dir = os.path.join(current_dir, f"level_{i}")
                os.makedirs(current_dir, exist_ok=True)
                nested_path.append(current_dir)
            
            # 在每一层都放一个文件
            updater = KnowledgeGraphUpdater(self.db_path)
            files_processed = 0
            
            for i, dir_path in enumerate(nested_path):
                file_path = os.path.join(dir_path, f"file_level_{i}.ts")
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f'function funcLevel{i}() {{ return {i}; }}\n')
                
                if updater.update_file(file_path):
                    files_processed += 1
            
            updater.close()
            
            elapsed = time.time() - start_time
            self.log_result(
                "深层嵌套目录", 
                files_processed == 25, 
                f"处理了 {files_processed} 层嵌套目录中的文件",
                elapsed
            )
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"嵌套目录测试异常: {e}")
            self.log_result("嵌套目录", False, f"异常: {str(e)}", elapsed)
    
    def test_special_characters(self):
        """测试特殊字符和Unicode"""
        print("\n" + "="*80)
        print("🌍 测试 4: 特殊字符和Unicode支持")
        print("="*80)
        
        start_time = time.time()
        try:
            # 创建包含各种特殊字符的文件
            special_file = os.path.join(self.test_dir, "special_chars.ts")
            with open(special_file, 'w', encoding='utf-8') as f:
                f.write('// 中文注释\n')
                f.write('// 日本語コメント\n')
                f.write('// 한국어 댓글\n')
                f.write('// Emoji: 🚀🔥💻📱🌐💡🎯✅\n')
                f.write('// 数学符号: ∑∞π√≠≤≥±×÷\n')
                f.write('// 箭头: ←↑→↓↔↕\n')
                f.write('\n')
                f.write('class 中文类名 {\n')
                f.write('  公共方法() {\n')
                f.write('    console.log("测试");\n')
                f.write('  }\n')
                f.write('}\n')
                f.write('\n')
                f.write('const 变量名 = "值";\n')
            
            updater = KnowledgeGraphUpdater(self.db_path)
            success = updater.update_file(special_file)
            updater.close()
            
            elapsed = time.time() - start_time
            
            if success:
                db = Database(self.db_path)
                file_info = db.get_file_by_path(os.path.abspath(special_file))
                db.close()
                
                if file_info:
                    self.log_result(
                        "特殊字符处理", 
                        True, 
                        "Unicode和特殊字符支持正常",
                        elapsed
                    )
                else:
                    self.log_result("特殊字符处理", False, "文件记录未找到", elapsed)
            else:
                self.log_result("特殊字符处理", False, "更新失败", elapsed)
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"特殊字符测试异常: {e}")
            self.log_result("特殊字符处理", False, f"异常: {str(e)}", elapsed)
    
    def test_extreme_concurrency(self):
        """测试极限并发（20个线程）"""
        print("\n" + "="*80)
        print("⚡ 测试 5: 极限并发（20个线程）")
        print("="*80)
        
        start_time = time.time()
        success_count = 0
        error_count = 0
        operations_completed = 0
        
        def worker(thread_id: int, num_ops: int):
            nonlocal success_count, error_count, operations_completed
            local_updater = None
            try:
                local_updater = KnowledgeGraphUpdater(self.db_path)
                for i in range(num_ops):
                    file_path = os.path.join(self.test_dir, f"concurrency_{thread_id}_{i:03d}.ts")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(f'function thread{thread_id}Func{i}() {{ return {thread_id * 100 + i}; }}\n')
                    
                    if local_updater.update_file(file_path):
                        success_count += 1
                    operations_completed += 1
            except Exception as e:
                logger.error(f"线程 {thread_id} 异常: {e}")
                error_count += 1
            finally:
                if local_updater:
                    local_updater.close()
        
        try:
            threads = []
            for i in range(20):
                t = threading.Thread(target=worker, args=(i, 30))
                threads.append(t)
                t.start()
            
            for t in threads:
                t.join()
            
            elapsed = time.time() - start_time
            
            self.log_result(
                "极限并发", 
                error_count == 0, 
                f"{20}个线程，{operations_completed}次操作，成功 {success_count}，错误 {error_count}",
                elapsed
            )
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"并发测试异常: {e}")
            self.log_result("极限并发", False, f"异常: {str(e)}", elapsed)
    
    def test_rapid_file_changes(self):
        """测试快速文件变化（1000次更新）"""
        print("\n" + "="*80)
        print("🔄 测试 6: 快速文件变化（1000次更新）")
        print("="*80)
        
        start_time = time.time()
        changes_made = 0
        try:
            updater = KnowledgeGraphUpdater(self.db_path)
            change_file = os.path.join(self.test_dir, "rapid_changes.ts")
            
            for i in range(1000):
                with open(change_file, 'w', encoding='utf-8') as f:
                    f.write(f'function version{i}() {{ return {i}; }}\n')
                
                if updater.update_file(change_file):
                    changes_made += 1
            
            updater.close()
            
            elapsed = time.time() - start_time
            
            self.log_result(
                "快速文件变化", 
                changes_made == 1000, 
                f"完成 {changes_made}/1000 次文件更新",
                elapsed
            )
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"快速文件变化测试异常: {e}")
            self.log_result("快速文件变化", False, f"异常: {str(e)}", elapsed)
    
    def test_complex_typing(self):
        """测试复杂TypeScript类型声明"""
        print("\n" + "="*80)
        print("📝 测试 7: 复杂TypeScript类型")
        print("="*80)
        
        start_time = time.time()
        try:
            typing_file = os.path.join(self.test_dir, "complex_types.ts")
            with open(typing_file, 'w', encoding='utf-8') as f:
                f.write('// Complex TypeScript Types\n')
                f.write('type User = {\n')
                f.write('  id: number;\n')
                f.write('  name: string;\n')
                f.write('  email: string;\n')
                f.write('  age?: number;\n')
                f.write('};\n')
                f.write('\n')
                f.write('interface Product {\n')
                f.write('  id: string;\n')
                f.write('  name: string;\n')
                f.write('  price: number;\n')
                f.write('}\n')
                f.write('\n')
                f.write('type ApiResponse<T> = {\n')
                f.write('  data: T;\n')
                f.write('  status: number;\n')
                f.write('  message?: string;\n')
                f.write('};\n')
                f.write('\n')
                f.write('type UserProduct = User & Product;\n')
                f.write('\n')
                f.write('function processData<T>(data: T): ApiResponse<T> {\n')
                f.write('  return {\n')
                f.write('    data,\n')
                f.write('    status: 200\n')
                f.write('  };\n')
                f.write('}\n')
            
            updater = KnowledgeGraphUpdater(self.db_path)
            success = updater.update_file(typing_file)
            updater.close()
            
            elapsed = time.time() - start_time
            
            if success:
                db = Database(self.db_path)
                file_info = db.get_file_by_path(os.path.abspath(typing_file))
                db.close()
                
                self.log_result(
                    "复杂TypeScript类型", 
                    True, 
                    "复杂类型声明处理正常",
                    elapsed
                )
            else:
                self.log_result("复杂TypeScript类型", False, "更新失败", elapsed)
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"复杂类型测试异常: {e}")
            self.log_result("复杂TypeScript类型", False, f"异常: {str(e)}", elapsed)
    
    def test_all(self):
        """运行所有极限测试"""
        print("🚀 开始运行极限测试套件...")
        
        self.test_very_large_file()
        self.test_many_small_files()
        self.test_deeply_nested_directories()
        self.test_special_characters()
        self.test_extreme_concurrency()
        self.test_rapid_file_changes()
        self.test_complex_typing()
        
        # 总结
        print("\n" + "="*80)
        print("📊 极限测试总结")
        print("="*80)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"\n✅ 总测试数: {total_tests}")
        print(f"✅ 通过: {passed_tests}")
        print(f"❌ 失败: {failed_tests}")
        
        if self.errors:
            print(f"\n❌ 失败详情:")
            for error in self.errors:
                print(f"  - {error['test_name']}: {error['details']}")
        else:
            print(f"\n🎉 所有极限测试通过！")
        
        return passed_tests == total_tests
    
    def cleanup(self):
        """清理测试文件"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        print(f"\n🧹 测试文件已清理")

def main():
    """主函数"""
    print("="*80)
    print("🚀 极限测试：ArkTS知识图谱系统极端场景")
    print("="*80)
    
    test = ExtremeLimitTest()
    try:
        success = test.test_all()
        return 0 if success else 1
    finally:
        test.cleanup()

if __name__ == "__main__":
    sys.exit(main())
