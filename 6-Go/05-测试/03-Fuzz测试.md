# Fuzz Testing（模糊测试）

Go 1.18 引入的 fuzz testing 是测试领域的重要里程碑，专门用于发现边界条件和随机输入导致的 bug。

## 概述

Fuzz testing 通过生成大量随机、畸形或边界值输入，自动探索程序可能未处理到的代码路径。与传统测试不同，fuzzing 不需要预先知道具体的测试用例，而是让算法自动探索。

```
传统测试:  已知输入 → 验证输出 → 覆盖固定路径
Fuzz测试:  随机输入 → 探索边界 → 发现隐藏 bug
```

## 基本用法

### fuzzing 函数签名

```go
// 标准 fuzzing 函数签名 (Go 1.20+)
func FuzzXxx(f *testing.F)
```

### 最小示例

```go
package fuzz

import (
    "testing"
)

// 待测试函数
func Reverse(s string) string {
    runes := []rune(s)
    for i, j := 0, len(runes)-1; i < j; i, j = i+1, j-1 {
        runes[i], runes[j] = runes[j], runes[i]
    }
    return string(runes)
}

// 种子语料库 - 提供初始测试用例
func TestReverse(t *testing.T) {
    cases := []struct {
        input    string
        expected string
    }{
        {"hello", "olleh"},
        {"world", "dlrow"},
        {"", ""},
        {"a", "a"},
    }

    for _, c := range cases {
        got := Reverse(c.input)
        if got != c.expected {
            t.Errorf("Reverse(%q) = %q; want %q", c.input, got, c.expected)
        }
    }
}

// Fuzz 测试
func FuzzReverse(f *testing.F) {
    // 添加种子语料库（可选但推荐）
    f.Add("hello")
    f.Add("world")
    f.Add("")

    f.Fuzz(func(t *testing.T, orig string) {
        // 1. 反转两次应该回到原字符串
        rev := Reverse(orig)
        revRev := Reverse(rev)
        if revRev != orig {
            t.Errorf("Reverse(Reverse(%q)) = %q; want %q", orig, revRev, orig)
        }

        // 2. 验证字节切片转换后反转与 rune 反转结果一致
        if len(orig) > 0 {
            bytes := []byte(orig)
            // 对字节切片进行反转
            for i, j := 0, len(bytes)-1; i < j; i, j = i+1, j-1 {
                bytes[i], bytes[j] = bytes[j], bytes[i]
            }
            byteRev := string(bytes)
            runeRev := Reverse(orig)
            if byteRev != runeRev {
                t.Errorf("字节反转与 rune 反转结果不一致: %q vs %q", byteRev, runeRev)
            }
        }
    })
}
```

### 运行 Fuzz 测试

```bash
# 运行 fuzz 测试（默认 30 秒后停止）
go test -fuzz=FuzzReverse

# 运行 fuzz 测试 1 分钟
go test -fuzz=FuzzReverse -fuzztime=1m

# 运行 fuzz 测试直到发现 bug 或时间耗尽
go test -fuzz=FuzzReverse -fuzztime=30s

# 继续上次的 fuzzing（使用 crashers 目录）
go test -fuzz=FuzzReverse -fuzzcontinue

# 显示详细 fuzzing 过程
go test -fuzz=FuzzReverse -v
```

## 高级用法

### 多参数 Fuzzing

```go
func FuzzStringReplace(f *testing.F) {
    // 种子语料库：多个参数
    f.Add("hello world", "world", "go", 0)

    f.Fuzz(func(t *testing.T, s, old, new string, n int) {
        // 使用 strings.Replace 测试
        result := strings.Replace(s, old, new, n)

        // 验证：替换次数为负数时应该替换所有
        if n < 0 {
            expected := strings.ReplaceAll(s, old, new)
            if result != expected {
                t.Errorf("Replace(%q, %q, %q, %d) = %q; want %q",
                    s, old, new, n, result, expected)
            }
        }

        // 验证：old 为空字符串时，n 应该减 1
        if old == "" && n > 0 {
            // strings.Replace("", "", "x", n) = strings.Repeat("x", n+1) - len(s)
            // 这个边界条件容易被忽略
        }
    })
}
```

### 自定义 corpus 生成器

