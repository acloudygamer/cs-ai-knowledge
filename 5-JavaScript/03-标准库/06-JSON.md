# JSON

> 前置：[05-正则表达式](./05-正则表达式.md) · 后续：[07-Intl 国际化](./07-Intl国际化.md)

> **版本基准**：Node 24 stable / Node 26 latest。本篇示例实测环境：Node v24.13.1（V8 13.6），Windows x64。

## 本质

JSON 是**独立的文本数据交换格式**，由 ECMA-404 定义——它不是 JavaScript 的一部分，也不是 JavaScript 的子集。它与 JavaScript 对象字面量长得像纯属设计选择（JSON 的语法源自 JavaScript 的早期版本），但两者的**值域不同**：

| | JSON 支持 | JavaScript 支持 |
|---|---|---|
| 值 | 对象、数组、字符串、数字、`true`/`false`/`null` | 以上全部，外加 `undefined`、函数、符号、`bigint`、`Date`、`Map`、`Set`…… |
| 数字 | 十进制浮点/整数（无 `NaN`、无 `Infinity`） | `number`（含 `NaN`、`Infinity`）+ `bigint` |
| 键 | 必须是双引号字符串 | 字符串或符号，可不加引号 |
| 注释 / 尾逗号 | 不允许 | 允许 |

`JSON.stringify` 与 `JSON.parse` 做的就是在这两个值域之间**有损地**转换——"有损"是理解它们全部行为的钥匙。

## 机制

### `stringify`：不在值域里的东西怎么办

```console
$ node j.mjs
{"n":null,"i":null}
数组里的 undefined 变 null: [null,null,1]
```

输入是 `{u: undefined, f: () => {}, s: Symbol("x"), n: NaN, i: Infinity}`，输出只剩 `{"n":null,"i":null}`。规则分三类：

| 值 | 在**对象**里 | 在**数组**里 |
|---|---|---|
| `undefined`、函数、符号 | **整个键被丢弃** | 变成 `null` |
| `NaN`、`Infinity`、`-Infinity` | 变成 `null` | 变成 `null` |
| `bigint` | **抛 `TypeError`** | 抛 `TypeError` |
| `Date` | 转成 ISO 字符串（走 `toJSON`） | 同左 |
| `Map`、`Set` | 变成 `{}`（没有可枚举自身属性） | 变成 `{}` |

```console
$ node j.mjs
TypeError: Do not know how to serialize a BigInt
```

`bigint` 是唯一直接抛错的类型（因为它无法无损地表示为 JSON 数字）。`Map` / `Set` 静默变成 `{}` 更危险——不报错，数据没了。

### 循环引用

```console
$ node j.mjs
TypeError: Converting circular structure to JSON
```

对象引用自身（或经若干层引用回自身）时抛错，错误信息会指出闭环的起点。需要序列化有环结构时，用 `replacer` 手工处理，或改用支持引用的格式。

### 三个自定义钩子

**`toJSON()`**：对象自己决定被序列化成什么。`Date` 就是靠它输出 ISO 字符串：

```console
$ node j.mjs
{"v":"被替换"}
```

**`replacer` 函数**：对每个键值对调用，返回 `undefined` 即删除该键：

```console
$ node j.mjs
{"c":3}
```

**`replacer` 数组**：白名单，只保留列出的键：

```console
$ node j.mjs
{"a":1,"c":3}
```

**`reviver`**：`parse` 的对应物，自底向上对每个键值对调用，可还原自定义类型：

```console
$ node j.mjs
{"d":"2026-01-01T00:00:00.000Z","n":5}
```

上例把 `"2026-01-01"` 还原成了 `Date` 对象（再次 `stringify` 时又变回 ISO 字符串）。

### 键顺序被保留

```console
$ node j.mjs
{"z":1,"a":2,"m":3}
```

`parse` 与 `stringify` 都保持插入序。但注意这是**字符串键**的情况——对象里若有整数索引键，顺序仍按 [03-Object 与 Map/Set](./03-Object与Map-Set.md) 那条三段式规则重排。

### 数字精度

```console
$ node j.mjs
9007199254740992 （原值 9007199254740993）
```

JSON 的数字没有精度约定，`JSON.parse` 一律解析成 `number`（float64），因此超出 $2^{53}$ 的整数**在解析阶段就丢了精度**——这不是 `JSON.parse` 的 bug，是 `number` 的边界（见 [01-语言核心/02-绑定与类型](../01-语言核心/02-绑定与类型.md)）。大整数 ID（如雪花 ID、数据库主键）应**以字符串传输**。

### 安全：`__proto__` 键的处理差异

`JSON.parse` 遇到 `"__proto__"` 键时，把它建成**自身数据属性**，不触发原型设置：

```console
$ node p.mjs
1. JSON.parse 结果自身: __proto__ | parsed.polluted = undefined
2. 展开后 copy 自身键: __proto__ | copy.polluted = undefined
3. Object.assign 后:  | assigned.polluted = true
```

三行的差异是本篇最需要记住的一点：

| 操作 | `__proto__` 的归宿 | 是否污染 |
|---|---|---|
| `JSON.parse` | 自身数据属性 | 否 |
| `{ ...parsed }` | 自身数据属性 | 否 |
| `Object.assign({}, parsed)` | **走 `[[Set]]`，触发原型设置器** | **是** |

`Object.assign` 用赋值语义写入目标对象，而 `__proto__` 是 `Object.prototype` 上的访问器（见 [02-对象模型与运行时/01-原型链与继承](../02-对象模型与运行时/01-原型链与继承.md)），于是目标的**原型被换掉**——`assigned` 自身键为空，`assigned.polluted` 却是 `true`。

**结论：合并来自外部的 JSON 时用展开运算符，不要用 `Object.assign`。** 更彻底的防护是丢弃 `__proto__` / `constructor` / `prototype` 键，或用 `Object.create(null)` 作为目标。

## 连接：JSON 与 JavaScript 值

| JavaScript 值 | `JSON.stringify` 结果 |
|---|---|
| `{a: 1}` | `{"a":1}` |
| `[1, "x", null]` | `[1,"x",null]` |
| `undefined`（对象属性） | 键被删除 |
| `undefined`（数组元素） | `null` |
| `NaN` / `Infinity` | `null` |
| `10n` | 抛 `TypeError` |
| `new Date(0)` | `"1970-01-01T00:00:00.000Z"` |
| `new Map()` / `new Set()` | `{}` |
| 函数 / 符号 | 键被删除（数组里变 `null`） |
| 循环引用 | 抛 `TypeError` |

## 边界

- **JSON 不是 JavaScript 的子集**：`{a: 1}` 是合法 JS 字面量但不是合法 JSON（键没加双引号）；`NaN` 是合法 JS 值但不是合法 JSON。
- **`Map` / `Set` 静默变成 `{}`**：序列化前先转成数组或对象。
- **大整数必须用字符串传输**：`number` 无法精确表示超过 $2^{53}$ 的整数。
- **合并外部 JSON 用展开而非 `Object.assign`**：后者会触发 `__proto__` 的原型设置。
- **`JSON.parse` 不校验结构**：它只保证语法合法，字段类型与存在性需要自己检查——这正是 [TypeScript](../../7-TypeScript/) 与运行时校验库的用武之地。

---

> 前置：[05-正则表达式](./05-正则表达式.md) · 后续：[07-Intl 国际化](./07-Intl国际化.md)——最后一块内建能力：让输出适配使用者的语言与地区
