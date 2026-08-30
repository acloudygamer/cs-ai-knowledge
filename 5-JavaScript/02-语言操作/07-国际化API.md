# 国际化 API

## 定义

`Intl` 对象是 ECMAScript 国际化 API 的**命名空间**，提供语言敏感的字符串比较、数字格式化、日期时间格式化、复数规则、分词等功能。所有主流浏览器原生支持，无需 polyfill。

## 数学模型

### 区域敏感比较

`Intl.Collator` 的排序基于 **Unicode 排序算法（UCA）**：每个字符映射到一组排序权重键（collation key），比较时逐级比较权重：

$$
compare_{Collator}(a, b) = \sum_{i} weight\_key(a, i) \ominus weight\_key(b, i)
$$

其中 $\ominus$ 表示权重键的比较结果（负数/零/正数）。 表示权重键的比较结果（负数/零/正数）。

**Unicode 排序算法的数学基础**：UCA 定义了一个加权键序列 $\{P_1, S_1, T_1, Q_1\}$ 用于每个字符，其中： 用于每个字符，其中：
- $P_1$ ：主权重（最关键，区分语义） ：主权重（最关键，区分语义）
- $S_1$ ：次权重（区分重音/变体） ：次权重（区分重音/变体）
- $T_1$ ：三级权重（区分大小写） ：三级权重（区分大小写）
- $Q_1$ ：四级权重（其他变体） ：四级权重（其他变体）

比较时从主权重开始逐级比较，直到得出非零结果。

**中文排序选项**：

| 排序策略 | `sensitivity` | `numeric` | 效果 |
|----------|--------------|-----------|------|
| 拼音顺序 | `'accent'` | `true` | "北京" < "上海" |
| Unicode 码点 | `'base'` | `false` | 按码点排序 |
| 笔画数 | 需自定义 | - | 需扩展比较器 |

### Intl.Segmenter 的分词算法

`Intl.Segmenter` 基于 **Unicode 文本分割算法**（UAX #29），对不同语言有不同的断词规则：

**粒度类型**：

| 粒度 | 中文行为 | 英文行为 |
|------|----------|----------|
| `'grapheme'` | 按字符切分 | 按字符合并 |
| `'word'` | 按字符切分，`isWordLike` 判断 | 按空格/标点切分 |
| `'sentence'` | 按句号/问号切分 | 按句号/问号/感叹号切分 |

**UAX #29 的状态机模型**：文本切分基于一个有限状态机，在**字素簇边界**（Grapheme Cluster Boundary）、**词边界**（Word Boundary）和**句子边界**（Sentence Boundary）处进行切分。状态机的规则存储在 Unicode Character Database（UCD）的 `Boundaries.txt` 文件中。

### 数字格式化的精度

`Intl.NumberFormat` 的 `maximumFractionDigits` 控制小数位数。格式化是**舍入**而非截断：

| 输入 | `maximumFractionDigits: 0` | `maximumFractionDigits: 2` |
|------|---------------------------|---------------------------|
| `2.5` | `"3"` | `"2.50"` |
| `2.555` | `"3"` | `"2.56"` |
| `2.554` | `"3"` | `"2.55"` |

**舍入模式**（默认为 `roundHalfUp`）：

$$
roundHalfUp(x, n) = \begin{cases}
floor(x \cdot 10^n + 0.5) / 10^n & x \geq 0 \\
ceil(x \cdot 10^n - 0.5) / 10^n & x < 0
\end{cases}
$$

### 时区计算

`Intl.DateTimeFormat` 的 `timeZone` 选项接受 IANA 时区名称（如 `'Asia/Shanghai'`）。时间戳到本地时间的转换：

$$
T_{local} = T_{utc} + UTC_{offset}(T_{utc}, timezone)
$$

**夏令时（DST）影响**：

$$
UTC_{offset}(T, 'Asia/Shanghai') = \begin{cases}
+9h & T \in [DST\_start, DST\_end) \\
+8h & otherwise
\end{cases}
$$

例如 `Asia/Shanghai` 在夏令时期间偏移为 `UTC+9`，非夏令时为 `UTC+8`。

**DST 切换的数学描述**：UTC 偏移是一个**分段常数函数**，切换时刻由 IANA 时区数据库（tz database）定义。对于 `Asia/Shanghai`，DST 开始于 3 月第二个星期日 02:00（本地时间），结束于 11 月第一个星期日 02:00（本地时间）。

### PluralRules 的复数类别

`Intl.PluralRules` 基于 CLDR（Common Locale Data Repository）定义的复数规则库。每种语言的复数类别集合不同：

| 语言 | one | two | few | many | other |
|------|-----|-----|-----|------|-------|
| `en` | 1 | - | - | - | 其余 |
| `ru` | 1（结尾非11）| 2-4（结尾非12-14）| - | 5-20 | 其余 |
| `ar` | 0, 1 | 2 | 3-10 | 11-99 | 其余 |
| `zh` | - | - | - | - | 所有 |

