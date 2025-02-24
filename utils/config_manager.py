import json
import os
from pathlib import Path
from typing import Dict, Any
from utils.logger import get_child_logger

class ConfigManager:
    """配置管理器"""
    def __init__(self, config_file: str = 'data/config.json'):
        self.logger = get_child_logger('config')
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self.load()
        
    def load(self) -> None:
        """加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                self.logger.info("配置加载成功")
        except Exception as e:
            self.logger.error("加载配置失败", exc_info=True)
            self.config = {}
            
    def save(self) -> None:
        """保存配置"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            self.logger.info("配置保存成功")
        except Exception as e:
            self.logger.error("保存配置失败", exc_info=True)
            
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self.config.get(key, default)
        
    def set(self, key: str, value: Any) -> None:
        """设置配置项"""
        self.config[key] = value
        self.save() 