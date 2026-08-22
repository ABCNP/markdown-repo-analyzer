# Markdown Repo Analyzer

使用 Python 标准库递归分析本地 Markdown 仓库的 MVP 工具。

## 功能

- 扫描 `.md` 和 `.markdown` 文件
- 统计文件数量和去除空白字符后的总字数
- 找出按字节计算的最大文件和最近修改的文件
- 生成 Markdown 格式报告

## 使用方式

无需安装第三方依赖：

```bash
python analyzer.py <扫描目录> [-o <报告路径>]
```

## 测试

```bash
python -m unittest discover -s tests -v
```
