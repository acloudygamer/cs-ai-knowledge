# JSON处理

## 定义

JSON 处理是将 Go 结构化数据与 JSON 文本相互转换的过程，核心是 `encoding/json` 标准库通过结构体 tag 控制字段命名、空值行为和类型适配。

JSON 序列化的本质是**带类型的字符串序列化**：在保持类型信息的前提下将内存结构转换为文本交换格式，解析时再将文本还原为带类型结构。

## 数学模型

### 序列化复杂度

`json.Marshal` 时间复杂度为 $O(n)$，其中 $n$ 为字段数（不含跳过字段）。

内存分配模式：
- 每个导出字段约 1-2 次分配（字段名、字符串值）
- 嵌套结构递归序列化
- 对于 1000 字段的结构体，单次 Marshal 约 50-200μs

**归约终点**：序列化过程可归结为**递归树遍历**，每个节点的处理成本 $c_i$ 与字段类型相关，总成本 $\sum_i c_i$。

### omitzero vs omitempty 的语义差异

| 条件 | 无标签 | `omitempty` | `omitzero` (Go 1.24+) |
|------|--------|-------------|------------------------|
| nil 切片 | `null` | 跳过 | 跳过 |
| 空切片 `[]int{}` | `[]int{}` | `[]int{}` | `[]int{}` |
| nil 映射 | `null` | 跳过 | 跳过 |
| 空映射 `map[K]V{}` | `{}` | `{}` | **跳过** |
| 空字符串 `""` | `""` | 跳过 | 跳过 |
| 零值 int `0` | `0` | 跳过 | 跳过 |

**数学本质**：`omitempty` 判断"是否等于 Go 类型的零值"，`omitzero` 扩展判断"是否等于 Go 类型的零值 **或** 是否为空容器"。

## 数据流

### Marshal 过程

<pre>
Go 结构体
    │
    │ 遍历导出字段
    ▼
字段级处理（tag解析、空值判断）
    │
    ├─── 跳过（omitempty 触发）
    │
    └─── 序列化（递归处理嵌套结构）
            │
            ▼
        JSON 文本
</pre>

**数据所有权变换**：
- 输入：Go 结构体（堆/栈内存）
- 中间：临时字符串缓冲区
- 输出：完整 JSON 文本（堆内存）

### 流式解析（json.Decoder）

<pre>
JSON 文件/流
    │
    │ dec.More() 检测是否还有对象
    ▼
逐个 Decode() 到目标结构体
    │
    │ 每读一个对象，指针前移
    ▼
无需一次性加载整个文件
</pre>

### 自定义序列化

<pre>
类型 T
    │
    │ 实现 MarshalJSON()
    ▼
自定义 []byte 输出
    │
    │ json.Marshal 优先调用自定义实现
    ▼
直接写入 JSON 输出流
</pre>

## 机制

### tag 解析的编译时行为

结构体 tag 是编译时绑定的字符串常量，`json.Unmarshal` 在运行时通过反射解析。tag 解析优先级：

1. `json:"-"` → 跳过字段
2. `json:"name"` → 使用指定名称
3. 无 tag → 使用字段名（小写转大写后作为 JSON key）

**约束**：tag 中的引号需要转义，如 `json:"name,string"`。

### omitempty 的空值陷阱

`omitempty` 的空值判定是**反射反射再反射**：

```go
// 以下情况不会被 omitempty 跳过
var ptr *T           // nil 指针不会被跳过（除非类型是 nil-able）
var arr [5]int       // 固定长度数组，永不为空
var m map[K]V = map[K]V{}  // 空映射，Go 1.24+ omitzero 会跳过
```

**最佳实践**：切片和映射使用指针类型 `*[]int`、`*map[string]int` 以正确触发 omitempty。

### 自定义序列化的边界

实现 `MarshalJSON()` 和 `UnmarshalJSON()` 时：
- 必须返回有效 JSON，否则 marshaling 失败
- 解析时需处理所有边界情况，否则 unmarshaling 失败
- 自定义序列化覆盖所有 tag 配置（名称、omitempty 等失效）

典型应用：`time.Time` 的 RFC3339 格式、`decimal.Decimal` 的精确小数表示。

### json-iterator 的实现原理

`json-iterator` 通过**代码生成**替代运行时反射：

- 生成特定类型的高速 Marshal/Unmarshal 代码
- 避免 `reflect.TypeOf` 的接口类型转换开销
- 使用字节指针操作替代字符串拼接

性能提升：3-10 倍，取决于字段数和复杂度。

## 参考存根

```go
// 基本序列化
data, _ := json.Marshal(User{Name: "Tom"})
// {"name":"Tom"}

// omitzero（Go 1.24+）
type Config struct {
    Name string `json:"name"`
    Data []int  `json:"data,omitzero"`
}
json.Marshal(Config{Name: "test", Data: nil})
// {"name":"test"}  // Data 被跳过

// 自定义序列化
type CustomTime struct{ time.Time }
func (t CustomTime) MarshalJSON() ([]byte, error) {
    return []byte(`"` + t.Format("2006-01-02") + `"`), nil
}

// 流式解析 NDJSON
dec := json.NewDecoder(file)
for dec.More() {
    var item map[string]interface{}
    if err := dec.Decode(&item); err != nil {
        log.Fatal(err)
    }
    // 处理 item
}

// 高性能序列化（json-iterator）
var jsonIterator = jsoniter.ConfigCompatibleWithStandardLibrary
data, _ := jsonIterator.Marshal(&myStruct)
```

## 性能选择决策

| 场景 | 推荐 |
|------|------|
| < 10万次/秒序列化 | 标准库 `encoding/json` |
| > 10万次/秒，高吞吐量 | `json-iterator` |
| 需要流式处理大文件 | `json.Decoder` |
| 极简依赖 | `encoding/json`（零外部依赖） |
