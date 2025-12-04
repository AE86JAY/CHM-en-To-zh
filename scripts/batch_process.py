#!/usr/bin/env python3
"""
增强版批量处理脚本，支持通配符和文件列表
"""
import os
import sys
import fnmatch
import argparse
import subprocess
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import logging

logger = logging.getLogger(__name__)

def expand_pattern(pattern: str, search_dir: str = "input") -> list:
    """
    扩展通配符模式为文件列表
    
    Args:
        pattern: 通配符模式，如 "*.chm", "help*.chm", "*manual*.chm"
        search_dir: 搜索目录
        
    Returns:
        匹配的文件路径列表
    """
    input_dir = Path(search_dir)
    if not input_dir.exists():
        return []
    
    # 如果pattern包含逗号，先分割
    if ',' in pattern:
        all_files = []
        for sub_pattern in pattern.split(','):
            sub_pattern = sub_pattern.strip()
            if sub_pattern:
                matched = expand_pattern(sub_pattern, search_dir)
                all_files.extend(matched)
        # 去重
        return list(set(all_files))
    
    # 处理通配符
    matched_files = []
    
    # 检查是否已经是完整文件名（无通配符）
    if '*' not in pattern and '?' not in pattern:
        file_path = input_dir / pattern
        if file_path.exists() and file_path.is_file():
            return [file_path]
        else:
            logger.warning(f"文件不存在: {file_path}")
            return []
    
    # 使用通配符匹配
    for file_path in input_dir.rglob("*"):
        if file_path.is_file():
            # 使用fnmatch进行通配符匹配
            if fnmatch.fnmatch(file_path.name, pattern):
                matched_files.append(file_path)
            # 也尝试匹配相对路径
            rel_path = file_path.relative_to(input_dir)
            if fnmatch.fnmatch(str(rel_path), pattern):
                matched_files.append(file_path)
    
    return sorted(set(matched_files))

