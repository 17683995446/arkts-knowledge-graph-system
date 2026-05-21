import os
import time
from typing import Optional
from src.database.database_logged import Database
from src.parser.arkts_parser_logged import ArkTSParser
from src.logger import logger, log_function

class KnowledgeGraphUpdater:
    def __init__(self, db_path: str = "knowledge_graph.db"):
        logger.info("[KnowledgeGraphUpdater.__init__] Initializing updater")
        self.db = Database(db_path)
        self.parser = ArkTSParser()
        logger.info("[KnowledgeGraphUpdater.__init__] Updater initialized")

    @log_function
    def update_file(self, file_path: str) -> bool:
        logger.info(f"[KnowledgeGraphUpdater.update_file] Processing file: {file_path}")
        start_time = time.time()

        abs_path = os.path.abspath(file_path)
        logger.debug(f"[KnowledgeGraphUpdater.update_file] Absolute path: {abs_path}")

        if not os.path.exists(abs_path):
            logger.error(f"[KnowledgeGraphUpdater.update_file] File not found: {abs_path}")
            print(f"File not found: {abs_path}")
            return False

        logger.debug("[KnowledgeGraphUpdater.update_file] Computing file hash")
        new_hash = self.db.compute_file_hash(abs_path)

        logger.debug("[KnowledgeGraphUpdater.update_file] Checking if file exists in DB")
        existing_file = self.db.get_file_by_path(abs_path)

        if existing_file:
            logger.debug(f"[KnowledgeGraphUpdater.update_file] File exists, id={existing_file['id']}")
            if existing_file['hash'] == new_hash:
                logger.info(f"[KnowledgeGraphUpdater.update_file] File unchanged, skipping: {abs_path}")
                print(f"File unchanged, skipping: {abs_path}")
                return False
            else:
                logger.info(f"[KnowledgeGraphUpdater.update_file] File changed, updating: {abs_path}")
                print(f"Updating file: {abs_path}")
                self.db.delete_file_data(existing_file['id'])

        logger.debug("[KnowledgeGraphUpdater.update_file] Parsing file")
        print(f"Parsing file: {abs_path}")
        parsed_data = self.parser.parse_file(abs_path)

        logger.debug("[KnowledgeGraphUpdater.update_file] Getting modified time")
        modified_time = int(os.path.getmtime(abs_path))

        logger.debug("[KnowledgeGraphUpdater.update_file] Inserting file record")
        file_id = self.db.insert_file(abs_path, new_hash, modified_time)

        logger.debug(f"[KnowledgeGraphUpdater.update_file] Inserting {len(parsed_data['functions'])} functions")
        for func in parsed_data['functions']:
            func_id = self.db.insert_function(
                file_id,
                func['name'],
                func['line_start'],
                func['line_end'],
                func['content']
            )
            logger.debug(f"[KnowledgeGraphUpdater.update_file] Checking calls for {func['name']}")
            for call in parsed_data.get('calls', []):
                if call.get('caller_name') == func['name']:
                    self.db.insert_call(
                        func_id,
                        func['name'],
                        call['callee_name']
                    )

        logger.debug(f"[KnowledgeGraphUpdater.update_file] Inserting {len(parsed_data['classes'])} classes")
        for cls in parsed_data['classes']:
            class_id = self.db.insert_class(
                file_id,
                cls['name'],
                cls['line_start'],
                cls['line_end'],
                cls['content']
            )

            if 'methods' in cls:
                logger.debug(f"[KnowledgeGraphUpdater.update_file] Inserting {len(cls['methods'])} methods for {cls['name']}")
                for method in cls['methods']:
                    method_id = self.db.insert_class_method(
                        class_id,
                        method['name'],
                        method['line_start'],
                        method['line_end'],
                        method['content']
                    )
                    logger.debug(f"[KnowledgeGraphUpdater.update_file] Checking calls for method {method['name']}")
                    for call in parsed_data.get('calls', []):
                        if call.get('caller_name') == method['name']:
                            self.db.insert_call(
                                method_id,
                                method['name'],
                                call['callee_name']
                            )

        logger.debug(f"[KnowledgeGraphUpdater.update_file] Inserting {len(parsed_data['imports'])} imports")
        for imp in parsed_data['imports']:
            self.db.insert_import(file_id, imp['source'], imp['symbol'])

        elapsed_time = time.time() - start_time
        logger.info(f"[KnowledgeGraphUpdater.update_file] File processed in {elapsed_time:.3f}s: {abs_path}")
        print(f"File processed in {elapsed_time:.3f}s: {abs_path}")
        return True

    @log_function
    def full_scan(self, directory: str):
        logger.info(f"[KnowledgeGraphUpdater.full_scan] Starting full scan of {directory}")
        print(f"Starting full scan of {directory}")
        start_time = time.time()

        count = 0
        logger.debug("[KnowledgeGraphUpdater.full_scan] Walking directory")
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(('.ts', '.tsx', '.js', '.jsx', '.arkts')):
                    file_path = os.path.join(root, file)
                    logger.debug(f"[KnowledgeGraphUpdater.full_scan] Found: {file_path}")
                    if self.update_file(file_path):
                        count += 1

        elapsed_time = time.time() - start_time
        logger.info(f"[KnowledgeGraphUpdater.full_scan] Complete: {count} files in {elapsed_time:.2f}s")
        print(f"Full scan complete. Processed {count} files in {elapsed_time:.2f}s")

    @log_function
    def close(self):
        logger.info("[KnowledgeGraphUpdater.close] Closing updater")
        self.db.close()
        logger.info("[KnowledgeGraphUpdater.close] Updater closed")
