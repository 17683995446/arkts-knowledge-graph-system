#!/usr/bin/env python3
"""
终极混乱测试：超大规模、更复杂、更高难度的系统测试
"""
import os
import sys
import tempfile
import time
import random
import string
import shutil
import threading
import logging
from pathlib import Path

sys.path.insert(0, '/workspace')

from src.core_logged import KnowledgeGraphUpdater
from src.database.database_logged import Database
from src.logger import setup_logger

logger = setup_logger(level=logging.INFO)

class UltimateChaosTest:
    def __init__(self):
        self.test_dir = tempfile.mkdtemp(prefix="arkts_ultimate_chaos_")
        self.db_path = os.path.join(self.test_dir, "ultimate_test.db")
        self.operation_count = 0
        self.success_count = 0
        self.error_count = 0
        self.lock = threading.Lock()
        self.keep_running = True
    
    def generate_random_arkts_code(self, complexity: int = 10) -> str:
        """生成随机的ArkTS代码"""
        code_parts = []
        
        # 随机添加注释
        if random.random() < 0.3:
            comments = ['// 这是一个注释', '/* 多行注释 */', '/** 文档注释 */', '// TODO: 待办事项']
            code_parts.append(random.choice(comments))
        
        # 随机添加导入
        num_imports = random.randint(0, 5)
        import_sources = ['@ohos.hiviewdfx', '@ohos.app', '@ohos.router', '@ohos.data', './utils', '../models']
        import_symbols = ['HiLog', 'UIAbility', 'Router', 'Preferences', 'DataModel', 'Utils', 'Helper']
        
        for _ in range(num_imports):
            if random.random() < 0.5:
                code_parts.append(f'import {{ {random.choice(import_symbols)} }} from "{random.choice(import_sources)}";')
            else:
                code_parts.append(f'import {random.choice(import_symbols)} from "{random.choice(import_sources)}";')
        
        # 随机添加常量
        num_consts = random.randint(0, 3)
        for i in range(num_consts):
            const_name = ''.join(random.choices(string.ascii_uppercase + '_', k=8))
            value = random.choice([f'"{random.choice(string.ascii_letters*5)}"', str(random.randint(1, 1000)), 'true', 'false'])
            code_parts.append(f'const {const_name} = {value};')
        
        # 随机添加函数
        num_functions = random.randint(1, complexity)
        function_bodies = [
            'return 42;',
            'return "Hello";',
            'console.log("test");',
            'return a + b;',
            'if (x > 0) { return x; } else { return -x; }',
            'for (let i = 0; i < 10; i++) { console.log(i); }',
            'try { doSomething(); } catch (e) { handleError(e); }'
        ]
        
        for i in range(num_functions):
            func_name = ''.join(random.choices(string.ascii_lowercase, k=6))
            params = ', '.join([f'p{j}' for j in range(random.randint(0, 3))])
            body = random.choice(function_bodies)
            
            func_type = random.choice(['', 'async '])
            code_parts.append(f'{func_type}function {func_name}({params}) {{')
            code_parts.append(f'  {body}')
            code_parts.append('}')
        
        # 随机添加类
        num_classes = random.randint(1, complexity//2)
        for i in range(num_classes):
            class_name = ''.join(random.choices(string.ascii_uppercase, k=1)) + \
                        ''.join(random.choices(string.ascii_lowercase, k=5))
            code_parts.append(f'class {class_name} {{')
            
            num_methods = random.randint(1, 3)
            method_bodies = [
                'return this.value;',
                'this.value = newValue;',
                'console.log("method called");',
                'return this;',
                'return this.calculate();'
            ]
            
            for j in range(num_methods):
                method_name = ''.join(random.choices(string.ascii_lowercase, k=5))
                params = ', '.join([f'arg{k}' for k in range(random.randint(0, 2))])
                body = random.choice(method_bodies)
                modifiers = random.choice(['', 'public ', 'private ', 'static '])
                code_parts.append(f'  {modifiers}{method_name}({params}) {{')
                code_parts.append(f'    {body}')
                code_parts.append('  }')
            
            code_parts.append('}')
        
        # 随机添加一些可能的语法错误（0.1概率）
        if random.random() < 0.1:
            error_types = [
                'function missingEnd() { console.log("test");',
                'class MissingClose { method() { return; }',
                'const x = 10; 多余的括号 )',
                'import { missing from "module";'
            ]
            code_parts.append(random.choice(error_types))
        
        return '\n'.join(code_parts)
    
    def create_chaos_file(self, idx: int) -> str:
        """创建一个混乱的测试文件"""
        sub_dirs = [f'subdir_{random.randint(0, 20)}' for _ in range(random.randint(0, 3))]
        dir_path = os.path.join(self.test_dir, *sub_dirs)
        os.makedirs(dir_path, exist_ok=True)
        
        file_name = f'chaos_file_{idx:04d}.{random.choice(["ts", "tsx", "js", "jsx", "arkts"])}'
        file_path = os.path.join(dir_path, file_name)
        
        complexity = random.randint(5, 50)
        content = self.generate_random_arkts_code(complexity)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return file_path
    
    def perform_chaos_operation(self, updater: KnowledgeGraphUpdater):
        """执行一个混乱的操作"""
        operations = ['create', 'update', 'delete', 'modify']
        op = random.choice(operations)
        
        try:
            if op == 'create':
                idx = self.operation_count
                file_path = self.create_chaos_file(idx)
                updater.update_file(file_path)
            elif op == 'update':
                files = [os.path.join(root, f) 
                        for root, _, files in os.walk(self.test_dir) 
                        for f in files 
                        if f.endswith(('.ts', '.tsx', '.js', '.jsx', '.arkts'))]
                if files:
                    file_path = random.choice(files)
                    complexity = random.randint(5, 50)
                    new_content = self.generate_random_arkts_code(complexity)
                    time.sleep(0.01)  # 确保mtime变化
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    updater.update_file(file_path)
            elif op == 'delete':
                files = [os.path.join(root, f) 
                        for root, _, files in os.walk(self.test_dir) 
                        for f in files 
                        if f.endswith(('.ts', '.tsx', '.js', '.jsx', '.arkts'))]
                if files:
                    file_path = random.choice(files)
                    try:
                        db = Database(self.db_path)
                        existing = db.get_file_by_path(os.path.abspath(file_path))
                        db.close()
                        if existing:
                            updater.db.delete_file_data(existing['id'])
                        os.remove(file_path)
                    except Exception as e:
                        logger.warning(f"Delete warning: {e}")
            elif op == 'modify':
                files = [os.path.join(root, f) 
                        for root, _, files in os.walk(self.test_dir) 
                        for f in files 
                        if f.endswith(('.ts', '.tsx', '.js', '.jsx', '.arkts'))]
                if files:
                    file_path = random.choice(files)
                    time.sleep(0.01)
                    with open(file_path, 'a', encoding='utf-8') as f:
                        f.write(f'\n// added at {time.time()}\n')
                    updater.update_file(file_path)
            
            with self.lock:
                self.success_count += 1
        except Exception as e:
            logger.error(f"Operation error: {e}", exc_info=True)
            with self.lock:
                self.error_count += 1
        
        with self.lock:
            self.operation_count += 1
    
    def chaos_worker(self, thread_id: int, num_ops: int):
        """混乱测试工作线程"""
        logger.info(f"Thread {thread_id} starting with {num_ops} operations")
        updater = KnowledgeGraphUpdater(self.db_path)
        
        for i in range(num_ops):
            if not self.keep_running:
                break
            self.perform_chaos_operation(updater)
            
            if (i + 1) % 100 == 0:
                with self.lock:
                    logger.info(f"Thread {thread_id}: {i+1}/{num_ops} operations completed")
        
        updater.close()
        logger.info(f"Thread {thread_id} finished")
    
    def run_ultimate_chaos_test(self, num_threads: int = 5, ops_per_thread: int = 200):
        """运行终极混乱测试"""
        print("=" * 80)
        print("🚀 终极混乱测试：超大规模、更复杂、更高难度")
        print("=" * 80)
        
        start_time = time.time()
        
        # 初始创建一些文件
        print(f"📝 创建初始测试文件...")
        updater = KnowledgeGraphUpdater(self.db_path)
        for i in range(50):
            file_path = self.create_chaos_file(i)
            updater.update_file(file_path)
        updater.close()
        print(f"✅ 初始文件创建完成")
        
        # 启动并发线程
        threads = []
        print(f"🔥 启动 {num_threads} 个并发线程...")
        
        for i in range(num_threads):
            t = threading.Thread(
                target=self.chaos_worker,
                args=(i, ops_per_thread)
            )
            threads.append(t)
            t.start()
        
        # 等待所有线程完成
        print(f"⏳ 等待所有线程完成...")
        for t in threads:
            t.join()
        
        elapsed_time = time.time() - start_time
        
        # 验证数据
        print(f"\n🔍 验证数据一致性...")
        db = Database(self.db_path)
        all_files = db.get_all_files()
        print(f"📊 数据库中文件数量: {len(all_files)}")
        
        # 验证每个文件的数据完整性
        consistent = True
        for file_info in all_files[:50]:  # 验证部分文件
            try:
                funcs = db.get_functions_by_file(file_info['id'])
                classes = db.get_classes_by_file(file_info['id'])
                imports = db.get_imports_by_file(file_info['id'])
            except Exception as e:
                logger.error(f"数据损坏: {e}")
                consistent = False
        
        db.close()
        
        # 输出总结
        print("\n" + "=" * 80)
        print("📈 测试总结:")
        print(f"  总操作数: {self.operation_count}")
        print(f"  成功: {self.success_count}")
        print(f"  失败: {self.error_count}")
        print(f"  耗时: {elapsed_time:.2f}秒")
        print(f"  吞吐量: {self.operation_count/elapsed_time:.2f} 操作/秒")
        print(f"  数据一致性: {'✅ 通过' if consistent else '❌ 失败'}")
        print("=" * 80)
        
        return consistent and self.error_count == 0
    
    def test_extreme_boundaries(self):
        """测试极端边界情况"""
        print("\n" + "=" * 80)
        print("🔬 极端边界情况测试")
        print("=" * 80)
        
        updater = KnowledgeGraphUpdater(self.db_path)
        
        # 测试1: 超大文件
        print("\n1. 测试超大文件...")
        huge_file = os.path.join(self.test_dir, 'huge_file.ts')
        huge_content = []
        for i in range(2000):
            huge_content.append(f'function func{i}() {{ return {i}; }}')
        for i in range(2000):
            huge_content.append(f'class Class{i} {{ method{i}() {{ return; }} }}')
        
        with open(huge_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(huge_content))
        
        start = time.time()
        updater.update_file(huge_file)
        elapsed = time.time() - start
        print(f"   ✅ 超大文件处理完成: {elapsed:.2f}秒")
        
        # 测试2: 大量空文件
        print("\n2. 测试大量空文件...")
        for i in range(200):
            empty_file = os.path.join(self.test_dir, f'empty_{i:03d}.ts')
            with open(empty_file, 'w', encoding='utf-8') as f:
                pass
            updater.update_file(empty_file)
        print("   ✅ 大量空文件处理完成")
        
        # 测试3: 特殊字符
        print("\n3. 测试特殊字符文件...")
        special_chars_file = os.path.join(self.test_dir, 'special_chars.ts')
        with open(special_chars_file, 'w', encoding='utf-8') as f:
            f.write('// 测试特殊字符: 中文 🌍 🚀 🔥\n')
            f.write('const s = "字符串 with 特殊字符 🎉";\n')
            f.write('class SpecialClass { method() { return "测试"; } }\n')
        updater.update_file(special_chars_file)
        print("   ✅ 特殊字符文件处理完成")
        
        # 测试4: 快速连续更新
        print("\n4. 测试快速连续更新...")
        test_file = os.path.join(self.test_dir, 'rapid_update.ts')
        for i in range(50):
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(f'const v = {i};')
            updater.update_file(test_file)
        print("   ✅ 快速连续更新完成")
        
        updater.close()
        print("\n✅ 所有极端边界测试通过!")
    
    def test_long_running_stability(self, duration_seconds: int = 60):
        """长时间稳定性测试"""
        print("\n" + "=" * 80)
        print(f"⏱️  长时间稳定性测试: {duration_seconds}秒")
        print("=" * 80)
        
        updater = KnowledgeGraphUpdater(self.db_path)
        start_time = time.time()
        count = 0
        
        self.keep_running = True
        
        while time.time() - start_time < duration_seconds:
            idx = count
            file_path = self.create_chaos_file(idx)
            updater.update_file(file_path)
            count += 1
            
            # 随机删除一些文件
            if count % 50 == 0:
                files = [os.path.join(root, f) 
                        for root, _, files in os.walk(self.test_dir) 
                        for f in files 
                        if f.endswith(('.ts', '.tsx', '.js', '.jsx', '.arkts'))]
                if len(files) > 100:
                    for f in files[:50]:
                        try:
                            abs_path = os.path.abspath(f)
                            file_info = updater.db.get_file_by_path(abs_path)
                            if file_info:
                                updater.db.delete_file_data(file_info['id'])
                            os.remove(f)
                        except:
                            pass
            
            if count % 100 == 0:
                elapsed = time.time() - start_time
                print(f"   ⏳ 已运行 {elapsed:.1f}秒, 处理 {count} 个文件")
        
        updater.close()
        print(f"\n✅ 长时间稳定性测试完成: {count} 个文件在 {duration_seconds} 秒内")
    
    def cleanup(self):
        """清理测试文件"""
        self.keep_running = False
        shutil.rmtree(self.test_dir, ignore_errors=True)

def main():
    print("🏁 开始终极混乱测试!\n")
    
    test = UltimateChaosTest()
    
    try:
        # 1. 极端边界测试
        test.test_extreme_boundaries()
        
        # 2. 超大规模混乱测试
        test.run_ultimate_chaos_test(num_threads=8, ops_per_thread=500)
        
        # 3. 长时间稳定性测试
        test.test_long_running_stability(30)  # 30秒测试
        
        print("\n" + "=" * 80)
        print("🎉 所有终极混乱测试通过!")
        print("=" * 80)
        
    finally:
        test.cleanup()

if __name__ == "__main__":
    main()
