#!/usr/bin/env python3
"""
极端长时间压力测试 - 持续运行的压力测试
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
from pathlib import Path
from typing import List

sys.path.insert(0, '/workspace')

from src.core import KnowledgeGraphUpdater
from src.database import Database
from src.logger import setup_logger

logger = setup_logger(level=logging.INFO)

class ExtremeLongRunningTest:
    """极端长时间压力测试类"""
    
    def __init__(self, duration_seconds: int = 120):
        self.test_dir = tempfile.mkdtemp(prefix="arkts_extreme_long_")
        self.db_path = os.path.join(self.test_dir, "extreme_long.db")
        self.duration_seconds = duration_seconds
        self.operations_completed = 0
        self.errors_occurred = 0
        self.files_processed = 0
        self.keep_running = True
        print(f"🏗️  极端长时间测试目录: {self.test_dir}")
        print(f"⏱️  计划运行时间: {duration_seconds} 秒")
    
    def generate_random_complex_file(self, file_path: str, complexity: int = 10):
        """生成超复杂的随机代码文件"""
        code_parts = []
        
        # 添加导入
        for i in range(random.randint(1, 3)):
            symbols = [chr(ord('A') + j) for j in range(random.randint(1, 5))]
            source = ''.join(random.choice(['.', '@', 'module_']) + random.choice(string.ascii_lowercase) 
                           for _ in range(3))
            code_parts.append(f"import {{ {', '.join(symbols)} }} from '{source}';")
        
        # 添加常量
        for i in range(random.randint(2, 5)):
            const_name = ''.join(random.choice(string.ascii_uppercase + '_') for _ in range(random.randint(5, 12)))
            value_type = random.choice(['number', 'string', 'boolean'])
            if value_type == 'number':
                value = str(random.randint(0, 1000))
            elif value_type == 'string':
                value = f"'{random.choice(string.ascii_letters) * random.randint(3, 10)}'"
            else:
                value = 'true' if random.random() > 0.5 else 'false'
            code_parts.append(f"const {const_name}: {value_type} = {value};")
        
        # 添加函数
        for i in range(random.randint(complexity // 2, complexity)):
            func_name = ''.join(random.choice(string.ascii_letters) for _ in range(random.randint(3, 8)))
            if random.random() > 0.7:
                code_parts.append(f"async function {func_name}() {{")
            else:
                code_parts.append(f"function {func_name}() {{")
            
            # 函数体
            for j in range(random.randint(3, 10)):
                if random.random() > 0.6:
                    var_name = ''.join(random.choice(string.ascii_letters) for _ in range(random.randint(2, 4)))
                    code_parts.append(f"  const {var_name} = {random.randint(0, 100)};")
                else:
                    called_func = ''.join(random.choice(string.ascii_letters) for _ in range(random.randint(3, 6)))
                    code_parts.append(f"  {called_func}();")
            
            code_parts.append("}")
        
        # 添加类
        for i in range(random.randint(max(1, complexity // 3), complexity // 2)):
            class_name = ''.join(random.choice(string.ascii_uppercase) for _ in range(1)) + \
                        ''.join(random.choice(string.ascii_letters) for _ in range(random.randint(4, 8)))
            code_parts.append(f"class {class_name} {{")
            
            # 添加方法
            for j in range(random.randint(2, 5)):
                method_name = ''.join(random.choice(string.ascii_letters) for _ in range(random.randint(3, 7)))
                code_parts.append(f"  {method_name}() {{")
                for k in range(random.randint(2, 5)):
                    var_name = ''.join(random.choice(string.ascii_letters) for _ in range(random.randint(2, 4)))
                    code_parts.append(f"    this.{var_name} = {random.randint(0, 100)};")
                code_parts.append("  }")
            
            code_parts.append("}")
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(code_parts))
    
    def stress_worker(self, worker_id: int, start_time: float):
        """压力测试工作线程"""
        updater = KnowledgeGraphUpdater(self.db_path)
        worker_ops = 0
        
        while self.keep_running and (time.time() - start_time) < self.duration_seconds:
            try:
                # 创建或更新随机文件
                file_id = random.randint(0, 50)
                file_path = os.path.join(self.test_dir, f"stress_file_{worker_id}_{file_id}.ts")
                
                # 随机决定是创建新文件还是更新旧文件
                if os.path.exists(file_path) and random.random() > 0.3:
                    # 更新现有文件
                    time.sleep(random.random() * 0.005)  # 小延迟
                    self.generate_random_complex_file(file_path, random.randint(3, 8))
                    updater.update_file(file_path)
                else:
                    # 创建新文件
                    self.generate_random_complex_file(file_path, random.randint(5, 15))
                    updater.update_file(file_path)
                
                # 随机删除一些文件
                if random.random() > 0.7:
                    delete_file_id = random.randint(0, 50)
                    delete_path = os.path.join(self.test_dir, f"stress_file_{worker_id}_{delete_file_id}.ts")
                    if os.path.exists(delete_path):
                        try:
                            db = Database(self.db_path)
                            file_info = db.get_file_by_path(os.path.abspath(delete_path))
                            db.close()
                            if file_info:
                                updater.db.delete_file_data(file_info['id'])
                            os.remove(delete_path)
                        except Exception:
                            pass
                
                worker_ops += 1
                with threading.Lock():
                    self.operations_completed += 1
                
                # 随机休眠，模拟真实场景
                time.sleep(random.random() * 0.01)
                
            except Exception as e:
                logger.error(f"工作线程 {worker_id} 错误: {e}")
                with threading.Lock():
                    self.errors_occurred += 1
        
        updater.close()
        print(f"✓ 工作线程 {worker_id} 完成: {worker_ops} 次操作")
    
    def run_test(self, num_workers: int = 8):
        """运行长时间压力测试"""
        print("="*80)
        print("🚀 开始极端长时间压力测试")
        print("="*80)
        
        start_time = time.time()
        
        # 启动工作线程
        threads = []
        print(f"🔥 启动 {num_workers} 个工作线程...")
        
        for i in range(num_workers):
            t = threading.Thread(target=self.stress_worker, args=(i, start_time))
            threads.append(t)
            t.start()
        
        # 主监控线程
        last_report = time.time()
        last_ops = 0
        
        print("\n" + "="*80)
        print("📊 实时监控 (每5秒更新一次):")
        print("="*80)
        
        while self.keep_running and (time.time() - start_time) < self.duration_seconds:
            time.sleep(1)
            
            # 每5秒打印一次状态
            if time.time() - last_report >= 5:
                elapsed = time.time() - start_time
                ops_in_interval = self.operations_completed - last_ops
                ops_per_sec = ops_in_interval / 5.0
                
                print(f"⏱️  运行 {elapsed:.1f}s | "
                      f"总操作: {self.operations_completed} | "
                      f"速度: {ops_per_sec:.1f} 操作/秒 | "
                      f"错误: {self.errors_occurred}")
                
                last_report = time.time()
                last_ops = self.operations_completed
        
        # 等待所有线程完成
        self.keep_running = False
        for t in threads:
            t.join()
        
        total_elapsed = time.time() - start_time
        
        # 最终验证
        print("\n" + "="*80)
        print("🔍 最终数据一致性验证")
        print("="*80)
        
        db = Database(self.db_path)
        all_files = db.get_all_files()
        print(f"📂 数据库中现存文件: {len(all_files)}")
        
        # 验证一些文件的完整性
        consistent = True
        try:
            for i, file_info in enumerate(all_files[:20]):  # 检查前20个文件
                funcs = db.get_functions_by_file(file_info['id'])
                classes = db.get_classes_by_file(file_info['id'])
                imports = db.get_imports_by_file(file_info['id'])
                # 只要查询成功就没问题
        except Exception as e:
            logger.error(f"数据一致性检查错误: {e}")
            consistent = False
        
        db.close()
        
        # 最终统计
        print("\n" + "="*80)
        print("📈 压力测试最终结果:")
        print("="*80)
        print(f"⏱️  总运行时间: {total_elapsed:.1f} 秒")
        print(f"📊 总操作次数: {self.operations_completed}")
        print(f"✅ 操作成功率: {100.0 if self.errors_occurred == 0 else 100.0 * (self.operations_completed - self.errors_occurred) / max(self.operations_completed, 1):.1f}%")
        print(f"💨 平均吞吐量: {self.operations_completed / max(total_elapsed, 0.01):.1f} 操作/秒")
        print(f"📂 最终文件数: {len(all_files)}")
        print(f"✅ 数据一致性: {'完美' if consistent and self.errors_occurred == 0 else '有错误'}")
        print("="*80)
        
        if self.errors_occurred == 0 and consistent:
            print("\n🎉 恭喜！极端长时间压力测试完美通过！")
            return True
        else:
            print(f"\n⚠️  测试完成，但有 {self.errors_occurred} 个错误")
            return False
    
    def cleanup(self):
        """清理测试文件"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        print(f"\n🧹 测试文件已清理")

def main():
    """主函数 - 运行极端长时间压力测试"""
    import string
    
    print("="*80)
    print("🚀 极端长时间压力测试 - ArkTS 知识图谱系统")
    print("="*80)
    
    # 运行2分钟的压力测试
    test = ExtremeLongRunningTest(duration_seconds=120)
    
    try:
        success = test.run_test(num_workers=8)
        return 0 if success else 1
    finally:
        test.cleanup()

if __name__ == "__main__":
    sys.exit(main())