**复数规则的数学表示**：每种语言的复数规则可表示为一个分段函数 $f: \mathbb{Z} \rightarrow C$ ，其中 $C$ 是该语言的复数类别集合。规则由条件表达式定义（如 "n % 10 == 1 && n % 100 != 11"）。 ，其中 $C$ 是该语言的复数类别集合。规则由条件表达式定义（如 "n % 10 == 1 && n % 100 != 11"）。 是该语言的复数类别集合。规则由条件表达式定义（如 "n % 10 == 1 && n % 100 != 11"）。

## 数据流

```
Intl.NumberFormat 流程：
输入数值 + locale + options → 实例化 NumberFormat（内部缓存）
                                       ↓
                              format() → 根据 options 格式化 → 区域化字符串

Intl.DateTimeFormat 流程：
输入 Date + locale + options → 实例化 DateTimeFormat
                                       ↓
                              format(date) → 提取 date 各组件（年/月/日/时/分/秒）
                                       ↓
                              根据 locale 的日历系统和时区规则格式化
                                       ↓
                              formatToParts(date) → 返回分段数组 [{ type, value }, ...]

Intl.RelativeTimeFormat 流程：
输入 数值 + 单位 + locale → 实例化 RelativeTimeFormat
                              ↓
                      format(value, unit) → 根据 numeric 选项（'always'/'auto'）格式化
                              ↓
                      'auto': 负数用 "昨天"，正数用 "明天"（无数字前缀）

Intl.ListFormat 流程：
输入 [字符串数组] + locale + options → 实例化 ListFormat
                                        ↓
                              format(['a', 'b', 'c']) → 根据 type/style 连接
                                        ↓
                              type: 'conjunction' (和) / 'disjunction' (或) / 'unit' (单位)
                              style: 'long' (完整) / 'short' (缩写)

Intl.Collator 流程：
输入 locale + options → 实例化 Collator（内部缓存）
                                ↓
                        compare(a, b) → UCA 比较 → 负数/0/正数

Intl.Segmenter 流程：
输入 字符串 + locale + options → 实例化 Segmenter
                                   ↓
                           segment(str) → 返回可迭代 Segment 对象
                                   ↓
                           遍历每个 Segment: { segment, index, input, isWordLike }

Intl.PluralRules 流程：
输入 locale → 实例化 PluralRules
                          ↓
                  select(n) → 返回复数类别
                          ↓
                  'one': 1 / 'two': 2（部分语言）/ 'few'/ 'many'/ 'other': 其他

Intl.DisplayNames 流程：
输入 locale + options → 实例化 DisplayNames
                                  ↓
                          of(code) → 根据 type 返回本地化名称
                          ↓
                          type: 'language'/'region'/'currency'/'calendar'/...
```

## 机制

### NumberFormat 的格式化规则

**style 选项**：

| style | 用途 | 示例输出 |
|-------|------|----------|
| `'decimal'` | 纯数字 | `1,234.56` |
| `'currency'` | 货币（需指定 `currency`）| `¥1,234.56` |
| `'percent'` | 百分比 | `50%` |
| `'unit'` | 单位（需指定 `unit`）| `50 km/h` |

**notation 选项**：

| notation | 用途 | 示例输出 |
|----------|------|----------|
| `'standard'` | 普通记数法 | `123456789` |
| `'scientific'` | 科学计数法 | `1.23456789E8` |
| `'engineering'` | 工程计数法（指数为 3 的倍数）| `123.456789E6` |
| `'compact'` | 紧凑记数法 | `123M` |

### DateTimeFormat 的日期组件

`formatToParts()` 返回分段数组，适用于需要单独样式化日期各部分的场景：

```javascript
const parts = new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: 'long' }).formatToParts(new Date());
parts.find(p => p.type === 'month').value; // "四月"
```

**dateStyle/timeStyle 选项**：

| dateStyle | timeStyle | 输出示例 |
|-----------|-----------|----------|
| `'full'` | `'full'` | 2024年3月15日星期五 14:30:45 中国标准时间 |
| `'long'` | `'long'` | 2024年3月15日 14:30:45 GMT+8 |
| `'medium'` | `'medium'` | 2024年3月15日 14:30:45 |
| `'short'` | `'short'` | 2024/3/15 14:30 |

### Collator 的敏感度选项

`sensitivity` 选项控制比较粒度：

| sensitivity | `'a'` vs `'A'` | `'à'` vs `'a'` | `'a'` vs `'b'` |
|-------------|----------------|----------------|----------------|
| `'base'` | 相等（0） | 相等（0） | 不等 |
| `'accent'` | 相等（0） | 不等 | 不等 |
| `'case'` | 不等 | 相等（0） | 不等 |
| `'variant'` | 不等 | 不等 | 不等 |

