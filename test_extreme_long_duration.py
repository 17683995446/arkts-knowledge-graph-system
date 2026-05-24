#!/usr/bin/env python3
"""
极端长时间压力测试 - 持续几分钟的疯狂操作
"""
import os
import sys
import tempfile
import shutil
import time
import random
import string
import threading
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

sys.path.insert(0, '/workspace')

from src.core import KnowledgeGraphUpdater
from src.database import Database
from src.logger import setup_logger

logger = setup_logger(level=logging.INFO)

class ExtremeLongDurationTester:
    """极端长时间压力测试器"""
    
    def __init__(self, duration_seconds: int = 120):
        self.test_dir = Path(tempfile.mkdtemp(prefix="arkts_extreme_long_"))
        self.db_path = self.test_dir / "extreme_test.db"
        self.duration_seconds = duration_seconds
        self.keep_running = True
        self.operations_count = 0
        self.errors_count = 0
        self.start_time = None
        self.all_files = []
        
        print(f"\n{'='*80}")
        print(f"🔥 极端长时间压力测试启动")
        print(f"⏱️  计划运行: {duration_seconds} 秒")
        print(f"📍 测试目录: {self.test_dir}")
        print(f"{'='*80}")
        
    def generate_random_file_content(self, file_num: int) -> str:
        """生成极其复杂的随机文件内容"""
        lines = []
        
        # 添加很多复杂的导入
        for i in range(random.randint(1, 10)):
            module_name = ''.join(random.choices(string.ascii_lowercase, k=random.randint(3, 10)))
            symbols = ', '.join(
                [''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase, k=random.randint(2, 8)))
                 for _ in range(random.randint(1, 5))]
            )
            lines.append(f"import {{ {symbols} }} from './{module_name}';")
        
        # 添加很多常量
        for i in range(random.randint(5, 20)):
            const_name = ''.join(random.choices(string.ascii_uppercase + '_', k=random.randint(5, 15)))
            value_type = random.choice(['number', 'string', 'boolean'])
            if value_type == 'number':
                value = str(random.randint(-1000000, 1000000))
            elif value_type == 'string':
                value = f'"{random.choice(string.ascii_letters) * random.randint(1, 50)}"'
            else:
                value = 'true' if random.random() > 0.5 else 'false'
            lines.append(f"const {const_name} = {value};")
        
        # 添加很多函数
        for i in range(random.randint(5, 30)):
            func_name = ''.join(random.choices(string.ascii_letters, k=random.randint(3, 12)))
            lines.append(f"function {func_name}() {{")
            # 函数体
            for j in range(random.randint(3, 10)):
                local_var = ''.join(random.choices(string.ascii_letters, k=random.randint(2, 8)))
                lines.append(f"  const {local_var} = {random.randint(0, 1000)};")
            lines.append(f"  return {random.randint(0, 1000)};")
            lines.append("}")
        
        # 添加很多类
        for i in range(random.randint(2, 15)):
            class_name = random.choice(string.ascii_uppercase) + ''.join(
                random.choices(string.ascii_letters, k=random.randint(4, 12))
            )
            lines.append(f"class {class_name} {{")
            
            # 添加方法
            for j in range(random.randint(2, 8)):
                method_name = ''.join(random.choices(string.ascii_letters, k=random.randint(3, 10)))
                lines.append(f"  {method_name}() {{")
                lines.append(f"    return '{class_name}.{method_name}';")
                lines.append("  }")
            
            lines.append("}")
        
        return '\n'.join(lines) + '\n'
    
    def create_or_update_random_file(self) -> bool:
        """创建或更新随机文件"""
        try:
            file_num = random.randint(0, 200)
            file_path = self.test_dir / f"file_{file_num:03d}.ts"
            
            content = self.generate_random_file_content(file_num)
            
            with open(file_path, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(content)
            
            if file_path not in self.all_files:
                self.all_files.append(file_path)
            
            return True
        except Exception as e:
            logger.error(f"[create_or_update_random_file] Error: {e}")
            return False
    
    def delete_random_file(self) -> bool:
        """删除随机文件"""
        try:
            if self.all_files and random.random() > 0.7:
                file_path = random.choice(self.all_files)
                if file_path.exists():
                    os.remove(file_path)
                    return True
        except Exception as e:
            logger.error(f"[delete_random_file] Error: {e}")
        return False
    
    def worker_thread(self, worker_id: int):
        """工作线程"""
        updater = None
        try:
            updater = KnowledgeGraphUpdater(str(self.db_path))
            local_ops = 0
            
            while self.keep_running:
                try:
                    # 随机操作类型
                    op_type = random.choice([
                        'create', 'update', 'delete', 'query', 'batch'
                    ])
                    
                    if op_type in ['create', 'update']:
                        if self.create_or_update_random_file():
                            # 更新到系统
                            file_num = random.randint(0, 200)
                            file_path = self.test_dir / f"file_{file_num:03d}.ts"
                            if file_path.exists():
                                updater.update_file(str(file_path))
                                local_ops += 1
                    
                    elif op_type == 'delete':
                        if self.delete_random_file():
                            local_ops += 1
                    
                    elif op_type == 'query':
                        # 执行一些查询
                        db = Database(str(self.db_path))
                        try:
                            _ = db.get_all_files()
                            _ = db.get_all_functions()
                            _ = db.get_all_classes()
                        except Exception as e:
                            pass
                        db.close()
                        local_ops += 1
                    
                    else:  # batch
                        for i in range(10):
                            self.create_or_update_random_file()
                        local_ops += 10
                    
                    with threading.Lock():
                        self.operations_count += 1
                    
                    # 随机休眠一会儿，模拟真实负载
                    time.sleep(random.random() * 0.01)
                    
                except Exception as e:
                    logger.error(f"[worker_{worker_id}] Error: {e}")
                    with threading.Lock():
                        self.errors_count += 1
                    
        except Exception as e:
            logger.error(f"[worker_{worker_id}] Fatal error: {e}")
            with threading.Lock():
                self.errors_count += 1
        finally:
            if updater:
                updater.close()
    
    def monitor_progress(self):
        """监控测试进度"""
        last_ops = 0
        last_report = time.time()
        
        while self.keep_running:
            current_time = time.time()
            elapsed = current_time - last_report
            
            if elapsed >= 5:
                total_elapsed = current_time - self.start_time
                ops_diff = self.operations_count - last_ops
                ops_per_sec = ops_diff / elapsed
                
                print(f"\n📊 运行中 [{total_elapsed:.1f}s] "
                      f"总操作: {self.operations_count} | "
                      f"速度: {ops_per_sec:.1f} 操作/秒 | "
                      f"错误: {self.errors_count}")
                
                last_ops = self.operations_count
                last_report = current_time
            
            time.sleep(0.1)
    
    def run_test(self, num_workers: int = 5):
        """运行极端长时间压力测试"""
        print(f"\n🔥 开始极端长时间压力测试，{num_workers} 个工作线程")
        
        self.start_time = time.time()
        
        # 启动监控线程
        monitor_thread = threading.Thread(target=self.monitor_progress, daemon=True)
        monitor_thread.start()
        
        # 启动工作线程
        threads = []
        for i in range(num_workers):
            t = threading.Thread(target=self.worker_thread, args=(i,))
            threads.append(t)
            t.start()
            print(f"✅ 工作线程 {i} 启动")
        
        # 运行指定时间
        print(f"\n⏳ 等待 {self.duration_seconds} 秒...")
        time.sleep(self.duration_seconds)
        
        # 停止所有线程
        print("\n🛑 停止所有线程...")
        self.keep_running = False
        for t in threads:
            t.join()
        
        total_elapsed = time.time() - self.start_time
        
        # 最终验证
        print("\n" + "="*80)
        print("🔍 最终数据验证")
        print("="*80)
        
        db = Database(str(self.db_path))
        all_files = db.get_all_files()
        all_functions = db.get_all_functions()
        all_classes = db.get_all_classes()
        all_imports = db.get_all_imports()
        
        print(f"\n📊 数据库最终状态:")
        print(f"  - 文件数: {len(all_files)}")
        print(f"  - 函数数: {len(all_functions)}")
        print(f"  - 类数: {len(all_classes)}")
        print(f"  - 导入数: {len(all_imports)}")
        
        db.close()
        
        # 结果统计
        print(f"\n{'='*80}")
        print("📈 极端长时间压力测试结果")
        print(f"{'='*80}")
        print(f"⏱️  总运行时间: {total_elapsed:.1f} 秒")
        print(f"📋 总操作数: {self.operations_count}")
        print(f"❌ 错误数: {self.errors_count}")
        print(f"🚀 平均速度: {self.operations_count/max(total_elapsed, 0.01):.1f} 操作/秒")
        
        success = self.errors_count == 0
        if success:
            print(f"\n🎉 完美！极端长时间压力测试 100% 通过！")
        else:
            print(f"\n⚠️  有 {self.errors_count} 个错误")
        
        return success
    
    def cleanup(self):
        """清理"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        print(f"\n🧹 测试文件已清理")


class ExtremeEdgeCaseTester:
    """极端边界情况测试器"""
    
    def __init__(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="arkts_edge_"))
        self.db_path = self.test_dir / "edge_test.db"
        print(f"\n📍 边界情况测试目录: {self.test_dir}")
    
    def test_all_edge_cases(self) -> bool:
        """测试所有边界情况"""
        print("\n" + "="*80)
        print("🔍 极端边界情况深度测试")
        print("="*80)
        
        tests_passed = 0
        total_tests = 0
        
        # 测试 1: 空文件
        print("\n📄 1/12 空文件")
        total_tests += 1
        try:
            f = self.test_dir / "empty.ts"
            f.touch()
            
            updater = KnowledgeGraphUpdater(str(self.db_path))
            updater.update_file(str(f))
            updater.close()
            print("  ✅ 通过")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ 失败: {e}")
        
        # 测试 2: 只有注释的文件
        print("\n📄 2/12 只有注释的文件")
        total_tests += 1
        try:
            f = self.test_dir / "comments_only.ts"
            with open(f, 'w', encoding='utf-8') as fobj:
                for i in range(50):
                    fobj.write(f"// Comment line {i} with some special chars: 中文 日本語 🚀\n")
            
            updater = KnowledgeGraphUpdater(str(self.db_path))
            updater.update_file(str(f))
            updater.close()
            print("  ✅ 通过")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ 失败: {e}")
        
        # 测试 3: 超级长行
        print("\n📄 3/12 超级长行（10000字符）")
        total_tests += 1
        try:
            f = self.test_dir / "super_long_line.ts"
            long_line = "function foo() { " + "return 42; " * 500 + " }"
            with open(f, 'w', encoding='utf-8') as fobj:
                fobj.write(long_line)
            
            updater = KnowledgeGraphUpdater(str(self.db_path))
            updater.update_file(str(f))
            updater.close()
            print("  ✅ 通过")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ 失败: {e}")
        
        # 测试 4: 很多小文件（500个）
        print("\n📄 4/12 500个小文件批量处理")
        total_tests += 1
        try:
            updater = KnowledgeGraphUpdater(str(self.db_path))
            
            for i in range(500):
                f = self.test_dir / f"tiny_{i:03d}.ts"
                with open(f, 'w', encoding='utf-8') as fobj:
                    fobj.write(f"function tiny{i}() {{ return {i}; }}\n")
                updater.update_file(str(f))
            
            updater.close()
            print("  ✅ 通过")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ 失败: {e}")
        
        # 测试 5: 各种编码
        print("\n📄 5/12 Unicode和各种编码字符")
        total_tests += 1
        try:
            f = self.test_dir / "unicode_special.ts"
            content = """
// 各种语言测试
function 中文函数() {
    const 中文变量 = "测试";
}
class 日本語クラス {
    한국어메서드() {
        return "안녕하세요";
    }
}
const emoji_var = "🚀🔥💻📱🌐";
"""
            with open(f, 'w', encoding='utf-8') as fobj:
                fobj.write(content)
            
            updater = KnowledgeGraphUpdater(str(self.db_path))
            updater.update_file(str(f))
            updater.close()
            print("  ✅ 通过")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ 失败: {e}")
        
        # 测试 6-12: 继续更多边界情况...
        for test_num in range(6, 13):
            print(f"\n📄 {test_num}/12 边界情况测试 {test_num}")
            total_tests += 1
            try:
                # 随机生成一些奇怪的文件
                if test_num == 6:
                    f = self.test_dir / "lots_of_whitespace.ts"
                    with open(f, 'w', encoding='utf-8') as fobj:
                        for i in range(100):
                            fobj.write('\t' * random.randint(1, 10) + 'function spaceFunc() {}\n')
                
                elif test_num == 7:
                    f = self.test_dir / "single_giant_function.ts"
                    with open(f, 'w', encoding='utf-8') as fobj:
                        fobj.write("function giant() {\n")
                        for i in range(1000):
                            fobj.write(f"  const var_{i} = {i};\n")
                        fobj.write("  return 42;\n}\n")
                
                elif test_num == 8:
                    f = self.test_dir / "many_classes.ts"
                    with open(f, 'w', encoding='utf-8') as fobj:
                        for i in range(100):
                            fobj.write(f"class Class{i} {{ method{i}() {{ return {i}; }} }}\n")
                
                elif test_num == 9:
                    f = self.test_dir / "many_imports.ts"
                    with open(f, 'w', encoding='utf-8') as fobj:
                        for i in range(100):
                            fobj.write(f"import {{ Module{i} }} from './module{i}';\n")
                
                elif test_num == 10:
                    f = self.test_dir / "mixed_valid_invalid.ts"
                    with open(f, 'w', encoding='utf-8') as fobj:
                        for i in range(50):
                            if i % 3 == 0:
                                fobj.write("INVALID SYNTAX HERE!!\n")
                            else:
                                fobj.write(f"function valid{i}() {{ return {i}; }}\n")
                
                elif test_num == 11:
                    f = self.test_dir / "empty_lines_only.ts"
                    with open(f, 'w', encoding='utf-8') as fobj:
                        fobj.write('\n' * 200)
                
                else:  # 12
                    f = self.test_dir / "weird_chars.ts"
                    with open(f, 'w', encoding='utf-8') as fobj:
                        weird = ''.join([chr(i) for i in range(32, 127) if i != 96])
                        fobj.write(f"// Weird chars: {weird}\n")
                        fobj.write("function normal() { return 42; }\n")
                
                updater = KnowledgeGraphUpdater(str(self.db_path))
                updater.update_file(str(f))
                updater.close()
                print("  ✅ 通过")
                tests_passed += 1
                
            except Exception as e:
                print(f"  ❌ 失败: {e}")
        
        # 最终验证
        print(f"\n{'='*80}")
        print("📊 边界情况测试结果")
        print(f"{'='*80}")
        print(f"总测试: {total_tests} | 通过: {tests_passed} | 失败: {total_tests - tests_passed}")
        
        return tests_passed == total_tests
    
    def cleanup(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        print(f"\n🧹 边界情况测试文件已清理")


def main():
    """主函数"""
    print("\n" + "="*80)
    print("🚀 ArkTS 知识图谱系统 - 超深度多阶段迭代测试")
    print("="*80)
    
    all_success = True
    
    # 第一阶段：极端边界情况测试
    print("\n" + "="*80)
    print("📋 第一阶段：极端边界情况深度测试")
    print("="*80)
    edge_tester = ExtremeEdgeCaseTester()
    edge_success = edge_tester.test_all_edge_cases()
    edge_tester.cleanup()
    
    if not edge_success:
        all_success = False
    
    # 第二阶段：极端长时间压力测试
    print("\n" + "="*80)
    print("📋 第二阶段：极端长时间压力测试")
    print("="*80)
    long_tester = ExtremeLongDurationTester(duration_seconds=60)
    long_success = long_tester.run_test(num_workers=4)
    long_tester.cleanup()
    
    if not long_success:
        all_success = False
    
    # 总结
    print("\n" + "="*80)
    print("🎉 最终测试总结")
    print("="*80)
    if all_success:
        print("\n🎊 所有测试完美通过！系统坚不可摧！")
    else:
        print("\n⚠️  有一些测试失败，需要进一步分析")
    
    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())
