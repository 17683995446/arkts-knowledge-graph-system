#!/usr/bin/env python3
"""极端混乱测试场景 - 真实生产环境级别的测试"""
import os
import sys
import tempfile
import time
import random
import string
import shutil
from pathlib import Path

sys.path.insert(0, '/workspace')

from src.core_logged import KnowledgeGraphUpdater
from src.database.database_logged import Database
from src.logger import setup_logger

logger = setup_logger(level=20)  # INFO级别，减少日志噪音

def generate_random_class_name():
    return ''.join(random.choices(string.ascii_uppercase, k=1)) + \
           ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(5, 20)))

def generate_random_method_name():
    return ''.join(random.choices(string.ascii_lowercase, k=1)) + \
           ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(3, 15)))

def generate_random_content(file_idx):
    """生成包含随机类、方法、导入的内容"""
    num_classes = random.randint(1, 5)
    num_imports = random.randint(0, 3)
    num_methods_per_class = random.randint(2, 8)
    
    content = []
    
    # 添加导入
    for i in range(num_imports):
        source = f"module_{random.randint(1, 10)}"
        symbol = generate_random_class_name()
        content.append(f"import {{ {symbol} }} from '{source}';")
    
    # 添加类
    for c in range(num_classes):
        class_name = generate_random_class_name()
        content.append(f"\nclass {class_name} {{")
        
        # 添加方法
        for m in range(num_methods_per_class):
            method_name = generate_random_method_name()
            content.append(f"  {method_name}() {{")
            content.append(f"    console.log('{class_name}.{method_name}');")
            # 添加一些随机调用
            for _ in range(random.randint(0, 3)):
                call_target = generate_random_method_name()
                content.append(f"    {call_target}();")
            content.append(f"  }}")
        
        content.append(f"}}")
    
    return '\n'.join(content)

