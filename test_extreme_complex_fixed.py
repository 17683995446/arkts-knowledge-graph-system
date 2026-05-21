#!/usr/bin/env python3
"""
超复杂真实场景深度测试
专注于复杂代码结构的解析和处理能力
"""
import os
import sys
import tempfile
import shutil
import time
import logging
from typing import List, Dict, Any

sys.path.insert(0, '/workspace')

from src.core_logged import KnowledgeGraphUpdater
from src.database.database_logged import Database
from src.parser import ArkTSParser
from src.logger import setup_logger

logger = setup_logger(level=logging.INFO)

class ExtremeComplexTest:
    """超复杂真实场景深度测试"""
    
    def __init__(self):
        self.test_dir = tempfile.mkdtemp(prefix="arkts_extreme_complex_")
        self.db_path = os.path.join(self.test_dir, "extreme_test.db")
        print(f"📂 测试目录: {self.test_dir}")
    
    def test_deeply_nested_classes(self) -> bool:
        """测试深度嵌套的类结构"""
        print("\n" + "=" * 70)
        print("🏗️  测试1: 深度嵌套的类结构")
        print("=" * 70)
        
        updater = KnowledgeGraphUpdater(self.db_path)
        try:
            # 创建多层嵌套类
            nested_code = '''
// 深度嵌套类结构
class Level1 {
    name: string = "Level1";
    
    level1Method(): void {
        console.log("Level1 method");
    }
    
    class Level2 {
        name: string = "Level2";
        
        level2Method(): void {
            console.log("Level2 method");
        }
        
        class Level3 {
            name: string = "Level3";
            
            level3Method(): void {
                this.level2Method();
            }
        }
        
        static staticLevel2Method(): void {
            console.log("Static level2");
        }
    }
    
    static staticLevel1Method(): void {
        console.log("Static level1");
    }
}

// 复杂的泛型类
class GenericContainer<T, U> {
    private key: T;
    private value: U;
    
    constructor(key: T, value: U) {
        this.key = key;
        this.value = value;
    }
    
    getKey(): T {
        return this.key;
    }
    
    setValue(val: U): void {
        this.value = val;
    }
    
    transform<V>(fn: (val: U) => V): V {
        return fn(this.value);
    }
}

// 多重继承模拟（通过组合）
class MultiImplementation {
    private impl1: Interface1;
    private impl2: Interface2;
    
    constructor() {
        this.impl1 = new Impl1();
        this.impl2 = new Impl2();
    }
    
    doSomething(): void {
        this.impl1.method1();
        this.impl2.method2();
    }
}

interface Interface1 {
    method1(): void;
}

interface Interface2 {
    method2(): void;
}

class Impl1 implements Interface1 {
    method1(): void {
        console.log("Impl1 method");
    }
}

class Impl2 implements Interface2 {
    method2(): void {
        console.log("Impl2 method");
    }
}
'''
            
            nested_file = os.path.join(self.test_dir, "deeply_nested.ts")
            with open(nested_file, 'w', encoding='utf-8') as f:
                f.write(nested_code)
            
            start = time.time()
            result = updater.update_file(nested_file)
            elapsed = time.time() - start
            
            print(f"   ⏱️  处理耗时: {elapsed:.3f}秒")
            print(f"   ✅ 处理结果: {'成功' if result else '跳过'}")
            
            # 验证解析结果
            db = Database(self.db_path)
            file_info = db.get_file_by_path(os.path.abspath(nested_file))
            if file_info:
                classes = db.get_classes_by_file(file_info['id'])
                functions = db.get_functions_by_file(file_info['id'])
                
                print(f"   📊 解析统计:")
                print(f"      - 类: {len(classes)} 个")
                print(f"      - 函数: {len(functions)} 个")
                
                # 验证每个类
                for cls in classes:
                    print(f"      类 '{cls['name']}': {len(cls.get('methods', []))} 个方法")
            
            db.close()
            return True
            
        except Exception as e:
            logger.error(f"深度嵌套类测试失败: {e}", exc_info=True)
            return False
        finally:
            updater.close()
    
    def test_complex_async_patterns(self) -> bool:
        """测试复杂的异步模式"""
        print("\n" + "=" * 70)
        print("⚡ 测试2: 复杂的异步模式")
        print("=" * 70)
        
        updater = KnowledgeGraphUpdater(self.db_path)
        try:
            async_code = '''
// 复杂的异步模式
async function fetchData<T>(url: string): Promise<T> {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

async function processWithRetry(
    operation: () => Promise<any>,
    maxRetries: number = 3
): Promise<any> {
    let lastError: Error;
    
    for (let i = 0; i < maxRetries; i++) {
        try {
            return await operation();
        } catch (error) {
            lastError = error;
            if (i < maxRetries - 1) {
                await delay(1000 * Math.pow(2, i));
            }
        }
    }
    
    throw lastError;
}

function delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
}

class AsyncQueue<T> {
    private queue: Array<() => Promise<T>> = [];
    private processing: boolean = false;
    
    async add(task: () => Promise<T>): Promise<T> {
        return new Promise((resolve, reject) => {
            this.queue.push(async () => {
                try {
                    const result = await task();
                    resolve(result);
                    return result;
                } catch (error) {
                    reject(error);
                    throw error;
                }
            });
            
            if (!this.processing) {
                this.processQueue();
            }
        });
    }
    
    private async processQueue(): Promise<void> {
        if (this.queue.length === 0) {
            this.processing = false;
            return;
        }
        
        this.processing = true;
        const task = this.queue.shift();
        if (task) {
            await task();
        }
        await this.processQueue();
    }
}

// Promise.all with timeout
async function promiseWithTimeout<T>(
    promise: Promise<T>,
    timeoutMs: number
): Promise<T> {
    const timeout = new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error('Timeout')), timeoutMs)
    );
    
    return Promise.race([promise, timeout]);
}

// 复杂的回调地狱
const complexCallback = (callback: (err: Error, result: any) => void) => {
    step1((err1, result1) => {
        if (err1) return callback(err1, null);
        
        step2(result1, (err2, result2) => {
            if (err2) return callback(err2, null);
            
            step3(result2, (err3, result3) => {
                if (err3) return callback(err3, null);
                
                step4(result3, (err4, result4) => {
                    if (err4) return callback(err4, null);
                    
                    callback(null, result4);
                });
            });
        });
    });
};

function step1(callback: Function): void {
    setTimeout(() => callback(null, 'step1'), 10);
}

function step2(data: any, callback: Function): void {
    setTimeout(() => callback(null, `${data}-step2`), 10);
}

function step3(data: any, callback: Function): void {
    setTimeout(() => callback(null, `${data}-step3`), 10);
}

function step4(data: any, callback: Function): void {
    setTimeout(() => callback(null, `${data}-step4`), 10);
}

// 事件发射器模式
class EventEmitter {
    private events: Map<string, Array<Function>> = new Map();
    
    on(event: string, listener: Function): this {
        if (!this.events.has(event)) {
            this.events.set(event, []);
        }
        this.events.get(event).push(listener);
        return this;
    }
    
    emit(event: string, ...args: any[]): void {
        const listeners = this.events.get(event);
        if (listeners) {
            listeners.forEach(listener => {
                try {
                    listener.apply(this, args);
                } catch (error) {
                    console.error(`Error in event listener: ${error}`);
                }
            });
        }
    }
    
    once(event: string, listener: Function): this {
        const onceWrapper = (...args: any[]) => {
            listener.apply(this, args);
            this.off(event, onceWrapper);
        };
        return this.on(event, onceWrapper);
    }
    
    off(event: string, listener: Function): this {
        const listeners = this.events.get(event);
        if (listeners) {
            const index = listeners.indexOf(listener);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
        return this;
    }
}
'''
            
            async_file = os.path.join(self.test_dir, "async_patterns.ts")
            with open(async_file, 'w', encoding='utf-8') as f:
                f.write(async_code)
            
            start = time.time()
            result = updater.update_file(async_file)
            elapsed = time.time() - start
            
            print(f"   ⏱️  处理耗时: {elapsed:.3f}秒")
            print(f"   ✅ 处理结果: {'成功' if result else '跳过'}")
            
            db = Database(self.db_path)
            file_info = db.get_file_by_path(os.path.abspath(async_file))
            if file_info:
                functions = db.get_functions_by_file(file_info['id'])
                classes = db.get_classes_by_file(file_info['id'])
                
                print(f"   📊 解析统计:")
                print(f"      - 异步函数: {len([f for f in functions if 'async' in f['content']])} 个")
                print(f"      - 类: {len(classes)} 个")
                print(f"      - 总函数: {len(functions)} 个")
            
            db.close()
            return True
            
        except Exception as e:
            logger.error(f"异步模式测试失败: {e}", exc_info=True)
            return False
        finally:
            updater.close()
    
    def test_complex_module_dependencies(self) -> bool:
        """测试复杂的模块依赖"""
        print("\n" + "=" * 70)
        print("🔗 测试3: 复杂的模块依赖关系")
        print("=" * 70)
        
        updater = KnowledgeGraphUpdater(self.db_path)
        try:
            # 创建多个相互依赖的文件
            files_content = {
                'base.ts': '''
import { Utility } from './utils';
import { Constants } from './constants';

export class BaseClass {
    protected utility: Utility;
    
    constructor() {
        this.utility = new Utility();
    }
    
    baseMethod(): void {
        this.utility.doSomething();
    }
}
''',
                'constants.ts': '''
export const APP_NAME = "KnowledgeGraph";
export const VERSION = "1.0.0";
export const MAX_RETRY = 3;

export class Constants {
    static readonly TIMEOUT = 5000;
    static readonly RETRY_DELAY = 1000;
}
''',
                'utils.ts': '''
import { Constants } from './constants';

export class Utility {
    doSomething(): void {
        console.log("Doing something with timeout:", Constants.TIMEOUT);
    }
    
    calculate(a: number, b: number): number {
        return a + b;
    }
}
''',
                'derived.ts': '''
import { BaseClass } from './base';
import { Utility } from './utils';
import { Constants } from './constants';

export class DerivedClass extends BaseClass {
    private utility: Utility;
    
    constructor() {
        super();
        this.utility = new Utility();
    }
    
    derivedMethod(): void {
        this.baseMethod();
        this.utility.doSomething();
        
        const retry = Constants.MAX_RETRY;
        console.log("Max retry:", retry);
    }
}
''',
                'main.ts': '''
import { BaseClass } from './base';
import { DerivedClass } from './derived';
import { Constants } from './constants';
import { Utility } from './utils';

class Main {
    run(): void {
        const base = new BaseClass();
        const derived = new DerivedClass();
        const utility = new Utility();
        
        base.baseMethod();
        derived.derivedMethod();
        derived.baseMethod();
        
        utility.doSomething();
        
        console.log("App:", Constants.APP_NAME);
        console.log("Version:", Constants.VERSION);
    }
}

const main = new Main();
main.run();
'''
            }
            
            # 创建文件
            for filename, content in files_content.items():
                filepath = os.path.join(self.test_dir, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # 批量更新
            start = time.time()
            for filename in files_content.keys():
                filepath = os.path.join(self.test_dir, filename)
                updater.update_file(filepath)
            elapsed = time.time() - start
            
            print(f"   ⏱️  处理耗时: {elapsed:.3f}秒")
            print(f"   📝 处理了 {len(files_content)} 个相互依赖的文件")
            
            # 验证导入关系
            db = Database(self.db_path)
            all_files = db.get_all_files()
            
            total_imports = 0
            for file_info in all_files:
                imports = db.get_imports_by_file(file_info['id'])
                total_imports += len(imports)
                print(f"   📄 {os.path.basename(file_info['path'])}: {len(imports)} 个导入")
            
            print(f"   📊 总导入数: {total_imports}")
            db.close()
            
            return True
            
        except Exception as e:
            logger.error(f"模块依赖测试失败: {e}", exc_info=True)
            return False
        finally:
            updater.close()
    
    def test_complex_control_flow(self) -> bool:
        """测试复杂的控制流"""
        print("\n" + "=" * 70)
        print("🔀 测试4: 复杂的控制流结构")
        print("=" * 70)
        
        updater = KnowledgeGraphUpdater(self.db_path)
        try:
            control_flow_code = '''
// 复杂的控制流结构
function complexControlFlow(
    value: number,
    callback: (result: number) => void
): void {
    // 多层条件嵌套
    if (value > 0) {
        if (value > 100) {
            if (value > 1000) {
                callback(value * 10);
            } else {
                callback(value * 5);
            }
        } else {
            if (value > 50) {
                callback(value * 3);
            } else {
                callback(value * 2);
            }
        }
    } else if (value < 0) {
        // 负数处理
        callback(Math.abs(value) * -1);
    } else {
        callback(0);
    }
}

// switch的高级用法
function advancedSwitch(type: string): void {
    switch (type) {
        case "A":
            console.log("Type A");
            break;
        case "B":
            console.log("Type B");
            break;
        default:
            console.log("Unknown type");
    }
}

// try-catch-finally链
function tryCatchChain(): void {
    try {
        try {
            throw new Error("Inner error");
        } catch (inner) {
            console.error("Inner catch:", inner);
            throw inner;
        }
    } catch (outer) {
        console.error("Outer catch:", outer);
    } finally {
        console.log("Finally block");
    }
}

// while和for的混合使用
function mixedLoop(): number {
    let result = 0;
    
    for (let i = 0; i < 10; i++) {
        let j = 0;
        while (j < 5) {
            if (i === j) {
                result += i * j;
            }
            j++;
        }
    }
    
    return result;
}

// do-while循环
function doWhileLoop(): void {
    let i = 0;
    do {
        console.log(i);
        i++;
    } while (i < 10);
}

// for...in 和 for...of
function iterateOver(): void {
    const array = [1, 2, 3, 4, 5];
    
    for (const item of array) {
        console.log(item);
    }
    
    const obj = { a: 1, b: 2 };
    for (const key in obj) {
        console.log(key, obj[key]);
    }
}

// label语句
function labeledStatement(): void {
    outer: for (let i = 0; i < 3; i++) {
        for (let j = 0; j < 3; j++) {
            if (i === j) {
                continue outer;
            }
            console.log(i, j);
        }
    }
}

// 复杂的条件表达式
function complexExpression(): boolean {
    return (
        (true && false) ||
        (!false || true) &&
        (10 > 5 && 20 < 30)
    );
}

// 三元运算符嵌套
function nestedTernary(x: number): string {
    return x > 0
        ? x > 10
            ? "large"
            : "small"
        : "negative";
}

// break和continue
function breakContinue(): void {
    for (let i = 0; i < 10; i++) {
        if (i === 3) {
            continue;
        }
        if (i === 7) {
            break;
        }
        console.log(i);
    }
}
'''
            
            control_file = os.path.join(self.test_dir, "control_flow.ts")
            with open(control_file, 'w', encoding='utf-8') as f:
                f.write(control_flow_code)
            
            start = time.time()
            result = updater.update_file(control_file)
            elapsed = time.time() - start
            
            print(f"   ⏱️  处理耗时: {elapsed:.3f}秒")
            print(f"   ✅ 处理结果: {'成功' if result else '跳过'}")
            
            db = Database(self.db_path)
            file_info = db.get_file_by_path(os.path.abspath(control_file))
            if file_info:
                functions = db.get_functions_by_file(file_info['id'])
                
                print(f"   📊 解析统计:")
                print(f"      - 复杂控制流函数: {len(functions)} 个")
                
                for func in functions:
                    print(f"      📌 {func['name']} (行 {func['line_start']}-{func['line_end']})")
            
            db.close()
            return True
            
        except Exception as e:
            logger.error(f"控制流测试失败: {e}", exc_info=True)
            return False
        finally:
            updater.close()
    
    def test_extreme_edge_cases(self) -> bool:
        """测试极端边界情况"""
        print("\n" + "=" * 70)
        print("⚠️  测试5: 极端边界情况")
        print("=" * 70)
        
        updater = KnowledgeGraphUpdater(self.db_path)
        try:
            # 空文件
            empty_file = os.path.join(self.test_dir, "empty.ts")
            with open(empty_file, 'w') as f:
                pass
            
            # 特殊字符文件
            unicode_file = os.path.join(self.test_dir, "unicode.ts")
            with open(unicode_file, 'w', encoding='utf-8') as f:
                f.write('''
// 中文注释：这是一个测试文件
// 日本語コメント
// 한국어 댓글
// Emoji: 🚀🔥💻📱🌐

class 中文类 {
    公共方法(): void {
        console.log("测试");
    }
}

const 变量 = "值";
''')
            
            # 只有空格和换行的文件
            whitespace_file = os.path.join(self.test_dir, "whitespace.ts")
            with open(whitespace_file, 'w') as f:
                f.write('   \n\n   \n   \n')
            
            # 特殊文件名
            special_name_file = os.path.join(self.test_dir, "file-with-dashes_and_underscores.ts")
            with open(special_name_file, 'w', encoding='utf-8') as f:
                f.write('function test() { return true; }\n')
            
            # 超大文件（模拟）
            huge_file = os.path.join(self.test_dir, "huge_file.ts")
            with open(huge_file, 'w', encoding='utf-8') as f:
                # 生成1000行代码
                for i in range(1000):
                    f.write(f'function func{i}() {{ return {i}; }}\n')
                    f.write(f'class Class{i} {{ method{i}() {{ return {i}; }} }}\n')
            
            # 测试所有这些文件
            test_files = [huge_file, empty_file, unicode_file, whitespace_file, special_name_file]
            results = []
            
            for filepath in test_files:
                start = time.time()
                try:
                    result = updater.update_file(filepath)
                    elapsed = time.time() - start
                    results.append({
                        'file': os.path.basename(filepath),
                        'success': True,
                        'elapsed': elapsed
                    })
                except Exception as e:
                    results.append({
                        'file': os.path.basename(filepath),
                        'success': False,
                        'error': str(e)
                    })
            
            print(f"   📊 边界测试结果:")
            for r in results:
                if r['success']:
                    print(f"      ✅ {r['file']}: {r['elapsed']:.3f}秒")
                else:
                    print(f"      ❌ {r['file']}: {r['error']}")
            
            return all(r['success'] for r in results)
            
        except Exception as e:
            logger.error(f"边界测试失败: {e}", exc_info=True)
            return False
        finally:
            updater.close()
    
    def test_mixed_complex_scenarios(self) -> bool:
        """混合复杂场景测试"""
        print("\n" + "=" * 70)
        print("🎯 测试6: 混合复杂场景")
        print("=" * 70)
        
        updater = KnowledgeGraphUpdater(self.db_path)
        try:
            # 创建大量复杂文件
            for i in range(50):
                code_lines = [
                    f'// 文件 {i} - 复杂场景测试',
                    '',
                    f'import {{ Utility{i}, Handler{i} }} from \'./module{i}\';',
                    f"import * as Utils from './utils{i}';",
                    '',
                    f'class Service{i} {{',
                    f'    private handlers{i}: Handler{i}[] = [];',
                    f'    private utility{i}: Utility{i};',
                    '    ',
                    '    constructor() {',
                    f'        this.utility{i} = new Utility{i}();',
                    '    }',
                    '    ',
                    f'    async process{i}(data: any): Promise<any> {{',
                    '        try {',
                    '            const result = await this.utility{i}.process(data);',
                    '            this.handlers{i}.forEach(h => h.handle(result));',
                    '            return result;',
                    '        }} catch (error) {{',
                    '            console.error(error);',
                    '            throw error;',
                    '        }}',
                    '    }',
                    '    ',
                    f'    addHandler{i}(handler: Handler{i}): void {{',
                    '        this.handlers{i}.push(handler);',
                    '    }}',
                    '    ',
                    f'    removeHandler{i}(handler: Handler{i}): void {{',
                    '        const index = this.handlers{i}.indexOf(handler);',
                    '        if (index > -1) {{',
                    '            this.handlers{i}.splice(index, 1);',
                    '        }}',
                    '    }}',
                    '    ',
                    f'    clearHandlers{i}(): void {{',
                    '        this.handlers{i} = [];',
                    '    }}',
                    '    ',
                    f'    getHandlerCount{i}(): number {{',
                    '        return this.handlers{i}.length;',
                    '    }}',
                    '}',
                    '',
                    f'interface Handler{i} {{',
                    '    handle(data: any): void;',
                    '}}',
                    '',
                    f'class HandlerImpl{i} {{',
                    '    handle(data: any): void {{',
                    '        console.log("Handling:", data);',
                    '    }}',
                    '}',
                    '',
                    f'function utilityFunction{i}(value: any): any {{',
                    '    return value;',
                    '}}',
                    '',
                    f'const arrowFunction{i} = (x: number) => {{',
                    '    return x * x;',
                    '}};',
                    '',
                    f'async function asyncFunction{i}(): Promise<void> {{',
                    '    await new Promise(resolve => setTimeout(resolve, 100));',
                    f'    console.log("Async {i}");',
                    '}}',
                    '',
                    f'class GenericClass{i} {{',
                    '    private first: any;',
                    '    private second: any;',
                    '    ',
                    '    constructor(first: any, second: any) {',
                    '        this.first = first;',
                    '        this.second = second;',
                    '    }',
                    '    ',
                    '    getFirst(): any {',
                    '        return this.first;',
                    '    }',
                    '    ',
                    '    getSecond(): any {',
                    '        return this.second;',
                    '    }}',
                    '}',
                    ''
                ]
                complex_code = '\n'.join(code_lines)
                
                filepath = os.path.join(self.test_dir, f'complex_{i:03d}.ts')
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(complex_code)
                
                updater.update_file(filepath)
            
            print(f"   ✅ 创建并处理了 50 个复杂文件")
            
            # 验证数据一致性
            db = Database(self.db_path)
            all_files = db.get_all_files()
            
            total_classes = 0
            total_functions = 0
            total_imports = 0
            
            for file_info in all_files:
                classes = db.get_classes_by_file(file_info['id'])
                functions = db.get_functions_by_file(file_info['id'])
                imports = db.get_imports_by_file(file_info['id'])
                
                total_classes += len(classes)
                total_functions += len(functions)
                total_imports += len(imports)
            
            print(f"   📊 解析统计:")
            print(f"      - 文件: {len(all_files)} 个")
            print(f"      - 类: {total_classes} 个")
            print(f"      - 函数: {total_functions} 个")
            print(f"      - 导入: {total_imports} 个")
            
            db.close()
            return True
            
        except Exception as e:
            logger.error(f"混合场景测试失败: {e}", exc_info=True)
            return False
        finally:
            updater.close()
    
    def run_all_tests(self) -> bool:
        """运行所有测试"""
        print("\n" + "=" * 70)
        print("🚀 开始超复杂真实场景深度测试")
        print("=" * 70)
        
        tests = [
            ("深度嵌套类结构", self.test_deeply_nested_classes),
            ("复杂异步模式", self.test_complex_async_patterns),
            ("复杂模块依赖", self.test_complex_module_dependencies),
            ("复杂控制流", self.test_complex_control_flow),
            ("极端边界情况", self.test_extreme_edge_cases),
            ("混合复杂场景", self.test_mixed_complex_scenarios),
        ]
        
        pass_count = 0
        fail_count = 0
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                if result:
                    pass_count += 1
                    print(f"   ✅ {test_name}: 通过")
                else:
                    fail_count += 1
                    print(f"   ❌ {test_name}: 失败")
            except Exception as e:
                logger.error(f"测试 {test_name} 异常: {e}", exc_info=True)
                fail_count += 1
                print(f"   💥 {test_name}: 异常 - {e}")
        
        print("\n" + "=" * 70)
        print(f"📊 测试总结:")
        print(f"   ✅ 通过: {pass_count}/{len(tests)}")
        print(f"   ❌ 失败: {fail_count}/{len(tests)}")
        print("=" * 70)
        
        return fail_count == 0
    
    def cleanup(self):
        """清理测试文件"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

def main():
    print("🏁 开始超复杂真实场景深度测试\n")
    
    test = ExtremeComplexTest()
    try:
        success = test.run_all_tests()
        if success:
            print("\n🎉 所有超复杂场景测试通过!")
        else:
            print("\n⚠️  部分测试失败")
    finally:
        test.cleanup()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
