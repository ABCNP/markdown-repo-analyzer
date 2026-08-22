"""Analyze a local repository of Markdown files."""
import argparse
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

MARKDOWN_SUFFIXES = {".md", ".markdown"}
LONG_FILE_THRESHOLD = 10000

@dataclass
class FileInfo:
    """记录单个 Markdown 文件的分析信息。"""
    path: Path
    size: int
    character_count: int
    modified_time: float
    heading_count: int
    code_block_count: int
    link_count: int
    image_count: int

@dataclass
class AnalysisResult:
    """保存整个目录的 Markdown 分析结果。"""
    directory: Path
    files: list[FileInfo]
    total_character_count: int
    largest_file: FileInfo | None
    latest_file: FileInfo | None
    warnings: list[str]
    total_size: int
    average_character_count: float
    directory_statistics: dict[str, dict[str, int]]
    empty_files: list[Path]
    total_heading_count: int
    total_code_block_count: int
    long_files: list[Path]
    broken_links: list[str]

def count_characters(text: str) -> int:
    """统计去除空白字符后的字符数量。"""
    return sum(not character.isspace() for character in text)

def count_headings(text: str) -> int:
    """统计 Markdown ATX 标题行数量。"""
    return sum(line.lstrip().startswith("#") for line in text.splitlines())

def count_code_blocks(text: str) -> int:
    """统计 Markdown 代码块数量。"""
    fence_count = sum(line.strip().startswith("```") for line in text.splitlines())
    return fence_count // 2

def extract_links(text: str) -> tuple[int, int, list[str]]:
    """统计链接和图片，并返回无法找到的本地链接。"""
    image_targets = re.findall(r"!\[[^]]*\]\(([^)]+)\)", text)
    link_targets = re.findall(r"(?<!!)\[[^]]*\]\(([^)]+)\)", text)
    return len(link_targets), len(image_targets), link_targets

def scan_markdown_files(directory: Path, warnings: list[str] | None = None) -> list[FileInfo]:
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
            message = f"Unable to read file {path}: {exc}"
            if warnings is None:
                raise RuntimeError(message) from exc
            warnings.append(message)
            continue
        link_count, image_count, link_targets = extract_links(text)
        for target in link_targets:
            target = target.split("#", 1)[0].strip().strip("<>")
            if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            if not (path.parent / target).exists() and warnings is not None:
                warnings.append(f"Broken local link in {path}: {target}")
        files.append(FileInfo(path, stat.st_size, count_characters(text), stat.st_mtime,
                              count_headings(text), count_code_blocks(text),
                              link_count, image_count))
    return files

def analyze_directory(directory: Path) -> AnalysisResult:
    """分析指定目录，返回文件数、总字数及最大和最近文件。"""
    warnings: list[str] = []
    files = scan_markdown_files(directory, warnings)
    directory_statistics: dict[str, dict[str, int]] = {}
    empty_files: list[Path] = []
    long_files: list[Path] = []
    for item in files:
        if item.character_count == 0:
            empty_files.append(item.path)
        if item.character_count >= LONG_FILE_THRESHOLD:
            long_files.append(item.path)
        relative_directory = item.path.parent.relative_to(directory)
        directory_name = str(relative_directory) if str(relative_directory) != "." else "."
        statistics = directory_statistics.setdefault(
            directory_name, {"file_count": 0, "character_count": 0, "size": 0}
        )
        statistics["file_count"] += 1
        statistics["character_count"] += item.character_count
        statistics["size"] += item.size
    return AnalysisResult(
        directory=directory,
        files=files,
        total_character_count=sum(item.character_count for item in files),
        largest_file=max(files, key=lambda item: item.size, default=None),
        latest_file=max(files, key=lambda item: item.modified_time, default=None),
        warnings=warnings,
        total_size=sum(item.size for item in files),
        average_character_count=(
            sum(item.character_count for item in files) / len(files) if files else 0
        ),
        directory_statistics=directory_statistics,
        empty_files=empty_files,
        total_heading_count=sum(item.heading_count for item in files),
        total_code_block_count=sum(item.code_block_count for item in files),
        long_files=long_files,
        broken_links=[warning for warning in warnings if warning.startswith("Broken local link")],
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
             f"- Total file size: {format_size(result.total_size)}",
             f"- Average characters per file: {result.average_character_count:.2f}",
             f"- Warnings: {len(result.warnings)}",
             f"- Total headings: {result.total_heading_count}",
             f"- Total code blocks: {result.total_code_block_count}",
             f"- Broken local links: {len(result.broken_links)}",
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
    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in result.warnings)
    lines.extend(["", "## Empty Files", "", f"- Count: {len(result.empty_files)}"])
    if result.empty_files:
        lines.extend(f"- File: `{path}`" for path in result.empty_files)
    lines.extend(["", "## Long Files", "", f"- Count: {len(result.long_files)}"])
    if result.long_files:
        lines.extend(f"- File: `{path}`" for path in result.long_files)
    lines.extend(["", "## Directory Summary", "", "| Directory | Files | Characters | Size |",
                   "|---|---:|---:|---:|"])
    if result.directory_statistics:
        for directory, statistics in sorted(result.directory_statistics.items()):
            lines.append(
                f"| `{directory}` | {statistics['file_count']} | "
                f"{statistics['character_count']:,} | {format_size(statistics['size'])} |"
            )
    else:
        lines.append("| No Markdown files | 0 | 0 | 0 B |")
    lines.extend(["", "## File Details", "", "| File | Characters | Headings | Code blocks | Links | Images |",
                   "|---|---:|---:|---:|---:|---:|"])
    for item in result.files:
        lines.append(f"| `{item.path}` | {item.character_count:,} | {item.heading_count} | "
                     f"{item.code_block_count} | {item.link_count} | {item.image_count} |")
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
