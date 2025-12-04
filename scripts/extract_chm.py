#!/usr/bin/env python3
"""
CHM文件提取脚本
支持多种提取方式
"""
import os
import sys
import subprocess
import zipfile
import tempfile
from pathlib import Path
import argparse
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CHMExtractor:
    def __init__(self, use_7zip=True, use_wine=False):
        self.use_7zip = use_7zip
        self.use_wine = use_wine
        
    def extract_with_7zip(self, chm_file, output_dir):
        """使用7z提取CHM"""
        try:
            cmd = ['7z', 'x', chm_file, f'-o{output_dir}', '-y']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info("7z提取成功")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"7z提取失败: {e.stderr}")
            return False
    
    def extract_with_hhw(self, chm_file, output_dir):
        """使用HTML Help Workshop反编译（需要Windows环境）"""
        try:
            # 检查是否在Windows下
            if sys.platform != 'win32' and not self.use_wine:
                logger.warning("HTML Help Workshop仅支持Windows，跳过此方法")
                return False
            
            # 查找hhw.exe
            hhw_paths = [
                "C:\\Program Files (x86)\\HTML Help Workshop\\hhw.exe",
                "C:\\Program Files\\HTML Help Workshop\\hhw.exe",
            ]
            
            hhw_exe = None
            for path in hhw_paths:
                if os.path.exists(path):
                    hhw_exe = path
                    break
            
            if not hhw_exe:
                logger.warning("未找到HTML Help Workshop")
                return False
            
            # 创建临时项目文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.hhp', delete=False) as f:
                project_content = f"""[OPTIONS]
Compatibility=1.1 or later
Compiled file={chm_file}
Contents file=contents.hhc
Index file=index.hhk
Default topic=index.html
Title=Extracted CHM

[FILES]
"""
                f.write(project_content)
                project_file = f.name
            
            try:
                # 反编译命令
                cmd = [hhw_exe, '/decompile', output_dir, project_file]
                
                if self.use_wine and sys.platform != 'win32':
                    cmd = ['wine'] + cmd
                
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                logger.info("HTML Help Workshop反编译成功")
                return True
            finally:
                os.unlink(project_file)
                
        except Exception as e:
            logger.error(f"HTML Help Workshop提取失败: {e}")
            return False
    
    def extract_with_chmlib(self, chm_file, output_dir):
        """使用Python的chmlib库提取"""
        try:
            import chmlib
            chm = chmlib.CHM(chm_file)
            
            # 遍历所有文件
            for i in range(chm.get_file_count()):
                file_info = chm.get_file_info(i)
                if file_info:
                    file_path = file_info['path'].decode('utf-8', errors='ignore')
                    output_path = os.path.join(output_dir, file_path)
                    
                    # 确保目录存在
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    
                    # 提取文件内容
                    content = chm.extract_file(i)
                    if content:
                        with open(output_path, 'wb') as f:
                            f.write(content)
            
            logger.info("chmlib提取成功")
            return True
        except ImportError:
            logger.warning("未安装chmlib库，跳过此方法")
            return False
        except Exception as e:
            logger.error(f"chmlib提取失败: {e}")
            return False
    
    def extract(self, chm_file, output_dir):
        """主提取方法，尝试多种方式"""
        # 确保输出目录存在
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"开始提取CHM文件: {chm_file}")
        logger.info(f"输出目录: {output_dir}")
        
        # 方法1: 使用7zip
        if self.use_7zip:
            if self.extract_with_7zip(chm_file, output_dir):
                return True
        
        # 方法2: 使用HTML Help Workshop
        if self.extract_with_hhw(chm_file, output_dir):
            return True
        
        # 方法3: 使用chmlib
        if self.extract_with_chmlib(chm_file, output_dir):
            return True
        
        # 方法4: 尝试作为ZIP文件处理
        try:
            with zipfile.ZipFile(chm_file, 'r') as zip_ref:
                zip_ref.extractall(output_dir)
            logger.info("作为ZIP文件提取成功")
            return True
        except:
            logger.warning("ZIP提取失败")
        
        logger.error("所有提取方法都失败")
        return False

def main():
    parser = argparse.ArgumentParser(description='CHM文件提取工具')
    parser.add_argument('--input', '-i', required=True, help='输入CHM文件路径')
    parser.add_argument('--output', '-o', required=True, help='输出目录')
    parser.add_argument('--no-7zip', action='store_true', help='不使用7zip')
    parser.add_argument('--use-wine', action='store_true', help='使用Wine运行Windows工具')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    
    args = parser.parse_args()
    
    # 设置日志级别
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # 执行提取
    extractor = CHMExtractor(
        use_7zip=not args.no_7zip,
        use_wine=args.use_wine
    )
    
    success = extractor.extract(args.input, args.output)
    
    if success:
        logger.info("✅ CHM提取完成")
        sys.exit(0)
    else:
        logger.error("❌ CHM提取失败")
        sys.exit(1)

if __name__ == "__main__":
    main()