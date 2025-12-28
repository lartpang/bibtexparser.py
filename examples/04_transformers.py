"""
示例：使用转换器（Transformers）

演示如何使用各种转换器来标准化和修改解析后的 Library。
"""

import sys

sys.path.insert(0, "..")  # 将上级目录添加到 sys.path 以导入 bibtexparser

from bibtexparser import parse
from bibtexparser.formatters import BibtexFormatter
from bibtexparser.transformers import (
    DuplicateKeyHandler,
    EntryTypeNormalizer,
    FieldFilter,
    FieldNormalizer,
    PageNormalizer,
    apply_transformers,
)

# 需要标准化的 BibTeX 内容
BIB_CONTENT = """
@ARTICLE{paper1,
    AUTHOR = {John Smith},
    Title = {First Paper},
    pages = {100-110},
    year = {2023},
    abstract = {This is a long abstract that we might want to remove...},
}

% 使用 conference 类型（应该转换为 inproceedings）
@Conference{paper2,
    author = {Jane Doe},
    title = {Second Paper},
    PAGES = {200 - 220},
    Year = {2022},
    keywords = {machine learning, deep learning},
}

% 重复的键名
@article{paper1,
    author = {Duplicate Key Author},
    title = {Duplicate Entry},
    year = {2021},
}
"""

print("=" * 60)
print("转换器 (Transformers) 示例")
print("=" * 60)
print()

# 解析
library = parse(BIB_CONTENT)
print(f"原始条目数: {len(library.entries)}")
print()

# 1. 字段名标准化（全部小写）
print("1. 字段名标准化 (FieldNormalizer)")
print("-" * 40)
library = FieldNormalizer(case="lower").transform(library)
entry = library.entries[0]
print(f"   字段名: {list(entry.fields.keys())}")
print()

# 2. 页码标准化（使用 -- 分隔）
print("2. 页码标准化 (PageNormalizer)")
print("-" * 40)
library = PageNormalizer(separator="--").transform(library)
for entry in library.entries:
    if "pages" in entry.fields:
        print(f"   {entry.key}: pages = {entry.get('pages')}")
print()

# 3. 条目类型标准化（处理别名）
print("3. 条目类型标准化 (EntryTypeNormalizer)")
print("-" * 40)
print("   Before:")
for entry in library.entries:
    print(f"     {entry.key}: {entry.entry_type}")
library = EntryTypeNormalizer(case="lower", resolve_aliases=True).transform(library)
print("   After:")
for entry in library.entries:
    print(f"     {entry.key}: {entry.entry_type}")
print()

# 4. 处理重复键名
print("4. 处理重复键名 (DuplicateKeyHandler)")
print("-" * 40)
print(f"   当前条目数: {len(library.entries)}")
# 使用 'rename' 策略给重复键添加后缀
library = DuplicateKeyHandler(strategy="rename").transform(library)
print(f"   处理后条目键: {[e.key for e in library.entries]}")
print()

# 5. 过滤字段（移除不需要的字段）
print("5. 过滤字段 (FieldFilter)")
print("-" * 40)
print("   移除 abstract 和 keywords 字段...")
library = FieldFilter(exclude=["abstract", "keywords"]).transform(library)
for entry in library.entries:
    print(f"   {entry.key}: {list(entry.fields.keys())}")
print()

# 使用 apply_transformers 一次性应用多个转换器
print("=" * 60)
print("使用 apply_transformers 一次性应用多个转换器")
print("=" * 60)

# 重新解析原始内容
library = parse(BIB_CONTENT)

# 一次性应用所有转换
library = apply_transformers(
    library,
    FieldNormalizer(case="lower"),
    PageNormalizer(separator="--"),
    EntryTypeNormalizer(case="lower"),
    DuplicateKeyHandler(strategy="keep_first"),  # 保留第一个重复项
    FieldFilter(exclude=["abstract", "keywords"]),
)

print(f"\n处理后的条目数: {len(library.entries)}")
print("\n格式化输出:")
formatter = BibtexFormatter()
print(formatter.format(library))
