"""
示例：@string 定义和字符串拼接

演示如何使用 @string 定义和 # 运算符进行字符串拼接。
"""

import sys

sys.path.insert(0, "..")  # 将上级目录添加到 sys.path 以导入 bibtexparser

from bibtexparser import parse
from bibtexparser.formatters import BibtexFormatter, FormattingOptions

# 包含 @string 定义的 BibTeX 内容
BIB_WITH_STRINGS = """
% 定义常用的期刊和会议名称缩写
@string{ieee = {IEEE}}
@string{acm = {ACM}}
@string{tnn = {Transactions on Neural Networks}}
@string{cvpr = {Conference on Computer Vision and Pattern Recognition}}

% 使用 @string 和字符串拼接
@article{paper1,
    author = {John Smith},
    title = {Deep Learning Methods},
    journal = ieee # " " # tnn,
    year = {2023},
}

@inproceedings{paper2,
    author = {Jane Doe},
    title = {Vision Transformers},
    booktitle = ieee # "/" # acm # " " # cvpr,
    year = {2022},
}
"""

print("=" * 60)
print("@string 定义和字符串拼接示例")
print("=" * 60)
print()

# 解析
library = parse(BIB_WITH_STRINGS)

# 显示解析到的 @string 定义
print("解析到的 @string 定义:")
print("-" * 40)
for key, string_def in library.strings.items():
    print(f"  {key} = {{{string_def.value}}}")
print()

# 显示条目（字符串已展开）
print("解析后的条目（字符串已展开）:")
print("-" * 40)
for entry in library.entries:
    print(f"\n[{entry.entry_type}] {entry.key}")
    for field in entry.fields.values():
        print(f"    {field.key} = {field.value}")
print()

# 格式化输出（会包含展开后的字符串）
print("格式化输出:")
print("-" * 40)
formatter = BibtexFormatter()
print(formatter.format(library))
