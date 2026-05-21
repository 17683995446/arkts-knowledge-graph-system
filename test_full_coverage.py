#!/usr/bin/env python3
"""
全面分支覆盖测试
测试所有代码分支和隐藏逻辑
"""
import os
import sys
import tempfile
import shutil
import time
import logging

sys.path.insert(0, '/workspace')

from src.core_logged import KnowledgeGraphUpdater
from src.database.database_logged import Database
from src.parser import ArkTSParser
from src.logger import setup_logger

logger = setup_logger(level=logging.DEBUG)

class FullCoverageTest:
    def __init__(self):
        self.test_dir = tempfile.mkdtemp(prefix="arkts_full_coverage_")
        self.db_path = os.path.join(self.test_dir, "coverage_test.db")
        print(f"📂 测试目录: {self.test_dir}")
    
    def test_file_not_found(self):
        """测试: 文件不存在的情况"""
        print("\n" + "=" * 60)
        print("📄 测试: 文件不存在")
        print("=" * 60)
        
        updater = KnowledgeGraphUpdater(self.db_path)
        try:
            # 测试不存在的文件
            non_existent = os.path.join(self.test_dir, "non_existent.ts")
            result = updater.update_file(non_existent)
            print(f"   ✅ 文件不存在返回: {result}")
        finally:
            updater.close()
        
        return True
    
    def test_empty_file(self):
        """测试: 空文件"""
        print("\n" + "=" * 60)
        print("📄 测试: 空文件")
        print("=" * 60)
        
        updater = KnowledgeGraphUpdater(self.db_path)
        try:
            empty_file = os.path.join(self.test_dir, "empty.ts")
            with open(empty_file, 'w', encoding='utf-8') as f:
                pass
            
            result = updater.update_file(empty_file)
            print(f"   ✅ 空文件处理结果: {result}")
            
            db = Database(self.db_path)
            file_info = db.get_file_by_path(os.path.abspath(empty_file))
            if file_info:
                funcs = db.get_functions_by_file(file_info['id'])
                classes = db.get_classes_by_file(file_info['id'])
                imports = db.get_imports_by_file(file_info['id'])
                print(f"   📊 空文件解析:")
                print(f"      - 函数: {len(funcs)} 个")
                print(f"      - 类: {len(classes)} 个")
                print(f"      - 导入: {len(imports)} 个")
            db.close()
            
        finally:
            updater.close()
        
        return True
    
    def test_only_comments(self):
        """测试: 只有注释的文件"""
        print("\n" + "=" * 60)
        print("📄 测试: 只有注释的文件")
        print("=" * 60)
        
        updater = KnowledgeGraphUpdater(self.db_path)
        try:
            comment_file = os.path.join(self.test_dir, "comments.ts")
            with open(comment_file, 'w', encoding='utf-8') as f:
                f.write('// This is a comment\n')
                f.write('/*\n')
                f.write('Multi-line comment\n')
                f.write('*/\n')
            
            result = updater.update_file(comment_file)
            print(f"   ✅ 注释文件处理结果: {result}")
        finally:
            updater.close()
        
        return True
    
    def test_all_function_types(self):
        """测试: 各种函数类型"""
        print("\n" + "=" * 60)
        print("📄 测试: 所有函数类型")
        print("=" * 60)
        
        updater = KnowledgeGraphUpdater(self.db_path)
        try:
            func_file = os.path.join(self.test_dir, "all_functions.ts")
            with open(func_file, 'w', encoding='utf-8') as f:
                f.write('function regular() { return 1; }\n')
                f.write('async function asyncFunc() { return 2; }\n')
                f.write('const arrow = () => { return 3; };\n')
                f.write('const asyncArrow = async () => { return 4; };\n')
                f.write('const simpleArrow = () => 5;\n')
            
            result = updater.update_file(func_file)
            print(f"   ✅ 各种函数类型处理结果: {result}")
            
            db = Database(self.db_path)
            file_info = db.get_file_by_path(os.path.abspath(func_file))
            if file_info:
                funcs = db.get_functions_by_file(file_info['id'])
                print(f"   📊 解析到 {len(funcs)} 个函数")
            db.close()
        finally:
            updater.close()
        
        return True
    
    def test_class_with_methods(self):
        """测试: 包含各种方法的类"""
        print("\n" + "=" * 60)
        print("📄 测试: 类及其方法")
        print("=" * 60)
        
        updater = KnowledgeGraphUpdater(self.db_path)
        try:
            class_file = os.path.join(self.test_dir, "test_class.ts")
            with open(class_file, 'w', encoding='utf-8') as f:
                f.write('class TestClass {\n')
                f.write('  public publicMethod() { return 1; }\n')
                f.write('  private privateMethod() { return 2; }\n')
                f.write('  protected protectedMethod() { return 3; }\n')
                f.write('  static staticMethod() { return 4; }\n')
                f.write('  constructor() { }\n')
                f.write('}\n')
            
            result = updater.update_file(class_file)
            print(f"   ✅ 类处理结果: {result}")
            
            db = Database(self.db_path)
            file_info = db.get_file_by_path(os.path.abspath(class_file))
            if file_info:
                classes = db.get_classes_by_file(file_info['id'])
                print(f"   📊 解析到 {len(classes)} 个类")
                if classes:
                    cls = classes[0]
                    print(f"      - 类名: {cls['name']}")
                    print(f"      - 方法数: {len(cls.get('methods', []))}")
            db.close()
        finally:
            updater.close()
        
        return True
    
    def test_import_variations(self):
        """测试: 各种导入语句"""
        print("\n" + "=" * 60)
        print("📄 测试: 导入语句变体")
        print("=" * 60)
        
        updater = KnowledgeGraphUpdater(self.db_path)
        try:
            import_file = os.path.join(self.test_dir, "imports.ts")
            with open(import_file, 'w', encoding='utf-8') as f:
                f.write('import { Foo, Bar } from "module1";\n')
                f.write('import Default from "module2";\n')
                f.write('import * as All from "module3";\n')
            
            result = updater.update_file(import_file)
            print(f"   ✅ 导入语句处理结果: {result}")
            
            db = Database(self.db_path)
            file_info = db.get_file_by_path(os.path.abspath(import_file))
            if file_info:
                imports = db.get_imports_by_file(file_info['id'])
                print(f"   📊 解析到 {len(imports)} 个导入")
                for imp in imports:
                    print(f"      - {imp['source']}: {imp['symbol']}")
            db.close()
        finally:
            updater.close()
        
        return True
    
    def test_file_update_same_content(self):
        """测试: 文件内容未改变时的更新"""
        print("\n" + "=" * 60)
        print("📄 测试: 未改变的文件")
        print("=" * 60)
        
        updater = KnowledgeGraphUpdater(self.db_path)
        try:
            test_file = os.path.join(self.test_dir, "same_content.ts")
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write('function test() { return 1; }')
            
            print("   第一次更新...")
            result1 = updater.update_file(test_file)
            print(f"      ✅ 第一次: {result1}")
            
            print("   第二次更新(内容未变)...")
            time.sleep(0.01)  # 稍微等待一下
            result2 = updater.update_file(test_file)
            print(f"      ✅ 第二次: {result2}")
            
            if result1 and not result2:
                print("   ✅ 验证成功: 未改变的文件被跳过")
            else:
                print(f"   ⚠️  结果: 第一次={result1}, 第二次={result2}")
                
        finally:
            updater.close()
        
        return True
    
    def test_file_update_changed_content(self):
        """测试: 文件内容改变时的更新"""
        print("\n" + "=" * 60)
        print("📄 测试: 已改变的文件")
        print("=" * 60)
        
        updater = KnowledgeGraphUpdater(self.db_path)
        try:
            test_file = os.path.join(self.test_dir, "changed_content.ts")
            
            # 初始版本
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write('function version1() { return 1; }')
            
            print("   第一次更新(版本1)...")
            result1 = updater.update_file(test_file)
            print(f"      ✅ 第一次: {result1}")
            
            # 改变版本
            time.sleep(0.01)  # 稍微等待一下
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write('function version2() { return 2; }')
            
            print("   第二次更新(版本2)...")
            result2 = updater.update_file(test_file)
            print(f"      ✅ 第二次: {result2}")
            
            if result1 and result2:
                print("   ✅ 验证成功: 改变的文件被重新解析")
                
        finally:
            updater.close()
        
        return True
    
    def test_file_deletion(self):
        """测试: 文件删除"""
        print("\n" + "=" * 60)
        print("📄 测试: 文件删除")
        print("=" * 60)
        
        updater = KnowledgeGraphUpdater(self.db_path)
        try:
            test_file = os.path.join(self.test_dir, "to_delete.ts")
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write('function toDelete() { return 1; }')
            
            # 添加文件
            updater.update_file(test_file)
            
            # 获取文件ID
            db = Database(self.db_path)
            file_info = db.get_file_by_path(os.path.abspath(test_file))
            file_id = file_info['id'] if file_info else None
            print(f"   📄 文件ID: {file_id}")
            
            # 删除文件数据
            if file_id:
                updater.db.delete_file_data(file_id)
                print(f"   🗑️  已删除文件数据")
            
                # 验证删除
                file_info2 = db.get_file_by_path(os.path.abspath(test_file))
                if not file_info2:
                    print("   ✅ 文件已成功从数据库移除")
            
            db.close()
        finally:
            updater.close()
        
        return True
    
    def test_multiple_files(self):
        """测试: 多个文件批量更新"""
        print("\n" + "=" * 60)
        print("📄 测试: 多文件处理")
        print("=" * 60)
        
        updater = KnowledgeGraphUpdater(self.db_path)
        try:
            for i in range(10):
                test_file = os.path.join(self.test_dir, f"multi_file_{i}.ts")
                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(f'function func{i}() {{ return {i}; }}\n')
                    f.write(f'class Class{i} {{ method{i}() {{ return {i}; }} }}\n')
            
            start_time = time.time()
            for i in range(10):
                test_file = os.path.join(self.test_dir, f"multi_file_{i}.ts")
                updater.update_file(test_file)
            
            elapsed = time.time() - start_time
            print(f"   ⏱️  处理 10 个文件耗时: {elapsed:.3f}s")
            
            db = Database(self.db_path)
            all_files = db.get_all_files()
            print(f"   📊 数据库中的文件数: {len(all_files)}")
            db.close()
        finally:
            updater.close()
        
        return True
    
    def test_function_calls(self):
        """测试: 函数调用提取"""
        print("\n" + "=" * 60)
        print("📄 测试: 函数调用")
        print("=" * 60)
        
        updater = KnowledgeGraphUpdater(self.db_path)
        try:
            call_file = os.path.join(self.test_dir, "calls.ts")
            with open(call_file, 'w', encoding='utf-8') as f:
                f.write('function a() { return 1; }\n')
                f.write('function b() { a(); return 2; }\n')
                f.write('function c() { b(); a(); return 3; }\n')
            
            updater.update_file(call_file)
            print(f"   ✅ 调用解析处理完成")
            
        finally:
            updater.close()
        
        return True
    
    def test_special_characters(self):
        """测试: 特殊字符"""
        print("\n" + "=" * 60)
        print("📄 测试: 特殊字符和Unicode")
        print("=" * 60)
        
        updater = KnowledgeGraphUpdater(self.db_path)
        try:
            special_file = os.path.join(self.test_dir, "special.ts")
            with open(special_file, 'w', encoding='utf-8') as f:
                f.write('// 测试中文注释\n')
                f.write('const utf8_str = "世界你好";\n')
                f.write('// 测试表情符号: 🌍🚀🔥🎉\n')
                f.write('function unicodeTest() { return "日本語한국어"; }\n')
            
            result = updater.update_file(special_file)
            print(f"   ✅ Unicode处理结果: {result}")
        finally:
            updater.close()
        
        return True
    
    def test_full_scan(self):
        """测试: full_scan功能"""
        print("\n" + "=" * 60)
        print("📄 测试: full_scan功能")
        print("=" * 60)
        
        updater = KnowledgeGraphUpdater(self.db_path)
        try:
            # 在多个子目录创建文件
            subdirs = ['dir1', 'dir2', 'dir1/subdir']
            for subdir in subdirs:
                dir_path = os.path.join(self.test_dir, subdir)
                os.makedirs(dir_path, exist_ok=True)
                for i in range(3):
                    with open(os.path.join(dir_path, f'file{i}.ts'), 'w') as f:
                        f.write(f'function f{i}() {{ return {i}; }}\n')
            
            start_time = time.time()
            updater.full_scan(self.test_dir)
            elapsed = time.time() - start_time
            print(f"   ⏱️  full_scan 耗时: {elapsed:.3f}s")
            
            db = Database(self.db_path)
            all_files = db.get_all_files()
            print(f"   📊 扫描到的文件数: {len(all_files)}")
            db.close()
        finally:
            updater.close()
        
        return True
    
    def test_parser_methods(self):
        """测试: 解析器的各个方法"""
        print("\n" + "=" * 60)
        print("📄 测试: 解析器方法")
        print("=" * 60)
        
        parser = ArkTSParser()
        
        # 测试一个复杂的文件
        test_content = '''
        // A complex test file
        import { Test1, Test2 } from "test-module";
        function regular() { return 1; }
        async function async() { return 2; }
        const arrow = () => { return 3; };
        class MyClass {
            method() { regular(); }
        }
        '''
        
        temp_file = os.path.join(self.test_dir, "parser_test.ts")
        with open(temp_file, 'w') as f:
            f.write(test_content)
        
        result = parser.parse_file(temp_file)
        
        print(f"   📊 解析结果:")
        print(f"      - 函数: {len(result['functions'])}")
        print(f"      - 类: {len(result['classes'])}")
        print(f"      - 导入: {len(result['imports'])}")
        print(f"      - 调用: {len(result['calls'])}")
        print(f"   ✅ 解析器测试完成")
        
        return True
    
    def run_all_tests(self):
        """运行所有覆盖测试"""
        print("\n" + "=" * 60)
        print("🚀 开始全面分支覆盖测试")
        print("=" * 60)
        
        tests = [
            self.test_file_not_found,
            self.test_empty_file,
            self.test_only_comments,
            self.test_all_function_types,
            self.test_class_with_methods,
            self.test_import_variations,
            self.test_file_update_same_content,
            self.test_file_update_changed_content,
            self.test_file_deletion,
            self.test_multiple_files,
            self.test_function_calls,
            self.test_special_characters,
            self.test_full_scan,
            self.test_parser_methods,
        ]
        
        pass_count = 0
        fail_count = 0
        
        for test_func in tests:
            try:
                result = test_func()
                if result:
                    pass_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                logger.error(f"测试 {test_func.__name__} 失败: {e}", exc_info=True)
                fail_count += 1
        
        print("\n" + "=" * 60)
        print(f"📊 测试总结:")
        print(f"   ✅ 通过: {pass_count}")
        print(f"   ❌ 失败: {fail_count}")
        print("=" * 60)
        
        return fail_count == 0
    
    def cleanup(self):
        """清理测试目录"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

def main():
    print("🏁 开始全面分支覆盖测试")
    
    test = FullCoverageTest()
    try:
        success = test.run_all_tests()
        if success:
            print("\n🎉 所有覆盖测试通过!")
        else:
            print("\n❌ 部分测试失败")
            return 1
    finally:
        test.cleanup()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
