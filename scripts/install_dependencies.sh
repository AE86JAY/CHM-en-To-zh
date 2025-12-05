#!/bin/bash
# 安装依赖脚本

# 更新包管理器
sudo apt-get update

# 安装Python依赖
pip install -r requirements.txt

# 安装系统依赖
sudo apt-get install -y \
    python3-dev \
    build-essential \
    libchm-dev \
    p7zip-full \
    wget \
    gcc

# 编译extract_chm工具
if [ ! -f "extract_chm" ]; then
    wget https://raw.githubusercontent.com/dottedmag/archivemount-chm/master/extract_chmlib.c
    gcc -o extract_chm extract_chmlib.c -lchm
    chmod +x extract_chm
fi

echo "依赖安装完成!"