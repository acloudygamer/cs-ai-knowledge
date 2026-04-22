# JSON处理

Go 的 `encoding/json` 将 JSON 数据与 Go 结构体相互转换。结构体标签（tag）控制字段命名、空值处理和忽略行为。

## encoding/json

### 结构体标签

```go
type User struct {
    Name     string   `json:"name"`
    Age      int      `json:"age"`
    Email    string   `json:"email,omitempty"`  // 空值忽略
    Password string   `json:"-"`                 // 忽略此字段
}
```

### Marshal/Unmarshal

```go
// 序列化
user := User{Name: "Tom", Age: 30}
data, err := json.Marshal(user)
if err != nil {
    panic(err)
}
fmt.Println(string(data))  // {"name":"Tom","age":30}

// 格式化输出
data, _ = json.MarshalIndent(user, "", "  ")

// 反序列化
jsonStr := `{"name":"Tom","age":30}`
var u User
err = json.Unmarshal([]byte(jsonStr), &u)
if err != nil {
    panic(err)
}
fmt.Println(u.Name, u.Age)
```

### 参考样例

```go
// 处理 map
var m map[string]interface{}
json.Unmarshal([]byte(jsonStr), &m)
fmt.Println(m["name"])

// 流式解析（大量数据）
decoder := json.NewDecoder(bytes.NewReader(data))
for decoder.More() {
    var u User
    decoder.Decode(&u)
}
```

## json-iterator（高性能）

标准库 encoding/json 的替代品，性能提升显著。

### 参考样例

```go
import "github.com/json-iterator/go"

var json = jsoniter.ConfigCompatibleWithStandardLibrary

// 快速序列化
data, _ := json.Marshal(user)
// 快速反序列化
json.Unmarshal(data, &user)
```

## JSON 标签详解

| 标签 | 序列化 | 反序列化 |
|------|--------|----------|
| `json:"name"` | 正常输出 | 正常解析 |
| `json:"name,omitempty"` | 空值忽略 | 空值忽略 |
| `json:"-"` | 忽略 | 忽略 |
| `json:"name,string"` | 转字符串 | 从字符串解析 |
| `json:"name,omitempty,string"` | 空值忽略 | 从字符串解析 |
| `json:"name,omitempty,omitzero"` | 零值忽略，空切片/映射保留 | 空值忽略 |

`omitzero`（Go 1.24+）只省略零值，保留空切片和空映射。

### 参考样例

```go
type Person struct {
    // omitempty：零值时忽略（零值：空字符串、0、false、nil 切片/映射）
    Name    string   `json:"name"`
    Age     int      `json:"age"`
    Email   string   `json:"email,omitempty"`
    Phone   string   `json:"phone,omitempty"`

    // string：反序列化时将值作为字符串解析（用于 number -> string 场景）
    ID      int64    `json:"id,string"`

    // 忽略字段
    Secret  string   `json:"-"`

    // 保留原始 JSON（嵌套 JSON 字符串）
    Meta    RawMessage `json:"meta,omitempty"`
}

// string 标签常用场景：JavaScript API 兼容
// {"id": "123"} 而不是 {"id": 123}
```

## 自定义序列化

实现 `json.Marshaler` 和 `json.Unmarshaler` 接口自定义序列化逻辑。

### 参考样例

```go
import (
    "encoding/json"
    "fmt"
    "strings"
    "time"
)

// 1. 实现 json.Marshaler 接口
type UpperCaseString string

func (u UpperCaseString) MarshalJSON() ([]byte, error) {
    return json.Marshal(strings.ToUpper(string(u)))
}

// 2. 实现 json.Unmarshaler 接口
type LowerCaseString string

func (l *LowerCaseString) UnmarshalJSON(data []byte) error {
    var s string
    if err := json.Unmarshal(data, &s); err != nil {
        return err
    }
    *l = LowerCaseString(strings.ToLower(s))
    return nil
}

// 3. 自定义时间序列化
type CustomTime struct {
    time.Time
}

func (t CustomTime) MarshalJSON() ([]byte, error) {
    return json.Marshal(t.Time.Format("2006-01-02 15:04:05"))
}

func (t *CustomTime) UnmarshalJSON(data []byte) error {
    var s string
    if err := json.Unmarshal(data, &s); err != nil {
        return err
    }
    parsed, err := time.Parse("2006-01-02 15:04:05", s)
    if err != nil {
        return err
    }
    t.Time = parsed
    return nil
}

// 使用示例
type User struct {
    Name    UpperCaseString `json:"name"`
    Email   string          `json:"email"`
    Created CustomTime      `json:"created"`
}
```

## 匿名结构体与动态 JSON

临时数据结构使用匿名结构体，动态键使用 map。

### 参考样例

```go
// 1. 匿名结构体（临时数据）
data, _ := json.Marshal(struct {
    Name  string `json:"name"`
    Value int    `json:"value"`
}{
    Name:  "test",
    Value: 42,
})

// 2. 匿名嵌入
type Response struct {
    Code int
    Data struct {
        ID   int    `json:"id"`
        Name string `json:"name"`
    } `json:"data"`
}

// 3. 动态键（map）
dynamic := map[string]interface{}{
    "id":    1,
    "name":  "test",
    "extra": map[string]interface{}{
        "key": "value",
    },
}
jsonBytes, _ := json.Marshal(dynamic)
```

## 流式解析与生成

大文件使用流式 API 避免一次性加载到内存。

### 参考样例

```go
import (
    "bufio"
    "encoding/json"
    "os"
)

// 流式解析大文件
func parseLargeJSON(file string) error {
    f, err := os.Open(file)
    if err != nil {
        return err
    }
    defer f.Close()

    scanner := bufio.NewScanner(f)
    buf := make([]byte, 0, 64*1024)
    scanner.Buffer(buf, 1024*1024)

    for scanner.Scan() {
        line := scanner.Bytes()
        if len(line) == 0 {
            continue
        }
        var item map[string]interface{}
        if err := json.Unmarshal(line, &item); err != nil {
            continue
        }
        _ = item
    }
    return scanner.Err()
}

// JSON 合并补丁（RFC 6902）
func mergePatch(original, patch []byte) ([]byte, error) {
    var origMap, patchMap map[string]interface{}
    json.Unmarshal(original, &origMap)
    json.Unmarshal(patch, &patchMap)

    for k, v := range patchMap {
        if v == nil {
            delete(origMap, k)
        } else {
            origMap[k] = v
        }
    }
    return json.Marshal(origMap)
}
```

## 常见问题

### 参考样例

```go
// 1. JSON 中的数字精度丢失
// 解决：使用 json.Number 或 string 标签
type IDWithPrecision struct {
    ID int64 `json:"id,string"`
}

// 2. HTML 字符转义（> 变成 >）
// 解决：使用 htmlEscaped = false

// 3. 反序列化到 nil 映射/切片
var m map[string]int
// json.Unmarshal 会自动初始化 map
// 但切片需要预先分配
slice := make([]int, 0)
json.Unmarshal([]byte("[1,2,3]"), &slice)
```
