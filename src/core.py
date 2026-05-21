import os
import time
from typing import Optional
from src.database import Database
from src.parser import ArkTSParser
from src.logger import logger, log_function


class KnowledgeGraphUpdater:
    def __init__(self, db_path: str = "knowledge_graph.db"):
        logger.debug(f"[KnowledgeGraphUpdater] Initializing with db_path: {db_path}")
        self.db = Database(db_path)
        self.parser = ArkTSParser()

    @log_function
    def update_file(self, file_path: str) -> bool:
        logger.debug(f"[update_file] Starting update for file: {file_path}")
        start_time = time.time()

        abs_path = os.path.abspath(file_path)
        if not os.path.exists(abs_path):
            logger.error(f"[update_file] File not found: {abs_path}")
            return False

        logger.debug(f"[update_file] Computing hash for {abs_path}")
        new_hash = self.db.compute_file_hash(abs_path)
        existing_file = self.db.get_file_by_path(abs_path)

        if existing_file:
            logger.debug(f"[update_file] Existing file found with id: {existing_file['id']}")
            if existing_file['hash'] == new_hash:
                logger.debug(f"[update_file] File unchanged, skipping: {abs_path}")
                print(f"File unchanged, skipping: {abs_path}")
                return False
            else:
                logger.debug(f"[update_file] File changed, deleting old data")
                print(f"Updating file: {abs_path}")
                self.db.delete_file_data(existing_file['id'])

        logger.debug(f"[update_file] Parsing file: {abs_path}")
        print(f"Parsing file: {abs_path}")
        parsed_data = self.parser.parse_file(abs_path)
        modified_time = int(os.path.getmtime(abs_path))

        logger.debug(f"[update_file] Inserting new file record")
        file_id = self.db.insert_file(abs_path, new_hash, modified_time)

        logger.debug(f"[update_file] Processing {len(parsed_data['functions'])} functions")
        for func in parsed_data['functions']:
            func_id = self.db.insert_function(
                file_id,
                func['name'],
                func['line_start'],
                func['line_end'],
                func['content']
            )
            for call in parsed_data.get('calls', []):
                if call.get('caller_name') == func['name']:
                    self.db.insert_call(
                        func_id,
                        func['name'],
                        call['callee_name']
                    )

        logger.debug(f"[update_file] Processing {len(parsed_data['classes'])} classes")
        for cls in parsed_data['classes']:
            class_id = self.db.insert_class(
                file_id,
                cls['name'],
                cls['line_start'],
                cls['line_end'],
                cls['content']
            )

            if 'methods' in cls:
                logger.debug(f"[update_file] Processing {len(cls['methods'])} methods for class {cls['name']}")
                for method in cls['methods']:
                    method_id = self.db.insert_class_method(
                        class_id,
                        method['name'],
                        method['line_start'],
                        method['line_end'],
                        method['content']
                    )
                    for call in parsed_data.get('calls', []):
                        if call.get('caller_name') == method['name']:
                            self.db.insert_call(
                                method_id,
                                method['name'],
                                call['callee_name']
                            )

        logger.debug(f"[update_file] Processing {len(parsed_data['imports'])} imports")
        for imp in parsed_data['imports']:
            self.db.insert_import(file_id, imp['source'], imp['symbol'])

        elapsed_time = time.time() - start_time
        logger.debug(f"[update_file] File processed in {elapsed_time:.3f}s")
        print(f"File processed in {elapsed_time:.3f}s: {abs_path}")
        return True

    @log_function
    def full_scan(self, directory: str):
        logger.debug(f"[full_scan] Starting full scan of {directory}")
        print(f"Starting full scan of {directory}")
        start_time = time.time()

        count = 0
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(('.ts', '.tsx', '.js', '.jsx', '.arkts')):
                    file_path = os.path.join(root, file)
                    if self.update_file(file_path):
                        count += 1

        elapsed_time = time.time() - start_time
        logger.debug(f"[full_scan] Complete. Processed {count} files in {elapsed_time:.2f}s")
        print(f"Full scan complete. Processed {count} files in {elapsed_time:.2f}s")

    @log_function
    def close(self):
        logger.debug(f"[close] Closing KnowledgeGraphUpdater")
        self.db.close()