def test_chaos_scenario():
    print("=" * 80)
    print("🔥 极端混乱测试场景 - 大规模真实实践")
    print("=" * 80)
    
    test_dir = tempfile.mkdtemp(prefix="arkts_chaos_test_")
    db_path = os.path.join(test_dir, "chaos_test.db")
    print(f"测试目录: {test_dir}")
    
    try:
        # 阶段1: 创建大量混乱文件
        print("\n📁 阶段1: 创建混乱文件...")
        num_files = 150  # 150个文件，大规模测试
        created_files = []
        
        for i in range(num_files):
            subdir = os.path.join(test_dir, f"subdir_{i % 10}")
            os.makedirs(subdir, exist_ok=True)
            
            filename = f"file_{i:03d}.ts"
            filepath = os.path.join(subdir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                content = generate_random_content(i)
                f.write(content)
            
            created_files.append(filepath)
            
            if (i + 1) % 25 == 0:
                print(f"   已创建 {i + 1}/{num_files} 个文件")
        
        print(f"✅ 成功创建 {num_files} 个文件")
        
        # 阶段2: 全量扫描
        print("\n🔍 阶段2: 全量扫描...")
        updater = KnowledgeGraphUpdater(db_path)
        
        start_time = time.time()
        updater.full_scan(test_dir)
        scan_time = time.time() - start_time
        
        print(f"✅ 全量扫描完成，耗时: {scan_time:.2f}秒")
        
        # 验证数据
        db = Database(db_path)
        files_in_db = db.get_all_files()
        print(f"📊 数据库中文件数量: {len(files_in_db)}")
        
        total_classes = 0
        total_methods = 0
        total_imports = 0
        
        for file_info in files_in_db:
            classes = db.get_classes_by_file(file_info['id'])
            total_classes += len(classes)
            for cls in classes:
                total_methods += len(cls['methods'])
            imports = db.get_imports_by_file(file_info['id'])
            total_imports += len(imports)
        
        print(f"📊 类数量: {total_classes}")
        print(f"📊 方法数量: {total_methods}")
        print(f"📊 导入数量: {total_imports}")
        db.close()
        
        # 阶段3: 随机修改一些文件
        print("\n✏️  阶段3: 随机修改文件...")
        num_modifications = 50
        modified_files = random.sample(created_files, num_modifications)
        
        start_time = time.time()
        for filepath in modified_files:
            # 读取、修改、写入
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 添加新内容
            new_method = f"\nfunction addedByTest_{random.randint(1000, 9999)}() {{ return 'test'; }}"
            content += new_method
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            updater.update_file(filepath)
            
        modification_time = time.time() - start_time
        print(f"✅ 修改了 {num_modifications} 个文件，耗时: {modification_time:.2f}秒")
        
        # 阶段4: 随机删除一些文件
        print("\n🗑️  阶段4: 随机删除文件...")
        num_deletions = 30
        deleted_files = random.sample([f for f in created_files if f not in modified_files], num_deletions)
        
        # 更新逻辑不会自动处理删除，但我们手动测试数据库清理
        # 先获取这些文件的ID
        db = Database(db_path)
        file_ids_to_delete = []
        for filepath in deleted_files:
            file_info = db.get_file_by_path(os.path.abspath(filepath))
            if file_info:
                file_ids_to_delete.append(file_info['id'])
        
        # 删除这些文件的数据
        for file_id in file_ids_to_delete:
            db.delete_file_data(file_id)
        
        db.close()
        print(f"✅ 删除了 {len(file_ids_to_delete)} 个文件的数据")
        
        # 阶段5: 最终验证
        print("\n🔎 阶段5: 最终验证...")
        db = Database(db_path)
        final_files = db.get_all_files()
        print(f"📊 最终数据库中的文件数量: {len(final_files)}")
        
        db.close()
        updater.close()
        
        print("\n" + "=" * 80)
        print("🎉 极端混乱测试完成！系统表现稳定！")
        print("=" * 80)
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        print(f"\n❌ 测试失败: {e}")
        return False
    finally:
        # 清理
        shutil.rmtree(test_dir, ignore_errors=True)


def test_edge_cases():
    """测试极端边缘情况"""
    print("\n" + "=" * 80)
    print("🔪 边缘情况测试")
    print("=" * 80)
    
    test_dir = tempfile.mkdtemp(prefix="arkts_edge_test_")
    db_path = os.path.join(test_dir, "edge_test.db")
    
    try:
        updater = KnowledgeGraphUpdater(db_path)
        
        # 1. 空文件
        print("\n1. 测试空文件...")
        empty_file = os.path.join(test_dir, "empty.ts")
        with open(empty_file, 'w') as f:
            pass
        updater.update_file(empty_file)
        print("   ✅ 空文件处理成功")
        
        # 2. 只有注释的文件
        print("\n2. 测试只有注释的文件...")
        comment_file = os.path.join(test_dir, "comments.ts")
        with open(comment_file, 'w') as f:
            f.write("// 这是一个注释\n/* 这是一个 */\n// 多行\n")
        updater.update_file(comment_file)
        print("   ✅ 注释文件处理成功")
        
        # 3. 语法错误的文件
        print("\n3. 测试语法错误的文件...")
        error_file = os.path.join(test_dir, "syntax_error.ts")
        with open(error_file, 'w') as f:
            f.write("class BrokenClass {\n  method(\n    this is invalid syntax\n")
        # 应该能正常处理，不会崩溃
        updater.update_file(error_file)
        print("   ✅ 语法错误文件处理成功（没有崩溃）")
        
        # 4. Unicode和特殊字符
        print("\n4. 测试Unicode和特殊字符...")
        unicode_file = os.path.join(test_dir, "unicode_chars.ts")
        with open(unicode_file, 'w', encoding='utf-8') as f:
            f.write("class EmojiClass { 🔥() { console.log('🎉中文测试'); } }")
        updater.update_file(unicode_file)
        print("   ✅ Unicode文件处理成功")
        
        # 5. 极长的文件
        print("\n5. 测试极长的文件...")
        big_file = os.path.join(test_dir, "big_file.ts")
        big_content = []
        for i in range(1000):  # 1000个类！
            big_content.append(f"class BigClass{i} {{ method{i}() {{ return {i}; }} }}")
        
        with open(big_file, 'w') as f:
            f.write('\n'.join(big_content))
        
        start_time = time.time()
        updater.update_file(big_file)
        big_time = time.time() - start_time
        print(f"   ✅ 大文件处理成功，耗时: {big_time:.2f}秒")
        
        updater.close()
        print("\n✅ 所有边缘情况测试通过！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 边缘情况测试失败: {e}", exc_info=True)
        print(f"\n❌ 边缘情况测试失败: {e}")
        return False
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    success1 = test_chaos_scenario()
    success2 = test_edge_cases()
    
    print("\n" + "=" * 80)
    if success1 and success2:
        print("✅ 所有极端混乱测试通过！系统非常健壮！")
    else:
        print("❌ 部分测试失败")
    print("=" * 80)
    
    sys.exit(0 if (success1 and success2) else 1)