```go
func FuzzURLParse(f *testing.F) {
    // 添加各种 URL 格式作为种子
    f.Add("https://example.com/path?query=value")
    f.Add("http://localhost:8080")
    f.Add("ftp://files.server.com")
    f.Add("///unusual///path///")
    f.Add("scheme://host/path#fragment")

    f.Fuzz(func(t *testing.T, rawURL string) {
        parsed, err := url.Parse(rawURL)
        if err != nil {
            // 无效 URL 不应该导致 panic
            return
        }

        // 验证：解析后重新组装应该等价
        reconstructed := parsed.String()
        reparsed, err := url.Parse(reconstructed)
        if err != nil {
            t.Errorf("re-parse of %q failed: %v", reconstructed, err)
            return
        }

        // 验证关键字段
        if reparsed.Scheme != parsed.Scheme {
            t.Errorf("scheme mismatch: %q vs %q", reparsed.Scheme, parsed.Scheme)
        }
    })
}
```

### 结构化 Fuzzing（Go 1.20+）

```go
// 使用编码器生成复杂结构
func FuzzJSONDecode(f *testing.F) {
    // 种子：有效的 JSON 数据
    f.Add([]byte(`{"name":"test","age":42}`))
    f.Add([]byte(`[1,2,3]`))
    f.Add([]byte(`"string"`))
    f.Add([]byte(`123`))
    f.Add([]byte(`true`))
    f.Add([]byte(`null`))

    f.Fuzz(func(t *testing.T, data []byte) {
        // 测试 JSON 解析
        var v any
        err := json.Unmarshal(data, &v)
        if err != nil {
            return // 无效 JSON 是预期的
        }

        // 测试重新编码
        encoded, err := json.Marshal(v)
        if err != nil {
            t.Errorf("re-encode failed: %v", err)
            return
        }

        // 验证可以再次解析
        var v2 any
        if err := json.Unmarshal(encoded, &v2); err != nil {
            t.Errorf("re-decode failed: %v", err)
        }
    })
}
```

### 关联参数约束

```go
func FuzzMathPow(f *testing.F) {
    // base 和 exp 单独 fuzz，但验证关系
    f.Add(2.0, 10.0)
    f.Add(10.0, 2.0)
    f.Add(0.0, 0.0) // 0^0 边界

    f.Fuzz(func(t *testing.T, base, exp float64) {
        result := math.Pow(base, exp)

        // 验证基本数学性质
        if !math.IsNaN(result) && !math.IsInf(result, 0) {
            // base^0 = 1 (除了 0^0)
            if exp == 0 && base != 0 {
                if result != 1 {
                    t.Errorf("Pow(%v, 0) = %v; want 1", base, result)
                }
            }

            // 1^exp = 1
            if base == 1 && result != 1 {
                t.Errorf("Pow(1, %v) = %v; want 1", exp, result)
            }

            // 0^exp = 0 (exp > 0)
            if base == 0 && exp > 0 && result != 0 {
                t.Errorf("Pow(0, %v) = %v; want 0", exp, result)
            }
        }

        // 检测 NaN 传播
        if math.IsNaN(base) || math.IsNaN(exp) {
            if !math.IsNaN(result) {
                t.Errorf("Pow(%v, %v) = %v; want NaN", base, exp, result)
            }
        }
    })
}
```

## 实际应用场景

### HTTP Handler Fuzzing

```go
func FuzzHTTPHandler(f *testing.F) {
    handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        body, err := io.ReadAll(r.Body)
        if err != nil {
            http.Error(w, err.Error(), 400)
            return
        }

        // 解析为 JSON
        var data map[string]any
        if err := json.Unmarshal(body, &data); err != nil {
            http.Error(w, err.Error(), 400)
            return
        }

        // 简单处理：提取 name 字段
        if name, ok := data["name"].(string); ok {
            w.Write([]byte("Hello, " + name))
        } else {
            w.Write([]byte("Hello, World"))
        }
    })

    f.Fuzz(func(t *testing.T, method string, path string, body []byte) {
        // 验证 method 有效性
        if method != http.MethodGet && method != http.MethodPost &&
           method != http.MethodPut && method != http.MethodDelete {
            return // 跳过无效 method
        }

        req := httptest.NewRequest(method, path, bytes.NewReader(body))
        rr := httptest.NewRecorder()

        // 不应该 panic
        func() {
            defer func() {
                if r := recover(); r != nil {
                    t.Errorf("handler panicked: %v", r)
                }
            }()
            handler.ServeHTTP(rr, req)
        }()
    })
}
```

### 正则表达式 Fuzzing

