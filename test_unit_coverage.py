#!/usr/bin/env python3
"""
全面的单元测试覆盖
"""
import os
import sys
import tempfile
import time
import shutil

sys.path.insert(0, '/workspace')

from src.core_logged import KnowledgeGraphUpdater
from src.database.database_logged import Database
from src.parser.arkts_parser_logged import ArkTSParser
from src.logger import logger

class TestRunner:
    def __init__(self):
        self.test_count = 0
        self.pass_count = 0
        self.fail_count = 0
        self.test_dir = tempfile.mkdtemp(prefix="arkts_kg_test_")
        
    def run_all_tests(self):
        print("="*80)
        print("🧪 RUNNING ALL UNIT TESTS")
        print("="*80)
        
        try:
            self.test_database()
            self.test_parser()
            self.test_core_logic()
            self.test_edge_cases()
            self.test_concurrent()
            self.test_performance()
            
            self.print_summary()
        finally:
            shutil.rmtree(self.test_dir, ignore_errors=True)
            
    def assert_true(self, condition: bool, message: str = "Assertion failed"):
        self.test_count += 1
        if condition:
            print(f"  ✅ PASS: {message}")
            self.pass_count += 1
        else:
            print(f"  ❌ FAIL: {message}")
            self.fail_count += 1
            
    def test_database(self):
        print("\n📚 Test 1: Database Operations")
        db_path = os.path.join(self.test_dir, "test.db")
        db = Database(db_path)
        
        try:
            test_file_path = os.path.join(self.test_dir, "test1.ts")
            with open(test_file_path, 'w') as f:
                f.write("function test() { return 1; }")
            
            file_hash = db.compute_file_hash(test_file_path)
            self.assert_true(len(file_hash) > 0, "Compute file hash")
            
            file_id = db.insert_file(test_file_path, file_hash, int(time.time()))
            self.assert_true(file_id > 0, "Insert file record")
            
            retrieved = db.get_file_by_path(test_file_path)
            self.assert_true(retrieved is not None, "Get file by path")
            self.assert_true(retrieved['id'] == file_id, "File ID matches")
            
            func_id = db.insert_function(file_id, "test", 1, 10, "function test() { return 1; }")
            self.assert_true(func_id > 0, "Insert function")
            
            funcs = db.get_functions_by_file(file_id)
            self.assert_true(len(funcs) == 1, "Retrieve functions")
            
            db.delete_file_data(file_id)
            funcs_after = db.get_functions_by_file(file_id)
            self.assert_true(len(funcs_after) == 0, "Delete file data")
            
            all_files = db.get_all_files()
            self.assert_true(len(all_files) == 0, "File deleted from DB")
            
        finally:
            db.close()
            
    def test_parser(self):
        print("\n📜 Test 2: Parser")
        parser = ArkTSParser()
        
        test_files = [
            (1, "function test() { return 1; }"),
            (2, "const add = (a, b) => { return a + b; }"),
            (3, "async function fetch() { return await data; }"),
            (4, "class MyClass { method() { return 42; } }"),
            (5, "import { x, y } from 'module';"),
        ]
        
        for i, content in test_files:
            test_file = os.path.join(self.test_dir, f"parser_test{i}.ts")
            with open(test_file, 'w') as f:
                f.write(content)
                
            result = parser.parse_file(test_file)
            self.assert_true('functions' in result, "Has functions key")
            self.assert_true('classes' in result, "Has classes key")
            self.assert_true('imports' in result, "Has imports key")
            
    def test_core_logic(self):
        print("\n🎯 Test 3: Core Logic")
        db_path = os.path.join(self.test_dir, "core.db")
        updater = KnowledgeGraphUpdater(db_path)
        
        test_file = os.path.join(self.test_dir, "core_test.ts")
        with open(test_file, 'w') as f:
            f.write("""
class Calculator {
    add(a, b) {
        return a + b;
    }
    
    subtract(a, b) {
        return a - b;
    }
}

function multiply(x, y) {
    return x * y;
}
""")
        
        result = updater.update_file(test_file)
        self.assert_true(result is True, "File updated successfully")
        
        db = Database(db_path)
        files = db.get_all_files()
        self.assert_true(len(files) == 1, "File in database")
        
        classes = db.get_classes_by_file(files[0]['id'])
        self.assert_true(len(classes) == 1, "Class found")
        self.assert_true(len(classes[0]['methods']) == 2, "Methods found")
        
        functions = db.get_functions_by_file(files[0]['id'])
        self.assert_true(len(functions) == 1, "Function found")
        
        result2 = updater.update_file(test_file)
        self.assert_true(result2 is False, "Unchanged file skipped")
        
        db.close()
        updater.close()
        
    def test_edge_cases(self):
        print("\n🎭 Test 4: Edge Cases")
        db_path = os.path.join(self.test_dir, "edge.db")
        updater = KnowledgeGraphUpdater(db_path)
        
        empty_file = os.path.join(self.test_dir, "empty.ts")
        with open(empty_file, 'w') as f:
            f.write("")
        result = updater.update_file(empty_file)
        self.assert_true(result is True, "Empty file processed")
        
        nonexistent = os.path.join(self.test_dir, "not_exist.ts")
        result = updater.update_file(nonexistent)
        self.assert_true(result is False, "Nonexistent file handled")
        
        special_file = os.path.join(self.test_dir, "special.ts")
        with open(special_file, 'w', encoding='utf-8') as f:
            f.write("""
// Special characters test: 中文测试 😀🎉
class SpecialClass {
    method() { return "special"; }
}
""")
        result = updater.update_file(special_file)
        self.assert_true(result is True, "Special characters handled")
        
        updater.close()
        
    def test_concurrent(self):
        print("\n🔄 Test 5: Concurrent Operations")
        import threading
        
        db_path = os.path.join(self.test_dir, "concurrent.db")
        updater = KnowledgeGraphUpdater(db_path)
        
        test_file = os.path.join(self.test_dir, "concurrent.ts")
        with open(test_file, 'w') as f:
            f.write("function test() { return 1; }")
        
        errors = []
        
        def update_worker():
            try:
                for i in range(10):
                    updater.update_file(test_file)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=update_worker) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
            
        self.assert_true(len(errors) == 0, "No concurrent errors")
        updater.close()
        
    def test_performance(self):
        print("\n⚡ Test 6: Performance")
        db_path = os.path.join(self.test_dir, "perf.db")
        updater = KnowledgeGraphUpdater(db_path)
        
        large_file = os.path.join(self.test_dir, "large.ts")
        code = "// Large test file\n"
        for i in range(100):
            code += f"function func{i}() {{ return {i}; }}\n"
        with open(large_file, 'w') as f:
            f.write(code)
            
        start = time.time()
        updater.update_file(large_file)
        elapsed = (time.time() - start) * 1000
        print(f"  📊 Performance: {elapsed:.2f}ms")
        
        self.assert_true(elapsed < 5000, "Performance within limits (5s)")
        
        updater.close()
        
    def print_summary(self):
        print("\n" + "="*80)
        print("📊 TEST SUMMARY")
        print("="*80)
        print(f"  Total: {self.test_count}")
        print(f"  Pass:  {self.pass_count}")
        print(f"  Fail:  {self.fail_count}")
        print("="*80)
        print(f"  {'✅ ALL TESTS PASSED' if self.fail_count == 0 else '❌ Some tests failed'}")
        print("="*80)

def main():
    runner = TestRunner()
    runner.run_all_tests()
    
if __name__ == "__main__":
    main()
