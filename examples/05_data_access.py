"""
示例：访问和操作 Library 数据

演示 Library 和 Entry 对象的各种访问方法。
"""

import sys

sys.path.insert(0, "..")  # 将上级目录添加到 sys.path 以导入 bibtexparser

from bibtexparser import parse

BIB_CONTENT = """
@article{smith2023,
    author = {John Smith and Jane Doe},
    title = {Machine Learning Study},
    journal = {Nature},
    year = {2023},
    volume = {100},
    pages = {1-20},
}

@book{wilson2021,
    author = {Bob Wilson},
    title = {Deep Learning},
    publisher = {MIT Press},
    year = {2021},
    isbn = {978-0-262-04630-5},
}

@inproceedings{doe2022,
    author = {Jane Doe},
    title = {Computer Vision},
    booktitle = {CVPR},
    year = {2022},
    pages = {100-110},
}
"""

print("=" * 60)
print("Library 和 Entry 数据访问示例")
print("=" * 60)
print()

library = parse(BIB_CONTENT)

# 1. Library 基本操作
print("1. Library 基本操作")
print("-" * 40)
print(f"   条目数量: len(library) = {len(library)}")
print(f"   所有键名: library.keys() = {library.keys()}")
print()

# 2. 检查条目是否存在
print("2. 检查条目是否存在 (in 运算符)")
print("-" * 40)
print(f"   'smith2023' in library = {'smith2023' in library}")
print(f"   'unknown' in library = {'unknown' in library}")
print()

# 3. 按键名获取条目
print("3. 按键名获取条目 (get_entry)")
print("-" * 40)
entry = library.get_entry("smith2023")
if entry:
    print(f"   library.get_entry('smith2023') = Entry(key='{entry.key}', type='{entry.entry_type}')")
not_found = library.get_entry("unknown")
print(f"   library.get_entry('unknown') = {not_found}")
print()

# 4. 遍历所有条目
print("4. 遍历所有条目 (for entry in library)")
print("-" * 40)
for entry in library:
    print(f"   {entry.key}: @{entry.entry_type}")
print()

# 5. Entry 字段访问
print("5. Entry 字段访问")
print("-" * 40)
entry = library.entries[0]
print(f"   entry.key = '{entry.key}'")
print(f"   entry.entry_type = '{entry.entry_type}'")
print(f"   entry.get('author') = '{entry.get('author')}'")
print(f"   entry.get('missing', 'default') = '{entry.get('missing', 'default')}'")
print()

# 6. 字段存在性检查
print("6. 字段存在性检查 (in 运算符)")
print("-" * 40)
print(f"   'author' in entry = {'author' in entry}")
print(f"   'abstract' in entry = {'abstract' in entry}")
# 大小写不敏感
print(f"   'AUTHOR' in entry = {'AUTHOR' in entry}  # 大小写不敏感")
print()

# 7. 使用 [] 访问字段
print("7. 使用 [] 访问字段")
print("-" * 40)
print(f"   entry['title'] = '{entry['title']}'")
print(f"   entry['year'] = '{entry['year']}'")
try:
    _ = entry["missing"]
except KeyError as e:
    print(f"   entry['missing'] → KeyError: {e}")
print()

# 8. 访问 Field 对象详细信息
print("8. 访问 Field 对象详细信息")
print("-" * 40)
author_field = entry.fields["author"]
print(f"   field.key = '{author_field.key}'")
print(f"   field.value = '{author_field.value}'")
print(f"   field.line = {author_field.line}  # 源文件行号")
print()

# 9. 按条目类型筛选
print("9. 按条目类型筛选")
print("-" * 40)
articles = [e for e in library if e.entry_type == "article"]
books = [e for e in library if e.entry_type == "book"]
print(f"   Articles: {[e.key for e in articles]}")
print(f"   Books: {[e.key for e in books]}")
print()

# 10. 按年份排序
print("10. 按年份排序")
print("-" * 40)
sorted_entries = sorted(library.entries, key=lambda e: e.get("year", "0"))
for entry in sorted_entries:
    print(f"   {entry.get('year')}: {entry.key}")