```go
func FuzzRegexp(f *testing.F) {
    // 测试各种正则模式
    patterns := []string{
        `^\d+$`,           // 纯数字
        `^[a-zA-Z]+$`,     // 纯字母
        `^.{3,10}$`,       // 3-10 个任意字符
        `^(foo|bar)$`,     // foo 或 bar
        `\[\d+\]`,         // [数字]
    }

    for _, pattern := range patterns {
        re, err := regexp.Compile(pattern)
        if err != nil {
            continue
        }

        f.Add(pattern, "abc123")
        f.Add(pattern, "foo")
        f.Add(pattern, "")
    }

    f.Fuzz(func(t *testing.T, patternStr string, input string) {
        re, err := regexp.Compile(patternStr)
        if err != nil {
            return // 跳过无效正则
        }

        // 测试各种方法不应该 panic
        re.MatchString(input)
        re.FindString(input)
        re.FindAllString(input, -1)
        re.ReplaceAllString(input, "替换")

        // Split 也不应该有问题
        re.Split(input, -1)
    })
}
```

### 命令行参数解析 Fuzzing

```go
func FuzzFlagParse(f *testing.F) {
    f.Add([]string{"-n", "10", "-o", "output.txt"})
    f.Add([]string{"--name=John", "--count=5"})
    f.Add([]string{})

    f.Fuzz(func(t *testing.T, args []string) {
        // 每个测试需要独立的 flag 集合
        fs := flag.NewFlagSet("test", flag.ContinueOnError)

        n := fs.Int("n", 0, "number")
        s := fs.String("s", "", "string")
        b := fs.Bool("b", false, "bool")

        // 解析不应该 panic
        err := fs.Parse(args)
        if err != nil {
            return
        }

        // 验证标志位已正确设置
        _ = *n // 使用这些值避免编译器优化
        _ = *s
        _ = *b
    })
}
```

## 语料库管理

### 种子语料库结构

```bash
testdata/
└── fuzz/
    └── FuzzReverse/
        ├── seed1           # 手动创建的测试用例
        │   └── input       # bytes of "hello"
        └── FuzzJSONDecode/
            └── seed1
                └── input   # bytes of valid JSON
```

### 添加语料库文件

```bash
# 直接运行 fuzz 测试，会自动生成语料库
go test -fuzz=FuzzReverse

# 查看生成的语料库
ls -la /tmp/.../fuzz/FuzzReverse/

# 使用现有的 crashers 进行测试
go test -fuzz=FuzzReverse -fuzz=.
```

### 语料库压缩

```bash
# 运行足够长时间后，语料库可能很大
# 可以导出最小化语料库
go test -fuzz=FuzzReverse -fuzzminimize

# 查看当前语料库大小
du -sh testdata/fuzz/FuzzReverse/
```

## 常见问题与解决方案

### Fuzzing 内存泄漏

```go
// 问题：大对象在 fuzzing 循环中累积
func FuzzBad(f *testing.F) {
    var largeData [][]byte // 错误：累积内存

    f.Fuzz(func(t *testing.T, data []byte) {
        largeData = append(largeData, data) // 永远不清理
        // ...
    })
}

// 解决方案：使用有界缓存或每次创建新对象
func FuzzGood(f *testing.F) {
    f.Fuzz(func(t *testing.T, data []byte) {
        // 每次都是新对象，处理完即释放
        process(data)
    })
}
```

### 超时设置

```go
// 长时间运行的 fuzzing
func FuzzLongRunning(f *testing.F) {
    f.Fuzz(func(t *testing.T, data []byte) {
        // 设置内部超时
        ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
        defer cancel()

        select {
        case <-ctx.Done():
            t.Skip("processing too slow")
        default:
            processWithContext(ctx, data)
        }
    })
}
```

### 并行 Fuzzing

```go
// 运行多个 fuzzing 函数
// go test -fuzz=FuzzA -fuzz=B  # 不支持，只能一次一个

// 使用 -cpu 参数（仅对单元测试有效）
go test -v -fuzz=FuzzReverse -fuzztime=30s -cpu=4
```

## 最佳实践

### 1. 从单元测试迁移到 Fuzzing

