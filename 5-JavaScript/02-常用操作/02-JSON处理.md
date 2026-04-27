# JSON 处理

## 定义

JSON（JavaScript Object Notation）是 JavaScript 对象字面量语法的**一个子集**，被设计为轻量级数据交换格式。JavaScript 通过 `JSON.parse()` 将 JSON 字符串反序列化为对象（原生值：string/number/boolean/null/array/object），通过 `JSON.stringify()` 将对象序列化为 JSON 字符串。ES2024 的 `structuredClone` 提供了原生深拷贝能力。

## 数学模型

### 序列化复杂度

设对象图中的节点数为 $N$（对象/数组/原始值），序列化时间复杂度为 $\mathcal{O}(N)$：每个节点恰好访问一次。字符串化后的长度与对象的结构相关：

- 对象键数量为 $K$，平均键长度为 $\bar{l_k}$，平均值为 $\bar{v}$：
$$|JSON| = \mathcal{O}\left(\sum_{k \in K} (l_k + |v_k|) + K \cdot 2\right)$$

- 特殊值处理：`undefined`/`Symbol`/`Function` 在 `JSON.stringify` 中被忽略（对象属性）或转为 `undefined`（数组元素）或 `null`（单独参数）。`BigInt` 抛出 `TypeError`。

### structuredClone 的能力边界

`structuredClone(value)` 使用**结构化克隆算法**，可复制：
- 所有原生类型（除 `Symbol`）
- `Object`（包括 `Map`/`Set`/`Date`/`RegExp`/`ArrayBuffer`/`TypedArray`）
- 嵌套对象

不可复制：
- `Function`（抛出 `DataCloneError`）
- DOM 节点（抛出 `DataCloneError`）
- 闭包（闭包引用的外层变量无法被克隆）

### JSON Merge Patch（RFC 7386）

JSON Merge Patch 是部分更新语义：
$$P_{patch}(D, P) = \begin{cases}
P & P \neq null \land P \neq \{\} \\
D \backslash P & P = null \lor (P = \{\} \land D\ is\ object)
\end{cases}$$

- `P = null`：删除目标
- `P = {}`：清空对象
- `P = { k: v }`：递归合并或替换

## 数据流

<pre>
JSON.parse 流程：
字符串 → 词法分析（token 化）→ 解析器（递归下降）→ 对象构建
          ↓
    语法错误 → 抛出 SyntaxError

JSON.stringify 流程：
对象遍历（DFS）→ 字符串拼接 → 输出字符串
          ↓
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
</pre>

## 机制

### JSON.parse 的安全边界

`JSON.parse` 在 V8 引擎中由 **Scanner-Lexer-Parser** 三阶段实现。解析过程将字符串转换为 AST，再构建对象图。解析器实现为**递归下降**，对嵌套深度有限制（V8 默认约为 10000 层），超出后抛出 `SyntaxError`。

**约束**：JSON 语法严格，不允许尾随逗号、不支持注释、不支持单引号字符串。解析器不进行 schema 验证，合法 JSON 但不符合业务预期的数据会静默通过。

### JSON.stringify 的遍历语义

`JSON.stringify` 使用 **DFS 前序遍历**对象图，依次处理每个可枚举自有属性。遍历过程中维护一个"正在访问对象栈"以检测循环引用——若检测到循环，抛出 `TypeError`。

**replacer 参数的作用域**：replacer 函数对每个键值对调用一次，`this` 绑定当前属性所在对象，`k` 为属性名，`v` 为属性值。返回值 `undefined` 导致该属性被跳过（对象属性）或被序列化为 `null`（数组元素）。

### structuredClone 与 JSON 深拷贝的本质差异

JSON 深拷贝：对象 → JSON 字符串 → 新对象。经历了序列化/反序列化，适合包含原始类型的普通对象。

`structuredClone`：对象 → 结构化克隆 → 新对象。直接复制对象图结构，支持更多类型，不经过字符串转换（因此避免了 JSON 字符串的长度限制和精度问题，如 `Number.MAX_SAFE_INTEGER` 以上的整数）。

**约束**：`structuredClone` 不执行 getter/setter，仅复制值语义。

### JSON Merge Patch 的语义边界

JSON Merge Patch 定义了"最小 diff"语义：只描述需要变更的部分。但其语义存在歧义——当期望将某个键的值设为 `null` 时，`null` 被解释为"删除键"，而非"设置值为 null"。`undefined` 键同理。这导致无法用 Merge Patch 表示"将值设为 null 或 undefined"的意图。

## 参考存根

```javascript
// BigInt 序列化/反序列化
const ser = (v) => typeof v === 'bigint' ? v.toString() : v;
const deser = (k, v) => typeof v === 'string' && /^\d+$/.test(v) ? BigInt(v) : v;
JSON.stringify(obj, ser); JSON.parse(str, deser);

// safeParse
const safeParse = jsonString => { try { return { ok: true, data: JSON.parse(jsonString) }; } catch { return { ok: false }; } };

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
    if (typeof s[k] === 'object' && !Array.isArray(s[k]) && s[k] !== null) r[k] = deepMerge(r[k] || {}, s[k]);
    else r[k] = s[k];
  }
  return r;
};
```
