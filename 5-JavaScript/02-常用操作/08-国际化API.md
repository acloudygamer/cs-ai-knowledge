# 国际化 API

## Intl 概述

Intl 对象是 ECMAScript 国际化 API 的命名空间，提供语言敏感的字符串比较、数字格式化、日期时间格式化等功能。

```javascript
// 所有浏览器原生支持
console.log(typeof Intl);  // 'object'
```

---

## Intl.NumberFormat

### 基本数字格式化

```javascript
// 整数
new Intl.NumberFormat('zh-CN').format(1234567);
// '1,234,567'

// 小数
new Intl.NumberFormat('zh-CN').format(1234.56);
// '1,234.56'

// 带小数的格式
new Intl.NumberFormat('en-US').format(1234.5);
// '1,234.5'
```

### 货币格式

```javascript
// 人民币
new Intl.NumberFormat('zh-CN', {
  style: 'currency',
  currency: 'CNY'
}).format(1234.56);
// '¥1,234.56'

// 美元
new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD'
}).format(1234.56);
// '$1,234.56'

// 欧元
new Intl.NumberFormat('de-DE', {
  style: 'currency',
  currency: 'EUR'
}).format(1234.56);
// '1.234,56 €'
```

### 百分比

```javascript
new Intl.NumberFormat('zh-CN', {
  style: 'percent'
}).format(0.25);
// '25%'

new Intl.NumberFormat('en-US', {
  style: 'percent',
  minimumFractionDigits: 2
}).format(0.256);
// '25.60%'
```

### 单位格式

```javascript
new Intl.NumberFormat('zh-CN', {
  style: 'unit',
  unit: 'kilometer-per-hour',
  unitDisplay: 'long'
}).format(120);
// '每小时 120 公里'

new Intl.NumberFormat('en-US', {
  style: 'unit',
  unit: 'mile-per-hour',
  unitDisplay: 'short'
}).format(60);
// '60 mph'
```

### 科学计数法

```javascript
new Intl.NumberFormat('zh-CN', {
  notation: 'scientific',
  maximumFractionDigits: 2
}).format(1234567);
// '1.23E6'

new Intl.NumberFormat('en-US', {
  notation: 'engineering'
}).format(12345);
// '12.345E3'
```

### 有效数字

```javascript
new Intl.NumberFormat('en-US', {
  notation: 'compact',
  compactDisplay: 'long'
}).format(123456789);
// '123 million'

new Intl.NumberFormat('zh-CN', {
  notation: 'compact',
  compactDisplay: 'short'
}).format(123456789);
// '1亿'
```

---

## Intl.DateTimeFormat

### 基本日期格式化

```javascript
const date = new Date('2024-03-15T09:30:00');

new Intl.DateTimeFormat('zh-CN').format(date);
// '2024/3/15'

new Intl.DateTimeFormat('en-US').format(date);
// '3/15/2024'

new Intl.DateTimeFormat('ja-JP').format(date);
// '2024/3/15'
```

### 完整格式

```javascript
new Intl.DateTimeFormat('zh-CN', {
  dateStyle: 'full'
}).format(date);
// '2024年3月15日星期五'

new Intl.DateTimeFormat('en-US', {
  dateStyle: 'full'
}).format(date);
// 'Friday, March 15, 2024'
```

### 时间格式化

```javascript
new Intl.DateTimeFormat('zh-CN', {
  timeStyle: 'short'
}).format(date);
// '上午9:30'

new Intl.DateTimeFormat('en-US', {
  timeStyle: 'medium'
}).format(date);
// '9:30:00 AM'
```

### 组合格式

```javascript
new Intl.DateTimeFormat('zh-CN', {
  dateStyle: 'medium',
  timeStyle: 'short'
}).format(date);
// '2024/3/15 上午9:30'
```

### 单独组件

```javascript
const formatter = new Intl.DateTimeFormat('zh-CN', {
  year: 'numeric',
  month: 'long',
  day: 'numeric',
  weekday: 'long'
});

formatter.format(date);
// '2024年3月15日星期五'

// 单独获取
formatter.formatToParts(date).forEach(({ type, value }) => {
  console.log(`${type}: ${value}`);
});
// year: 2024
// month: 3
// day: 15
// weekday: 星期五
```

### 时区

```javascript
// 显示指定时区
new Intl.DateTimeFormat('en-US', {
  timeZone: 'America/New_York',
  dateStyle: 'full',
  timeStyle: 'short'
}).format(date);
// 'Friday, March 15, 2024 at 9:30 AM'

// ISO 字符串
new Intl.DateTimeFormat('zh-CN', {
  timeZone: 'Asia/Shanghai',
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit'
}).format(date);
// '2024/03/15 09:30:00'

// UTC
new Intl.DateTimeFormat('en-US', {
  timeZone: 'UTC',
  timeZoneName: 'short'
}).format(date);
// '3/15/2024, 1:30 AM GMT'
```

