#!/usr/bin/env python3
"""
批量翻译CHM文件的脚本
支持同时翻译多个文件，生成 _zh-cn.chm 后缀的文件
"""

import os
import sys
import glob
import tempfile
import shutil
import subprocess
from pathlib import Path
from googletrans import Translator
from bs4 import BeautifulSoup
import html2text
import re

class CHMTranslator:
    def __init__(self, target_lang='zh-CN'):
        self.translator = Translator()
        self.target_lang = target_lang
        self.translated_count = 0
        
    def extract_chm(self, chm_file, output_dir):
        """提取CHM文件到指定目录"""
        try:
            # 方法1: 使用extract_chm工具
            extract_cmd = f'./extract_chm "{chm_file}" "{output_dir}"'
            result = subprocess.run(extract_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                # 方法2: 使用7zip（备用）
                print(f"方法1失败，尝试7zip...")
                subprocess.run(['7z', 'x', chm_file, f'-o{output_dir}'], 
                             capture_output=True)
            
            return True
        except Exception as e:
            print(f"提取失败: {e}")
            return False
    
    def create_chm(self, input_dir, output_file):
        """从目录创建CHM文件"""
        try:
            # 创建HHP项目文件
            hhp_content = f"""[OPTIONS]
Compatibility=1.1 or later
Compiled file={output_file}
Contents file=Table of Contents.hhc
Default Window=Main
Default topic=index.html
Display compile progress=No
Full-text search=Yes
Index file=Index.hhk
Language=0x804 Chinese (Simplified, China)
Title={Path(output_file).stem}

[WINDOWS]
Main=,"Table of Contents.hhc","Index.hhk","index.html","index.html",,,,,0x23520,222,0x1046,[10,10,800,600],0x0,0x0,,,,,0

[FILES]
"""
            
            # 收集所有HTML文件
            html_files = []
            for root, dirs, files in os.walk(input_dir):
                for file in files:
                    if file.endswith(('.html', '.htm')):
                        rel_path = os.path.relpath(os.path.join(root, file), input_dir)
                        html_files.append(rel_path)
                        hhp_content += f"{rel_path}\n"
            
            # 写入HHP文件
            hhp_file = os.path.join(input_dir, "project.hhp")
            with open(hhp_file, 'w', encoding='utf-8') as f:
                f.write(hhp_content)
            
            # 创建HHC文件（目录）
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
            
            for html_file in html_files:
                if 'index' in html_file.lower() or html_file == 'index.html':
                    hhc_content += f'	<LI> <OBJECT type="text/sitemap">\n'
                    hhc_content += f'		<param name="Name" value="主页">\n'
                    hhc_content += f'		<param name="Local" value="{html_file}">\n'
                    hhc_content += f'	</OBJECT>\n'
            
            hhc_content += "</UL>\n</BODY>\n</HTML>"
            
            hhc_file = os.path.join(input_dir, "Table of Contents.hhc")
            with open(hhc_file, 'w', encoding='utf-8') as f:
                f.write(hhc_content)
            
            # 使用hhc编译（需要安装HTML Help Workshop）
            # 这里使用开源工具作为替代
            compile_cmd = f"hhc {hhp_file}"
            try:
                subprocess.run(compile_cmd, shell=True, check=True)
            except:
                # 备用方法：使用chmcmd
                print("使用chmcmd编译...")
                chmcmd_cmd = f"chmcmd {hhp_file}"
                subprocess.run(chmcmd_cmd, shell=True)
            
            # 检查输出文件是否创建
            if os.path.exists(output_file):
                print(f"成功创建: {output_file}")
                return True
            else:
                print(f"编译失败，文件未生成")
                return False
                
        except Exception as e:
            print(f"创建CHM失败: {e}")
            return False
    
    def translate_html_file(self, html_file):
        """翻译单个HTML文件"""
        try:
            with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'lxml')
            
            # 找到所有需要翻译的文本节点
            translatable_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                               'li', 'td', 'th', 'span', 'div', 'a', 'title']
            
            for tag in translatable_tags:
                elements = soup.find_all(tag)
                for element in elements:
                    # 跳过包含代码或特殊内容的元素
                    if element.find('code') or element.find('pre'):
                        continue
                    
                    text = element.get_text().strip()
                    if text and len(text) > 1:
                        try:
                            # 翻译文本
                            translated = self.translator.translate(
                                text, 
                                dest=self.target_lang
                            ).text
                            
                            # 替换文本内容
                            if element.string:
                                element.string.replace_with(translated)
                            else:
                                for child in element.children:
                                    if child.name is None:  # 文本节点
                                        child.replace_with(translated)
                                        break
                                        
                        except Exception as e:
                            print(f"翻译失败 '{text[:50]}...': {e}")
                            continue
            
            # 保存翻译后的文件
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(str(soup))
                
            return True
            
        except Exception as e:
            print(f"翻译HTML文件失败 {html_file}: {e}")
            return False
    
    def translate_directory(self, directory):
        """翻译目录中的所有HTML文件"""
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(('.html', '.htm')):
                    file_path = os.path.join(root, file)
                    print(f"翻译: {file_path}")
                    if self.translate_html_file(file_path):
                        self.translated_count += 1
    
    def process_chm_file(self, chm_file):
        """处理单个CHM文件"""
        print(f"\n{'='*60}")
        print(f"处理文件: {chm_file}")
        print(f"{'='*60}")
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            extract_dir = os.path.join(temp_dir, 'extracted')
            os.makedirs(extract_dir)
            
            # 提取CHM
            print("步骤1: 提取CHM文件...")
            if not self.extract_chm(chm_file, extract_dir):
                print("提取失败，跳过此文件")
                return False
            
            # 翻译内容
            print("步骤2: 翻译内容...")
            self.translate_directory(extract_dir)
            
            # 生成输出文件名
            chm_path = Path(chm_file)
            output_file = chm_path.parent / f"{chm_path.stem}_zh-cn.chm"
            
            # 重新打包CHM
            print(f"步骤3: 重新打包为 {output_file}...")
            if self.create_chm(extract_dir, str(output_file)):
                print(f"✓ 完成: {output_file}")
                return True
            else:
                print(f"✗ 失败: {chm_file}")
                return False

def main():
    if len(sys.argv) < 2:
        print("用法: python translate_chm.py <文件模式>")
        print("示例: python translate_chm.py '*.chm'")
        print("示例: python translate_chm.py 'docs/*.chm'")
        sys.exit(1)
    
    file_pattern = sys.argv[1]
    
    # 查找所有匹配的CHM文件
    chm_files = glob.glob(file_pattern, recursive=True)
    
    if not chm_files:
        print(f"未找到匹配的文件: {file_pattern}")
        sys.exit(1)
    
    print(f"找到 {len(chm_files)} 个CHM文件:")
    for file in chm_files:
        print(f"  - {file}")
    
    # 创建翻译器
    translator = CHMTranslator(target_lang='zh-CN')
    
    # 处理每个文件
    success_count = 0
    for chm_file in chm_files:
        if translator.process_chm_file(chm_file):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"处理完成!")
    print(f"成功: {success_count}/{len(chm_files)} 个文件")
    print(f"翻译了 {translator.translated_count} 个HTML文件")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()