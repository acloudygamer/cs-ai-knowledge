# JSON 处理

## 定义

JSON（JavaScript Object Notation）是 JavaScript 对象字面量语法的**一个严格子集**，被设计为轻量级数据交换格式。JavaScript 通过 `JSON.parse()` 将 JSON 字符串反序列化为对象（原生值：string/number/boolean/null/array/object），通过 `JSON.stringify()` 将对象序列化为 JSON 字符串。ES2024 的 `structuredClone` 提供了原生深拷贝能力，绕过了字符串中转。

## 数学模型

### 序列化复杂度

设对象图中的节点数为 $N$（对象/数组/原始值），序列化时间复杂度为 $\mathcal{O}(N)$：每个节点恰好访问一次。

字符串化后的长度与对象的结构相关：

$$
|JSON| = \mathcal{O}\left(\sum_{k \in K} (l_k + |v_k|) + K \cdot 2\right)
$$

其中 $K$ 为对象键数量，$l_k$ 为键长度，$|v_k|$ 为值长度（字符串值按引号内字符计）。

**JSON.stringify 特殊值处理**：

| 输入类型 | 对象属性行为 | 数组元素行为 | 单独参数行为 |
|----------|-------------|-------------|-------------|
| `undefined` | 跳过（不输出） | 输出 `null` | 输出 `undefined` |
| `Symbol` | 跳过 | 输出 `null` | 输出 `undefined` |
| `Function` | 跳过 | 输出 `null` | 输出 `undefined` |
| `BigInt` | 抛出 `TypeError` | 抛出 `TypeError` | 抛出 `TypeError` |
| 循环引用 | 抛出 `TypeError` | 抛出 `TypeError` | 抛出 `TypeError` |

### structuredClone 的能力边界

`structuredClone(value)` 使用**结构化克隆算法**（Structured Clone Algorithm），直接复制对象图而不经过字符串序列化。

**可复制类型**：
- 所有原生类型（除 `Symbol`）
- `Object`（包括 `Map`/`Set`/`Date`/`RegExp`/`ArrayBuffer`/`TypedArray`/`Blob`/`File`）
- 嵌套对象图

**不可复制类型**（抛出 `DataCloneError`）：
- `Function`（闭包无法序列化）
- DOM 节点（宿主对象具有循环引用）
- 闭包引用的外层变量

### JSON Merge Patch（RFC 7386）

JSON Merge Patch 定义了**最小 diff 语义**的部分更新操作：

$$
P_{patch}(D, P) = \begin{cases}
P & P \neq null \land P \neq \{\} \\
D \backslash P & P = null \lor (P = \{\} \land D\ is\ object) \\
null & P = null \land D\ is\ null
\end{cases}
$$

**语义解释**：
- `P = { k: v }`（$v \neq null, v \neq \{\}$）：递归合并或替换 `D[k]`
- `P = { k: null }`：删除 `D[k]`
- `P = \{\}`：清空 `D` 的所有键
- `P = null`：将 `D` 替换为 `null`

**语义歧义**：无法用 Merge Patch 表示"将值设为 `null`"的意图，因为 `null` 被解释为删除操作。

## 数据流

```
JSON.parse 流程：
字符串 → 词法分析（token 化）→ 解析器（递归下降）→ 对象构建
          ↓
    语法错误 → 抛出 SyntaxError

JSON.stringify 流程：
对象遍历（DFS）→ 字符串拼接 → 输出字符串
          ↓
    循环引用检测 → 跳过函数/Symbol/undefined 属性
    键值收集 → JSON 字符串构造 → 可选 replacer 过滤 → 可选 space 格式化

structuredClone 流程：
输入值 → 结构化克隆算法 → 目标内存区域 → 输出副本
          ↓
    不可克隆类型 → 抛出 DataCloneError

JSON Merge Patch 流程：
目标文档 D + 补丁 P → 遍历 P 键
    ├── P[k] = null → delete D[k]
    ├── P[k] = 原始值 → D[k] = P[k]
    └── P[k] = 复合对象 → 递归 applyMergePatch(D[k], P[k])

深合并流程：
target + source → 遍历 source 键
    ├── source[k] 是原始值 → target[k] = source[k]
    ├── source[k] 是数组 → target[k] = source[k]（替换，非合并）
    └── source[k] 是对象 → target[k] = deepMerge(target[k] || {}, source[k])
```

## 机制

### JSON.parse 的安全边界

`JSON.parse` 在 V8 引擎中由 **Scanner-Lexer-Parser** 三阶段实现：

1. **Scanner（词法分析）**：将输入字符串分解为 token 序列
2. **Lexer（语义分析）**：将 token 转换为中间表示
3. **Parser（解析）**：递归下降解析，输出 AST，再构建对象图

**解析器约束**：
- V8 默认嵌套深度限制约 10000 层，超出后抛出 `SyntaxError`
- JSON 语法严格：不允许尾随逗号、不支持注释、不支持单引号字符串
- 解析器不进行 schema 验证，合法 JSON 但不符合业务预期的数据会静默通过

**安全风险**：解析不可信 JSON 可能触发 ReDoS（正则表达式 denial of service）或内存耗尽。生产环境应使用 `reviver` 函数进行 schema 验证。

