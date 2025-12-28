# bibtexparser

一个功能完整的 BibTeX 解析器，支持容错解析、中间表示（IR）层，以及可配置的输出格式化选项。

## 特性

- **容错解析**：能够处理格式不规范的 BibTeX 文件，解析失败的条目会被记录而不会中断整个解析过程
- **中间表示**：使用结构化的数据类表示 BibTeX 库，便于程序化操作
- **可配置格式化**：支持多种输出格式选项
  - 大小写控制（条目类型、字段名）
  - 括号样式（花括号 `{}` 或圆括号 `()`）
  - 值包裹方式（花括号 `{}` 或引号 `""`）
  - 缩进和对齐选项

## 快速开始

```python
from bibtexparser import parse
from bibtexparser.formatters import BibtexFormatter, FormattingOptions

# 解析 BibTeX 文件
with open("refs.bib", "r", encoding="utf-8") as f:
    library = parse(f.read())

# 查看解析结果
print(f"成功解析 {len(library.entries)} 个条目")
if library.failed_blocks:
    print(f"解析失败 {len(library.failed_blocks)} 个块")

# 自定义格式化输出
options = FormattingOptions(
    indent=4,
    entry_type_case="lower",      # article, book, ...
    field_name_case="lower",      # author, title, ...
    value_wrapper="braces",       # {value} 或 "value"
    trailing_comma=True,
)
formatter = BibtexFormatter(options)
output = formatter.format(library)
print(output)
```
