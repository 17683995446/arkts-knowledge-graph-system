import os
import sys
import threading
import argparse
from src.core import KnowledgeGraphUpdater
from src.watcher import FileWatcher
from src.database import Database
from src.llm import LLMClient
from src.web.app import init_app, run_server


def main():
    parser = argparse.ArgumentParser(description='ArkTS 代码知识图谱系统')
    parser.add_argument('path', nargs='?', default='.', help='要监听和扫描的目录路径')
    parser.add_argument('--api-key', default='REDACTED_API_KEY', help='硅基流动 API 密钥')
    parser.add_argument('--full-scan', action='store_true', help='启动时执行全量扫描')
    parser.add_argument('--port', type=int, default=5000, help='Web 服务器端口')
    parser.add_argument('--no-watch', action='store_true', help='不启动文件监听')
    parser.add_argument('--no-web', action='store_true', help='不启动 Web 服务器')
    
    args = parser.parse_args()
    
    watch_path = os.path.abspath(args.path)
    if not os.path.exists(watch_path):
        print(f"错误: 路径不存在: {watch_path}")
        return 1
    
    print("=" * 60)
    print("ArkTS 代码知识图谱系统")
    print("=" * 60)
    
    updater = KnowledgeGraphUpdater()
    llm = LLMClient(args.api_key)
    
    if args.full_scan:
        updater.full_scan(watch_path)
    
    if not args.no_watch:
        print(f"\n启动文件监听: {watch_path}")
        watcher = FileWatcher(watch_path, updater.update_file)
        watcher.start()
    
    if not args.no_web:
        print(f"初始化 Web 服务器...")
        init_app(updater.db, llm)
        
        print(f"启动 Web 服务器: http://localhost:{args.port}")
        web_thread = threading.Thread(target=run_server, kwargs={'port': args.port}, daemon=True)
        web_thread.start()
    
    print("\n系统已启动，按 Ctrl+C 停止\n")
    
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止...")
        if not args.no_watch:
            watcher.stop()
        updater.close()
        print("已停止")


if __name__ == "__main__":
    sys.exit(main())