### JSON.stringify 的遍历语义

`JSON.stringify` 使用 **DFS 前序遍历**对象图：

$$
\text{Traverse}(obj, visited) = \begin{cases}
null & obj \in visited \lor obj \in \{undefined, Symbol, Function\} \\
"string" & typeof\ obj = string \\
number & typeof\ obj = number \\
boolean & typeof\ obj = boolean \\
JSON.stringify(obj) & typeof\ obj = object \land obj \neq null \\
undefined & otherwise
\end{cases}
$$

**循环引用检测**：遍历过程中维护"正在访问对象栈"以检测循环引用。若检测到循环，抛出 `TypeError: Converting circular structure to JSON`。

**replacer 参数的作用域**：

| 调用次数 | `this` | `k`（键） | `v`（值） |
|----------|--------|-----------|-----------|
| 首次 | 空对象 `{}` 或 replacer 函数自身 | 空字符串 `""` | 被序列化的对象 |
| 后续 | 当前属性所在对象 | 属性名 | 属性值 |

返回值 `undefined` 导致：
- 对象属性：跳过该属性（不输出）
- 数组元素：输出 `null`

### structuredClone 与 JSON 深拷贝的本质差异

**JSON 深拷贝路径**：
$$
obj \xrightarrow{JSON.stringify} json\_string \xrightarrow{JSON.parse} obj'
$$

**structuredClone 路径**：
$$
obj \xrightarrow{structuredClone} obj'
$$

两者差异：

| 维度 | JSON 深拷贝 | structuredClone |
|------|-------------|-----------------|
| 类型支持 | 原始类型 + 普通对象/数组 | 所有可序列化类型（含 Map/Set/Date/TypedArray）|
| 循环引用 | 不支持（抛异常）| 支持（深度遍历）|
| 精度问题 | 超过 `Number.MAX_SAFE_INTEGER` 的整数可能丢失精度 | 无精度问题 |
| 性能 | 需遍历两遍（序列化+反序列化）| 单次深度遍历 |
| 内存 | 需在内存中同时存在输入、字符串、输出 | 可原地构造 |

**约束**：`structuredClone` 不执行 getter/setter，仅复制值语义。

### JSON Merge Patch 的语义边界

**无法表示的意图**：
- "将键 `k` 的值设为 `null`" → Merge Patch 会删除键 `k`
- "将键 `k` 的值设为 `undefined`" → Merge Patch 会删除键 `k`

**替代方案**：若需精确控制 `null` 值，应使用 **JSON Patch（RFC 6902）**，支持 `add`/`remove`/`replace`/`move`/`copy`/`test` 六种操作。

### 深合并 vs 浅合并

**浅合并（Object.assign）**：
$$
M_{浅}(target, source) = target \cup \{ (k, source[k]) \mid k \in keys(source) \}
$$

**深合并（递归合并）**：
$$
M_{深}(target, source) = \begin{cases}
target & keys(source) = \emptyset \\
M_{深}(target[k], source[k]) \cup target & typeof\ source[k] = object \land source[k] \neq null \land typeof\ target[k] = object \land target[k] \neq null \\
source[k] \cup target & typeof\ source[k] = object \land source[k] \neq null \\
source & otherwise
\end{cases}
$$

**数组处理**：深合并不递归合并数组，而是替换（`source[k]` 覆盖 `target[k]`）。

## 参考存根

```javascript
// BigInt 序列化/反序列化（自定义 reviver/replacer）
const ser = (k, v) => typeof v === 'bigint' ? v.toString() : v;
const deser = (k, v) => typeof v === 'string' && /^\d+$/.test(v) ? BigInt(v) : v;
JSON.stringify(obj, ser); JSON.parse(str, deser);

// safeParse（防御性解析）
const safeParse = jsonString => {
  try {
    return { ok: true, data: JSON.parse(jsonString) };
  } catch (e) {
    return { ok: false, error: e.message };
  }
};

// structuredClone（深拷贝）
const clone = structuredClone(obj);

// JSON Merge Patch
const applyPatch = (doc, patch) => {
  if (patch === null) return null;
  const r = Array.isArray(doc) ? [...doc] : { ...doc };
  for (const k of Object.keys(patch)) {
    if (patch[k] === null) delete r[k];
    else if (typeof patch[k] === 'object') r[k] = applyPatch(r[k] || {}, patch[k]);
    else r[k] = patch[k];
  }
  return r;
};

// 深合并
const deepMerge = (t, s) => {
  const r = { ...t };
  for (const k of Object.keys(s)) {
    if (typeof s[k] === 'object' && !Array.isArray(s[k]) && s[k] !== null)
      r[k] = deepMerge(r[k] || {}, s[k]);
    else r[k] = s[k];
  }
  return r;
};

// JSON Patch（RFC 6902）替代 Merge Patch
const applyJSONPatch = (doc, patch) => {
  let result = JSON.parse(JSON.stringify(doc)); // 深拷贝
  for (const op of patch) {
    switch (op.op) {
      case 'replace': result[op.path] = op.value; break;
      case 'remove': delete result[op.path]; break;
      case 'add': result[op.path] = op.value; break;
      // ... move, copy, test
    }
  }
  return result;
};
```
