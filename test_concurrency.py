#!/usr/bin/env python3
"""并发压力测试 - 多线程同时操作数据库"""
import os
import sys
import tempfile
import time
import random
import shutil
import threading
from pathlib import Path

sys.path.insert(0, '/workspace')

from src.core_logged import KnowledgeGraphUpdater
from src.database.database_logged import Database
from src.logger import setup_logger

logger = setup_logger(level=20)  # INFO级别


class ConcurrencyTest:
    def __init__(self):
        self.test_dir = tempfile.mkdtemp(prefix="arkts_concurrency_test_")
        self.db_path = os.path.join(self.test_dir, "concurrency_test.db")
        self.created_files = []
        self.success_count = 0
        self.error_count = 0
        self.lock = threading.Lock()
    
    def setup_test_files(self, num_files=50):
        """准备测试文件"""
        print(f"📁 准备 {num_files} 个测试文件...")
        for i in range(num_files):
            filepath = os.path.join(self.test_dir, f"concurrency_file_{i:02d}.ts")
            with open(filepath, 'w') as f:
                f.write(f"class TestClass{i} {{ method{i}() {{ return {i}; }} }}")
            self.created_files.append(filepath)
        print(f"✅ 准备完成")
    
    def worker_update_files(self, thread_id, num_operations):
        """线程工作函数：随机更新文件"""
        try:
            # 每个线程有自己的数据库连接
            updater = KnowledgeGraphUpdater(self.db_path)
            
            for i in range(num_operations):
                # 随机选择一个文件
                filepath = random.choice(self.created_files)
                
                # 随机决定是更新还是跳过
                if random.random() > 0.3:  # 70%的概率进行修改
                    # 读取现有内容
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                    except:
                        content = ""
                    
                    # 添加随机新内容
                    new_content = content + f"\nfunction thread{thread_id}_func{i}() {{ return 't{thread_id}_op{i}'; }}"
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                
                # 更新文件
                updater.update_file(filepath)
                
                if (i + 1) % 10 == 0:
                    with self.lock:
                        print(f"   线程 {thread_id}: 完成 {i + 1}/{num_operations} 次操作")
            
            updater.close()
            
            with self.lock:
                self.success_count += 1
                
        except Exception as e:
            logger.error(f"线程 {thread_id} 出错: {e}", exc_info=True)
            with self.lock:
                self.error_count += 1
    
    def run_concurrent_test(self, num_threads=10, num_operations_per_thread=30):
        """运行并发测试"""
        print("=" * 80)
        print(f"🚀 并发压力测试: {num_threads} 个线程同时操作")
        print("=" * 80)
        
        self.success_count = 0
        self.error_count = 0
        
        threads = []
        start_time = time.time()
        
        # 创建并启动所有线程
        print(f"\n🔧 启动 {num_threads} 个线程...")
        for i in range(num_threads):
            t = threading.Thread(
                target=self.worker_update_files,
                args=(i, num_operations_per_thread)
            )
            threads.append(t)
            t.start()
        
        # 等待所有线程完成
        print("\n⏳ 等待所有线程完成...")
        for t in threads:
            t.join()
        
        total_time = time.time() - start_time
        total_operations = num_threads * num_operations_per_thread
        
        print("\n" + "=" * 80)
        print(f"📊 并发测试结果:")
        print(f"   总耗时: {total_time:.2f}秒")
        print(f"   总操作数: {total_operations}")
        print(f"   成功线程数: {self.success_count}")
        print(f"   错误线程数: {self.error_count}")
        print(f"   吞吐量: {total_operations/total_time:.2f} 操作/秒")
        print("=" * 80)
        
        # 验证数据一致性
        print("\n🔍 验证数据一致性...")
        db = Database(self.db_path)
        files = db.get_all_files()
        print(f"   数据库中的文件数量: {len(files)}")
        
        # 检查每个文件的完整性
        consistent = True
        for file_info in files:
            # 确保我们可以查询类和方法
            try:
                classes = db.get_classes_by_file(file_info['id'])
                imports = db.get_imports_by_file(file_info['id'])
            except Exception as e:
                logger.error(f"文件 {file_info['path']} 数据损坏: {e}")
                consistent = False
        
        db.close()
        
        if consistent:
            print("   ✅ 数据一致性验证通过！")
        else:
            print("   ❌ 数据一致性验证失败！")
        
        return self.error_count == 0 and consistent
    
    def cleanup(self):
        """清理测试文件"""
        shutil.rmtree(self.test_dir, ignore_errors=True)


def test_simple_concurrency():
    """简单的并发测试"""
    print("\n" + "=" * 80)
    print("🔬 简单并发测试")
    print("=" * 80)
    
    test = ConcurrencyTest()
    test.setup_test_files(num_files=30)
    
    success = test.run_concurrent_test(num_threads=5, num_operations_per_thread=20)
    
    test.cleanup()
    return success


def test_high_concurrency():
    """高并发测试"""
    print("\n" + "=" * 80)
    print("⚡ 高并发压力测试")
    print("=" * 80)
    
    test = ConcurrencyTest()
    test.setup_test_files(num_files=100)
    
    success = test.run_concurrent_test(num_threads=15, num_operations_per_thread=50)
    
    test.cleanup()
    return success


if __name__ == "__main__":
    print("🏁 开始并发压力测试...")
    
    success1 = test_simple_concurrency()
    success2 = test_high_concurrency()
    
    print("\n" + "=" * 80)
    if success1 and success2:
        print("✅ 所有并发压力测试通过！系统线程安全！")
    else:
        print("❌ 部分并发测试失败")
    print("=" * 80)
    
    sys.exit(0 if (success1 and success2) else 1)
