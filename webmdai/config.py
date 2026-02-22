#!/usr/bin/env python3
"""
配置管理模块 - 处理全局配置和模型配置
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, Any


class Config:
    """配置管理类"""
    
    CONFIG_DIR = Path.home() / ".webmdai"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    
    # 默认配置
    DEFAULT_CONFIG = {
        "default_model": None,
        "models": {},
        "fetch": {
            "default_reader": "jina",
            "timeout": 30,
            "retry_times": 3,
            "delay": 1.0,
            "jina_api_key": None,
        },
        "llm": {
            "default_output_dir": "llm_output",
            "max_tokens": 4000,
            "temperature": 0.7,
        }
    }
    
    def __init__(self):
        """初始化配置管理器"""
        self._config = None
        self._ensure_config_exists()
    
    def _ensure_config_exists(self):
        """确保配置文件存在"""
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if not self.CONFIG_FILE.exists():
            self._save_config(self.DEFAULT_CONFIG)
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return self.DEFAULT_CONFIG.copy()
    
    def _save_config(self, config: Dict[str, Any]):
        """保存配置文件"""
        with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取当前配置"""
        if self._config is None:
            self._config = self._load_config()
        return self._config
    
    def save(self):
        """保存当前配置"""
        self._save_config(self.config)
        self._config = None  # 强制下次重新加载
    
    # ========== 模型管理 ==========
    
    def get_model(self, name: str) -> Optional[Dict[str, str]]:
        """
        获取模型配置
        
        Args:
            name: 模型别名
            
        Returns:
            模型配置字典，不存在返回None
        """
        model = self.config.get("models", {}).get(name)
        if model:
            # 解析环境变量
            model = self._resolve_env_vars(model)
        return model
    
    def list_models(self) -> Dict[str, Dict[str, str]]:
        """
        列出所有已配置的模型
        
        Returns:
            模型配置字典
        """
        models = self.config.get("models", {})
        return {name: self._resolve_env_vars(model) for name, model in models.items()}
    
    def add_model(self, name: str, endpoint: str, model: str, key: str):
        """
        添加新模型
        
        Args:
            name: 模型别名
            endpoint: API端点
            model: 模型名称
            key: API密钥
        """
        if "models" not in self.config:
            self.config["models"] = {}
        
        self.config["models"][name] = {
            "endpoint": endpoint,
            "model": model,
            "key": key,
        }
        
        # 如果是第一个模型，设为默认
        if self.config.get("default_model") is None:
            self.config["default_model"] = name
        
        self.save()
    
    def remove_model(self, name: str) -> bool:
        """
        删除模型
        
        Args:
            name: 模型别名
            
        Returns:
            是否成功删除
        """
        if name in self.config.get("models", {}):
            del self.config["models"][name]
            
            # 如果删除的是默认模型，清除默认设置
            if self.config.get("default_model") == name:
                self.config["default_model"] = None
            
            self.save()
            return True
        return False
    
    def set_default_model(self, name: str) -> bool:
        """
        设置默认模型
        
        Args:
            name: 模型别名
            
        Returns:
            是否成功设置
        """
        if name in self.config.get("models", {}):
            self.config["default_model"] = name
            self.save()
            return True
        return False
    
    def get_default_model(self) -> Optional[Dict[str, str]]:
        """
        获取默认模型配置
        
        Returns:
            默认模型配置，未设置返回None
        """
        default_name = self.config.get("default_model")
        if default_name:
            return self.get_model(default_name)
        return None
    
    def _resolve_env_vars(self, model: Dict[str, str]) -> Dict[str, str]:
        """
        解析模型配置中的环境变量
        
        Args:
            model: 模型配置
            
        Returns:
            解析后的配置
        """
        resolved = {}
        for key, value in model.items():
            if isinstance(value, str) and value.startswith("$"):
                env_var = value[1:]
                resolved[key] = os.environ.get(env_var, value)
            else:
                resolved[key] = value
        return resolved
    
    # ========== 获取配置项 ==========
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置键（支持点号分隔，如 'fetch.timeout'）
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """
        设置配置项
        
        Args:
            key: 配置键（支持点号分隔）
            value: 配置值
        """
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save()


# 全局配置实例
_config_instance = None


def get_config() -> Config:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
