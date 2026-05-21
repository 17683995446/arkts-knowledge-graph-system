#!/usr/bin/env python3
"""调试级联删除的测试"""
import os
import sys
import tempfile
sys.path.insert(0, '/workspace')

from src.database.database_logged import Database

def debug_test():
    print("=== 调试级联删除测试 ===")
    
    temp_dir = tempfile.mkdtemp(prefix="arkts_debug_")
    db_path = os.path.join(temp_dir, "debug.db")
    print(f"数据库路径: {db_path}")
    
    # 初始化数据库
    db = Database(db_path)
    
    # 插入测试数据
    print("\n1. 插入测试数据...")
    file_id = db.insert_file("/test/file.ts", b"test_hash", 12345)
    print(f"   插入文件，ID: {file_id}")
    
    class_id = db.insert_class(file_id, "TestClass", 1, 10, "class TestClass {}")
    print(f"   插入类，ID: {class_id}")
    
    method_id = db.insert_class_method(class_id, "testMethod", 2, 5, "testMethod() {}")
    print(f"   插入方法，ID: {method_id}")
    
    db.insert_call(method_id, "TestClass.testMethod", "otherFunction")
    print(f"   插入调用")
    
    # 验证数据存在
    print("\n2. 验证数据存在...")
    files_before = db.get_all_files()
    print(f"   文件数量: {len(files_before)}")
    
    classes_before = db.get_classes_by_file(file_id)
    print(f"   类数量: {len(classes_before)}")
    for cls in classes_before:
        print(f"     类: {cls['name']}")
        print(f"       方法数量: {len(cls['methods'])}")
    
    # 执行删除
    print("\n3. 执行删除...")
    db.delete_file_data(file_id)
    
    # 验证删除
    print("\n4. 验证删除结果...")
    files_after = db.get_all_files()
    print(f"   文件数量: {len(files_after)}")
    
    # 关闭数据库
    db.close()
    
    print("\n=== 测试完成 ===")
    return len(files_after) == 0

if __name__ == "__main__":
    success = debug_test()
    print(f"\n最终结果: {'SUCCESS' if success else 'FAILURE'}")
    sys.exit(0 if success else 1)
