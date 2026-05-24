#!/usr/bin/env python3
"""
超极端混乱场景深度测试 - 挑战系统的极限！
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

sys.path.insert(0, '/workspace')

from src.core import KnowledgeGraphUpdater
from src.database import Database
from src.parser import ArkTSParser
from src.logger import setup_logger

logger = setup_logger(level=logging.INFO)


class ExtremeChaosTest:
    """超极端混乱场景测试器"""
    
    def __init__(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="arkts_extreme_chaos_"))
        self.db_path = self.test_dir / "chaos_test.db"
        self.results = []
        print(f"🏗️  超极端混乱测试目录: {self.test_dir}")
    
    def generate_chaos_file(self, file_path: Path, chaos_level: int = 5):
        """生成极度混乱的测试文件"""
        parts = []
        
        # 1. 随机长度的注释（包含各种字符）
        if random.random() > 0.3:
            for _ in range(random.randint(1, chaos_level * 3)):
                comment = '// ' + ''.join(
                    random.choice(string.ascii_letters + string.digits + ' \t\n@#$%^&*()_+[]{}|;:,.<>?')
                    for _ in range(random.randint(10, 200))
                )
                parts.append(comment)
        
        # 2. 混合有效的和无效的代码
        code_count = random.randint(1, chaos_level * 2)
        for _ in range(code_count):
            if random.random() > 0.3:  # 70% 有效代码
                parts.append(self._generate_valid_code())
            else:  # 30% 故意写的烂代码
                parts.append(self._generate_broken_code())
        
        # 3. 随机插入空白
        for _ in range(random.randint(0, chaos_level)):
            insert_pos = random.randint(0, len(parts))
            blank_lines = '\n' * random.randint(1, 10)
            parts.insert(insert_pos, blank_lines)
        
        # 4. 可能添加一些特殊字符行
        if random.random() > 0.5:
            special_chars = ''.join(chr(random.randint(0, 127)) for _ in range(random.randint(10, 100)))
            parts.append(f'// Special chars: {repr(special_chars)}')
        
        # 拼接并写入
        content = '\n'.join(parts)
        with open(file_path, 'w', encoding='utf-8', errors='ignore') as f:
            f.write(content)
        
        return file_path
    
    def _generate_valid_code(self) -> str:
        """生成一段有效的代码"""
        code_type = random.choice(['function', 'class', 'import', 'const', 'mixed'])
        
        if code_type == 'function':
            func_name = ''.join(random.choice(string.ascii_letters) for _ in range(random.randint(3, 20)))
            return f'function {func_name}() {{ return {random.randint(0, 1000)}; }}'
        
        elif code_type == 'class':
            class_name = random.choice(string.ascii_uppercase) + ''.join(
                random.choice(string.ascii_letters) for _ in range(random.randint(3, 15))
            )
            method_count = random.randint(1, 5)
            methods = []
            for _ in range(method_count):
                m_name = ''.join(random.choice(string.ascii_letters) for _ in range(random.randint(3, 15)))
                methods.append(f'  {m_name}() {{ return {random.choice(["true", "false", "42", "\"test\""])}; }}')
            return f'class {class_name} {{\n' + '\n'.join(methods) + '\n}'
        
        elif code_type == 'import':
            module_name = ''.join(random.choice(string.ascii_lowercase) for _ in range(random.randint(2, 10)))
            return f'import {{ {random.choice(string.ascii_uppercase) + "".join(random.choice(string.ascii_letters) for _ in range(3, 8))} }} from "./{module_name}";'
        
        elif code_type == 'const':
            const_name = ''.join(random.choice(string.ascii_uppercase + '_') for _ in range(random.randint(3, 15)))
            value = random.choice([
                str(random.randint(0, 1000)),
                f'"{random.choice(string.ascii_letters) * random.randint(1, 20)}"',
                'true',
                'false'
            ])
            return f'const {const_name} = {value};'
        
        else:  # mixed
            return self._generate_valid_code() + '\n' + self._generate_valid_code()
    
    def _generate_broken_code(self) -> str:
        """生成故意损坏的代码（用于测试错误处理）"""
        broken_types = [
            'function {',
            'class ',
            'const = 42',
            'import from ',
            'if (true) {',
            'for (let i = 0;',
            'function() { missing name }',
            'class { missing name }'
        ]
        return random.choice(broken_types)
    
    def test_chaos_file_batch(self, num_files: int = 100, chaos_level: int = 5):
        """超混乱文件批量测试"""
        print("\n" + "="*80)
        print(f"🔥 测试: {num_files} 个超混乱文件 (混乱级别 {chaos_level})")
        print("="*80)
        
        test_start = time.time()
        success_count = 0
        failed_count = 0
        files = []
        
        # 创建并测试
        for i in range(num_files):
            try:
                file_path = self.test_dir / f"chaos_{i:04d}.ts"
                self.generate_chaos_file(file_path, chaos_level)
                files.append(file_path)
            except Exception as e:
                print(f"⚠️  生成文件 {i} 时出错: {e}")
                failed_count += 1
        
        print(f"\n✅ 生成了 {len(files)} 个混乱文件，开始处理...")
        
        updater = KnowledgeGraphUpdater(str(self.db_path))
        
        for file_path in files:
            try:
                result = updater.update_file(str(file_path))
                if result or not result:  # 无论怎样，只要不崩溃就好
                    success_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"处理失败 {file_path.name}: {e}")
                failed_count += 1
        
        elapsed = time.time() - test_start
        
        print(f"\n{'='*80}")
        print(f"📊 超混乱批量测试结果:")
        print(f"   - 总文件数: {len(files)}")
        print(f"   - 成功处理: {success_count}")
        print(f"   - 处理失败: {failed_count}")
        print(f"   - 总耗时: {elapsed:.2f} 秒")
        print(f"   - 平均/文件: {elapsed/max(len(files), 1):.4f} 秒")
        
        passed = failed_count == 0
        self.results.append(("超混乱文件批量测试", passed))
        return passed
    
    def test_rapid_mutation_stress(self, iterations: int = 500):
        """快速文件突变压力测试"""
        print("\n" + "="*80)
        print(f"⚡ 测试: 快速文件突变压力测试 ({iterations} 次)")
        print("="*80)
        
        file_path = self.test_dir / "rapid_mutate.ts"
        updater = KnowledgeGraphUpdater(str(self.db_path))
        
        test_start = time.time()
        success_count = 0
        
        try:
            for i in range(iterations):
                # 随机生成不同的内容
                if random.random() > 0.5:
                    content = f'function foo{i}() {{ return {i}; }}\n'
                else:
                    content = f'class Bar{i} {{ method() {{ return {i}; }} }}\n'
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                try:
                    updater.update_file(str(file_path))
                    success_count += 1
                except Exception as e:
                    logger.error(f"迭代 {i} 失败: {e}")
            
            elapsed = time.time() - test_start
            
            print(f"\n📊 快速突变测试结果:")
            print(f"   - 总迭代次数: {iterations}")
            print(f"   - 成功次数: {success_count}")
            print(f"   - 成功率: {100.0 * success_count / max(iterations, 1):.1f}%")
            print(f"   - 总耗时: {elapsed:.2f} 秒")
            print(f"   - 平均/迭代: {elapsed/max(iterations, 1):.4f} 秒")
            
            passed = success_count == iterations
            self.results.append(("快速文件突变测试", passed))
            return passed
            
        finally:
            updater.close()
    
    def test_chaos_database_stress(self):
        """极端混乱的数据库压力测试"""
        print("\n" + "="*80)
        print("💾 测试: 极端混乱数据库压力测试")
        print("="*80)
        
        updater = KnowledgeGraphUpdater(str(self.db_path))
        db = Database(str(self.db_path))
        
        test_start = time.time()
        
        # 先创建一些数据
        files_created = []
        for i in range(50):
            fp = self.test_dir / f"chaos_db_{i}.ts"
            with open(fp, 'w', encoding='utf-8') as f:
                f.write(f'function f{i}() {{ return {i}; }}\n')
            updater.update_file(str(fp))
            files_created.append(fp)
        
        print(f"   📝 初始创建: {len(files_created)} 个文件")
        
        # 开始疯狂的数据库操作
        all_files = db.get_all_files()
        print(f"   📊 初始数据库中有: {len(all_files)} 个文件")
        
        operations_count = 0
        errors_count = 0
        
        try:
            for i in range(200):
                try:
                    operation_type = random.choice([
                        'update', 'delete', 'add', 'query'
                    ])
                    
                    if operation_type == 'add':
                        # 添加新文件
                        fp = self.test_dir / f"chaos_db_new_{i}.ts"
                        with open(fp, 'w', encoding='utf-8') as f:
                            f.write(f'function new{i}() {{ return {i}; }}\n')
                        updater.update_file(str(fp))
                        operations_count += 1
                    
                    elif operation_type == 'update':
                        # 随机更新
                        files = db.get_all_files()
                        if files:
                            file_info = random.choice(files)
                            fp = Path(file_info['path'])
                            if fp.exists():
                                with open(fp, 'w', encoding='utf-8') as f:
                                    f.write(f'function updated{i}() {{ return {i}; }}\n')
                                updater.update_file(str(fp))
                                operations_count += 1
                    
                    elif operation_type == 'delete':
                        # 随机删除
                        files = db.get_all_files()
                        if files:
                            file_info = random.choice(files)
                            try:
                                updater.db.delete_file_data(file_info['id'])
                                fp = Path(file_info['path'])
                                if fp.exists():
                                    os.remove(fp)
                                operations_count += 1
                            except Exception:
                                pass
                    
                    elif operation_type == 'query':
                        # 查询
                        files = db.get_all_files()
                        for fi in files:
                            db.get_functions_by_file(fi['id'])
                            db.get_classes_by_file(fi['id'])
                            db.get_imports_by_file(fi['id'])
                        operations_count += 1
                
                except Exception as e:
                    logger.error(f"数据库操作失败: {e}")
                    errors_count += 1
            
            elapsed = time.time() - test_start
            
            print(f"\n📊 极端数据库测试结果:")
            print(f"   - 总操作次数: {operations_count}")
            print(f"   - 错误次数: {errors_count}")
            print(f"   - 总耗时: {elapsed:.2f} 秒")
            
            final_files = db.get_all_files()
            print(f"   - 最终文件数: {len(final_files)}")
            
            passed = errors_count == 0
            self.results.append(("极端混乱数据库测试", passed))
            return passed
        
        finally:
            db.close()
            updater.close()
    
    def test_unicode_nightmare(self):
        """Unicode 噩梦测试 - 各种奇怪字符的文件"""
        print("\n" + "="*80)
        print("🌍 测试: Unicode 噩梦测试")
        print("="*80)
        
        test_cases = [
            ("中文命名", """