```go
// 单元测试
func TestStringToInt(t *testing.T) {
    tests := []struct {
        input    string
        expected int
        err      bool
    }{
        {"123", 123, false},
        {"-456", -456, false},
        {"abc", 0, true},
    }

    for _, tt := range tests {
        t.Run(tt.input, func(t *testing.T) {
            got, err := strconv.Atoi(tt.input)
            if tt.err && err == nil {
                t.Error("expected error")
            }
            if !tt.err && got != tt.expected {
                t.Errorf("got %d, want %d", got, tt.expected)
            }
        })
    }
}

// Fuzz 测试
func FuzzStringToInt(f *testing.F) {
    // 添加已知边界用例
    f.Add("0")
    f.Add("9")
    f.Add("999999999")
    f.Add("-999999999")
    f.Add("2147483647")   // int32 max
    f.Add("-2147483648")  // int32 min
    f.Add("2147483648")   // overflow
    f.Add("-2147483649")  // underflow

    f.Fuzz(func(t *testing.T, s string) {
        // 测试转换
        got, err := strconv.Atoi(s)

        // 验证逆转换（如果成功）
        if err == nil {
            back := strconv.Itoa(got)
            // 注意：itoa 可能有符号问题
        }
    })
}
```

### 2. 识别应该 panicking 的情况

```go
func FuzzSafeParser(f *testing.F) {
    f.Add("valid input")
    f.Add("")

    f.Fuzz(func(t *testing.T, input string) {
        // 使用 recover 捕获意外 panic
        defer func() {
            if r := recover(); r != nil {
                t.Errorf("parser panicked on %q: %v", input, r)
            }
        }()

        result := Parse(input)
        _ = result // 使用结果
    })
}
```

### 3. 结合 Property-Based Testing

```go
func FuzzReverser(f *testing.F) {
    // 属性 1：双重反转等于自身
    f.Fuzz(func(t *testing.T, s string) {
        if len(s) > 1000 {
            t.Skip("too long for property test")
        }

        r1 := Reverse(s)
        r2 := Reverse(r1)
        if r2 != s {
            t.Errorf("Reverse is not an involution for %q", s)
        }
    })

    // 属性 2：反转保持长度
    f.Fuzz(func(t *testing.T, s string) {
        if len(Reverse(s)) != len(s) {
            t.Errorf("Reverse changed length of %q", s)
        }
    })

    // 属性 3：反转不影响字母大小写（如果是纯 ASCII）
    f.Fuzz(func(t *testing.T, s string) {
        if isASCII(s) {
            lower := strings.ToLower(s)
            upper := strings.ToUpper(s)

            revLower := Reverse(lower)
            revUpper := Reverse(upper)

            if revLower != revUpper {
                t.Errorf("Case not preserved in reverse of %q", s)
            }
        }
    })
}

func isASCII(s string) bool {
    for _, r := range s {
        if r > 127 {
            return false
        }
    }
    return true
}
```

## 性能优化

### 并行 Fuzzing

```bash
# 使用多个 CPU核心加速 fuzzing
go test -fuzz=FuzzReverse -fuzztime=1m -parallel=4
```

### 持续 Fuzzing

```bash
# 使用 nohup 或后台运行
nohup go test -fuzz=FuzzReverse -fuzztime=24h > fuzz.log 2>&1 &

# 使用 atomicsofuzz 等专业工具进行持续 fuzzing
```

### 覆盖率引导

```bash
# 启用覆盖率引导（默认开启）
go test -fuzz=FuzzReverse -fuzzcoverage

# 查看覆盖率报告
go tool cover -html=fuzzcov.out
```

## 调试 Crashers

### 分析 Crash 输入

```bash
# 查看 crashers 目录
ls testdata/fuzz/FuzzReverse/crashers/

# 查看 crash 日志
cat testdata/fuzz/FuzzReverse/crashers/xxx.log

# 复现 crash
go test -run=FuzzReverse/xxx
```

### 最小化 Crash Input

```bash
# 使用 go-fuzz 进行输入最小化
go-fuzz-minimize testdata/fuzz/FuzzReverse/crashers/xxx
```

## 与 CI/CD 集成

```yaml
# GitHub Actions 示例
name: Fuzz Test
on: [push, pull_request]

jobs:
  fuzz:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.26'

      - name: Run Fuzz Test
        run: |
          # 运行 10 分钟 fuzzing
          go test -fuzz=FuzzReverse -fuzztime=10m -v
        continue-on-error: true  # fuzzing 可能发现 bug

      - name: Upload Crashers
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: fuzz-crashers
          path: testdata/fuzz/FuzzReverse/crashers/
```

## 总结

Fuzz testing 是 Go 测试工具箱中的强大补充，特别适合：

- 边界条件和异常输入
- 安全敏感代码（parser、serializer、validator）
- 复杂数据结构的序列化/反序列化
- 协议实现（HTTP、WebSocket、JSON/XML/Protocol Buffers）

与传统测试结合使用，可以显著提高代码质量和安全性。
