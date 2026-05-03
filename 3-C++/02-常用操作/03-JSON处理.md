# JSON处理

## 定义

JSON 处理是将 C++ 的类型系统（结构体、容器、枚举）与 JSON 的嵌套树结构（object/array/string/number/boolean/null）进行**结构保持的双射**过程。核心挑战在于类型系统的异构性（JSON 是动态类型，C++ 是静态强类型）以及序列化/反序列化过程中的所有权转移与错误恢复。

## 数学模型

### JSON解析的状态机（递归下降）

JSON 解析器本质上是 JSON 语法对应的**下推自动机（PDA）**。语法规则：

$$
\begin{aligned}
\text{value} &::= \text{object} \mid \text{array} \mid \text{string} \mid \text{number} \mid \text{true} \mid \text{false} \mid \text{null} \\
\text{object} &::= \text{`{' ws `}'} \mid \text{`{' members `}'} \\
\text{array} &::= \text{`[' ws `]'} \mid \text{`[' elements `]'} \\
\text{members} &::= \text{member} \mid \text{member `,' members} \\
\text{elements} &::= \text{value} \mid \text{value `,' elements}
\end{aligned}
$$

解析器对每个非终结符维护一个递归调用栈帧，栈深度等于 JSON 嵌套层数 $D$ 。解析复杂度 $O(N)$ ，其中 $N$ 是 JSON 文本字节数（每个字节只被处理一次）。

### nlohmann/json的ADL序列化查找

nlohmann/json 的序列化通过 **ADL**（Argument-Dependent Lookup，参数依赖查找）实现：

```cpp
// 当调用 to_json(j, obj) 时，编译器查找：
namespace adl_serializer {
    // 1. 首先在 obj 类型的命名空间中查找 to_json
    // 2. 若找不到，在 nlohmann::detail 命名空间中查找
}
```

ADL 使得为任意用户类型提供 `to_json/from_json` 特化时，无需显式声明依赖——只需在类型所在命名空间内定义或特化。

**查找路径的数学描述**：对类型 `T`，编译器构造候选函数集合 $S(T)$ ：

$$
S(T) = \{ f \mid f \in (\text{T}\text{的命名空间}) \cup (\text{T}\text{的模板实参的命名空间}) \}
$$

## 数据流

### JSON → C++ 反序列化数据流

<pre>
JSON 文本字节流       词法分析器            语法分析器（栈）         C++ 对象
+----------------+   +---------------+   +------------------+   +------------+
| "{"name":"Alice|   |  字符串token  |   |  ObjectState     |   | Person     |
| ,"age":30}"    | ─>  冒号 token  | ─>  KeyState        |   | {name:"A", |
| (字节序列)       |   数字 token    |   ValueState       |   |  age:30}   |
+----------------+   +---------------+   +------------------+   +------------+
     │                      │                    │                    │
     └── 字节 → token ──────┘ 所有权：lexer ───┘ 所有权：parser ───┘ 所有权：调用者
</pre>

**所有权流转**：
1. 词法分析器（lexer）将字节流切分为 token sequence，所有权归 parser。
2. 语法分析器（parser）按语法规则归约 token，构建中间表示（DOM tree），所有权归解析器。
3. `from_json` 将 DOM 节点的值拷贝/移动到目标 C++ 对象，完成数据提取。

### to_json/from_json 的 ADL 查找路径

<pre>
json j = person;
         │
         │  调用 to_json(j, person)
         │
         ▼
   ADL 查找 to_json
         │
         ├──> 在 person 类型所在命名空间查找
         │        ↓
         │    找到：to_json(json&, const Person&)
         │
         └──> 未找到：在 nlohmann::detail 查找 fallback
                  （处理基本类型）
</pre>

### JSON Schema 验证的状态机

JSON Schema 验证器对每个 JSON 值运行一系列断言，每个断言是一个**谓词函数**：

$$
\text{validate}(v, \text{schema}) = \bigwedge_{i} p_i(v, \text{schema}_i)
$$

其中 $p_i$ 可以是：类型检查（ $v.\text{type} == \text{schema.type}$ ）、值域检查（$v > \text{minimum}$）、枚举约束（$v \in \text{enum}$）、格式约束（正则表达式匹配）。任何 $p_i$ 为假则整体验证失败。

## 机制

### JSON Schema 的递归验证深度

JSON Schema 支持嵌套引用（`$ref`），验证器通过**递归**处理嵌套 schema。设 JSON 文档嵌套深度为 $D_{json}$，Schema 嵌套深度为 $D_{schema}$，最坏情况下的递归调用栈深度为：

$$
D_{max} = D_{json} \times D_{schema}
$$

这意味着恶意构造的深层嵌套 JSON 可导致栈溢出（Stack Overflow）。`$ref` 循环引用检测是防止无限递归的关键。

### JSONPatch 与 merge_patch 的语义差异

**JSONPatch（RFC 6902）**：操作序列式应用，支持 `add`/`remove`/`replace`/`move`/`copy`/`test`。语义是**有序的、确定性的转换**。

**merge_patch（RFC 7386）**：
- `null` 值：**删除**目标中的对应键。
- 非 `null` 值：**替换**目标中的对应值（若目标是 object，则递归合并）。

$$
\text{patch\_apply}(target, patch) = \begin{cases}
\text{recursive\_merge}(target, patch) & \text{若 patch 是 object} \\
patch & \text{否则（直接替换）}
\end{cases}
$$

其中 `recursive_merge` 的语义：对于 `patch` 中的每个键值对 $(k, v)$ ，若 $v$ 为 `null` 则从 `target` 删除 $k$ ，否则用 $v$ 覆盖 `target[k]`（若 $target[k]$ 也是 object 且 $v$ 是 object，则递归合并）。

### JSON 的数值精度问题

JSON 标准不限定数值的精度。C++ `double`（IEEE 754 双精度）有 53 位尾数精度（约 15-16 位十进制有效数字）。大于 $2^{53}$ （9007199254740992）的整数经 JSON 往返后可能丢失精度：

$$
\text{精度损失} = \left| x - \text{round}\left(\frac{x}{2^{53-x.\text{exponent}}}\right) \times 2^{53-x.\text{exponent}} \right|
$$

对于需要精确整数的场景（如金融数据），应使用字符串传输数值，在 C++ 端使用 `std::string` 或专用高精度库（如 `boost::multiprecision::cpp_int`）解析。

### JSONPath 的查询模型

JSONPath 表达式等价于在 JSON DOM 树上的**路径遍历+过滤**操作：

$$
\text{query}(j, p) = \{ v \mid \text{extract}(j, p) = v \}
$$

例如 `$.store.book[*].author` 等价于：
1. 找到根节点的 `store` 键 → `book` 键。
2. 对 `book` 数组的每个元素，取 `author` 字段。
3. 收集所有 `author` 值。

`*` 是通配符，遍历所有数组元素；`..` 是递归下降运算符，不限制树深度。

## 参考存根

```cpp
// 展示 ADL 机制：为自定义类型添加序列化
struct Point { double x, y; };

// 在 Point 所在命名空间定义 to_json/from_json
namespace geo {
    void to_json(nlohmann::json& j, const Point& p) {
        j = nlohmann::json{{"x", p.x}, {"y", p.y}};
    }
    void from_json(const nlohmann::json& j, Point& p) {
        p.x = j.at("x").get<double>();
        p.y = j.at("y").get<double>();
    }
}

// ADL 在 geo 命名空间找到上述定义
Point pt{1.5, 2.5};
nlohmann::json j = pt;  // 调用 geo::to_json
Point pt2 = j.get<Point>();  // 调用 geo::from_json
```
