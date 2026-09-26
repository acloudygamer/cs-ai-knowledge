# Intl 国际化

> 前置：[06-JSON](./06-JSON.md) · 后续：[04-异步与并发/01-事件循环与任务队列](../04-异步与并发/01-事件循环与任务队列.md)

> **版本基准**：Node 24 stable / Node 26 latest。本篇示例实测环境：Node v24.13.1（V8 13.6），Windows x64（默认区域 zh-CN）。

## 本质

`Intl` 把"格式化数字、日期、列表，按语言排序，判断单复数"这些**依赖语言与地区**的操作交给平台内置的国际化数据。它由 **ECMA-402** 定义——一个独立于 ECMA-262 的标准（见 [00-概览/01-JavaScript 全景](../00-概览/01-JavaScript全景.md) 的三层构成表）。

它存在的原因是：**这些规则无法手写**。货币符号的位置、千分位分隔符、日期的字段顺序、复数形式（英语 `1 item` / `2 items`，阿拉伯语有六种形式）、按语言排序的字母顺序——每一种都是长期演化的约定，且随语言而异。手写只会得到"英语环境能用、换个语言就错"的代码。

## 机制

### 默认区域来自环境

```console
$ node i.mjs
zh-CN | Asia/Hong_Kong
```

不传区域参数时，`Intl` 用宿主的默认区域与默认时区。**服务端不要依赖默认值**——同一份代码在开发机与服务器上会输出不同结果，必须显式传入。

### 六个构造器

**`Intl.NumberFormat`**：数字、货币、百分比、紧凑记数。

```console
$ node i.mjs
货币: ¥1,234,567.89
货币(德): 1.234.567,89 €
百分比: 12%
紧凑: 1235万
```

同一数字在 `zh-CN` 与 `de-DE` 下的小数点、千分位、符号位置全都不同；`notation: "compact"` 会按语言给出"万/亿"或"K/M"——**这四行没有一行能手写得到**。

**`Intl.DateTimeFormat`**：日期时间的语言化输出，同时处理时区。

```console
$ node i.mjs
zh-CN: 2026年9月27日星期日
en-US: Sunday, September 27, 2026
```

`timeZone` 选项让格式化与运行环境的时区解耦——服务端统一存 UTC，展示时指定目标时区（见 [04-日期与时间](./04-日期与时间.md)）。

**`Intl.RelativeTimeFormat`**：相对时间。

```console
$ node i.mjs
昨天 | 3个月后 | 今天
```

`numeric: "auto"` 允许"昨天"这类词而非"1 天前"。

**`Intl.Collator`**：按语言排序，而不是按码元（对比 [01-字符串与数字](./01-字符串与数字.md) 里 `"Z" < "a"` 的码元序）。

```console
$ node i.mjs
默认 sort: a,z,ä
Collator(de): a,ä,z
```

默认 `sort()` 把 `ä` 排在 `z` 之后（按码元）；德语排序规则把它排在 `a` 之后。**凡是给用户看的列表排序，都该用 `Collator`。**

**`Intl.PluralRules`**：选复数形式。

```console
$ node i.mjs
1 -> one | 2 -> other | 1.5 -> other
```

英语只有 `one` / `other`，其它语言可能有三到六种形式。`Intl.PluralRules` 给出类别名，翻译表按类别组织。

**`Intl.ListFormat`**：连接词。

```console
$ node i.mjs
甲、乙和丙
```

**`Intl.Segmenter`**：按语言规则切分文本（词、句、字素）。中文没有空格分词，只有它能正确切：

```console
$ node i.mjs
天气
```

### 构造器要复用

`Intl` 的每个构造器都要**加载语言数据并编译规则**，创建成本远高于普通对象。把 `new Intl.NumberFormat(...)` 放在循环里是常见性能问题。

`toLocaleString()` / `toLocaleDateString()` 是便捷写法，**每次调用都新建一个格式化器**——偶尔用可以，热路径上应显式建一次再复用。

### ICU 数据

`Intl` 的规则与语言数据来自 ICU 库，Node 的构建方式决定内置了多少数据。本机实测支持 162 种货币：

```console
$ node i.mjs
支持的区域数: 162
```

官方发行版带完整 ICU（full-icu）；自行编译时若选了 small-icu，只有英语数据，`Intl` 会静默退回英语输出——**不报错，只是结果不对**。这是容器化部署时值得核对的一项。

## 连接：手写与 `Intl` 对照

| 需求 | 手写 | `Intl` |
|---|---|---|
| 千分位 | `n.toLocaleString()` 或正则 | `NumberFormat` |
| 货币 | 拼符号 + `toFixed(2)` | `NumberFormat` + `currency` |
| 百分比 | `(n * 100).toFixed(1) + "%"` | `NumberFormat` + `style: "percent"` |
| 日期 | `getFullYear() + "年" + …` | `DateTimeFormat` |
| "3 天前" | 一堆 `if` | `RelativeTimeFormat` |
| 排序 | `sort()`（码元序） | `Collator` |
| 单复数 | `n === 1 ? "item" : "items"` | `PluralRules`（多语言正确） |

## 边界

- **不要依赖默认区域**：服务端与客户端的默认值可能不同，显式传入。
- **格式化器要复用**：构造开销大，循环内创建会明显变慢。
- **`Intl` 输出的是给人看的字符串，不是可解析格式**：需要机器可读就用 ISO 8601（`toISOString()`）。
- **`Intl` 不负责翻译**：它做的是数字、日期、复数、排序这类**规则化**的本地化；文案翻译是另一套体系。
- **small-icu 构建会静默降级**：部署时确认 ICU 数据完整度。

---

> 前置：[06-JSON](./06-JSON.md) · 后续：[04-异步与并发/01-事件循环与任务队列](../04-异步与并发/01-事件循环与任务队列.md)——语言与标准库讲完，进入 JavaScript 唯一的执行模型
