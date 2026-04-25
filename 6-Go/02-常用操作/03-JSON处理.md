# JSON处理

**定义**：JSON 处理是将 Go 结构化数据与 JSON 文本相互转换的过程，核心是 `encoding/json` 标准库通过结构体 tag 控制字段命名、空值行为和类型适配。

## 序列化核心机制

### 定义断言
JSON 序列化是字段级别的反射遍历过程：`json.Marshal` 对每个导出字段检查 tag，`omitempty` 判断该字段是否应跳过，空值判定标准是"是否等于 Go 类型的零值"。

### omitzero vs omitempty 关键差异

| 标签 | nil 切片 | 空切片 `[]int{}` | nil 映射 | 空映射 `map[string]int{}` |
|------|----------|-----------------|----------|------------------------|
| 无标签 | 序列化为 `null` | `[]int{}` | `null` | `{}` |
| `omitemtpy` | 跳过 | `[]int{}` | 跳过 | `{}` |
| `omitzero`（Go 1.24+） | 跳过 | `[]int{}` | 跳过 | **跳过** |

**机制**：`omitzero` 将"零值"判定扩展到空容器（空切片、空映射），因为 Go 1.24+ 认为空容器在语义上等同于"未设置"。但 `[]int{}` 和 `map[string]int{}` 是显式初始化的非零值，仍会被序列化。

### 数学模型
`json.Marshal` 时间复杂度为 O(n)，其中 n 为字段数（不含跳过字段）。内存分配：每字段约 1 次分配（字符串拷贝）。对于 1000 字段的结构体，单次 Marshal 约 50-200μs。

### 参考存 stub

```go
data, _ := json.Marshal(User{Name: "Tom"})
// {"name":"Tom"}
```

## 自定义序列化

### 定义断言
实现 `json.Marshaler`/`json.Unmarshaler` 接口可自定义字段级序列化逻辑，优先级高于 tag。适用于类型本身语义与 JSON 表现不一致的场景（如 `time.Time` vs RFC3339 字符串）。

### 参考存 stub

```go
func (t CustomTime) MarshalJSON() ([]byte, error) {
    return json.Marshal(t.Time.Format("2006-01-02"))
}
```

## 流式解析

### 定义断言
`json.Decoder` 支持流式解析 NDJSON（每行一个 JSON 对象），避免将整个文件加载到内存。适用于日志、事件流等超大 JSON 文件。

### 参考存 stub

```go
dec := json.NewDecoder(file)
for dec.More() {
    var item map[string]interface{}
    dec.Decode(&item)
}
```

## 性能选择

### json-iterator 适用场景
当序列化性能成为瓶颈（>10万次/秒）时，`json-iterator` 通过代码生成和字节指针操作替代反射，可将性能提升 3-10 倍。但对于大多数应用，标准库足够。

### 内存分配对比
标准库每次 `json.Marshal` 产生约 `2n` 次内存分配（n=字段数）。`json-iterator` 通过 `Opts` 复用缓冲区，可将分配降至接近零。
