"""Analyze a local repository of Markdown files."""
import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

MARKDOWN_SUFFIXES = {".md", ".markdown"}

@dataclass
class FileInfo:
    path: Path
    size: int
    character_count: int
    modified_time: float

def count_characters(text: str) -> int:
    return sum(not character.isspace() for character in text)

def scan_markdown_files(directory: Path) -> list[FileInfo]:
    if not directory.exists():
        raise FileNotFoundError(f"目录不存在: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"不是目录: {directory}")
    files = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in MARKDOWN_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
            stat = path.stat()
        except (OSError, UnicodeError) as exc:
            raise RuntimeError(f"无法读取文件 {path}: {exc}") from exc
        files.append(FileInfo(path, stat.st_size, count_characters(text), stat.st_mtime))
    return files

def analyze_directory(directory: Path) -> dict:
    files = scan_markdown_files(directory)
    return {"directory": directory, "files": files,
            "total_character_count": sum(item.character_count for item in files),
            "largest_file": max(files, key=lambda item: item.size, default=None),
            "latest_file": max(files, key=lambda item: item.modified_time, default=None)}

def format_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.2f} KB"
    return f"{size / (1024 * 1024):.2f} MB"

def generate_report(result: dict) -> str:
    lines = ["# Markdown 仓库分析报告", "",
             f"- 扫描目录：`{result['directory']}`",
             f"- Markdown 文件数：{len(result['files'])}",
             f"- 总字数：{result['total_character_count']:,}",
             f"- 报告生成时间：{datetime.now():%Y-%m-%d %H:%M:%S}", "",
             "## 最大文件", ""]
    largest = result["largest_file"]
    if largest:
        lines.extend([f"- 文件：`{largest.path}`", f"- 文件大小：{format_size(largest.size)}"])
    else:
        lines.append("暂无 Markdown 文件。")
    lines.extend(["", "## 最近修改文件", ""])
    latest = result["latest_file"]
    if latest:
        lines.extend([f"- 文件：`{latest.path}`",
                       f"- 修改时间：{datetime.fromtimestamp(latest.modified_time):%Y-%m-%d %H:%M:%S}"])
    else:
        lines.append("暂无 Markdown 文件。")
    return "\n".join(lines) + "\n"

def main() -> int:
    parser = argparse.ArgumentParser(description="分析本地 Markdown 文件仓库")
    parser.add_argument("directory", type=Path, help="要扫描的目录")
    parser.add_argument("-o", "--output", type=Path, default=Path("markdown-report.md"))
    args = parser.parse_args()
    try:
        args.output.write_text(generate_report(analyze_directory(args.directory)), encoding="utf-8")
    except (FileNotFoundError, NotADirectoryError, RuntimeError, OSError) as exc:
        parser.error(str(exc))
    print(f"报告已生成：{args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