class EnhancedBatchProcessor:
    def __init__(self, config):
        self.config = config
        self.setup_directories()
        
    def setup_directories(self):
        """创建必要的目录"""
        directories = [
            self.config.get('input_dir', 'input'),
            self.config.get('output_dir', 'output'),
            self.config.get('extracted_dir', 'extracted'),
            self.config.get('translated_dir', 'translated'),
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def find_chm_files(self, pattern: str):
        """查找CHM文件，支持通配符和文件列表"""
        input_dir = Path(self.config.get('input_dir', 'input'))
        
        logger.info(f"搜索模式: {pattern}")
        
        # 扩展通配符
        files = expand_pattern(pattern, str(input_dir))
        
        # 过滤只保留.chm文件
        chm_files = [f for f in files if f.suffix.lower() == '.chm']
        
        # 按文件大小排序（大文件优先）
        chm_files.sort(key=lambda x: x.stat().st_size if x.exists() else 0, reverse=True)
        
        logger.info(f"找到 {len(chm_files)} 个CHM文件")
        for i, file in enumerate(chm_files, 1):
            size_mb = file.stat().st_size / (1024 * 1024) if file.exists() else 0
            logger.info(f"  {i:2d}. {file.name} ({size_mb:.1f} MB)")
        
        return chm_files
    
    def process_single_file(self, chm_file, index, total):
        """处理单个CHM文件"""
        try:
            # 获取基础信息
            base_name = chm_file.stem
            suffix_format = self.config.get('suffix_format', '-{lang}')
            target_lang = self.config.get('target_lang', 'zh-CN')
            
            # 生成输出文件名
            lang_code = target_lang.lower().replace('-', '_')
            suffix = suffix_format.format(lang=lang_code)
            output_base_name = f"{base_name}{suffix}"
            
            logger.info(f"[{index+1}/{total}] 处理: {chm_file.name}")
            
            # 1. 提取CHM
            extracted_dir = Path(self.config.get('extracted_dir', 'extracted')) / base_name
            if extracted_dir.exists():
                logger.info(f"  已存在提取目录，跳过提取: {extracted_dir}")
            else:
                cmd_extract = [
                    sys.executable, 'scripts/extract_chm.py',
                    '--input', str(chm_file),
                    '--output', str(extracted_dir),
                    '--log-level', 'INFO'
                ]
                
                logger.debug(f"  执行提取: {' '.join(cmd_extract)}")
                result = subprocess.run(cmd_extract, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.error(f"  提取失败: {result.stderr[:200]}")
                    return False
                logger.info(f"  ✅ 提取完成")
            
            # 2. 翻译内容
            translated_dir = Path(self.config.get('translated_dir', 'translated')) / base_name
            cmd_translate = [
                sys.executable, 'scripts/translate_html.py',
                '--input', str(extracted_dir),
                '--output', str(translated_dir),
                '--target-lang', target_lang,
                '--suffix-format', suffix_format,
                '--output-filename', output_base_name,
                '--log-level', 'INFO'
            ]
            
            # 添加可选的配置
            if self.config.get('engine'):
                cmd_translate.extend(['--engine', self.config['engine']])
            if self.config.get('glossary_file') and os.path.exists(self.config['glossary_file']):
                cmd_translate.extend(['--glossary', self.config['glossary_file']])
            
            logger.debug(f"  执行翻译: {' '.join(cmd_translate)}")
            result = subprocess.run(cmd_translate, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"  翻译失败: {result.stderr[:200]}")
                return False
            logger.info(f"  ✅ 翻译完成")
            
            # 3. 重新编译CHM（如果启用）
            if self.config.get('rebuild_chm', True):
                output_dir = Path(self.config.get('output_dir', 'output'))
                output_file = output_dir / f"{output_base_name}.chm"
                
                cmd_rebuild = [
                    sys.executable, 'scripts/rebuild_chm.py',
                    '--input', str(translated_dir),
                    '--output', str(output_dir),
                    '--project-name', output_base_name,
                    '--output-filename', output_base_name,
                    '--log-level', 'INFO'
                ]
                
                if self.config.get('hhw_path'):
                    cmd_rebuild.extend(['--hhw-path', self.config['hhw_path']])
                
                logger.debug(f"  执行编译: {' '.join(cmd_rebuild)}")
                result = subprocess.run(cmd_rebuild, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.error(f"  编译失败: {result.stderr[:200]}")
                    return False
                
                if output_file.exists():
                    size_mb = output_file.stat().st_size / (1024 * 1024)
                    logger.info(f"  ✅ 编译完成: {output_file.name} ({size_mb:.1f} MB)")
                else:
                    logger.warning(f"  ⚠️  编译完成但未找到输出文件")
            
            logger.info(f"[{index+1}/{total}] ✅ 完成: {chm_file.name}")
            return True
            
        except Exception as e:
            logger.error(f"处理文件失败 {chm_file.name}: {str(e)[:100]}")
            return False
    
    def process_batch(self, pattern="*.chm", max_workers=2):
        """批量处理文件"""
        # 查找文件
        chm_files = self.find_chm_files(pattern)
        if not chm_files:
            logger.warning("未找到CHM文件")
            # 显示input目录内容帮助调试
            input_dir = Path(self.config.get('input_dir', 'input'))
            if input_dir.exists():
                logger.info(f"input目录内容:")
                for item in input_dir.iterdir():
                    logger.info(f"  - {item.name}")
            return 0, 0
        
        total_count = len(chm_files)
        logger.info(f"开始批量处理 {total_count} 个文件，并行数: {max_workers}")
        
        success_count = 0
        
        if max_workers > 1 and total_count > 1:
            # 多进程处理
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                for i, chm_file in enumerate(chm_files):
                    future = executor.submit(
                        self.process_single_file,
                        chm_file,
                        i,
                        total_count
                    )
                    futures.append(future)
                    logger.debug(f"提交任务: {chm_file.name}")
                
                for i, future in enumerate(as_completed(futures)):
                    result = future.result()
                    if result:
                        success_count += 1
                    logger.debug(f"任务完成 [{i+1}/{total_count}]: {result}")
        else:
            # 单进程处理
            for i, chm_file in enumerate(chm_files):
                if self.process_single_file(chm_file, i, total_count):
                    success_count += 1
        
        return success_count, total_count

def main():
    parser = argparse.ArgumentParser(
        description='批量处理CHM文件（支持通配符）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                          # 处理所有.chm文件
  %(prog)s --pattern "help*.chm"     # 处理以help开头的.chm文件
  %(prog)s --pattern "*manual*.chm"  # 处理包含manual的.chm文件
  %(prog)s --pattern "a.chm,b.chm"   # 处理指定文件
  %(prog)s --pattern "*.chm" --suffix-format "-zh_cn"  # 自定义后缀
        """
    )
    
    parser.add_argument('--pattern', default='*.chm', 
                       help='文件匹配模式。支持: *.chm, help*.chm, *manual*.chm 或逗号分隔列表')
    parser.add_argument('--target-lang', default='zh-CN', 
                       help='目标语言代码，如: zh-CN, en, ja')
    parser.add_argument('--suffix-format', default='-{lang}', 
                       help='输出文件后缀格式，{lang}会被替换为语言代码')
    parser.add_argument('--engine', default='translate', 
                       choices=['translate', 'google', 'deepl'], 
                       help='翻译引擎')
    parser.add_argument('--glossary', 
                       help='术语库文件路径（CSV格式）')
    parser.add_argument('--max-workers', type=int, default=2, 
                       help='最大并行处理数（推荐1-3）')
    parser.add_argument('--no-rebuild', action='store_true', 
                       help='不重新编译CHM，只提取和翻译')
    parser.add_argument('--input-dir', default='input', 
                       help='输入文件目录')
    parser.add_argument('--output-dir', default='output', 
                       help='输出文件目录')
    parser.add_argument('--log-level', default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='日志级别')
    
    args = parser.parse_args()
    
    # 设置日志
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    if args.log_level == 'DEBUG':
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format=log_format
    )
    
    # 配置
    config = {
        'input_dir': args.input_dir,
        'output_dir': args.output_dir,
        'extracted_dir': 'extracted',
        'translated_dir': 'translated',
        'target_lang': args.target_lang,
        'suffix_format': args.suffix_format,
        'engine': args.engine,
        'glossary_file': args.glossary,
        'rebuild_chm': not args.no_rebuild,
    }
    
    # 验证输入目录
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        logger.error(f"输入目录不存在: {input_dir}")
        sys.exit(1)
    
    # 处理批量文件
    processor = EnhancedBatchProcessor(config)
    success, total = processor.process_batch(args.pattern, args.max_workers)
    
    # 输出结果
    logger.info(f"\n{'='*60}")
    logger.info("批量处理完成报告:")
    logger.info(f"  成功: {success}/{total}")
    logger.info(f"  失败: {total - success}")
    logger.info(f"  成功率: {success/total*100:.1f}%" if total > 0 else "  成功率: N/A")
    
    # 显示输出文件
    output_dir = Path(args.output_dir)
    if output_dir.exists():
        chm_files = list(output_dir.glob("*.chm"))
        if chm_files:
            logger.info(f"\n生成的CHM文件 ({len(chm_files)} 个):")
            for chm_file in chm_files:
                size_mb = chm_file.stat().st_size / (1024 * 1024)
                logger.info(f"  - {chm_file.name} ({size_mb:.1f} MB)")
    
    if success > 0:
        logger.info("\n✅ 批量处理完成")
        sys.exit(0)
    else:
        logger.error("\n❌ 批量处理失败")
        sys.exit(1)

if __name__ == "__main__":
    main()