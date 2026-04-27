# f-string 格式化深入

## 定义

f-string 是在**编译期**将字符串字面量解析为 AST 节点，在**运行时**对嵌入的花括号表达式求值并通过 `__format__` 协议转换为字符串的格式化机制。其本质是**运行时解释执行的字符串字面量**——编译阶段确定求值表达式，运行时动态解释执行。

## 数学模型

f-string 格式化是一个偏函数 $F: O \times \Sigma^* \rightharpoonup S$：
$$F(v, \text{spec}) = v.\__format\_\_(\text{spec})$$

格式规格符的形式语言（EBNF）：
```
spec       ::= [[fill]align][sign][#][0][width][grouping][.prec][type]
type       ::= "b" | "c" | "d" | "e" | "E" | "f" | "F" | "g" | "G" | "n" | "o" | "s" | "x" | "X" | "%"
```

**求值时机对比**：

| 机制 | 求值时机 | 表达力 | 性能 |
|------|----------|--------|------|
| f-string | 运行时（动态） | 任意 Python 表达式 | 每次调用重新求值 |
| `str.format()` | 运行时（索引/关键字） | 受限于 `{0[key]}` 槽位 | 相同 |
| 预计算常量 | 编译期（静态） | 无表达式 | 最优 |

**归约终点**：f-string 的求值可归约为**字节码解释执行的表达式求值**——编译器生成 `LOAD_NAME`/`FORMAT_VALUE`/`BUILD_STRING` 指令序列，运行时由 Python 虚拟机解释执行这些指令。格式化协议 `__format__` 是 Python 鸭子类型系统在格式化场景的具体体现。

## 数据流

<pre>
源码: f"{expr:spec}"         词法/语法分析
      │                            │
      ▼                            ▼
  JoinedStr 节点              AST（编译期产物）
  ├── Constant（常量片段）         │
  └── FormattedValue            │
       ├── value: Name(expr)    │
       └── format_spec          │
                               ▼
                           字节码生成
  ┌─────────────────────────────────────┐
  │ LOAD_NAME expr                       │
  │ LOAD_CONST spec                      │
  │ FORMAT_VALUE (flags=0)               │ ← 调用 __format__
  │ BUILD_STRING 1                       │
  └─────────────────────────────────────┘
                               │
                               ▼
                          运行时求值
  ┌─────────────────────────────────────┐
  │ 1. 查找 expr 名字 → 对象 v          │
  │ 2. 调用 v.__format__(spec)          │
  │ 3. 结果字符串压栈                    │
  │ 4. BUILD_STRING 拼接所有片段         │
  └─────────────────────────────────────┘
                               │
                               ▼
                          输出字符串
</pre>

**f-string vs str.format 关键差异**：
- `f"{x}"`：在运行时，`x` 作为变量名直接查值，执行 `x.__format__("")`
- `"{0}".format(x)`：在运行时，`0` 作为位置索引查参数字典，执行 `x.__format__("")`
- 两者最终都调用 `__format__` 协议，但 f-string 的表达式是**直接求值**，str.format 是**间接索引**

## 机制

### FORMAT_VALUE 字节码的执行路径

`FORMAT_VALUE` 字节码指令的精确执行步骤：
1. 弹出栈顶的 `format_spec` 对象（字符串）
2. 弹出栈顶的 `value` 对象（待格式化值）
3. 若 `value` 是字符串且有转换标志（`!r`、`!s`、`!a`），执行预转换
4. 调用 `value.__format__(format_spec)`（或 `format(value, format_spec)`）
5. 将返回的字符串压回栈顶

**关键约束**：若对象没有 `__format__` 方法：
- Python 3.12+：调用 `__str__` 作为后备
- Python 3.11 及之前：抛出 `TypeError`

### 格式化规格符的设计动机

格式规格符的设计遵循**正交性原则**——每个子选项（对齐、填充、精度、类型）独立生效，组合时叠加效果。这种设计使得宽度的语义清晰：`width` 指定**总宽度**，不包括格式规格符本身的部分。

```python
# 宽度 vs 精度的边界
f"{'abc':>10.2}"     # 总宽度10，精度2（截断到2字符）→ "       ab"
f"{3.14159:10.2f}"   # 总宽度10，精度2位小数 → "     3.14"
# 注意：字符串精度的含义是最大字符数，数字精度的含义是小数位数
```

### datetime 的双重格式语义

`datetime.__format__` 内部逻辑是一个**二分支判定**：

```python
def __format__(self, format_spec):
    if any(c in format_spec for c in "%y%Y%m%d%H%M%S"):
        return self.strftime(format_spec)  # strftime 路径
    return super().__format__(format_spec)  # 宽度/对齐路径
```

这意味着 `%Y` 和 `>` 不能同时用于 datetime——strftime 格式规格符与通用对齐规格符是**互斥的**，不能混合使用。

### 调试格式 `{x=}` 的展开原理

`{x=}` 不是独立语法结构，而是词法分析器在扫描阶段将 `{x=}` 替换为字面量字符串 `x=x` 的前缀部分，AST 中 `FormattedValue` 节点携带 `conversion=-1` 标记。编译器在生成字节码时检测此标记，在格式化值后面追加输出变量名文本。

### 转义的精确语义

`{{` 在词法阶段被识别为转义序列（替换为单个 `{` 存入字符串 token），发生在语法分析之前。这保证了 `{{x}}` 产生字面量 `{x}`，而不是 `{` 后跟变量 `x` 再跟 `}`。

## 参考存根

```python
from datetime import datetime

# f-string vs str.format 对比
x = "hello"
f"{x}"           # 直接查变量，求值
"{0}".format(x)  # 按位置索引，间接查参数字典

# 调试格式
value = 42
f"{value=}"      # "value=42"

# datetime 双重语义（不能混用 strftime 和对齐）
dt = datetime(2024, 7, 15, 14, 30)
f"{dt:%Y-%m-%d}"    # "2024-07-15" — strftime 路径
f"{dt:%B %d, %Y}"   # "July 15, 2024" — strftime 路径
# f"{dt:%Y->10}"     # 错误：不能混用 strftime 和对齐

# 自定义 __format__
class Vector:
    def __init__(self, x, y):
        self.x, self.y = x, y
    def __format__(self, spec):
        if spec == "p":
            import math
            r = math.hypot(self.x, self.y)
            theta = math.atan2(self.y, self.x)
            return f"({r:.2f}∠{theta:.2f})"
        return f"({self.x}, {self.y})"

v = Vector(3, 4)
f"{v}"    # "(3, 4)"
f"{v:p}"  # "(5.00∠0.93)"
```
