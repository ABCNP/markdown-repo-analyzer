# Markdown Repo Analyzer

本地 Markdown 文档库分析工具，帮助你了解文档库的规模、结构和明显问题。

## 当前功能

- 递归扫描 `.md` 和 `.markdown` 文件
- 统计文件数量、总字数、总文件大小和平均字数
- 找出最大文件和最近修改文件
- 按目录统计文件数量、字数和大小
- 统计标题、代码块、链接和图片数量
- 检查空文件、超长文件和失效的本地链接
- 记录无法读取的文件并继续分析
- 生成 Markdown 格式报告

## 使用方式

项目使用 Python 标准库，不需要安装第三方依赖。

```powershell
python analyzer.py <文档目录> -o report.md
```

如果使用项目内的 Python 环境：

```powershell
.python\python.exe analyzer.py .\my-notes -o report.md
```

## 运行测试

```powershell
python -m unittest discover -s tests -v
```

## 报告内容

报告包括总体统计、最大文件、最近修改文件、警告、空文件、超长文件、目录汇总和每个文件的详细统计。
