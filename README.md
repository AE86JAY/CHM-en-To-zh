CHM 文件翻译自动化工具
这是一个自动将英文 CHM 帮助文件翻译成中文并重新打包的 GitHub 工作流解决方案。支持批量处理多个 CHM 文件，生成带有 _zh-cn.chm 后缀的中文版本。

🚀 功能特性
批量处理：同时翻译多个 CHM 文件

自动翻译：使用 Google 翻译 API 自动翻译 HTML 内容

保持格式：保留原始 CHM 文件的结构和格式

中文重打包：生成 原文件名_zh-cn.chm 的中文版本

GitHub 集成：完全自动化的工作流程

手动/自动触发：支持手动触发和推送自动触发

📁 项目结构
.
├── .github/workflows/
│   └── translate-chm.yml      # GitHub 工作流配置文件
├── scripts/
│   ├── translate_chm.py       # 主翻译脚本
│   └── install_dependencies.sh # 依赖安装脚本（可选）
├── requirements.txt           # Python 依赖包
├── README.md                  # 本说明文件
└── （您的 CHM 文件目录）/
    └── *.chm                  # 待翻译的 CHM 文件

⚙️ 快速开始
1. 克隆仓库
bash
git clone https://github.com/ae86jay/CHM-en-To-zh.git
cd CHM-en-To-zh
2. 添加 CHM 文件
将需要翻译的英文 CHM 文件放在仓库的任意目录下，例如：

根目录：*.chm

子目录：docs/*.chm

特定目录：help-files/*.chm

3. 配置工作流（可选）
如果需要自定义配置，可编辑 .github/workflows/translate-chm.yml：

修改默认文件匹配模式

调整触发条件

更改目标语言

4. 运行翻译
方式一：GitHub Actions 手动触发
访问 GitHub 仓库的 Actions 页面

选择 "Translate CHM Files" 工作流

点击 "Run workflow"

填写参数（或使用默认值）：

File pattern: 文件匹配模式（如 *.chm, docs/*.chm）

Target language: 目标语言（默认 zh-CN）

点击 "Run workflow" 开始翻译

方式二：推送自动触发
当推送包含 .chm 文件到仓库时，工作流会自动触发。

方式三：本地运行
bash
# 安装依赖
pip install -r requirements.txt
sudo apt-get install chm2html html2chm  # 或在 macOS 使用 brew

# 运行翻译脚本
python scripts/translate_chm.py "*.chm"
🔧 配置参数
工作流输入参数
参数	描述	默认值	示例
file_pattern	CHM 文件匹配模式	*.chm	docs/*.chm, help/*.chm
target_lang	目标语言代码	zh-CN	zh-TW, ja, ko
支持的 CHM 文件
标准 CHM 帮助文件

包含 HTML、CSS、JavaScript 的 CHM

多层级目录结构的 CHM

📊 输出结果
文件命名规则
输入：documentation.chm

输出：documentation_zh-cn.chm

输出位置
翻译后的文件与原始文件在同一目录

原始文件保持不变

新文件自动提交到仓库

🛠️ 技术细节
翻译流程
提取：将 CHM 文件解压到临时目录

解析：识别所有 HTML 文件内容

翻译：使用 Google 翻译 API 翻译文本内容

重建：保持原始结构重新打包为 CHM

保存：生成新的中文版 CHM 文件

支持的语言
可通过修改 target_lang 参数支持多种语言：

简体中文：zh-CN

繁体中文：zh-TW

日语：ja

韩语：ko

其他 Google 翻译支持的语言

⚠️ 注意事项
限制和约束
翻译质量：基于机器翻译，专业文档建议人工校对

API 限制：Google 翻译 API 有速率限制（大量文件请分批处理）

文件大小：大文件可能需要较长的处理时间

复杂格式：某些特殊格式的 CHM 文件可能无法完美处理

版权问题：请确保您有权翻译和分发相关文档

常见问题
Q: 翻译过程中断怎么办？
A: 工作流会自动重试，您也可以手动重新触发。

Q: 翻译质量不佳？
A: 可以：

编辑脚本调整翻译策略

使用专业翻译 API（如 DeepL）

人工校对重要文档

Q: 不支持某些 CHM 文件？
A: 尝试：

确保 CHM 文件没有损坏

使用其他 CHM 提取工具

将 CHM 转换为其他格式再处理

Q: 如何自定义翻译？
A: 编辑 scripts/translate_chm.py 中的 translate_html_file 方法：

python
# 自定义翻译逻辑
def custom_translate(self, text):
    # 添加术语表替换
    terminology = {
        "Windows": "视窗系统",
        "API": "应用程序接口"
    }
    for eng, chs in terminology.items():
        text = text.replace(eng, chs)
    return text
🔄 更新和维护
更新依赖
bash
# 更新 Python 包
pip install --upgrade -r requirements.txt

# 更新系统工具
sudo apt-get update && sudo apt-get upgrade
调试和日志
GitHub Actions 日志：查看工作流运行详情

本地调试：使用 python scripts/translate_chm.py --debug "*.chm"

临时文件：工作流会在 /tmp 生成中间文件用于调试

📄 许可证
本项目基于 MIT 许可证开源。使用 Google 翻译 API 需遵守其服务条款。

🤝 贡献指南
欢迎提交 Issue 和 Pull Request：

Fork 本仓库

创建功能分支

提交更改

推送分支并创建 Pull Request

📞 支持
如遇问题：

查看 GitHub Issues

检查工作流日志

提交新 Issue 描述问题

提示：对于重要文档，建议在自动翻译后进行人工校对以确保准确性。
