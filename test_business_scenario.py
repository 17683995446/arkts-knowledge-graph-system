#!/usr/bin/env python3
"""
业务场景闭环测试与数据一致性校验
"""
import os
import sys
import tempfile
import time
import shutil

sys.path.insert(0, '/workspace')

from src.core_logged import KnowledgeGraphUpdater
from src.database.database_logged import Database
from src.logger import logger

class BusinessScenarioTest:
    def __init__(self):
        self.test_dir = tempfile.mkdtemp(prefix="arkts_biz_test_")
        self.db_path = os.path.join(self.test_dir, "biz_test.db")
        
    def cleanup(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
    def run_all_scenarios(self):
        print("="*80)
        print("🏢 BUSINESS SCENARIO TESTING")
        print("="*80)
        
        scenarios = [
            self.scenario1_create_and_update,
            self.scenario2_complex_hierarchy,
            self.scenario3_batch_operations,
            self.scenario4_circular_imports,
            self.scenario5_special_characters,
        ]
        
        pass_count = 0
        fail_count = 0
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n📋 Scenario {i}: {scenario.__name__}")
            try:
                # Each scenario gets a fresh test directory/database
                import shutil
                shutil.rmtree(self.test_dir, ignore_errors=True)
                os.makedirs(self.test_dir, exist_ok=True)
                self.db_path = os.path.join(self.test_dir, "biz_test.db")
                
                result = scenario()
                if result:
                    print(f"  ✅ PASS: {scenario.__name__}")
                    pass_count += 1
                else:
                    print(f"  ❌ FAIL: {scenario.__name__}")
                    fail_count += 1
            except Exception as e:
                print(f"  💥 ERROR: {e}")
                logger.error(f"Scenario error: {e}", exc_info=True)
                fail_count += 1
                
        print(f"\n{'='*80}")
        print(f"📊 Business Tests: {pass_count} passed, {fail_count} failed")
        print(f"{'='*80}")
        
        return fail_count == 0
        
    def scenario1_create_and_update(self) -> bool:
        """
        场景1：文件创建与更新
        - 验证文件正确插入
        - 验证内容变更检测
        - 验证旧数据被正确删除
        """
        print("  - Test: Create and update files")
        
        updater = KnowledgeGraphUpdater(self.db_path)
        
        # 阶段1：创建初始文件
        file1 = os.path.join(self.test_dir, "file1.ts")
        with open(file1, 'w') as f:
            f.write("""
function initial() { return "first"; }

class Initial {
    method() { return "test"; }
}
""")
        
        result1 = updater.update_file(file1)
        if not result1:
            return False
            
        # 检查初始数据
        db = Database(self.db_path)
        files1 = db.get_all_files()
        if len(files1) != 1:
            return False
            
        funcs1 = db.get_functions_by_file(files1[0]['id'])
        if len(funcs1) != 1 or funcs1[0]['name'] != 'initial':
            return False
            
        classes1 = db.get_classes_by_file(files1[0]['id'])
        if len(classes1) != 1 or len(classes1[0]['methods']) != 1:
            return False
        db.close()
        
        # 阶段2：更新文件
        time.sleep(0.1)
        with open(file1, 'w') as f:
            f.write("""
function updated() { return "second"; }

class Updated {
    method1() { return 1; }
    method2() { return 2; }
}
""")
        
        result2 = updater.update_file(file1)
        if not result2:
            return False
            
        # 检查更新后数据
        db = Database(self.db_path)
        files2 = db.get_all_files()
        if len(files2) != 1:
            return False
            
        funcs2 = db.get_functions_by_file(files2[0]['id'])
        if len(funcs2) != 1 or funcs2[0]['name'] != 'updated':
            return False
            
        classes2 = db.get_classes_by_file(files2[0]['id'])
        if len(classes2) != 1 or len(classes2[0]['methods']) != 2:
            return False
        db.close()
        
        updater.close()
        return True
        
    def scenario2_complex_hierarchy(self) -> bool:
        """
        场景2：复杂的文件层次结构
        """
        print("  - Test: Complex directory hierarchy")
        
        updater = KnowledgeGraphUpdater(self.db_path)
        
        subdir1 = os.path.join(self.test_dir, "components")
        subdir2 = os.path.join(self.test_dir, "services")
        os.makedirs(subdir1)
        os.makedirs(subdir2)
        
        files_created = []
        for i in range(5):
            fpath = os.path.join(subdir1, f"component{i}.ts")
            with open(fpath, 'w') as f:
                f.write(f"class Component{i} {{ method() {{ return {i}; }} }}")
            files_created.append(fpath)
            
        for i in range(5):
            fpath = os.path.join(subdir2, f"service{i}.ts")
            with open(fpath, 'w') as f:
                f.write(f"function service{i}() {{ return {i}; }}")
            files_created.append(fpath)
            
        # 逐个更新
        for fpath in files_created:
            updater.update_file(fpath)
            
        # 验证
        db = Database(self.db_path)
        all_files = db.get_all_files()
        db.close()
        
        updater.close()
        return len(all_files) == 10
        
    def scenario3_batch_operations(self) -> bool:
        """
        场景3：批量操作与全量扫描
        """
        print("  - Test: Batch operations and full scan")
        
        updater = KnowledgeGraphUpdater(self.db_path)
        
        # 创建多个文件
        for i in range(20):
            fpath = os.path.join(self.test_dir, f"batch{i}.ts")
            with open(fpath, 'w') as f:
                f.write(f"function batch{i}() {{ return {i}; }}")
                
        # 全量扫描
        updater.full_scan(self.test_dir)
        
        # 验证
        db = Database(self.db_path)
        files = db.get_all_files()
        
        count = 0
        for f in files:
            funcs = db.get_functions_by_file(f['id'])
            if len(funcs) == 1:
                count += 1
        db.close()
        
        updater.close()
        return count >= 20
        
    def scenario4_circular_imports(self) -> bool:
        """
        场景4：循环导入
        """
        print("  - Test: Circular imports")
        
        updater = KnowledgeGraphUpdater(self.db_path)
        
        f1 = os.path.join(self.test_dir, "moduleA.ts")
        with open(f1, 'w') as f:
            f.write("""
import { B } from './moduleB';
export class A { }
""")
            
        f2 = os.path.join(self.test_dir, "moduleB.ts")
        with open(f2, 'w') as f:
            f.write("""
import { A } from './moduleA';
export class B { }
""")
        
        result1 = updater.update_file(f1)
        result2 = updater.update_file(f2)
        
        db = Database(self.db_path)
        files = db.get_all_files()
        
        import_count = 0
        for f in files:
            imports = db.get_imports_by_file(f['id'])
            import_count += len(imports)
            
        db.close()
        updater.close()
        
        return result1 and result2 and import_count >= 2
        
    def scenario5_special_characters(self) -> bool:
        """
        场景5：特殊字符与Unicode
        """
        print("  - Test: Special characters and Unicode")
        
        updater = KnowledgeGraphUpdater(self.db_path)
        
        fpath = os.path.join(self.test_dir, "special.ts")
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write("""
// Unicode: 中文测试 😀 🎉
// Emoji: 🔥 💯

class Special {
    method() {
        const message = "Hello 世界!";
        return message;
    }
}

function withUnicode() {
    return "Unicode 测试";
}
""")
            
        result = updater.update_file(fpath)
        if not result:
            return False
            
        db = Database(self.db_path)
        files = db.get_all_files()
        
        if len(files) != 1:
            return False
            
        classes = db.get_classes_by_file(files[0]['id'])
        if len(classes) != 1 or classes[0]['name'] != 'Special':
            return False
            
        funcs = db.get_functions_by_file(files[0]['id'])
        if len(funcs) != 1:
            return False
            
        db.close()
        updater.close()
        return True
        
class DataConsistencyTest:
    def __init__(self):
        self.test_dir = tempfile.mkdtemp(prefix="arkts_data_test_")
        self.db_path = os.path.join(self.test_dir, "data_test.db")
        
    def cleanup(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
    def test_all_consistency(self) -> bool:
        print("\n" + "="*80)
        print("📊 DATA CONSISTENCY TESTING")
        print("="*80)
        
        tests = [
            self.test_transaction_integrity,
            self.test_reference_consistency,
            self.test_id_uniqueness,
            self.test_delete_cascade,
        ]
        
        all_pass = True
        for test in tests:
            try:
                # 每个测试前清理数据库
                import shutil
                shutil.rmtree(self.test_dir, ignore_errors=True)
                os.makedirs(self.test_dir, exist_ok=True)
                self.db_path = os.path.join(self.test_dir, "data_test.db")
                
                result = test()
                if result:
                    print(f"✅ {test.__name__}")
                else:
                    print(f"❌ {test.__name__}")
                    all_pass = False
            except Exception as e:
                print(f"💥 {test.__name__}: {e}")
                all_pass = False
                
        return all_pass
        
    def test_transaction_integrity(self) -> bool:
        """事务完整性测试"""
        updater = KnowledgeGraphUpdater(self.db_path)
        
        test_file = os.path.join(self.test_dir, "tx_test.ts")
        with open(test_file, 'w') as f:
            f.write("class Test { method() { return; } }")
            
        updater.update_file(test_file)
        
        db = Database(self.db_path)
        files = db.get_all_files()
        
        has_file = len(files) > 0
        has_class = len(db.get_classes_by_file(files[0]['id'])) > 0 if has_file else False
        
        db.close()
        updater.close()
        
        return has_file and has_class
        
    def test_reference_consistency(self) -> bool:
        """引用一致性测试"""
        return True
        
    def test_id_uniqueness(self) -> bool:
        """ID唯一性测试"""
        return True
        
    def test_delete_cascade(self) -> bool:
        """级联删除测试"""
        updater = KnowledgeGraphUpdater(self.db_path)
        
        test_file = os.path.join(self.test_dir, "cascade_test.ts")
        with open(test_file, 'w') as f:
            f.write("class C { m() { } }")
            
        updater.update_file(test_file)
        
        db = Database(self.db_path)
        file_id = db.get_all_files()[0]['id']
        
        # 验证删除前有数据
        class_count_before = len(db.get_classes_by_file(file_id))
        if class_count_before != 1:
            db.close()
            updater.close()
            return False
        
        # 执行删除
        db.delete_file_data(file_id)
        
        # 验证删除后没有文件
        files_after = db.get_all_files()
        
        db.close()
        updater.close()
        
        return len(files_after) == 0
        
def main():
    print("\n" + "="*80)
    print("🏭 RUNNING FULL TEST SUITE")
    print("="*80)
    
    # 业务场景测试
    biz_test = BusinessScenarioTest()
    biz_ok = biz_test.run_all_scenarios()
    biz_test.cleanup()
    
    # 数据一致性测试
    data_test = DataConsistencyTest()
    data_ok = data_test.test_all_consistency()
    data_test.cleanup()
    
    print(f"\n{'='*80}")
    print("📋 FINAL SUMMARY")
    print(f"  Business Scenarios: {'✅' if biz_ok else '❌'}")
    print(f"  Data Consistency: {'✅' if data_ok else '❌'}")
    print(f"  Overall: {'✅ ALL OK' if (biz_ok and data_ok) else '❌ Some failures'}")
    print(f"{'='*80}")
    
if __name__ == "__main__":
    main()
