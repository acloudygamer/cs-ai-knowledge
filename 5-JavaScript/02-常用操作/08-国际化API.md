# 国际化 API

Intl 对象是 ECMAScript 国际化 API 的命名空间，提供语言敏感的字符串比较、数字格式化、日期时间格式化等功能。所有主流浏览器原生支持。

## Intl.NumberFormat

### 数据流

<pre>
输入数值 → 选择 locale/options → 实例化 NumberFormat → format() → 区域化字符串
</pre>

### 基本数字格式化

```javascript
new Intl.NumberFormat('zh-CN').format(1234567);
new Intl.NumberFormat('en-US').format(1234.5);
```

### 货币格式

```javascript
new Intl.NumberFormat('zh-CN', { style: 'currency', currency: 'CNY' }).format(1234.56);
new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(1234.56);
```

### 百分比

```javascript
new Intl.NumberFormat('zh-CN', { style: 'percent' }).format(0.25);
new Intl.NumberFormat('en-US', { style: 'percent', minimumFractionDigits: 2 }).format(0.256);
```

### 单位格式

```javascript
new Intl.NumberFormat('zh-CN', { style: 'unit', unit: 'kilometer-per-hour', unitDisplay: 'long' }).format(120);
new Intl.NumberFormat('en-US', { style: 'unit', unit: 'mile-per-hour', unitDisplay: 'short' }).format(60);
```

### 科学计数法

```javascript
new Intl.NumberFormat('zh-CN', { notation: 'scientific', maximumFractionDigits: 2 }).format(1234567);
new Intl.NumberFormat('en-US', { notation: 'engineering' }).format(12345);
```

### 有效数字

```javascript
new Intl.NumberFormat('en-US', { notation: 'compact', compactDisplay: 'long' }).format(123456789);
new Intl.NumberFormat('zh-CN', { notation: 'compact', compactDisplay: 'short' }).format(123456789);
```

## Intl.DateTimeFormat

### 基本日期格式化

```javascript
const date = new Date('2024-03-15T09:30:00');
new Intl.DateTimeFormat('zh-CN').format(date);
new Intl.DateTimeFormat('en-US').format(date);
```

### 完整格式

```javascript
new Intl.DateTimeFormat('zh-CN', { dateStyle: 'full' }).format(date);
new Intl.DateTimeFormat('en-US', { dateStyle: 'full' }).format(date);
```

### 时间格式化

```javascript
new Intl.DateTimeFormat('zh-CN', { timeStyle: 'short' }).format(date);
new Intl.DateTimeFormat('en-US', { timeStyle: 'medium' }).format(date);
```

### 组合格式

```javascript
new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
```

### 单独组件

```javascript
const f = new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' });
f.formatToParts(date).forEach(({ type, value }) => console.log(`${type}: ${value}`));
```

### 时区

```javascript
new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', dateStyle: 'full', timeStyle: 'short' }).format(date);
new Intl.DateTimeFormat('zh-CN', { timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit' }).format(date);
```

## Intl.RelativeTimeFormat

### 相对时间

```javascript
const rtf = new Intl.RelativeTimeFormat('zh-CN', { numeric: 'auto' });
rtf.format(-1, 'day');
rtf.format(1, 'hour');
rtf.format(-30, 'minute');
```

## Intl.ListFormat

### 列表格式化

```javascript
new Intl.ListFormat('zh-CN', { style: 'long', type: 'conjunction' }).format(['苹果', '香蕉', '橙子']);
new Intl.ListFormat('zh-CN', { style: 'short', type: 'disjunction' }).format(['苹果', '香蕉', '橙子']);
new Intl.ListFormat('en', { type: 'conjunction' }).format(['Apple', 'Banana']);
```

## Intl.Collator

### 字符串排序

```javascript
['北京', '上海', '广州', '深圳'].sort(new Intl.Collator('zh-CN').compare);
```

### 拼音排序

