import re
from typing import List, Dict, Any, Tuple
from src.logger import logger, log_function


class ArkTSParser:
    def __init__(self):
        logger.debug(f"[ArkTSParser] Initializing")
        self.import_pattern = re.compile(
            r'import\s+(?:\{([^}]+)\}|\s*(\w+))\s+from\s+[\'"]([^\'"]+)[\'"]',
            re.DOTALL
        )
        self.call_pattern = re.compile(r'(\w+)\s*\(')

    @log_function
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        logger.debug(f"[parse_file] Parsing file: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"[parse_file] Error reading file {file_path}: {e}")
            print(f"Error reading file {file_path}: {e}")
            return {
                'functions': [],
                'classes': [],
                'imports': [],
                'calls': []
            }

        lines = content.split('\n')

        logger.debug(f"[parse_file] Extracting classes with methods")
        classes = self._extract_classes_with_methods(content, lines)
        logger.debug(f"[parse_file] Extracted {len(classes)} classes")

        logger.debug(f"[parse_file] Extracting all functions")
        functions = self._extract_all_functions(content, lines)
        logger.debug(f"[parse_file] Extracted {len(functions)} functions")

        logger.debug(f"[parse_file] Extracting imports")
        imports = self._extract_imports(content)
        logger.debug(f"[parse_file] Extracted {len(imports)} imports")

        logger.debug(f"[parse_file] Extracting calls")
        calls = self._extract_calls(content, functions + [m for c in classes for m in c.get('methods', [])])
        logger.debug(f"[parse_file] Extracted {len(calls)} calls")

        result = {
            'functions': functions,
            'classes': classes,
            'imports': imports,
            'calls': calls
        }
        logger.debug(f"[parse_file] Parsing complete")
        return result

    @log_function
    def _extract_all_functions(self, content: str, lines: List[str]) -> List[Dict[str, Any]]:
        logger.debug(f"[_extract_all_functions] Starting")
        functions = []
        seen_names = set()

        functions.extend(self._extract_top_level_functions(lines, seen_names))
        functions.extend(self._extract_arrow_functions(lines, seen_names))
        functions.extend(self._extract_async_functions(lines, seen_names))

        logger.debug(f"[_extract_all_functions] Extracted {len(functions)} functions total")
        return functions

    @log_function
    def _extract_top_level_functions(self, lines: List[str], seen_names: set) -> List[Dict[str, Any]]:
        functions = []
        func_pattern = re.compile(r'^function\s+(\w+)\s*\(')

        for i, line in enumerate(lines):
            match = func_pattern.match(line.strip())
            if match:
                func_name = match.group(1)
                if func_name not in seen_names:
                    seen_names.add(func_name)
                    func_info = self._extract_function_body(lines, i, func_name)
                    if func_info:
                        functions.append(func_info)

        return functions

    @log_function
    def _extract_arrow_functions(self, lines: List[str], seen_names: set) -> List[Dict[str, Any]]:
        logger.debug(f"[_extract_arrow_functions] Starting")
        functions = []
        arrow_pattern = re.compile(r'const\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>|const\s+(\w+)\s*=\s*(?:async\s+)?\w+\s*=>')

        for i, line in enumerate(lines):
            match = arrow_pattern.search(line)
            if match:
                func_name = match.group(1) or match.group(2)
                if func_name and func_name not in seen_names:
                    seen_names.add(func_name)
                    func_info = self._extract_arrow_function_body(lines, i, func_name)
                    if func_info:
                        functions.append(func_info)

        logger.debug(f"[_extract_arrow_functions] Extracted {len(functions)} arrow functions")
        return functions

    @log_function
    def _extract_async_functions(self, lines: List[str], seen_names: set) -> List[Dict[str, Any]]:
        logger.debug(f"[_extract_async_functions] Starting")
        functions = []
        async_pattern = re.compile(r'async\s+function\s+(\w+)\s*\(')

        for i, line in enumerate(lines):
            match = async_pattern.search(line)
            if match:
                func_name = match.group(1)
                if func_name not in seen_names:
                    seen_names.add(func_name)
                    func_info = self._extract_function_body(lines, i, func_name)
                    if func_info:
                        functions.append(func_info)

        logger.debug(f"[_extract_async_functions] Extracted {len(functions)} async functions")
        return functions

    @log_function
    def _extract_function_body(self, lines: List[str], start_idx: int, func_name: str) -> Dict[str, Any]:
        logger.debug(f"[_extract_function_body] Extracting body for: {func_name}")
        start_line = start_idx + 1
        brace_count = 0
        end_line = start_line
        found_start = False

        for j in range(start_idx, len(lines)):
            line = lines[j]
            for char in line:
                if char == '{':
                    brace_count += 1
                    found_start = True
                elif char == '}':
                    brace_count -= 1
                    if found_start and brace_count == 0:
                        end_line = j + 1
                        break
            if found_start and brace_count == 0:
                break

        func_content = '\n'.join(lines[start_idx:end_line])
        result = {
            'name': func_name,
            'line_start': start_line,
            'line_end': end_line,
            'content': func_content
        }
        logger.debug(f"[_extract_function_body] Extracted body for: {func_name} (lines {start_line}-{end_line})")
        return result

    @log_function
    def _extract_arrow_function_body(self, lines: List[str], start_idx: int, func_name: str) -> Dict[str, Any]:
        logger.debug(f"[_extract_arrow_function_body] Extracting arrow function body for: {func_name}")
        start_line = start_idx + 1
        brace_count = 0
        end_line = start_line
        found_start = False
        found_arrow = False

        for j in range(start_idx, len(lines)):
            line = lines[j]
            for char in line:
                if char == '{':
                    if found_arrow:
                        brace_count += 1
                        found_start = True
                elif char == '}':
                    if found_start:
                        brace_count -= 1
                        if brace_count == 0:
                            end_line = j + 1
                            break
                elif char == '=' and j == start_idx:
                    if '=>' in line:
                        found_arrow = True
            if found_start and brace_count == 0:
                break

        func_content = '\n'.join(lines[start_idx:end_line])
        result = {
            'name': func_name,
            'line_start': start_line,
            'line_end': end_line,
            'content': func_content
        }
        logger.debug(f"[_extract_arrow_function_body] Extracted body for: {func_name}")
        return result

    @log_function
    def _extract_classes_with_methods(self, content: str, lines: List[str]) -> List[Dict[str, Any]]:
        logger.debug(f"[_extract_classes_with_methods] Starting")
        classes = []
        class_pattern = re.compile(r'class\s+(\w+)')

        for i, line in enumerate(lines):
            match = class_pattern.search(line)
            if match:
                class_name = match.group(1)
                logger.debug(f"[_extract_classes_with_methods] Found class: {class_name} at line {i+1}")
                start_line = i + 1

                brace_count = 0
                end_line = start_line
                found_start = False

                for j in range(i, len(lines)):
                    for char in lines[j]:
                        if char == '{':
                            brace_count += 1
                            found_start = True
                        elif char == '}':
                            brace_count -= 1
                            if found_start and brace_count == 0:
                                end_line = j + 1
                                break
                    if found_start and brace_count == 0:
                        break

                class_content = '\n'.join(lines[i:end_line])
                class_info = {
                    'name': class_name,
                    'line_start': start_line,
                    'line_end': end_line,
                    'content': class_content
                }

                logger.debug(f"[_extract_classes_with_methods] Extracting methods for class: {class_name}")
                methods = self._extract_class_methods(lines, i, end_line, class_name)
                class_info['methods'] = methods
                logger.debug(f"[_extract_classes_with_methods] Extracted {len(methods)} methods for class: {class_name}")
                classes.append(class_info)

        logger.debug(f"[_extract_classes_with_methods] Extracted {len(classes)} classes total")
        return classes

    @log_function
    def _extract_class_methods(self, lines: List[str], class_start: int, class_end: int, class_name: str) -> List[Dict[str, Any]]:
        logger.debug(f"[_extract_class_methods] Extracting methods for class: {class_name}")
        methods = []
        method_pattern = re.compile(
            r'(?:(public|private|protected|static|readonly)\s+)*(\w+)\s*\([^)]*\)\s*(?::\s*[^=]+)?\s*\{',
            re.DOTALL
        )

        for i in range(class_start, class_end):
            line = lines[i]
            match = method_pattern.search(line)
            if match:
                method_name = match.group(2)
                if method_name and method_name not in ['if', 'for', 'while', 'switch']:
                    method_info = self._extract_function_body(lines, i, f"{class_name}.{method_name}")
                    if method_info:
                        methods.append(method_info)

        logger.debug(f"[_extract_class_methods] Extracted {len(methods)} methods for class: {class_name}")
        return methods

    @log_function
    def _extract_imports(self, content: str) -> List[Dict[str, Any]]:
        logger.debug(f"[_extract_imports] Starting")
        imports = []
        matches = self.import_pattern.finditer(content)

        for match in matches:
            symbols_str = match.group(1)
            default_symbol = match.group(2)
            source = match.group(3)

            if symbols_str:
                symbols = [s.strip() for s in symbols_str.split(',')]
                for symbol in symbols:
                    if symbol:
                        imports.append({
                            'source': source,
                            'symbol': symbol
                        })
            elif default_symbol:
                imports.append({
                    'source': source,
                    'symbol': default_symbol
                })

        logger.debug(f"[_extract_imports] Extracted {len(imports)} imports")
        return imports

    @log_function
    def _extract_calls(self, content: str, functions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        logger.debug(f"[_extract_calls] Starting with {len(functions)} functions/methods")
        calls = []

        for func in functions:
            func_content = func['content']
            call_matches = self.call_pattern.finditer(func_content)

            for match in call_matches:
                callee_name = match.group(1)
                if callee_name != func['name'] and callee_name not in ['if', 'for', 'while', 'return', 'new', 'switch', 'console']:
                    calls.append({
                        'caller_name': func['name'],
                        'callee_name': callee_name
                    })

        logger.debug(f"[_extract_calls] Extracted {len(calls)} calls")
        return calls
