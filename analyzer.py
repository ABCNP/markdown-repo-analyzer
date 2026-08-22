"""Analyze a local repository of Markdown files."""
import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

MARKDOWN_SUFFIXES = {".md", ".markdown"}

@dataclass
class FileInfo:
    """记录单个 Markdown 文件的分析信息。"""
    path: Path
    size: int
    character_count: int
    modified_time: float

@dataclass
class AnalysisResult:
    """保存整个目录的 Markdown 分析结果。"""
    directory: Path
    files: list[FileInfo]
    total_character_count: int
    largest_file: FileInfo | None
    latest_file: FileInfo | None

def count_characters(text: str) -> int:
    """统计去除空白字符后的字符数量。"""
    return sum(not character.isspace() for character in text)

def scan_markdown_files(directory: Path) -> list[FileInfo]:
    """递归扫描目录，并读取所有 Markdown 文件的基础信息。"""
    if not directory.exists():
        raise FileNotFoundError(f"Directory does not exist: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")
    files = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in MARKDOWN_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
            stat = path.stat()
        except (OSError, UnicodeError) as exc:
            raise RuntimeError(f"Unable to read file {path}: {exc}") from exc
        files.append(FileInfo(path, stat.st_size, count_characters(text), stat.st_mtime))
    return files

def analyze_directory(directory: Path) -> AnalysisResult:
    """分析指定目录，返回文件数、总字数及最大和最近文件。"""
    files = scan_markdown_files(directory)
    return AnalysisResult(
        directory=directory,
        files=files,
        total_character_count=sum(item.character_count for item in files),
        largest_file=max(files, key=lambda item: item.size, default=None),
        latest_file=max(files, key=lambda item: item.modified_time, default=None),
    )

def format_size(size: int) -> str:
    """将文件字节数格式化为 B、KB 或 MB。"""
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.2f} KB"
    return f"{size / (1024 * 1024):.2f} MB"

def generate_report(result: AnalysisResult) -> str:
    """根据分析结果生成 Markdown 格式报告文本。"""
    lines = ["# Markdown Repository Analysis Report", "",
             f"- Directory: `{result.directory}`",
             f"- Markdown files: {len(result.files)}",
             f"- Total characters: {result.total_character_count:,}",
             f"- Generated at: {datetime.now():%Y-%m-%d %H:%M:%S}", "",
             "## Largest File", ""]
    largest = result.largest_file
    if largest:
        lines.extend([f"- File: `{largest.path}`", f"- Size: {format_size(largest.size)}"])
    else:
        lines.append("No Markdown files found.")
    lines.extend(["", "## Most Recently Modified File", ""])
    latest = result.latest_file
    if latest:
        lines.extend([f"- File: `{latest.path}`",
                       f"- Modified: {datetime.fromtimestamp(latest.modified_time):%Y-%m-%d %H:%M:%S}"])
    else:
        lines.append("No Markdown files found.")
    return "\n".join(lines) + "\n"

def main() -> int:
    """解析命令行参数并将分析报告写入文件。"""
    parser = argparse.ArgumentParser(description="Analyze a local Markdown repository")
    parser.add_argument("directory", type=Path, help="Directory to scan")
    parser.add_argument("-o", "--output", type=Path, default=Path("markdown-report.md"))
    args = parser.parse_args()
    try:
        args.output.write_text(generate_report(analyze_directory(args.directory)), encoding="utf-8")
    except (FileNotFoundError, NotADirectoryError, RuntimeError, OSError) as exc:
        parser.error(str(exc))
    print(f"Report generated: {args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