```javascript
new Intl.Collator('zh-CN', { sensitivity: 'base' }).compare('李四', '张三');
```

### 搜索匹配

```javascript
const c = new Intl.Collator('en', { sensitivity: 'base' });
c.compare('æ', 'ae');
```

## Intl.Segmenter

### 分词

```javascript
const segs = [...new Intl.Segmenter('zh-CN', { granularity: 'word' }).segment('你好，世界！')];
segs.forEach(s => console.log(s.segment));
```

### 句子分词

```javascript
[...new Intl.Segmenter('en', { granularity: 'sentence' }).segment('Hello! How are you?')].forEach(s => console.log(s.segment));
```

## Intl.PluralRules

### 复数规则

```javascript
const pr = new Intl.PluralRules('en');
pr.select(0);
pr.select(1);
```

### 复数形式选择

```javascript
const pluralize = (n, forms) => forms[new Intl.PluralRules('en').select(n)] || forms.other;
pluralize(1, { one: 'apple', other: 'apples' });
pluralize(3, { one: 'apple', other: 'apples' });
```

## Intl.DisplayNames

### 语言名称

```javascript
new Intl.DisplayNames(['zh-CN'], { type: 'language' }).of('en');
new Intl.DisplayNames(['zh-CN'], { type: 'language' }).of('ja');
```

### 地区名称

```javascript
new Intl.DisplayNames(['zh-CN'], { type: 'region' }).of('US');
new Intl.DisplayNames(['zh-CN'], { type: 'region' }).of('CN');
```

### 货币名称

```javascript
new Intl.DisplayNames(['zh-CN'], { type: 'currency' }).of('USD');
new Intl.DisplayNames(['zh-CN'], { type: 'currency' }).of('EUR');
```

## 实际应用场景

### 数字显示

```javascript
const formatPrice = (amount, currency = 'CNY') => new Intl.NumberFormat('zh-CN', { style: 'currency', currency }).format(amount);
formatPrice(999);
formatPrice(999, 'USD');
```

### 日期时间显示

```javascript
const formatDateTime = (date, locale = 'zh-CN') => new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeStyle: 'short' }).format(date);
formatDateTime(new Date());
formatDateTime(new Date(), 'en-US');
```

### 相对时间显示

```javascript
const formatRelative = (date) => {
  const diff = date - new Date();
  const rtf = new Intl.RelativeTimeFormat('zh-CN', { numeric: 'auto' });
  if (Math.abs(diff) < 60000) return rtf.format(Math.round(diff / 1000), 'second');
  if (Math.abs(diff) < 3600000) return rtf.format(Math.round(diff / 60000), 'minute');
  return rtf.format(Math.round(diff / 3600000), 'hour');
};
```

### 消息格式化

```javascript
const formatMsg = (tpl, vals, locale = 'zh-CN') => {
  const lf = new Intl.ListFormat(locale, { type: 'conjunction' });
  return tpl.replace('{count}', vals.count).replace('{items}', lf.format(vals.items));
};
```

## 浏览器兼容性

```javascript
const hasIntl = typeof Intl !== 'undefined';
const hasNumberFormat = typeof Intl.NumberFormat === 'function';
const hasDateTimeFormat = typeof Intl.DateTimeFormat === 'function';
const hasCollator = typeof Intl.Collator === 'function';
const hasSegmenter = typeof Intl.Segmenter === 'function';
```

## API 总结

| API | 用途 |
|-----|------|
| Intl.NumberFormat | 数字、货币、百分比格式化 |
| Intl.DateTimeFormat | 日期时间格式化 |
| Intl.RelativeTimeFormat | 相对时间显示 |
| Intl.ListFormat | 列表格式化（和、或） |
| Intl.Collator | 字符串排序和比较 |
| Intl.Segmenter | 文本分词（词、句、字符） |
| Intl.PluralRules | 复数规则 |
| Intl.DisplayNames | 语言/地区/货币名称 |
