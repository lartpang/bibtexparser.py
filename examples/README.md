# bibtexparser 示例

本目录包含多个示例脚本，演示 bibtexparser 库的各种功能。

## 示例列表

| 文件                                                 | 描述                      |
| ---------------------------------------------------- | ------------------------- |
| [01_basic_formatting.py](01_basic_formatting.py)     | 基本解析和格式化选项      |
| [02_error_tolerance.py](02_error_tolerance.py)       | 容错解析功能              |
| [03_string_definitions.py](03_string_definitions.py) | @string 定义和字符串拼接  |
| [04_transformers.py](04_transformers.py)             | 使用转换器标准化数据      |
| [05_data_access.py](05_data_access.py)               | Library 和 Entry 数据访问 |

## 运行示例

```bash
cd examples

python 01_basic_formatting.py
python 02_error_tolerance.py
# ...
```

## 格式化选项速查表

```python
from bibtexparser.formatters import FormattingOptions, Case, ValueWrapper, EntryDelimiter

options = FormattingOptions(
    # 缩进
    indent=2,                              # 缩进空格数 (负数使用 tab)

    # 大小写
    entry_type_case=Case.LOWER,            # @article (LOWER/UPPER/TITLE/PRESERVE)
    field_name_case=Case.LOWER,            # author = ...

    # 值包裹方式
    value_wrapper=ValueWrapper.BRACES,     # {value} (BRACES/QUOTES)

    # 分隔符
    entry_delimiter=EntryDelimiter.BRACES, # @article{...} (BRACES/PARENS)

    # 逗号
    trailing_comma=True,                   # 最后一个字段后是否有逗号

    # 对齐
    align_values=False,                    # 是否对齐所有等号

    # 排序
    sort_fields=False,                     # 是否按字母排序字段
    field_order=["author", "title"],       # 自定义字段顺序

    # 其他
    entry_separator=1,                     # 条目之间的空行数
)
```
