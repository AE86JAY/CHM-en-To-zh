#!/usr/bin/env python3
"""
CHM重新编译脚本
使用HTML Help Workshop重新编译翻译后的文件
"""
import os
import sys
import tempfile
import shutil
import subprocess
from pathlib import Path
import argparse
import logging
import configparser
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class CHMCompiler:
    def __init__(self, hhw_path=None):
        self.hhw_path = hhw_path or self._find_hhw()
        if not self.hhw_path:
            raise FileNotFoundError("未找到HTML Help Workshop")
        
        logger.info(f"使用HTML Help Workshop路径: {self.hhw_path}")
    
    def _find_hhw(self):
        """查找HTML Help Workshop安装路径"""
        # Windows默认路径
        if sys.platform == 'win32':
            paths = [
                "C:\\Program Files (x86)\\HTML Help Workshop",
                "C:\\Program Files\\HTML Help Workshop",
            ]
            for path in paths:
                if os.path.exists(os.path.join(path, "hhw.exe")):
                    return path
        
        # 环境变量
        env_path = os.environ.get('HHWPATH')
        if env_path and os.path.exists(os.path.join(env_path, "hhw.exe")):
            return env_path
        
        return None
    
    def create_hhp_file(self, project_dir, project_name, output_chm):
        """创建.hhp项目文件"""
        hhp_content = f"""[OPTIONS]
Compatibility=1.1 or later
Compiled file={output_chm}
Contents file=contents.hhc
Index file=index.hhk
Default topic=index.html
Title={project_name}
Default Window=main
Display compile progress=Yes
Language=0x804 Chinese (Simplified, China)

[WINDOWS]
main="","contents.hhc","index.hhk","index.html","index.html",,,,,0x23520,222,0x1046,[10,10,780,560],0xB0000,,,,,,0

[FILES]
"""
        
        # 收集所有HTML文件
        html_files = []
        for ext in ['*.html', '*.htm']:
            html_files.extend(Path(project_dir).rglob(ext))
        
        # 添加文件到项目
        for html_file in sorted(html_files):
            relative_path = html_file.relative_to(project_dir)
            hhp_content += f"{relative_path}\n"
        
        # 写入.hhp文件
        hhp_file = os.path.join(project_dir, f"{project_name}.hhp")
        with open(hhp_file, 'w', encoding='utf-8') as f:
            f.write(hhp_content)
        
        return hhp_file
    
    def create_contents_file(self, project_dir, start_file="index.html"):
        """创建目录文件(.hhc)"""
        hhc_content = """<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML//EN">
<HTML>
<HEAD>
<meta name="GENERATOR" content="Microsoft&reg; HTML Help Workshop 4.1">
<!-- Sitemap 1.0 -->
</HEAD>
<BODY>
<OBJECT type="text/site properties">
	<param name="Window Styles" value="0x227">
	<param name="ImageType" value="Folder">
</OBJECT>
<UL>
"""
        
        # 这里可以添加自动生成目录的逻辑
        # 简化版本：只添加一个根节点
        hhc_content += f"""	<LI> <OBJECT type="text/sitemap">
		<param name="Name" value="首页">
		<param name="Local" value="{start_file}">
	</OBJECT>
</UL>
</BODY>
</HTML>"""
        
        hhc_file = os.path.join(project_dir, "contents.hhc")
        with open(hhc_file, 'w', encoding='utf-8') as f:
            f.write(hhc_content)
        
        return hhc_file
    
    def create_index_file(self, project_dir):
        """创建索引文件(.hhk)"""
        hhk_content = """<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML//EN">
<HTML>
<HEAD>
<meta name="GENERATOR" content="Microsoft&reg; HTML Help Workshop 4.1">
<!-- Sitemap 1.0 -->
</HEAD>
<BODY>
<OBJECT type="text/site properties">
	<param name="Window Styles" value="0x227">
</OBJECT>
<UL>
</UL>
</BODY>
</HTML>"""
        
        hhk_file = os.path.join(project_dir, "index.hhk")
        with open(hhk_file, 'w', encoding='utf-8') as f:
            f.write(hhk_content)
        
        return hhk_file
    
    def compile_chm(self, project_dir, output_file):
        """编译CHM文件"""
        hhw_exe = os.path.join(self.hhw_path, "hhw.exe")
        
        if not os.path.exists(hhw_exe):
            raise FileNotFoundError(f"未找到hhw.exe: {hhw_exe}")
        
        # 查找.hhp文件
        hhp_files = list(Path(project_dir).glob("*.hhp"))
        if not hhp_files:
            raise FileNotFoundError("未找到.hhp项目文件")
        
        hhp_file = hhp_files[0]
        
        # 编译命令
        cmd = [hhw_exe, hhp_file]
        
        try:
            logger.info(f"开始编译CHM: {output_file}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=project_dir)
            
            # 检查输出文件
            if os.path.exists(output_file):
                logger.info(f"✅ CHM编译成功: {output_file}")
                return True
            else:
                logger.error(f"❌ CHM文件未生成")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"编译失败: {e.stderr}")
            return False
    
    def rebuild(self, input_dir, output_dir, project_name="TranslatedHelp"):
        """重新编译CHM主方法"""
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 输出CHM文件路径
        output_chm = output_path / f"{project_name}.chm"
        
        logger.info(f"开始重新编译CHM")
        logger.info(f"输入目录: {input_dir}")
        logger.info(f"输出文件: {output_chm}")
        
        try:
            # 1. 创建必要的项目文件
            logger.info("创建项目文件...")
            hhp_file = self.create_hhp_file(input_dir, project_name, output_chm)
            hhc_file = self.create_contents_file(input_dir)
            hhk_file = self.create_index_file(input_dir)
            
            logger.info(f"项目文件创建完成:")
            logger.info(f"  - {hhp_file}")
            logger.info(f"  - {hhc_file}")
            logger.info(f"  - {hhk_file}")
            
            # 2. 编译CHM
            success = self.compile_chm(input_dir, output_chm)
            
            if success:
                logger.info(f"🎉 CHM重新编译完成!")
                return str(output_chm)
            else:
                logger.error("CHM编译失败")
                return None
                
        except Exception as e:
            logger.error(f"重新编译过程中出错: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(description='CHM重新编译工具')
    parser.add_argument('--input', '-i', required=True, help='输入目录（翻译后的文件）')
    parser.add_argument('--output', '-o', required=True, help='输出目录')
    parser.add_argument('--project-name', default='TranslatedHelp', help='项目名称')
    parser.add_argument('--hhw-path', help='HTML Help Workshop安装路径')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    
    args = parser.parse_args()
    
    # 设置日志
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # 创建编译器实例
        compiler = CHMCompiler(args.hhw_path)
        
        # 重新编译CHM
        output_file = compiler.rebuild(
            args.input,
            args.output,
            args.project_name
        )
        
        if output_file:
            print(f"✅ CHM文件已生成: {output_file}")
            sys.exit(0)
        else:
            print("❌ CHM编译失败")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()