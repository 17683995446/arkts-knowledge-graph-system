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
                            time.sleep(delay * (2 ** retry_count))
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
        logger.debug(f"[Database.__init__] Start, db_path={db_path}")
        self.db_path = db_path
        self.conn = None
        self.lock = threading.Lock()
        self._initialize_database()
        logger.debug(f"[Database.__init__] Complete")

    @log_function
    def _initialize_database(self):
        logger.debug("[Database._initialize_database] Creating tables")
        self.conn = sqlite3.connect(
            self.db_path, 
            check_same_thread=False, 
            timeout=30.0
        )
        cursor = self.conn.cursor()
        
        # 启用WAL模式，提高并发性
        cursor.execute('PRAGMA journal_mode=WAL')
        logger.debug("[Database._initialize_database] WAL mode enabled")
        cursor.execute('PRAGMA synchronous=NORMAL')
        logger.debug("[Database._initialize_database] Synchronous mode set to NORMAL")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY,
                path TEXT UNIQUE NOT NULL,
                hash BLOB NOT NULL,
                modified INTEGER NOT NULL
            )
        ''')
        logger.debug("[Database._initialize_database] Table files created/verified")

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
        logger.debug("[Database._initialize_database] Table functions created/verified")

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
        logger.debug("[Database._initialize_database] Table classes created/verified")

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
        logger.debug("[Database._initialize_database] Table class_methods created/verified")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS imports (
                id INTEGER PRIMARY KEY,
                file_id INTEGER NOT NULL,
                source TEXT NOT NULL,
                symbol TEXT NOT NULL,
                FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE
            )
        ''')
        logger.debug("[Database._initialize_database] Table imports created/verified")

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
        logger.debug("[Database._initialize_database] Table calls created/verified")

        self.conn.commit()
        logger.info("[Database._initialize_database] All tables initialized successfully")

    @log_function
    def compute_file_hash(self, file_path: str) -> bytes:
        logger.debug(f"[Database.compute_file_hash] Computing hash for {file_path}")
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                hasher.update(f.read())
            hash_bytes = hasher.digest()
            logger.debug(f"[Database.compute_file_hash] Hash computed: {hash_bytes.hex()[:16]}...")
            return hash_bytes
        except Exception as e:
            logger.error(f"[Database.compute_file_hash] Error: {e}")
            return b''

    @log_function
    def get_file_by_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        logger.debug(f"[Database.get_file_by_path] Querying for {file_path}")
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, path, hash, modified FROM files WHERE path = ?', (file_path,))
        row = cursor.fetchone()
        if row:
            logger.debug(f"[Database.get_file_by_path] Found file with id={row[0]}")
            return {
                'id': row[0],
                'path': row[1],
                'hash': row[2],
                'modified': row[3]
            }
        logger.debug("[Database.get_file_by_path] File not found")
        return None

    @log_function
    @retry_on_locked(max_retries=10)
    def insert_file(self, file_path: str, file_hash: bytes, modified: int) -> int:
        logger.debug(f"[Database.insert_file] Inserting {file_path}")
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                'INSERT INTO files (path, hash, modified) VALUES (?, ?, ?)',
                (file_path, file_hash, modified)
            )
            self.conn.commit()
            row_id = cursor.lastrowid
        logger.info(f"[Database.insert_file] File inserted, id={row_id}")
        return row_id

    @log_function
    @retry_on_locked(max_retries=10)
    def update_file(self, file_id: int, file_hash: bytes, modified: int):
        logger.debug(f"[Database.update_file] Updating file {file_id}")
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                'UPDATE files SET hash = ?, modified = ? WHERE id = ?',
                (file_hash, modified, file_id)
            )
            self.conn.commit()
        logger.debug(f"[Database.update_file] File {file_id} updated")

    @log_function
    @retry_on_locked(max_retries=10)
    def delete_file_data(self, file_id: int):
        logger.debug(f"[Database.delete_file_data] Deleting data for file {file_id}")
        with self.lock:
            cursor = self.conn.cursor()
            try:
                cursor.execute('DELETE FROM calls WHERE caller_id IN (SELECT id FROM functions WHERE file_id = ?)', (file_id,))
                logger.debug(f"[Database.delete_file_data] Deleted calls from functions")
                
                cursor.execute('DELETE FROM calls WHERE caller_id IN (SELECT id FROM class_methods WHERE class_id IN (SELECT id FROM classes WHERE file_id = ?))', (file_id,))
                logger.debug(f"[Database.delete_file_data] Deleted calls from class_methods")
                
                cursor.execute('DELETE FROM functions WHERE file_id = ?', (file_id,))
                logger.debug(f"[Database.delete_file_data] Deleted functions")
                
                cursor.execute('DELETE FROM class_methods WHERE class_id IN (SELECT id FROM classes WHERE file_id = ?)', (file_id,))
                logger.debug(f"[Database.delete_file_data] Deleted class_methods")
                
                cursor.execute('DELETE FROM classes WHERE file_id = ?', (file_id,))
                logger.debug(f"[Database.delete_file_data] Deleted classes")
                
                cursor.execute('DELETE FROM imports WHERE file_id = ?', (file_id,))
                logger.debug(f"[Database.delete_file_data] Deleted imports")
                
                cursor.execute('DELETE FROM files WHERE id = ?', (file_id,))
                logger.debug(f"[Database.delete_file_data] Deleted file")
                
                self.conn.commit()
                logger.info(f"[Database.delete_file_data] All data for file {file_id} deleted successfully")
            except Exception as e:
                logger.error(f"[Database.delete_file_data] Error: {e}")
                self.conn.rollback()
                raise

    @log_function
    @retry_on_locked(max_retries=10)
    def insert_function(self, file_id: int, name: str, line_start: int, line_end: int, content: str) -> int:
        logger.debug(f"[Database.insert_function] Inserting function: {name}, lines={line_start}-{line_end}")
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                'INSERT INTO functions (file_id, name, line_start, line_end, content) VALUES (?, ?, ?, ?, ?)',
                (file_id, name, line_start, line_end, content)
            )
            self.conn.commit()
            row_id = cursor.lastrowid
        logger.debug(f"[Database.insert_function] Function {name} inserted, id={row_id}")
        return row_id

    @log_function
    @retry_on_locked(max_retries=10)
    def insert_class(self, file_id: int, name: str, line_start: int, line_end: int, content: str) -> int:
        logger.debug(f"[Database.insert_class] Inserting class: {name}, lines={line_start}-{line_end}")
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                'INSERT INTO classes (file_id, name, line_start, line_end, content) VALUES (?, ?, ?, ?, ?)',
                (file_id, name, line_start, line_end, content)
            )
            self.conn.commit()
            row_id = cursor.lastrowid
        logger.debug(f"[Database.insert_class] Class {name} inserted, id={row_id}")
        return row_id

    @log_function
    @retry_on_locked(max_retries=10)
    def insert_class_method(self, class_id: int, name: str, line_start: int, line_end: int, content: str) -> int:
        logger.debug(f"[Database.insert_class_method] Inserting method: {name}, lines={line_start}-{line_end}")
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                'INSERT INTO class_methods (class_id, name, line_start, line_end, content) VALUES (?, ?, ?, ?, ?)',
                (class_id, name, line_start, line_end, content)
            )
            self.conn.commit()
            row_id = cursor.lastrowid
        logger.debug(f"[Database.insert_class_method] Method {name} inserted, id={row_id}")
        return row_id

    @log_function
    @retry_on_locked(max_retries=10)
    def insert_import(self, file_id: int, source: str, symbol: str) -> int:
        logger.debug(f"[Database.insert_import] Inserting import: {symbol} from {source}")
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                'INSERT INTO imports (file_id, source, symbol) VALUES (?, ?, ?)',
                (file_id, source, symbol)
            )
            self.conn.commit()
            row_id = cursor.lastrowid
        logger.debug(f"[Database.insert_import] Import {symbol} inserted, id={row_id}")
        return row_id

    @log_function
    @retry_on_locked(max_retries=10)
    def insert_call(self, caller_id: int, caller_name: str, callee_name: str, callee_file_id: Optional[int] = None):
        logger.debug(f"[Database.insert_call] Inserting call: {caller_name} -> {callee_name}")
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                'INSERT INTO calls (caller_id, caller_name, callee_name, callee_file_id) VALUES (?, ?, ?, ?)',
                (caller_id, caller_name, callee_name, callee_file_id)
            )
            self.conn.commit()
        logger.debug(f"[Database.insert_call] Call inserted: {caller_name} -> {callee_name}")

    @log_function
    def get_all_files(self) -> List[Dict[str, Any]]:
        logger.debug("[Database.get_all_files] Querying all files")
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, path, hash, modified FROM files')
        rows = cursor.fetchall()
        result = [
            {'id': row[0], 'path': row[1], 'hash': row[2], 'modified': row[3]}
            for row in rows
        ]
        logger.debug(f"[Database.get_all_files] Found {len(result)} files")
        return result

    @log_function
    def get_functions_by_file(self, file_id: int) -> List[Dict[str, Any]]:
        logger.debug(f"[Database.get_functions_by_file] Querying for file {file_id}")
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, name, line_start, line_end, content FROM functions WHERE file_id = ?', (file_id,))
        rows = cursor.fetchall()
        result = [
            {'id': row[0], 'name': row[1], 'line_start': row[2], 'line_end': row[3], 'content': row[4]}
            for row in rows
        ]
        logger.debug(f"[Database.get_functions_by_file] Found {len(result)} functions")
        return result

    @log_function
    def get_classes_by_file(self, file_id: int) -> List[Dict[str, Any]]:
        logger.debug(f"[Database.get_classes_by_file] Querying for file {file_id}")
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
        logger.debug(f"[Database.get_classes_by_file] Found {len(result)} classes")
        return result

    @log_function
    def get_class_methods(self, class_id: int) -> List[Dict[str, Any]]:
        logger.debug(f"[Database.get_class_methods] Querying for class {class_id}")
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, name, line_start, line_end, content FROM class_methods WHERE class_id = ?', (class_id,))
        rows = cursor.fetchall()
        result = [
            {'id': row[0], 'name': row[1], 'line_start': row[2], 'line_end': row[3], 'content': row[4]}
            for row in rows
        ]
        logger.debug(f"[Database.get_class_methods] Found {len(result)} methods")
        return result

    @log_function
    def get_imports_by_file(self, file_id: int) -> List[Dict[str, Any]]:
        logger.debug(f"[Database.get_imports_by_file] Querying for file {file_id}")
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, source, symbol FROM imports WHERE file_id = ?', (file_id,))
        rows = cursor.fetchall()
        result = [
            {'id': row[0], 'source': row[1], 'symbol': row[2]}
            for row in rows
        ]
        logger.debug(f"[Database.get_imports_by_file] Found {len(result)} imports")
        return result

    @log_function
    def close(self):
        logger.debug("[Database.close] Closing database connection")
        if self.conn:
            self.conn.close()
            logger.info("[Database.close] Database connection closed")