---

## Intl.RelativeTimeFormat

### 相对时间

```javascript
const rtf = new Intl.RelativeTimeFormat('zh-CN', { numeric: 'auto' });

rtf.format(-1, 'day');   // '昨天'
rtf.format(-2, 'day');   // '前天'
rtf.format(1, 'day');    // '明天'
rtf.format(2, 'day');    // '后天'

rtf.format(-1, 'hour');  // '1小时前'
rtf.format(1, 'hour');   // '1小时后'

rtf.format(-30, 'minute'); // '30分钟前'
rtf.format(30, 'second');  // '30秒后'
```

### 英文相对时间

```javascript
const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });

rtf.format(-1, 'day');   // 'yesterday'
rtf.format(1, 'day');    // 'tomorrow'

rtf.format(-3, 'week');  // '3 weeks ago'
rtf.format(3, 'month');  // 'in 3 months'
```

---

## Intl.ListFormat

### 列表格式化

```javascript
const lf = new Intl.ListFormat('zh-CN', {
  style: 'long',
  type: 'conjunction'
});

lf.format(['苹果', '香蕉', '橙子']);
// '苹果、香蕉和橙子'

const lf2 = new Intl.ListFormat('zh-CN', {
  style: 'short',
  type: 'disjunction'
});

lf2.format(['苹果', '香蕉', '橙子']);
// '苹果、香蕉或橙子'
```

### 英文列表

```javascript
const lf = new Intl.ListFormat('en', { type: 'conjunction' });
lf.format(['Apple', 'Banana', 'Orange']);
// 'Apple, Banana, and Orange'

const lf2 = new Intl.ListFormat('en', { type: 'or' });
lf2.format(['Apple', 'Banana', 'Orange']);
// 'Apple, Banana, or Orange'

const lf3 = new Intl.ListFormat('en', { type: 'unit' });
lf3.format(['Apple', 'Banana', 'Orange']);
// 'Apple, Banana, Orange'
```

---

## Intl.Collator

### 字符串排序

```javascript
const zhCollator = new Intl.Collator('zh-CN');

const words = ['北京', '上海', '广州', '深圳'];
console.log(words.sort(zhCollator.compare));
// ['北京', '广州', '上海', '深圳']
```

### 拼音排序

```javascript
const pinyinCollator = new Intl.Collator('zh-CN', {
  sensitivity: 'base'
});

const names = ['张三', '李四', '王五', '赵六'];
console.log(names.sort(pinyinCollator.compare));
// 按拼音排序
```

### 英文排序

```javascript
const enCollator = new Intl.Collator('en', {
  caseFirst: 'upper'  // 大写优先
});

['apple', 'Banana', 'cherry'].sort(enCollator.compare);
// ['Banana', 'apple', 'cherry']
```

### 搜索匹配

```javascript
const collator = new Intl.Collator('en', { sensitivity: 'base' });

// 匹配 'æ' 和 'ae'
collator.compare('æ', 'ae');    // 0 (相等)
collator.compare('Æ', 'ae');    // 0 (相等)

// 不匹配
collator.compare('æ', 'b');     // -1
```

---

## Intl.Segmenter

### 分词

```javascript
const segmenter = new Intl.Segmenter('zh-CN', { granularity: 'word' });

const text = '你好，世界！';
const segments = [...segmenter.segment(text)];

segments.forEach(s => {
  console.log(`'${s.segment}' - ${s.index} to ${s.index + s.segment.length}`);
});

// '你' - 0 to 1
// '好' - 1 to 2
// '，' - 2 to 3
// '世' - 3 to 4
// '界' - 4 to 5
// '！' - 5 to 6
```

### 句子分词

```javascript
const segmenter = new Intl.Segmenter('en', { granularity: 'sentence' });

const text = 'Hello! How are you? I am fine.';
const segments = [...segmenter.segment(text)];

segments.forEach(s => console.log(`'${s.segment}'`));
// 'Hello! '
// 'How are you? '
// 'I am fine.'
```

### 字符粒度

```javascript
const segmenter = new Intl.Segmenter('en', { granularity: 'grapheme' });

[...segmenter.segment('hi')];
// [{ segment: 'h', index: 0 }, { segment: 'i', index: 1 }]
```

---

## Intl.PluralRules

### 复数规则

```javascript
const pr = new Intl.PluralRules('en');

pr.select(0);   // 'other'
pr.select(1);   // 'one'
pr.select(2);   // 'other'

pr.select(0);   // '其他' (中文只有 'other')
```

### 复数形式选择

