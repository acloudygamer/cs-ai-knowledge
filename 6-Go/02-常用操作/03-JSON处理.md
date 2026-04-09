# JSON处理

## encoding/json

```go
import (
    "encoding/json"
    "fmt"
)

// 结构体标签控制 JSON 字段
type User struct {
    Name     string   `json:"name"`
    Age      int      `json:"age"`
    Email    string   `json:"email,omitempty"`  // 空值忽略
    Password string   `json:"-"`                 // 忽略此字段
}

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

```go
import "github.com/json-iterator/go"

var json = jsoniter.ConfigCompatibleWithStandardLibrary

// 快速序列化
data, _ := json.Marshal(user)
// 快速反序列化
json.Unmarshal(data, &user)
```
