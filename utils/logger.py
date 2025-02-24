import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path

class CustomFormatter(logging.Formatter):
    """自定义日志格式化器"""
    
    COLORS = {
        'DEBUG': '\033[0;36m',    # Cyan
        'INFO': '\033[0;32m',     # Green
        'WARNING': '\033[0;33m',  # Yellow
        'ERROR': '\033[0;31m',    # Red
        'CRITICAL': '\033[0;35m', # Purple
        'RESET': '\033[0m',       # Reset
    }
    
    def format(self, record):
        # 为控制台添加颜色
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            record.color_start = self.COLORS.get(record.levelname, '')
            record.color_end = self.COLORS['RESET']
        else:
            record.color_start = ''
            record.color_end = ''
        return super().format(record)

def get_logger(name='Text2Voice'):
    """获取日志记录器"""
    logger = logging.getLogger(name)
    if logger.handlers:  # 如果已经有处理器，直接返回
        return logger
        
    logger.setLevel(logging.DEBUG)
    
    # 创建日志目录
    log_dir = Path('data/logs')
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 日志文件名格式：logs/text2voice_2024-02-24.log
    log_file = log_dir / f'text2voice_{datetime.now().strftime("%Y-%m-%d")}.log'
    
    # 文件处理器 - 记录所有日志
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10,  # 保留10个备份
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s - %(message)s (%(filename)s:%(lineno)d)'
    )
    file_handler.setFormatter(file_formatter)
    
    # 添加时间轮转
    time_handler = logging.handlers.TimedRotatingFileHandler(
        log_file,
        when='midnight',  # 每天午夜轮转
        interval=1,
        backupCount=30,  # 保留30天的日志
        encoding='utf-8'
    )
    time_handler.setFormatter(file_formatter)
    
    # 控制台处理器 - 带颜色
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # 错误日志处理器 - 单独记录错误
    error_file = log_dir / f'text2voice_error_{datetime.now().strftime("%Y-%m-%d")}.log'
    error_handler = logging.handlers.RotatingFileHandler(
        error_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s - %(message)s\n'
        'File: %(filename)s:%(lineno)d\n'
        'Function: %(funcName)s\n'
        'Exception: %(exc_info)s\n'
    )
    error_handler.setFormatter(error_formatter)
    
    # 清除现有的处理器
    logger.handlers.clear()
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.addHandler(error_handler)
    logger.addHandler(time_handler)
    
    return logger

# 创建全局日志实例
logger = get_logger()

def get_child_logger(name):
    """获取子日志记录器"""
    return get_logger(f"Text2Voice.{name}") 