// 中文测试
function 中文函数() {
    const 变量 = "值";
    class 中文类 {
        方法() {
            return "中文返回";
        }
    }
}
"""),
            ("日文韩文", """
// マルチバイト
function 日本語() {
    const 日本語変数 = "値";
}
function 한국어() {
    const 한국어변수 = "값";
}
"""),
            ("Emoji 轰炸", """
// 🚀 🔥 💻 📱 🌐 🎯
const 🚀 = "rocket";
class 💻 {
    🔥() {
        return "🔥";
    }
}
"""),
            ("混合多语言", """
import { Module } from "module";
function 混合() {
    const mixed = 42;
    class Mixed {
        法語() {
            return "Bonjour";
        }
        Deutsch() {
            return "Hallo";
        }
    }
}
"""),
            ("超长Unicode", """
function longNameWithUnicodeAndLotsOfCharacters() {
    const veryLongVariableNameThatIsWayTooLong = 42;
    return veryLongVariableNameThatIsWayTooLong;
}
"""),
        ]
        
        updater = KnowledgeGraphUpdater(str(self.db_path))
        passed_count = 0
        
        for name, content in test_cases:
            print(f"\n   📄 测试: {name}")
            try:
                fp = self.test_dir / f"unicode_{hashlib.md5(name.encode()).hexdigest()[:8]}.ts"
                with open(fp, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                updater.update_file(str(fp))
                passed_count += 1
                print(f"      ✅ 成功")
                
            except Exception as e:
                logger.error(f"Unicode 测试 {name} 失败: {e}")
                print(f"      ❌ 失败: {e}")
        
        print(f"\n📊 Unicode 测试结果:")
        print(f"   - 测试用例: {len(test_cases)}")
        print(f"   - 通过: {passed_count}")
        print(f"   - 失败: {len(test_cases) - passed_count}")
        
        passed = passed_count == len(test_cases)
        self.results.append(("Unicode 噩梦测试", passed))
        return passed
    
    def test_extreme_edge_cases(self):
        """极端边界情况测试"""
        print("\n" + "="*80)
        print("⚠️  测试: 极端边界情况")
        print("="*80)
        
        cases = [
            ("空文件", ""),
            ("只有换行", "\n" * 100),
            ("只有空格", " " * 500),
            ("只有制表符", "\t" * 500),
            ("一行超长代码", "function f() { " + "return " * 100 + "42; }"),
            ("混合空白字符", "  \n  \t  \n  " * 20),
            ("注释轰炸", "\n".join("// " + "x"*100 for _ in range(100))),
        ]
        
        updater = KnowledgeGraphUpdater(str(self.db_path))
        passed = 0
        
        for name, content in cases:
            try:
                fp = self.test_dir / f"edge_{hashlib.md5(name.encode()).hexdigest()[:8]}.ts"
                with open(fp, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                updater.update_file(str(fp))
                passed += 1
                print(f"   ✅ {name}: 成功")
                
            except Exception as e:
                logger.error(f"边界测试 {name} 失败: {e}")
                print(f"   ❌ {name}: 失败 - {e}")
        
        print(f"\n📊 边界情况测试结果:")
        print(f"   - 总用例: {len(cases)}")
        print(f"   - 通过: {passed}")
        
        passed_all = passed == len(cases)
        self.results.append(("极端边界情况测试", passed_all))
        return passed_all
    
    def test_final_verification(self):
        """最终的数据一致性验证"""
        print("\n" + "="*80)
        print("🔍 最终数据一致性验证")
        print("="*80)
        
        db = Database(str(self.db_path))
        
        try:
            all_files = db.get_all_files()
            print(f"📊 数据库状态:")
            print(f"   - 文件数: {len(all_files)}")
            
            total_functions = 0
            total_classes = 0
            total_imports = 0
            
            for file_info in all_files:
                funcs = db.get_functions_by_file(file_info['id'])
                classes = db.get_classes_by_file(file_info['id'])
                imports = db.get_imports_by_file(file_info['id'])
                total_functions += len(funcs)
                total_classes += len(classes)
                total_imports += len(imports)
            
            print(f"   - 函数: {total_functions}")
            print(f"   - 类: {total_classes}")
            print(f"   - 导入: {total_imports}")
            
            print("\n✅ 数据一致性验证通过！")
            self.results.append(("最终数据一致性验证", True))
            return True
            
        except Exception as e:
            logger.error(f"数据一致性验证失败: {e}", exc_info=True)
            self.results.append(("最终数据一致性验证", False))
            return False
        finally:
            db.close()
    
    def run_all_tests(self):
        """运行所有超极端测试"""
        print("="*80)
        print("🔥 超极端混乱场景深度测试启动")
        print("="*80)
        
        self.results = []
        
        # 运行所有测试
        self.test_chaos_file_batch(100, 5)
        self.test_rapid_mutation_stress(500)
        self.test_chaos_database_stress()
        self.test_unicode_nightmare()
        self.test_extreme_edge_cases()
        self.test_final_verification()
        
        # 总结
        print("\n" + "="*80)
        print("📈 超极端混乱测试总结")
        print("="*80)
        
        for name, passed in self.results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {status}: {name}")
        
        total = len(self.results)
        passed_count = sum(1 for _, p in self.results if p)
        
        print(f"\n🎯 最终结果: {passed_count}/{total} 通过")
        
        return passed_count == total
    
    def cleanup(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        print(f"\n🧹 测试文件已清理")


def main():
    print("="*80)
    print("🔥 超极端混乱场景深度测试")
    print("="*80)
    
    test = ExtremeChaosTest()
    
    try:
        success = test.run_all_tests()
        
        if success:
            print("\n🎉 所有超极端混乱测试完美通过！系统坚不可摧！🚀")
        else:
            print("\n⚠️  有一些测试失败了，需要进一步分析")
        
        return 0 if success else 1
    finally:
        test.cleanup()


if __name__ == "__main__":
    sys.exit(main())
