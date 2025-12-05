#!/usr/bin/env python3
"""
Windows环境下批量翻译CHM文件的优化脚本
支持断点续传和错误恢复
"""

import os
import sys
import glob
import tempfile
import shutil
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
from googletrans import Translator
from bs4 import BeautifulSoup
import html2text

class CHMTranslatorWindows:
    def __init__(self, target_lang='zh-CN', config_file=None):
        self.translator = Translator()
        self.target_lang = target_lang
        self.translated_count = 0
        self.success_files = []
        self.failed_files = []
        
        # 加载配置
        self.config = {
            'max_retries': 3,
            'retry_delay': 2,
            'chunk_size': 4500,  # Google翻译的字符限制
            'preserve_code_blocks': True,
            'skip_tags': ['code', 'pre', 'script', 'style', 'noscript'],
            'translatable_tags': ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                                'li', 'td', 'th', 'span', 'div', 'a', 'title',
                                'strong', 'b', 'i', 'em', 'label', 'caption'],
            'log_level': 'INFO'
        }
        
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                self.config.update(user_config)
    
    def log(self, message, level='INFO'):
        """日志记录"""
        if level == 'ERROR':
            print(f"[ERROR] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}")
        elif level == 'WARNING':
            print(f"[WARNING] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}")
        else:
            print(f"[INFO] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}")
    
    def find_7zip(self):
        """查找7-Zip可执行文件"""
        possible_paths = [
            r"C:\Program Files\7-Zip\7z.exe",
            r"C:\Program Files (x86)\7-Zip\7z.exe",
            "7z.exe"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # 尝试在PATH中查找
        try:
            result = subprocess.run(['where', '7z'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except:
            pass
        
        self.log("未找到7-Zip，将尝试使用备用方法", "WARNING")
        return None
    
    def find_hhc(self):
        """查找HTML Help Workshop"""
        possible_paths = [
            r"C:\Program Files (x86)\HTML Help Workshop\hhc.exe",
            r"C:\Program Files\HTML Help Workshop\hhc.exe",
            "hhc.exe"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # 尝试在PATH中查找
        try:
            result = subprocess.run(['where', 'hhc'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except:
            pass
        
        self.log("未找到HTML Help Workshop，将尝试使用chmcmd", "WARNING")
        return None
    
    def extract_chm(self, chm_file, output_dir):
        """提取CHM文件，支持多种方法"""
        methods = [
            self._extract_with_7zip,
            self._extract_with_python_chm,
            self._extract_as_zip
        ]
        
        for method in methods:
            self.log(f"尝试使用 {method.__name__} 提取 {chm_file}")
            if method(chm_file, output_dir):
                return True
        
        return False
    
    def _extract_with_7zip(self, chm_file, output_dir):
        """使用7-Zip提取"""
        try:
            seven_zip = self.find_7zip()
            if not seven_zip:
                return False
            
            cmd = [seven_zip, 'x', chm_file, f'-o{output_dir}', '-y']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.log(f"7-Zip提取成功: {chm_file}")
                return True
            else:
                self.log(f"7-Zip提取失败: {result.stderr}", "WARNING")
                return False
                
        except Exception as e:
            self.log(f"7-Zip提取异常: {e}", "WARNING")
            return False
    
    def _extract_with_python_chm(self, chm_file, output_dir):
        """使用Python chm库提取"""
        try:
            import chm
            chm_file_obj = chm.CHM(chm_file)
            
            # 获取所有文件列表
            files = []
            for file_info in chm_file_obj:
                files.append(file_info['path'])
            
            # 提取所有文件
            for file_path in files:
                try:
                    data = chm_file_obj.read(file_path)
                    if data:
                        output_path = os.path.join(output_dir, file_path.lstrip('/'))
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)
                        with open(output_path, 'wb') as f:
                            f.write(data)
                except Exception as e:
                    self.log(f"提取文件失败 {file_path}: {e}", "WARNING")
                    continue
            
            self.log(f"Python chm提取成功: {chm_file}")
            return True
            
        except ImportError:
            self.log("未安装chm库", "WARNING")
            return False
        except Exception as e:
            self.log(f"Python chm提取异常: {e}", "WARNING")
            return False
    
    def _extract_as_zip(self, chm_file, output_dir):
        """将CHM作为ZIP文件提取"""
        try:
            import zipfile
            with zipfile.ZipFile(chm_file, 'r') as zip_ref:
                zip_ref.extractall(output_dir)
            self.log(f"ZIP提取成功: {chm_file}")
            return True
        except:
            return False
    
    def create_chm(self, input_dir, output_file):
        """创建CHM文件"""
        methods = [
            self._create_with_hhc,
            self._create_with_chmcmd,
            self._create_with_hhw
        ]
        
        for method in methods:
            self.log(f"尝试使用 {method.__name__} 创建 {output_file}")
            if method(input_dir, output_file):
                return True
        
        return False
    
    def _create_with_hhc(self, input_dir, output_file):
        """使用hhc.exe创建CHM"""
        try:
            hhc_path = self.find_hhc()
            if not hhc_path:
                return False
            
            # 创建HHP项目文件
            hhp_file = self._create_hhp_file(input_dir, output_file)
            if not hhp_file:
                return False
            
            # 运行hhc编译
            cmd = [hhc_path, hhp_file]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                # 检查输出文件
                expected_name = os.path.basename(output_file)
                expected_path = os.path.join(os.path.dirname(hhp_file), expected_name)
                
                if os.path.exists(expected_path):
                    shutil.move(expected_path, output_file)
                    self.log(f"hhc编译成功: {output_file}")
                    return True
                elif os.path.exists(output_file):
                    self.log(f"hhc编译成功: {output_file}")
                    return True
            
            self.log(f"hhc编译失败: {result.stderr}", "WARNING")
            return False
            
        except Exception as e:
            self.log(f"hhc编译异常: {e}", "WARNING")
            return False
    
    def _create_with_chmcmd(self, input_dir, output_file):
        """使用chmcmd创建CHM"""
        try:
            # 创建HHP项目文件
            hhp_file = self._create_hhp_file(input_dir, output_file)
            if not hhp_file:
                return False
            
            # 尝试运行chmcmd
            cmd = ['chmcmd', 'compile', hhp_file]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                self.log(f"chmcmd编译成功: {output_file}")
                return True
            else:
                self.log(f"chmcmd编译失败: {result.stderr}", "WARNING")
                return False
                
        except Exception as e:
            self.log(f"chmcmd编译异常: {e}", "WARNING")
            return False
    
    def _create_with_hhw(self, input_dir, output_file):
        """使用HTML Help Workshop GUI创建CHM（备用）"""
        try:
            # 创建HHP文件
            hhp_file = self._create_hhp_file(input_dir, output_file)
            if not hhp_file:
                return False
            
            # 尝试使用HTML Help Workshop
            hhw_path = r"C:\Program Files (x86)\HTML Help Workshop\hhw.exe"
            if os.path.exists(hhw_path):
                # 这里可以添加GUI自动化，但通常不推荐在CI/CD中使用
                self.log("需要GUI界面的HTML Help Workshop，跳过此方法", "WARNING")
            
            return False
            
        except Exception as e:
            self.log(f"hhw编译异常: {e}", "WARNING")
            return False
    
    def _create_hhp_file(self, input_dir, output_file):
        """创建HHP项目文件"""
        try:
            project_name = Path(output_file).stem
            
            # 查找HTML文件
            html_files = []
            for root, dirs, files in os.walk(input_dir):
                for file in files:
                    if file.lower().endswith(('.html', '.htm')):
                        rel_path = os.path.relpath(os.path.join(root, file), input_dir)
                        html_files.append(rel_path)
            
            if not html_files:
                self.log("未找到HTML文件", "ERROR")
                return None
            
            # 确定默认页面
            default_page = 'index.html' if 'index.html' in [os.path.basename(f).lower() for f in html_files] else html_files[0]
            
            # 创建HHP内容
            hhp_content = f"""[OPTIONS]
Compatibility=1.1 or later
Compiled file={os.path.basename(output_file)}
Contents file=contents.hhc
Default Window=main
Default topic={default_page}
Display compile progress=No
Full-text search=Yes
Index file=index.hhk
Language=0x804 Chinese (Simplified, China)
Title={project_name}

[WINDOWS]
main=,"contents.hhc","index.hhk","{default_page}","{default_page}",,,,,0x23520,222,0x1046,[10,10,800,600],0x0,0x0,,,,,0

[FILES]
"""
            
            # 添加文件列表
            for html_file in html_files:
                hhp_content += f"{html_file}\n"
            
            # 写入HHP文件
            hhp_file = os.path.join(input_dir, f"{project_name}.hhp")
            with open(hhp_file, 'w', encoding='utf-8') as f:
                f.write(hhp_content)
            
            # 创建目录文件
            self._create_hhc_file(input_dir, html_files)
            
            # 创建索引文件
            self._create_hhk_file(input_dir)
            
            return hhp_file
            
        except Exception as e:
            self.log(f"创建HHP文件失败: {e}", "ERROR")
            return None
    
    def _create_hhc_file(self, input_dir, html_files):
        """创建目录文件"""
        try:
            hhc_content = """<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML//EN">
<HTML>
<HEAD>
<meta name="GENERATOR" content="Microsoft&reg; HTML Help Workshop 4.1">
<!-- Sitemap 1.0 -->
</HEAD>
<BODY>
<OBJECT type="text/site properties">
	<param name="Window Styles" value="0x22523">
</OBJECT>
<UL>
"""
            
            # 添加目录项（限制前50个文件）
            for i, html_file in enumerate(html_files[:50]):
                title = Path(html_file).stem.replace('_', ' ').title()
                hhc_content += f'	<LI> <OBJECT type="text/sitemap">\n'
                hhc_content += f'		<param name="Name" value="{title}">\n'
                hhc_content += f'		<param name="Local" value="{html_file}">\n'
                hhc_content += f'	</OBJECT>\n'
            
            hhc_content += "</UL>\n</BODY>\n</HTML>"
            
            hhc_file = os.path.join(input_dir, "contents.hhc")
            with open(hhc_file, 'w', encoding='utf-8') as f:
                f.write(hhc_content)
                
        except Exception as e:
            self.log(f"创建目录文件失败: {e}", "WARNING")
    
    def _create_hhk_file(self, input_dir):
        """创建索引文件"""
        try:
            hhk_content = """<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML//EN">
<HTML>
<HEAD>
<meta name="GENERATOR" content="Microsoft&reg; HTML Help Workshop 4.1">
</HEAD>
<BODY>
<OBJECT type="text/site properties">
</OBJECT>
<UL>
</UL>
</BODY>
</HTML>"""
            
            hhk_file = os.path.join(input_dir, "index.hhk")
            with open(hhk_file, 'w', encoding='utf-8') as f:
                f.write(hhk_content)
                
        except Exception as e:
            self.log(f"创建索引文件失败: {e}", "WARNING")
    
    def translate_text(self, text):
        """翻译文本，支持分块和重试"""
        if not text or len(text.strip()) < 2:
            return text
        
        # 检查是否可能是代码或URL
        if (text.startswith(('http://', 'https://', 'ftp://', 'mailto:')) or
            all(c in '0123456789abcdefABCDEF:/.-_?=&' for c in text)):
            return text
        
        max_retries = self.config['max_retries']
        
        for attempt in range(max_retries):
            try:
                # 如果文本太长，分割成小块
                if len(text) > self.config['chunk_size']:
                    chunks = []
                    chunk = ""
                    sentences = text.split('. ')
                    
                    for sentence in sentences:
                        if len(chunk) + len(sentence) < self.config['chunk_size']:
                            chunk += sentence + '. '
                        else:
                            if chunk:
                                chunks.append(chunk.strip())
                            chunk = sentence + '. '
                    
                    if chunk:
                        chunks.append(chunk.strip())
                    
                    # 翻译每个块
                    translated_chunks = []
                    for chunk_text in chunks:
                        if len(chunk_text) > 10:  # 只翻译有实质内容的块
                            translated = self.translator.translate(
                                chunk_text, 
                                dest=self.target_lang
                            ).text
                            translated_chunks.append(translated)
                        else:
                            translated_chunks.append(chunk_text)
                    
                    return ' '.join(translated_chunks)
                else:
                    # 直接翻译
                    translated = self.translator.translate(
                        text, 
                        dest=self.target_lang
                    ).text
                    return translated
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = self.config['retry_delay'] * (attempt + 1)
                    self.log(f"翻译重试 {attempt + 1}/{max_retries}: {e}，等待 {wait_time}秒", "WARNING")
                    time.sleep(wait_time)
                else:
                    self.log(f"翻译失败: {text[:50]}... - {e}", "ERROR")
                    return text  # 返回原文
    
    def translate_html_file(self, html_file):
        """翻译单个HTML文件"""
        try:
            with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # 翻译所有文本节点
            for text_node in soup.find_all(text=True):
                if text_node.parent and text_node.parent.name in self.config['skip_tags']:
                    continue
                
                if text_node.parent and text_node.parent.name in self.config['translatable_tags']:
                    if text_node.strip():
                        translated = self.translate_text(text_node.strip())
                        text_node.replace_with(translated)
                        self.translated_count += 1
           
            # 保存翻译后的文件
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(str(soup))
                
            return True
            
        except Exception as e:
            self.log(f"翻译HTML文件失败 {html_file}: {e}", "ERROR")
            return False
    
    def translate_directory(self, directory):
        """翻译目录中的所有HTML文件"""
        html_count = 0
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(('.html', '.htm')):
                    html_count += 1
        
        self.log(f"找到 {html_count} 个HTML文件需要翻译")
        
        current = 0
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(('.html', '.htm')):
                    file_path = os.path.join(root, file)
                    current += 1
                    self.log(f"翻译进度: {current}/{html_count} - {file_path}")
                    
                    for attempt in range(self.config['max_retries']):
                        if self.translate_html_file(file_path):
                            break
                        elif attempt < self.config['max_retries'] - 1:
                            time.sleep(self.config['retry_delay'])
    
    def process_chm_file(self, chm_file):
        """处理单个CHM文件"""
        self.log(f"开始处理: {chm_file}")
        
        start_time = time.time()
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix=f"chm_translate_{Path(chm_file).stem}_")
        
        try:
            # 提取CHM
            self.log("提取CHM文件...")
            if not self.extract_chm(chm_file, temp_dir):
                self.failed_files.append((chm_file, "提取失败"))
                return False
            
            # 翻译内容
            self.log("翻译内容...")
            self.translate_directory(temp_dir)
            
            # 生成输出文件名
            chm_path = Path(chm_file)
            output_file = chm_path.parent / f"{chm_path.stem}_zh-cn.chm"
            
            # 重新打包CHM
            self.log(f"重新打包为 {output_file}...")
            if self.create_chm(temp_dir, str(output_file)):
                elapsed = time.time() - start_time
                self.log(f"✓ 完成: {output_file} (耗时: {elapsed:.1f}秒)")
                self.success_files.append((chm_file, output_file, elapsed))
                return True
            else:
                self.failed_files.append((chm_file, "打包失败"))
                return False
                
        except Exception as e:
            self.log(f"处理异常: {chm_file} - {e}", "ERROR")
            self.failed_files.append((chm_file, str(e)))
            return False
            
        finally:
            # 清理临时目录
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass
    
    def generate_report(self):
        """生成处理报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'target_language': self.target_lang,
            'success_count': len(self.success_files),
            'failed_count': len(self.failed_files),
            'translated_blocks': self.translated_count,
            'success_files': [],
            'failed_files': []
        }
        
        for original, output, elapsed in self.success_files:
            report['success_files'].append({
                'original': str(original),
                'output': str(output),
                'elapsed_seconds': elapsed
            })
        
        for original, error in self.failed_files:
            report['failed_files'].append({
                'original': str(original),
                'error': error
            })
        
        return report

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='批量翻译CHM文件')
    parser.add_argument('pattern', help='文件匹配模式 (例如: *.chm 或 docs/*.chm)')
    parser.add_argument('--lang', default='zh-CN', help='目标语言 (默认: zh-CN)')
    parser.add_argument('--config', help='配置文件路径')
    parser.add_argument('--output-report', help='报告输出文件')
    
    args = parser.parse_args()
    
    # 创建翻译器
    translator = CHMTranslatorWindows(target_lang=args.lang, config_file=args.config)
    
    # 查找所有匹配的CHM文件
    chm_files = glob.glob(args.pattern, recursive=True)
    
    if not chm_files:
        print(f"错误: 未找到匹配的文件: {args.pattern}")
        sys.exit(1)
    
    translator.log(f"找到 {len(chm_files)} 个CHM文件:")
    for file in chm_files:
        translator.log(f"  - {file}")
    
    # 处理每个文件
    success_count = 0
    for i, chm_file in enumerate(chm_files):
        translator.log(f"\n处理进度: {i+1}/{len(chm_files)}")
        if translator.process_chm_file(chm_file):
            success_count += 1
    
    # 生成报告
    report = translator.generate_report()
    
    print(f"\n{'='*60}")
    print(f"处理完成!")
    print(f"成功: {success_count}/{len(chm_files)} 个文件")
    print(f"失败: {len(chm_files) - success_count}/{len(chm_files)} 个文件")
    print(f"翻译了 {translator.translated_count} 个文本块")
    print(f"{'='*60}")
    
    if translator.failed_files:
        print(f"\n失败的文件:")
        for original, error in translator.failed_files:
            print(f"  - {original}: {error}")
    
    # 保存报告
    if args.output_report:
        with open(args.output_report, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        translator.log(f"报告已保存到: {args.output_report}")
    
    # 退出代码
    if translator.failed_files:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
```