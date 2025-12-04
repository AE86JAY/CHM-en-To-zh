许可证
MIT License
###################################################################
# CHM自动化翻译流水线

基于GitHub Actions的CHM文件自动化翻译流水线，支持提取、翻译、重新编译全流程。

## 功能特性

- ✅ 自动提取CHM文件内容
- ✅ 支持多种翻译引擎（Google、DeepL、Microsoft）
- ✅ 术语库支持，确保翻译一致性
- ✅ 多线程处理，提高翻译效率
- ✅ 自动重新编译为CHM文件
- ✅ GitHub Actions自动化工作流
- ✅ 支持手动触发和自动触发

## 使用方法

### 1. 基本使用

1. 将CHM文件放入 `input/` 目录
2. 推送代码到GitHub
3. GitHub Actions会自动开始翻译流程
4. 在Releases页面下载翻译后的CHM文件

### 2. 手动触发

1. 在GitHub仓库的Actions页面
2. 选择"Manual CHM Translation"
3. 配置参数并运行

### 3. 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 提取CHM
python scripts/extract_chm.py --input input/help.chm --output extracted

# 翻译内容
python scripts/translate_html.py --input extracted --output translated --target-lang zh-CN

# 重新编译（需要Windows）
python scripts/rebuild_chm.py --input translated --output output --project-name MyHelp
#################################################################
配置说明
术语库
编辑 config/glossary.csv 文件，添加专业术语翻译。

翻译引擎
在GitHub Secrets中设置API密钥：

DEEPL_API_KEY: DeepL API密钥

MICROSOFT_TRANSLATOR_KEY: Microsoft Translator密钥
#################################################################
## 使用说明

### 1. **首次设置**
1. Fork或克隆此仓库
2. 在GitHub仓库Settings → Secrets中配置：
   - `DEEPL_API_KEY` (可选，如果需要DeepL翻译)
   - `MICROSOFT_TRANSLATOR_KEY` (可选)

### 2. **日常使用**
- **自动模式**：将CHM文件放入 `input/` 目录，推送后自动翻译
- **手动模式**：在GitHub Actions页面手动触发工作流
- **本地测试**：使用提供的Python脚本在本地测试

### 3. **自定义配置**
- 修改 `config/glossary.csv` 添加专业术语
- 调整工作流文件中的参数
- 根据需要修改翻译脚本

## 注意事项

1. **Windows环境**：重新编译CHM需要Windows环境，GitHub Actions中使用windows-latest运行器
2. **API限制**：免费的翻译API有调用限制，大文件可能需要分批处理
3. **质量检查**：机器翻译后建议人工校对关键内容
4. **文件大小**：GitHub Actions有存储限制，大CHM文件可能需要分拆