#!/usr/bin/env python3
"""
HTML翻译脚本
支持多种翻译引擎和术语库
"""
import os
import json
import csv
from pathlib import Path
import argparse
import logging
from typing import Dict, List, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

# 导入翻译模块
try:
    from deep_translator import GoogleTranslator, DeeplTranslator, MicrosoftTranslator
    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False
    logging.warning("deep-translator未安装，机器翻译功能不可用")

from bs4 import BeautifulSoup
import html

logger = logging.getLogger(__name__)

class TranslationEngine:
    """翻译引擎管理器"""
    
    def __init__(self, engine='google', source_lang='en', target_lang='zh-CN', api_key=None):
        self.engine = engine
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.api_key = api_key
        self.translator = None
        
        self._init_translator()
    
    def _init_translator(self):
        """初始化翻译器"""
        if not TRANSLATION_AVAILABLE:
            return
        
        try:
            if self.engine == 'google':
                self.translator = GoogleTranslator(
                    source=self.source_lang,
                    target=self.target_lang
                )
            elif self.engine == 'deepl':
                if not self.api_key:
                    raise ValueError("DeepL需要API密钥")
                self.translator = DeeplTranslator(
                    api_key=self.api_key,
                    source=self.source_lang,
                    target=self.target_lang,
                    use_free_api=True
                )
            elif self.engine == 'microsoft':
                if not self.api_key:
                    raise ValueError("Microsoft Translator需要API密钥")
                self.translator = MicrosoftTranslator(
                    api_key=self.api_key,
                    source=self.source_lang,
                    target=self.target_lang
                )
            else:
                raise ValueError(f"不支持的翻译引擎: {self.engine}")
                
        except Exception as e:
            logger.error(f"初始化翻译引擎失败: {e}")
            self.translator = None
    
    def translate(self, text: str, max_length: int = 5000) -> str:
        """翻译文本"""
        if not self.translator or not text.strip():
            return text
        
        try:
            # 清理文本
            text = text.strip()
            
            # 跳过不需要翻译的内容
            if self._should_skip(text):
                return text
            
            # 限制长度
            if len(text) > max_length:
                text = text[:max_length]
            
            # 翻译
            translated = self.translator.translate(text)
            return translated
            
        except Exception as e:
            logger.warning(f"翻译失败: {text[:50]}... - {e}")
            return text
    
    def _should_skip(self, text: str) -> bool:
        """判断是否应该跳过翻译"""
        import re
        
        # 跳过纯数字
        if re.match(r'^[\d\s\.\-%,]+$', text):
            return True
        
        # 跳过URL
        if re.match(r'^(https?://|ftp://|www\.|mailto:)', text):
            return True
        
        # 跳过Email
        if re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', text):
            return True
        
        # 跳过文件路径
        if re.match(r'^[A-Za-z]:\\|^/[\w/]', text):
            return True
        
        # 跳过代码片段
        if re.match(r'^[{}()\[\];=<>+/*-]+$', text):
            return True
        
        return False

class GlossaryManager:
    """术语库管理器"""
    
    def __init__(self, glossary_file=None):
        self.glossary: Dict[str, str] = {}
        self.partial_matches: Dict[str, str] = {}
        
        if glossary_file and os.path.exists(glossary_file):
            self.load_glossary(glossary_file)
    
    def load_glossary(self, glossary_file: str):
        """加载术语库"""
        try:
            with open(glossary_file, 'r', encoding='utf-8') as f:
                if glossary_file.endswith('.csv'):
                    reader = csv.DictReader(f)
                    for row in reader:
                        source = row.get('source', '').strip()
                        target = row.get('target', '').strip()
                        if source and target:
                            self.glossary[source.lower()] = target
                elif glossary_file.endswith('.json'):
                    data = json.load(f)
                    for item in data:
                        self.glossary[item['source'].lower()] = item['target']
                
            logger.info(f"加载术语库: {len(self.glossary)} 条术语")
            
            # 构建部分匹配字典
            for term in self.glossary.keys():
                words = term.split()
                if len(words) > 1:
                    for word in words:
                        if len(word) > 3:  # 只处理长度大于3的单词
                            self.partial_matches[word] = term
            
        except Exception as e:
            logger.error(f"加载术语库失败: {e}")
    
    def apply_glossary(self, text: str) -> str:
        """应用术语库"""
        if not self.glossary:
            return text
        
        result = text
        
        # 首先进行完全匹配
        for source, target in self.glossary.items():
            if source in result.lower():
                # 保持原始大小写
                pattern = re.compile(re.escape(source), re.IGNORECASE)
                result = pattern.sub(target, result)
        
        return result

