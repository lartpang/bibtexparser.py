"""
示例：基本解析和格式化

演示如何解析 BibTeX 文件并使用不同的格式化选项输出。
"""

import sys

sys.path.insert(0, "..")  # 将上级目录添加到 sys.path 以导入 bibtexparser

from bibtexparser import parse
from bibtexparser.formatters import (
    AlignedFormatter,
    BibtexFormatter,
    Case,
    CompactFormatter,
    EntryDelimiter,
    FormattingOptions,
    ValueWrapper,
)

# 示例 BibTeX 内容
SAMPLE_BIB = """
@article{smith2023,
    AUTHOR = {John Smith and Jane Doe},
    TITLE = {A Comprehensive Study of Machine Learning},
    JOURNAL = {IEEE Transactions on Neural Networks},
    YEAR = {2023},
    VOLUME = {34},
    PAGES = {1234-1256},
}

@book{wilson2021,
    author = {Bob Wilson},
    title = {Introduction to Algorithms},
    publisher = {MIT Press},
    year = {2021},
}
"""

# 1. 基本解析
print("=" * 60)
print("1. 基本解析")
print("=" * 60)

library = parse(SAMPLE_BIB)
print(f"解析了 {len(library)} 个条目:")
for entry in library:
    print(f"  - [{entry.entry_type}] {entry.key}")
    print(f"      Author: {entry.get('author', 'N/A')}")
    print(f"      Title: {entry.get('title', 'N/A')}")
print()

# 2. 默认格式化
print("=" * 60)
print("2. 默认格式化输出")
print("=" * 60)

formatter = BibtexFormatter()
print(formatter.format(library))
print()

# 3. 自定义大小写
print("=" * 60)
print("3. 大写条目类型 + 小写字段名")
print("=" * 60)

options = FormattingOptions(
    entry_type_case=Case.UPPER,  # @ARTICLE, @BOOK
    field_name_case=Case.LOWER,  # author, title
)
formatter = BibtexFormatter(options)
print(formatter.format_entry(library.entries[0]))
print()

# 4. 使用引号而非花括号
print("=" * 60)
print("4. 使用引号包裹值")
print("=" * 60)

options = FormattingOptions(
    value_wrapper=ValueWrapper.QUOTES,  # "value" 而非 {value}
)
formatter = BibtexFormatter(options)
print(formatter.format_entry(library.entries[0]))
print()

# 5. 使用圆括号分隔符
print("=" * 60)
print("5. 使用圆括号分隔符")
print("=" * 60)

options = FormattingOptions(
    entry_delimiter=EntryDelimiter.PARENS,  # @article(...) 而非 @article{...}
)
formatter = BibtexFormatter(options)
print(formatter.format_entry(library.entries[0]))
print()

# 6. 对齐格式化（所有等号对齐）
print("=" * 60)
print("6. 对齐格式化 (AlignedFormatter)")
print("=" * 60)

formatter = AlignedFormatter(indent=4)
print(formatter.format_entry(library.entries[0]))
print()

# 7. 紧凑格式化（单行输出）
print("=" * 60)
print("7. 紧凑格式化 (CompactFormatter)")
print("=" * 60)

formatter = CompactFormatter()
print(formatter.format(library))
print()

# 8. 自定义字段顺序
print("=" * 60)
print("8. 自定义字段顺序 (author, title, year 优先)")
print("=" * 60)

options = FormattingOptions(
    field_order=["author", "title", "year"],  # 这些字段优先显示
    trailing_comma=True,
)
formatter = BibtexFormatter(options)
print(formatter.format_entry(library.entries[0]))
print()

# 9. 排序字段（按字母顺序）
print("=" * 60)
print("9. 按字母顺序排序字段")
print("=" * 60)

options = FormattingOptions(
    sort_fields=True,
    trailing_comma=False,
)
formatter = BibtexFormatter(options)
print(formatter.format_entry(library.entries[0]))
print(formatter.format_entry(library.entries[0]))
