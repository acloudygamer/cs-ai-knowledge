# 国际化 API

## 定义

`Intl` 对象是 ECMAScript 国际化 API 的**命名空间**，提供语言敏感的字符串比较、数字格式化、日期时间格式化、复数规则、分词等功能。所有主流浏览器原生支持，无需 polyfill。

## 数学模型

### 区域敏感比较

`Intl.Collator` 的排序基于 **Unicode 排序算法（UCA）**：每个字符映射到一组排序权重键（collation key），比较时逐级比较权重。中文排序通常按**拼音**（`sensitivity: 'accent'`）或**码点**排序。

`Intl.Segmenter` 的分词基于 **Unicode 文本分割算法**（UAX #29），对不同语言有不同的断词规则：
- **词边界**：中文按字符切分（"你好" → ["你", "好"]），英文按空格/标点切分
- **句子边界**：按句号、问号等标点切分

### 数字格式化的精度

`Intl.NumberFormat` 的 `maximumFractionDigits` 控制小数位数。格式化是**舍入**而非截断：
- `format(2.5, { maximumFractionDigits: 0 })` → `"3"`（四舍五入）
- 舍入模式默认为 `roundHalfUp`

### 时区计算

`Intl.DateTimeFormat` 的 `timeZone` 选项接受 IANA 时区名称（如 `'Asia/Shanghai'`）。时间戳到本地时间的转换：
$$T_{local} = T_{utc} + UTC_{offset}(T_{utc}, timezone)$$

夏令时（DST）使 UTC 偏移随日期变化，`Asia/Shanghai` 在夏令时期间偏移为 `UTC+9`，非夏令时为 `UTC+8`。

## 数据流

<pre>
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
输入 数值 + 单位 → 实例化 RelativeTimeFormat
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
</pre>

## 机制

### NumberFormat 的格式化规则

`Intl.NumberFormat` 支持多种 `style`：
- `'decimal'`：纯数字
- `'currency'`：货币（需指定 `currency` 选项）
- `'percent'`：百分比
- `'unit'`：单位（需指定 `unit` 选项）

**notation 选项**：
- `'standard'`：普通记数法
- `'scientific'`：科学计数法（`3.5E8`）
- `'engineering'`：工程计数法（指数为 3 的倍数）
- `'compact'`：紧凑记数法（`1.2M`）

### DateTimeFormat 的日期组件

`formatToParts()` 返回分段数组，适用于需要单独样式化日期各部分的场景：
```javascript
const parts = new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: 'long' }).formatToParts(new Date());
parts.find(p => p.type === 'month').value; // "四月"
```

### Collator 的敏感度选项

`sensitivity` 选项控制比较粒度：
- `'base'`：仅比较基本字符（`'a' === 'A'`，`'à' === 'a'`）
- `'accent'`：比较字符和重音（`'à' !== 'a'`）
- `'case'`：比较字符和大写（`'a' !== 'A'`，`'à' === 'a'`）
- `'variant'`：比较字符、重音、大小写（全量）

### Segmenter 的粒度选项

`granularity: 'word'` 在中文中按字符切分（"你好" → ["你", "好"]），但 `isWordLike` 属性指示该字符是否构成"词"（中文单字总为 word-like，英文按空格判定）。

### PluralRules 的语言差异

复数规则因语言而异：
- 英语（`en`）：`one`(1), `other`(其余)
- 俄语（`ru`）：`one`(1结尾且非11), `few`(2-4结尾且非12-14), `many`(5-20), `other`(其余)
- 阿拉伯语（`ar`）：`zero`, `one`, `two`, `few`, `many`, `other`（6 个类别）

### DisplayNames 的 type 选项

| type | 用途 | 示例 |
|------|------|------|
| `'language'` | 语言名称 | `"中文"` |
| `'region'` | 地区名称 | `"中国"` |
| `'currency'` | 货币名称 | `"美元"` |
| `'calendar'` | 日历系统 | `"公历"` |

## 参考存根

```javascript
// NumberFormat
new Intl.NumberFormat('zh-CN').format(1234567); // "1,234,567"
new Intl.NumberFormat('zh-CN', { style: 'currency', currency: 'CNY' }).format(1234.56); // "￥1,234.56"
new Intl.NumberFormat('en-US', { notation: 'compact', compactDisplay: 'short' }).format(123456789); // "123M"

// DateTimeFormat
new Intl.DateTimeFormat('zh-CN', { dateStyle: 'full', timeStyle: 'short' }).format(new Date());
new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York' }).format(new Date());
const parts = new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: 'long' }).formatToParts(new Date());

// RelativeTimeFormat
const rtf = new Intl.RelativeTimeFormat('zh-CN', { numeric: 'auto' });
rtf.format(-1, 'day'); // "昨天"
rtf.format(1, 'hour'); // "1小时后"

// ListFormat
new Intl.ListFormat('zh-CN', { type: 'conjunction' }).format(['苹果', '香蕉']); // "苹果、香蕉"
new Intl.ListFormat('en', { type: 'disjunction' }).format(['A', 'B']); // "A or B"

// Collator
['北京', '上海'].sort(new Intl.Collator('zh-CN').compare);
new Intl.Collator('en', { sensitivity: 'base' }).compare('æ', 'ae'); // 0

// Segmenter
[...new Intl.Segmenter('zh-CN', { granularity: 'word' }).segment('你好世界')].forEach(s => console.log(s.segment));

// PluralRules
const pr = new Intl.PluralRules('en');
['0', '1', '2'].map(n => `${n}: ${pr.select(n)}`); // ["0: other", "1: one", "2: other"]

// DisplayNames
new Intl.DisplayNames(['zh-CN'], { type: 'language' }).of('en'); // "英语"
new Intl.DisplayNames(['zh-CN'], { type: 'currency' }).of('USD'); // "美元"

// 实用函数
const formatPrice = (amount, currency = 'CNY') => new Intl.NumberFormat('zh-CN', { style: 'currency', currency }).format(amount);
const formatDateTime = (date, locale = 'zh-CN') => new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeStyle: 'short' }).format(date);
```
