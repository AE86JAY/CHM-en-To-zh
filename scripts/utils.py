#!/usr/bin/env python3
"""
工具函数
"""
import os
import json
import yaml
import hashlib
from pathlib import Path
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

def load_config(config_file: str) -> Dict[str, Any]:
    """加载配置文件"""
    config_path = Path(config_file)
    
    if not config_path.exists():
        logger.warning(f"配置文件不存在: {config_file}")
        return {}
    
    try:
        if config_path.suffix == '.json':
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        elif config_path.suffix in ['.yaml', '.yml']:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        else:
            logger.error(f"不支持的配置文件格式: {config_path.suffix}")
            return {}
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return {}

def save_config(config: Dict[str, Any], config_file: str):
    """保存配置文件"""
    config_path = Path(config_file)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        if config_path.suffix == '.json':
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        elif config_path.suffix in ['.yaml', '.yml']:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True)
        else:
            logger.error(f"不支持的配置文件格式: {config_path.suffix}")
            return False
        
        logger.info(f"配置文件已保存: {config_file}")
        return True
    except Exception as e:
        logger.error(f"保存配置文件失败: {e}")
        return False

def calculate_md5(file_path: str) -> str:
    """计算文件的MD5哈希值"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def find_files(directory: str, patterns: List[str]) -> List[Path]:
    """查找匹配模式的文件"""
    dir_path = Path(directory)
    files = []
    
    for pattern in patterns:
        files.extend(dir_path.rglob(pattern))
    
    return sorted(files)

def cleanup_old_files(directory: str, days: int = 7):
    """清理旧文件"""
    import time
    from datetime import datetime, timedelta
    
    dir_path = Path(directory)
    cutoff_time = time.time() - (days * 24 * 60 * 60)
    
    for file_path in dir_path.rglob("*"):
        if file_path.is_file():
            file_time = file_path.stat().st_mtime
            if file_time < cutoff_time:
                try:
                    file_path.unlink()
                    logger.debug(f"已删除旧文件: {file_path}")
                except Exception as e:
                    logger.warning(f"删除文件失败 {file_path}: {e}")

def setup_logging(log_file: str = None, level: str = "INFO"):
    """配置日志"""
    log_level = getattr(logging, level.upper())
    
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )