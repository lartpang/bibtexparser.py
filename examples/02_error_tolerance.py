"""
示例：容错解析

演示解析器如何处理格式不规范的 BibTeX 文件。
"""

import sys

sys.path.insert(0, "..")  # 将上级目录添加到 sys.path 以导入 bibtexparser

from bibtexparser import parse
from bibtexparser.formatters import BibtexFormatter

# 包含错误的 BibTeX 内容
MALFORMED_BIB = """
% 这是一个包含各种问题的 BibTeX 文件

@article{good1,
    author = {Good Author},
    title = {This Entry is Valid},
    year = {2023},
}

% 这个条目缺少闭合花括号 - 会作为失败块记录
@article{broken,
    author = {Test Author},
    title = {Missing Closing Brace

% 另一个有效条目
@book{good2,
    author = {Another Author},
    title = {Valid Book},
    publisher = {Publisher},
    year = {2022},
}

% 多余的逗号 - 解析器会容忍
@article{tolerant,
    author = {Test},,
    title = {Multiple Commas},,
}

% 缺少逗号的条目 - 解析器会尝试恢复
@misc{nocomma,
    author = {Test}
    title = {No Comma Between Fields}
}
"""

print("=" * 60)
print("容错解析示例")
print("=" * 60)
print()

# 解析包含错误的内容
library = parse(MALFORMED_BIB)

print(f"成功解析的条目数: {len(library.entries)}")
print(f"解析失败的块数: {len(library.failed_blocks)}")
print()

# 显示成功解析的条目
print("成功解析的条目:")
print("-" * 40)
for entry in library.entries:
    print(f"  [{entry.entry_type}] {entry.key}")
print()

# 显示解析失败的块
if library.failed_blocks:
    print("解析失败的块:")
    print("-" * 40)
    for block in library.failed_blocks:
        print(f"  Line {block.line}: {block.error_message}")
        # 显示失败块的原始文本（前50个字符）
        preview = block.raw_text[:50].replace("\n", " ")
        print(f"    Preview: {preview}...")
    print()

# 检查是否有错误
if library.has_errors:
    print("⚠️  解析过程中出现了一些问题，但仍然提取了有效条目。")
else:
    print("✓ 所有内容解析成功。")
print()

# 格式化输出成功解析的条目
print("格式化输出（仅成功解析的条目）:")
print("-" * 40)
formatter = BibtexFormatter()
print(formatter.format(library))