```javascript
const pr = new Intl.PluralRules('en');

function pluralize(count, forms) {
  const rule = pr.select(count);
  return forms[rule] || forms.other;
}

const fruitForms = { one: 'apple', other: 'apples' };
pluralize(1, fruitForms);  // 'apple'
pluralize(3, fruitForms);  // 'apples'

// 中文（无复数）
const zhPr = new Intl.PluralRules('zh');
zhPr.select(1);   // 'other'
```

---

## Intl.DisplayNames

### 语言名称

```javascript
const dn = new Intl.DisplayNames(['zh-CN'], { type: 'language' });

dn.of('en');      // '英语'
dn.of('ja');      // '日语'
dn.of('zh-Hans'); // '简体中文'
dn.of('en-US');   // '美国英语'
```

### 地区名称

```javascript
const dn = new Intl.DisplayNames(['zh-CN'], { type: 'region' });

dn.of('US');      // '美国'
dn.of('GB');      // '英国'
dn.of('JP');      // '日本'
dn.of('CN');      // '中国'
```

### 货币名称

```javascript
const dn = new Intl.DisplayNames(['zh-CN'], { type: 'currency' });

dn.of('USD');     // '美元'
dn.of('EUR');     // '欧元'
dn.of('GBP');     // '英镑'
```

### 日历名称

```javascript
const dn = new Intl.DisplayNames(['zh-CN'], { type: 'calendar' });

dn.of('gregory'); // '公历'
dn.of('islamic'); // '伊斯兰历'
dn.of('japanese'); // '日本历'
```

---

## 实际应用场景

### 1. 数字显示（电商价格）

```javascript
function formatPrice(amount, currency = 'CNY', locale = 'zh-CN') {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    minimumFractionDigits: currency === 'JPY' ? 0 : 2
  }).format(amount);
}

formatPrice(999);           // '¥999.00'
formatPrice(999, 'USD');    // '$999.00'
formatPrice(999, 'JPY');    // '¥999'
```

### 2. 日期时间显示

```javascript
function formatDateTime(date, options = {}) {
  const {
    locale = 'zh-CN',
    format = 'medium',
    includeTime = true
  } = options;

  const dateStyle = format;
  const timeStyle = includeTime ? 'short' : undefined;

  return new Intl.DateTimeFormat(locale, { dateStyle, timeStyle }).format(date);
}

formatDateTime(new Date());                        // '2024/3/15 上午9:30'
formatDateTime(new Date(), { locale: 'en-US' });   // 'Mar 15, 2024, 9:30 AM'
```

### 3. 相对时间显示

```javascript
function formatRelativeTime(date, locale = 'zh-CN') {
  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' });

  const diff = date - new Date();
  const diffSec = Math.round(diff / 1000);
  const diffMin = Math.round(diff / 60000);
  const diffHour = Math.round(diff / 3600000);
  const diffDay = Math.round(diff / 86400000);

  if (Math.abs(diffSec) < 60) {
    return rtf.format(diffSec, 'second');
  } else if (Math.abs(diffMin) < 60) {
    return rtf.format(diffMin, 'minute');
  } else if (Math.abs(diffHour) < 24) {
    return rtf.format(diffHour, 'hour');
  } else {
    return rtf.format(diffDay, 'day');
  }
}

formatRelativeTime(new Date(Date.now() - 3600000)); // '1小时前'
```

### 4. 消息格式化

```javascript
function formatMessage(template, values, locale = 'zh-CN') {
  const lf = new Intl.ListFormat(locale, { type: 'conjunction' });

  return template
    .replace('{count}', values.count)
    .replace('{items}', lf.format(values.items))
    .replace('{date}', new Intl.DateTimeFormat(locale).format(values.date));
}

formatMessage(
  '已选择 {count} 个项目：{items}，更新于 {date}',
  {
    count: 3,
    items: ['苹果', '香蕉', '橙子'],
    date: new Date()
  }
);
// '已选择 3 个项目：苹果、香蕉和橙子，更新于 2024/3/15'
```

### 5. 分页显示

```javascript
function formatPagination(current, total, locale = 'zh-CN') {
  const nf = new Intl.NumberFormat(locale);

  return `第 ${nf.format(current)} 页，共 ${nf.format(total)} 页`;
}

formatPagination(1, 1000);   // '第 1 页，共 1,000 页'
formatPagination(1234, 99999); // '第 1,234 页，共 99,999 页'
```

---

## 浏览器兼容性

```javascript
// 检测支持
const hasIntl = typeof Intl !== 'undefined';
const hasNumberFormat = typeof Intl.NumberFormat === 'function';
const hasDateTimeFormat = typeof Intl.DateTimeFormat === 'function';
const hasCollator = typeof Intl.Collator === 'function';
const hasSegmenter = typeof Intl.Segmenter === 'function';

// Polyfill（可选，主流浏览器都已支持）
// Intl.PluralRules, Intl.ListFormat, Intl.Segmenter 可能需要 polyfill
```

---

## 总结

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
