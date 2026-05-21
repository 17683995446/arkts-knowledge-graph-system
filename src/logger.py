import logging
import sys
from datetime import datetime

def setup_logger(name='arkts_kg', level=logging.DEBUG):
    """设置详细的日志系统"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(module)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        file_handler = logging.FileHandler('arkts_kg_debug.log', encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

logger = setup_logger()

def log_function(func):
    """装饰器：记录函数进入和退出"""
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        logger.debug(f"⏳ ENTERING {func_name}, args={len(args)}, kwargs={len(kwargs)}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"✅ EXITING {func_name}, success=True")
            return result
        except Exception as e:
            logger.error(f"❌ ERROR in {func_name}: {e}", exc_info=True)
            raise
    return wrapper
