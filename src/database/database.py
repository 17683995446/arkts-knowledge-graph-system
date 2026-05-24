import sqlite3
import hashlib
import os
import time
import threading
from typing import Optional, List, Dict, Any, Callable
from src.logger import logger, log_function
from functools import wraps

def retry_on_locked(max_retries: int = 10, delay: float = 0.1):
    """装饰器：当数据库被锁定时自动重试"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            retry_count = 0
            last_exception = None
            
            while retry_count < max_retries:
                try:
                    return func(self, *args, **kwargs)
                except sqlite3.OperationalError as e:
                    if "database is locked" in str(e):
                        last_exception = e
                        retry_count += 1
                        if retry_count < max_retries:
                            logger.warning(
                                f"[retry_on_locked] Database locked, retrying {retry_count}/{max_retries}..."
                            )
                            time.sleep(delay * (2 ** retry_count))  # 指数退避
                        else:
                            logger.error(
                                f"[retry_on_locked] Max retries reached, giving up: {e}"
                            )
                    else:
                        raise
            raise last_exception
        return wrapper
    return decorator

class Database:
    def __init__(self, db_path: str = "knowledge_graph.db"):
        logger.debug(f"[Database] Initializing with db_path: {db_path}")
        self.db_path = db_path
        self.conn = None
        self.lock = threading.Lock()  # 线程锁，保护数据库操作
        self._initialize_database()

    @log_function
    def _initialize_database(self):
        logger.debug(f"[_initialize_database] Connecting to {self.db_path}")
        self.conn = sqlite3.connect(
            self.db_path, 
            check_same_thread=False,
            timeout=30.0  # 30秒超时
        )
        cursor = self.conn.cursor()
        
        # 启用WAL模式，提高并发性
        cursor.execute('PRAGMA journal_mode=WAL')
        logger.debug(f"[_initialize_database] WAL mode enabled")
        cursor.execute('PRAGMA synchronous=NORMAL')
        logger.debug(f"[_initialize_database] Synchronous mode set to NORMAL")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY,
                path TEXT UNIQUE NOT NULL,
                hash BLOB NOT NULL,
                modified INTEGER NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS functions (
                id INTEGER PRIMARY KEY,
                file_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                line_start INTEGER NOT NULL,
                line_end INTEGER NOT NULL,
                content TEXT NOT NULL,
                FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY,
                file_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                line_start INTEGER NOT NULL,
                line_end INTEGER NOT NULL,
                content TEXT NOT NULL,
                FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS class_methods (
                id INTEGER PRIMARY KEY,
                class_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                line_start INTEGER NOT NULL,
                line_end INTEGER NOT NULL,
                content TEXT NOT NULL,
                FOREIGN KEY (class_id) REFERENCES classes (id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS imports (
                id INTEGER PRIMARY KEY,
                file_id INTEGER NOT NULL,
                source TEXT NOT NULL,
                symbol TEXT NOT NULL,
                FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS calls (
                id INTEGER PRIMARY KEY,
                caller_id INTEGER NOT NULL,
                caller_name TEXT NOT NULL,
                callee_name TEXT NOT NULL,
                callee_file_id INTEGER,
                FOREIGN KEY (caller_id) REFERENCES functions (id) ON DELETE CASCADE,
                FOREIGN KEY (callee_file_id) REFERENCES files (id) ON DELETE CASCADE
            )
        ''')

        self.conn.commit()
        logger.debug(f"[_initialize_database] Database initialized successfully")

    @log_function
    def compute_file_hash(self, file_path: str) -> bytes:
        logger.debug(f"[compute_file_hash] Computing hash for: {file_path}")
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                hasher.update(f.read())
            digest = hasher.digest()
            logger.debug(f"[compute_file_hash] Hash computed: {digest.hex()[:16]}...")
            return digest
        except Exception as e:
            logger.error(f"[compute_file_hash] Error: {e}")
            return b''

    @log_function
    def get_file_by_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        logger.debug(f"[get_file_by_path] Querying for: {file_path}")
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, path, hash, modified FROM files WHERE path = ?', (file_path,))
        row = cursor.fetchone()
        if row:
            result = {
                'id': row[0],
                'path': row[1],
                'hash': row[2],
                'modified': row[3]
            }
            logger.debug(f"[get_file_by_path] Found file with id: {result['id']}")
            return result
        logger.debug(f"[get_file_by_path] File not found")
        return None

    @log_function
    @retry_on_locked(max_retries=10)
    def insert_file(self, file_path: str, file_hash: bytes, modified: int) -> int:
        logger.debug(f"[insert_file] Inserting file: {file_path}")
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                'INSERT INTO files (path, hash, modified) VALUES (?, ?, ?)',
                (file_path, file_hash, modified)
            )
            self.conn.commit()
            row_id = cursor.lastrowid
        logger.debug(f"[insert_file] File inserted with id: {row_id}")
        return row_id

    @log_function
    @retry_on_locked(max_retries=10)
    def update_file(self, file_id: int, file_hash: bytes, modified: int):
        logger.debug(f"[update_file] Updating file id: {file_id}")
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                'UPDATE files SET hash = ?, modified = ? WHERE id = ?',
                (file_hash, modified, file_id)
            )
            self.conn.commit()
        logger.debug(f"[update_file] File updated successfully")

    @log_function
    @retry_on_locked(max_retries=10)
    def delete_file_data(self, file_id: int):
        logger.debug(f"[delete_file_data] Deleting all data for file id: {file_id}")
        with self.lock:
            cursor = self.conn.cursor()
            try:
                cursor.execute('DELETE FROM calls WHERE caller_id IN (SELECT id FROM functions WHERE file_id = ?)', (file_id,))
                logger.debug(f"[delete_file_data] Deleted calls from functions")
                cursor.execute('DELETE FROM calls WHERE caller_id IN (SELECT id FROM class_methods WHERE class_id IN (SELECT id FROM classes WHERE file_id = ?))', (file_id,))
                logger.debug(f"[delete_file_data] Deleted calls from class methods")
                cursor.execute('DELETE FROM functions WHERE file_id = ?', (file_id,))
                logger.debug(f"[delete_file_data] Deleted functions")
                cursor.execute('DELETE FROM class_methods WHERE class_id IN (SELECT id FROM classes WHERE file_id = ?)', (file_id,))
                logger.debug(f"[delete_file_data] Deleted class methods")
                cursor.execute('DELETE FROM classes WHERE file_id = ?', (file_id,))
                logger.debug(f"[delete_file_data] Deleted classes")
                cursor.execute('DELETE FROM imports WHERE file_id = ?', (file_id,))
                logger.debug(f"[delete_file_data] Deleted imports")
                cursor.execute('DELETE FROM files WHERE id = ?', (file_id,))
                logger.debug(f"[delete_file_data] Deleted file record")
                self.conn.commit()
                logger.debug(f"[delete_file_data] All data deleted successfully")
            except Exception as e:
                logger.error(f"[delete_file_data] Error, rolling back: {e}")
                self.conn.rollback()
                raise

    @log_function
    @retry_on_locked(max_retries=10)
    def insert_function(self, file_id: int, name: str, line_start: int, line_end: int, content: str) -> int:
        logger.debug(f"[insert_function] Inserting function: {name} for file id: {file_id}")
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                'INSERT INTO functions (file_id, name, line_start, line_end, content) VALUES (?, ?, ?, ?, ?)',
                (file_id, name, line_start, line_end, content)
            )
            self.conn.commit()
            row_id = cursor.lastrowid
        logger.debug(f"[insert_function] Function inserted with id: {row_id}")
        return row_id

    @log_function
    @retry_on_locked(max_retries=10)
    def insert_class(self, file_id: int, name: str, line_start: int, line_end: int, content: str) -> int:
        logger.debug(f"[insert_class] Inserting class: {name} for file id: {file_id}")
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                'INSERT INTO classes (file_id, name, line_start, line_end, content) VALUES (?, ?, ?, ?, ?)',
                (file_id, name, line_start, line_end, content)
            )
            self.conn.commit()
            row_id = cursor.lastrowid
        logger.debug(f"[insert_class] Class inserted with id: {row_id}")
        return row_id

    @log_function
    @retry_on_locked(max_retries=10)
    def insert_class_method(self, class_id: int, name: str, line_start: int, line_end: int, content: str) -> int:
        logger.debug(f"[insert_class_method] Inserting method: {name} for class id: {class_id}")
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                'INSERT INTO class_methods (class_id, name, line_start, line_end, content) VALUES (?, ?, ?, ?, ?)',
                (class_id, name, line_start, line_end, content)
            )
            self.conn.commit()
            row_id = cursor.lastrowid
        logger.debug(f"[insert_class_method] Method inserted with id: {row_id}")
        return row_id

    @log_function
    @retry_on_locked(max_retries=10)
    def insert_import(self, file_id: int, source: str, symbol: str) -> int:
        logger.debug(f"[insert_import] Inserting import: {source}.{symbol} for file id: {file_id}")
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                'INSERT INTO imports (file_id, source, symbol) VALUES (?, ?, ?)',
                (file_id, source, symbol)
            )
            self.conn.commit()
            row_id = cursor.lastrowid
        logger.debug(f"[insert_import] Import inserted with id: {row_id}")
        return row_id

    @log_function
    @retry_on_locked(max_retries=10)
    def insert_call(self, caller_id: int, caller_name: str, callee_name: str, callee_file_id: Optional[int] = None):
        logger.debug(f"[insert_call] Inserting call: {caller_name} -> {callee_name}")
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                'INSERT INTO calls (caller_id, caller_name, callee_name, callee_file_id) VALUES (?, ?, ?, ?)',
                (caller_id, caller_name, callee_name, callee_file_id)
            )
            self.conn.commit()
        logger.debug(f"[insert_call] Call inserted successfully")

    @log_function
    def get_all_files(self) -> List[Dict[str, Any]]:
        logger.debug(f"[get_all_files] Querying all files")
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, path, hash, modified FROM files')
        rows = cursor.fetchall()
        result = [
            {'id': row[0], 'path': row[1], 'hash': row[2], 'modified': row[3]}
            for row in rows
        ]
        logger.debug(f"[get_all_files] Found {len(result)} files")
        return result

    @log_function
    def get_functions_by_file(self, file_id: int) -> List[Dict[str, Any]]:
        logger.debug(f"[get_functions_by_file] Querying functions for file id: {file_id}")
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, name, line_start, line_end, content FROM functions WHERE file_id = ?', (file_id,))
        rows = cursor.fetchall()
        result = [
            {'id': row[0], 'name': row[1], 'line_start': row[2], 'line_end': row[3], 'content': row[4]}
            for row in rows
        ]
        logger.debug(f"[get_functions_by_file] Found {len(result)} functions")
        return result

    @log_function
    def get_classes_by_file(self, file_id: int) -> List[Dict[str, Any]]:
        logger.debug(f"[get_classes_by_file] Querying classes for file id: {file_id}")
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, name, line_start, line_end, content FROM classes WHERE file_id = ?', (file_id,))
        rows = cursor.fetchall()
        result = []
        for row in rows:
            class_info = {
                'id': row[0],
                'name': row[1],
                'line_start': row[2],
                'line_end': row[3],
                'content': row[4],
                'methods': self.get_class_methods(row[0])
            }
            result.append(class_info)
        logger.debug(f"[get_classes_by_file] Found {len(result)} classes")
        return result

    @log_function
    def get_class_methods(self, class_id: int) -> List[Dict[str, Any]]:
        logger.debug(f"[get_class_methods] Querying methods for class id: {class_id}")
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, name, line_start, line_end, content FROM class_methods WHERE class_id = ?', (class_id,))
        rows = cursor.fetchall()
        result = [
            {'id': row[0], 'name': row[1], 'line_start': row[2], 'line_end': row[3], 'content': row[4]}
            for row in rows
        ]
        logger.debug(f"[get_class_methods] Found {len(result)} methods")
        return result

    @log_function
    def get_imports_by_file(self, file_id: int) -> List[Dict[str, Any]]:
        logger.debug(f"[get_imports_by_file] Querying imports for file id: {file_id}")
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, source, symbol FROM imports WHERE file_id = ?', (file_id,))
        rows = cursor.fetchall()
        result = [
            {'id': row[0], 'source': row[1], 'symbol': row[2]}
            for row in rows
        ]
        logger.debug(f"[get_imports_by_file] Found {len(result)} imports")
        return result

    @log_function
    def get_all_functions(self) -> List[Dict[str, Any]]:
        logger.debug(f"[get_all_functions] Querying all functions")
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, file_id, name, line_start, line_end, content FROM functions')
        rows = cursor.fetchall()
        result = [
            {'id': row[0], 'file_id': row[1], 'name': row[2], 'line_start': row[3], 'line_end': row[4], 'content': row[5]}
            for row in rows
        ]
        logger.debug(f"[get_all_functions] Found {len(result)} functions")
        return result

    @log_function
    def get_all_classes(self) -> List[Dict[str, Any]]:
        logger.debug(f"[get_all_classes] Querying all classes")
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, file_id, name, line_start, line_end, content FROM classes')
        rows = cursor.fetchall()
        result = []
        for row in rows:
            class_info = {
                'id': row[0], 'file_id': row[1], 'name': row[2], 
                'line_start': row[3], 'line_end': row[4], 'content': row[5],
                'methods': self.get_class_methods(row[0])
            }
            result.append(class_info)
        logger.debug(f"[get_all_classes] Found {len(result)} classes")
        return result

    @log_function
    def get_all_imports(self) -> List[Dict[str, Any]]:
        logger.debug(f"[get_all_imports] Querying all imports")
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, file_id, source, symbol FROM imports')
        rows = cursor.fetchall()
        result = [
            {'id': row[0], 'file_id': row[1], 'source': row[2], 'symbol': row[3]}
            for row in rows
        ]
        logger.debug(f"[get_all_imports] Found {len(result)} imports")
        return result

    @log_function
    def close(self):
        logger.debug(f"[close] Closing database connection")
        if self.conn:
            self.conn.close()
            logger.debug(f"[close] Database connection closed")