class HTMLTranslator:
    """HTML文件翻译器"""
    
    def __init__(self, config):
        self.config = config
        
        # 初始化翻译引擎
        self.translation_engine = TranslationEngine(
            engine=config.get('engine', 'google'),
            source_lang=config.get('source_lang', 'en'),
            target_lang=config.get('target_lang', 'zh-CN'),
            api_key=config.get('api_key')
        ) if config.get('use_machine_translation', True) else None
        
        # 初始化术语库
        self.glossary = GlossaryManager(config.get('glossary_file'))
        
        # 配置
        self.translatable_tags = [
            'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'span', 'div', 'li', 'td', 'th', 'a',
            'title', 'figcaption', 'caption', 'button',
            'label', 'option', 'strong', 'em', 'b', 'i'
        ]
        
        # 统计信息
        self.stats = {
            'files_processed': 0,
            'strings_translated': 0,
            'characters_translated': 0
        }
    
    def translate_file(self, input_file: Path, output_file: Path) -> bool:
        """翻译单个HTML文件"""
        try:
            # 读取文件
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # 翻译内容
            self._translate_soup(soup)
            
            # 保存文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            
            self.stats['files_processed'] += 1
            logger.debug(f"翻译完成: {input_file}")
            return True
            
        except Exception as e:
            logger.error(f"翻译文件失败 {input_file}: {e}")
            return False
    
    def _translate_soup(self, soup):
        """翻译BeautifulSoup对象"""
        import re
        
        # 翻译标签文本
        for tag in soup.find_all(self.translatable_tags):
            if tag.string and tag.string.strip():
                original = tag.string.strip()
                
                # 应用术语库
                if self.glossary:
                    original = self.glossary.apply_glossary(original)
                
                # 机器翻译
                if self.translation_engine:
                    translated = self.translation_engine.translate(original)
                else:
                    translated = original
                
                if translated != original:
                    tag.string.replace_with(translated)
                    self.stats['strings_translated'] += 1
                    self.stats['characters_translated'] += len(translated)
        
        # 翻译meta标签
        for meta in soup.find_all('meta'):
            if meta.get('name') in ['description', 'keywords']:
                content = meta.get('content', '')
                if content:
                    translated = self.translation_engine.translate(content) if self.translation_engine else content
                    meta['content'] = translated
        
        # 翻译alt属性
        for img in soup.find_all('img'):
            alt = img.get('alt', '')
            if alt:
                translated = self.translation_engine.translate(alt) if self.translation_engine else alt
                img['alt'] = translated

def batch_translate(input_dir, output_dir, config):
    """批量翻译"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 创建翻译器
    translator = HTMLTranslator(config)
    
    # 收集所有HTML文件
    html_files = list(input_path.rglob("*.html"))
    htm_files = list(input_path.rglob("*.htm"))
    all_files = html_files + htm_files
    
    logger.info(f"找到 {len(all_files)} 个HTML文件")
    
    # 多线程翻译
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        
        for file in all_files:
            # 保持目录结构
            relative_path = file.relative_to(input_path)
            output_file = output_path / relative_path
            
            # 确保输出目录存在
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 提交翻译任务
            future = executor.submit(
                translator.translate_file,
                file,
                output_file
            )
            futures.append((file, future))
        
        # 处理结果
        success_count = 0
        for file, future in futures:
            try:
                if future.result():
                    success_count += 1
            except Exception as e:
                logger.error(f"文件处理异常 {file}: {e}")
    
    # 复制其他文件
    for file in input_path.rglob("*"):
        if file.is_file() and file.suffix.lower() not in ['.html', '.htm']:
            relative_path = file.relative_to(input_path)
            output_file = output_path / relative_path
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            import shutil
            shutil.copy2(file, output_file)
    
    # 输出统计信息
    logger.info(f"批量翻译完成:")
    logger.info(f"  文件处理: {success_count}/{len(all_files)}")
    logger.info(f"  字符串翻译: {translator.stats['strings_translated']}")
    logger.info(f"  字符翻译: {translator.stats['characters_translated']}")
    
    return success_count

def main():
    parser = argparse.ArgumentParser(description='HTML文件批量翻译工具')
    parser.add_argument('--input', '-i', required=True, help='输入目录')
    parser.add_argument('--output', '-o', required=True, help='输出目录')
    parser.add_argument('--target-lang', default='zh-CN', help='目标语言')
    parser.add_argument('--source-lang', default='en', help='源语言')
    parser.add_argument('--engine', default='google', choices=['google', 'deepl', 'microsoft'], help='翻译引擎')
    parser.add_argument('--glossary', help='术语库文件路径')
    parser.add_argument('--use-mt', action='store_true', default=True, help='使用机器翻译')
    parser.add_argument('--api-key', help='翻译API密钥')
    parser.add_argument('--max-workers', type=int, default=4, help='最大工作线程数')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    
    args = parser.parse_args()
    
    # 设置日志
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 配置
    config = {
        'source_lang': args.source_lang,
        'target_lang': args.target_lang,
        'engine': args.engine,
        'use_machine_translation': args.use_mt,
        'api_key': args.api_key,
        'glossary_file': args.glossary
    }
    
    # 执行翻译
    success = batch_translate(args.input, args.output, config)
    
    if success > 0:
        logger.info("✅ 翻译完成")
        sys.exit(0)
    else:
        logger.error("❌ 翻译失败")
        sys.exit(1)

if __name__ == "__main__":
    main()