### Segmenter 的粒度与 isWordLike

```javascript
const seg = new Intl.Segmenter('zh-CN', { granularity: 'word' });
[...seg.segment('你好世界')].forEach(s => {
  console.log(s.segment, s.isWordLike); // 你 true, 好 true, 世 true, 界 true
});
```

**isWordLike 判断**：
- 中文单字：始终为 `true`
- 英文单词：`true`（由空格/标点分隔）
- 标点符号：`false`

### PluralRules 的语言差异

复数规则因语言而异（CLDR 规范）：

```javascript
const pr = new Intl.PluralRules('ru');
['1', '2', '5', '11', '21'].map(n => ` ${n}: $ {pr.select(n)}`);{pr.select(n)}`);
// ["1: one", "2: two", "5: many", "11: many", "21: one"]
```

### DisplayNames 的 type 选项

| type | 用途 | 示例 |
|------|------|------|
| `'language'` | 语言名称 | `'zh'` → `"中文"` |
| `'region'` | 地区名称 | `'CN'` → `"中国"` |
| `'currency'` | 货币名称 | `'USD'` → `"美元"` |
| `'calendar'` | 日历系统 | `'gregory'` → `"公历"` |
| `'dateTimeField'` | 日期时间字段 | `'dayOfMonth'` → `"日"` |

### RelativeTimeFormat 的 numeric 选项

```javascript
const rtf = new Intl.RelativeTimeFormat('zh-CN', { numeric: 'auto' });
rtf.format(-1, 'day'); // "昨天"
rtf.format(1, 'day');  // "1天后"

const rtf2 = new Intl.RelativeTimeFormat('zh-CN', { numeric: 'always' });
rtf2.format(-1, 'day'); // "-1天后"
rtf2.format(1, 'day');  // "1天后"
```

## 参考存根

```javascript
// NumberFormat
new Intl.NumberFormat('zh-CN').format(1234567); // "1,234,567"
new Intl.NumberFormat('zh-CN', { style: 'currency', currency: 'CNY' }).format(1234.56); // "￥1,234.56"
new Intl.NumberFormat('en-US', { notation: 'compact', compactDisplay: 'short' }).format(123456789); // "123M"
new Intl.NumberFormat('en-US', { notation: 'scientific' }).format(123456789); // "1.23456789E8"

// DateTimeFormat
new Intl.DateTimeFormat('zh-CN', { dateStyle: 'full', timeStyle: 'short' }).format(new Date());
new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York' }).format(new Date());
const parts = new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: 'long' }).formatToParts(new Date());
parts.find(p => p.type === 'month').value; // "四月"

// RelativeTimeFormat
const rtf = new Intl.RelativeTimeFormat('zh-CN', { numeric: 'auto' });
rtf.format(-1, 'day'); // "昨天"
rtf.format(1, 'hour'); // "1小时后"

// ListFormat
new Intl.ListFormat('zh-CN', { type: 'conjunction' }).format(['苹果', '香蕉']); // "苹果、香蕉"
new Intl.ListFormat('en', { type: 'disjunction' }).format(['A', 'B']); // "A or B"
new Intl.ListFormat('zh-CN', { type: 'unit', style: 'short' }).format(['5', '分钟']); // "5 分钟"

// Collator
['北京', '上海'].sort(new Intl.Collator('zh-CN').compare);
new Intl.Collator('en', { sensitivity: 'base' }).compare('æ', 'ae'); // 0

// Segmenter
[...new Intl.Segmenter('zh-CN', { granularity: 'word' }).segment('你好世界')].forEach(s => console.log(s.segment));
[...new Intl.Segmenter('en', { granularity: 'word' }).segment('Hello World!')].forEach(s => console.log(s.segment));

// PluralRules
const pr = new Intl.PluralRules('en');
['0', '1', '2'].map(n => ` ${n}: $ {pr.select(n)}`); // ["0: other", "1: one", "2: other"]{pr.select(n)}`); // ["0: other", "1: one", "2: other"]

// DisplayNames
new Intl.DisplayNames(['zh-CN'], { type: 'language' }).of('en'); // "英语"
new Intl.DisplayNames(['zh-CN'], { type: 'currency' }).of('USD'); // "美元"
new Intl.DisplayNames(['zh-CN'], { type: 'region' }).of('US'); // "美国"

// 实用函数
const formatPrice = (amount, currency = 'CNY') => new Intl.NumberFormat('zh-CN', { style: 'currency', currency }).format(amount);
const formatDateTime = (date, locale = 'zh-CN') => new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeStyle: 'short' }).format(date);

// ListFormat 实现原理
const formatList = (items, locale, type) => new Intl.ListFormat(locale, { type }).format(items);
formatList(['A', 'B', 'C'], 'zh-CN', 'conjunction'); // "A、B、C"
formatList(['A', 'B', 'C'], 'en', 'conjunction'); // "A, B, and C"
```
