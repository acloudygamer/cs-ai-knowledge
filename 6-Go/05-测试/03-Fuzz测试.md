# Fuzz Testing（模糊测试）

## 定义

Go 1.18 引入的 fuzz testing 是测试领域的重要里程碑，专门用于发现边界条件和随机输入导致的 bug。其本质是**基于覆盖引导的随机输入生成**——fuzzer 通过追踪代码覆盖路径，选择能触发新执行路径的输入进行变异，从而系统性地探索输入空间。

## 数学模型

### 覆盖引导的输入生成

```
fuzzing 的输入空间：所有可能的字节序列
F: 输入空间 → 代码覆盖空间

覆盖引导原理：
  1. 从种子语料库开始
  2. 选择一个输入执行 SUT
  3. 记录覆盖的代码路径（分支覆盖率）
  4. 若输入触发了新路径 → 保留，加入语料库
  5. 变异输入（bit flip, byte swap, arithmetic...）
  6. 重复 2-5

覆盖空间是有限的（分支数有限），但输入空间是无限的。
fuzzing 通过系统性探索，在有限时间内最大化覆盖。
```

### 语料库最小化

```
给定一个 crash 输入集合：
  crashers = {c1, c2, ..., cn}

最小化目标：
  找到最小的子集 S ⊆ crashers
  使得 coverage(S) = coverage(crashers)

算法：
  1. 按触发顺序排序 crashers
  2. 逐一移除，测试覆盖率是否变化
  3. 若覆盖率不变，丢弃；若变，保留

最终语料库：能触发所有 crash 的最小输入集
```

### 逆变不变性（Inverse Invariance）

```
大多数 fuzzing 测试基于**逆变性**：

对于函数 f：
  1. Double-Reverse 不变性：
     Reverse(Reverse(x)) = x（对所有 x）

  2. 解码-重新编码不变性：
     Decode(Encode(x)) = x

  3. 交换律不变性（特定操作）：
     a + b = b + a（某些数值运算）

若不变性被违反 → 发现 bug
```

## 数据流

### fuzzing 执行流

<pre>
f.Fuzz(func(t *testing.T, orig string) {
    rev := Reverse(orig)
    revRev := Reverse(rev)
    if revRev != orig {
        t.Errorf("...")
    }
})

    │
    ├── 初始化语料库（f.Add）
    │
    ├── 选择输入（从语料库或变异生成）
    │
    ├── 字节级变异：
    │   ├── bit flip（逐位翻转）
    │   ├── byte swap（相邻字节交换）
    │   ├── arithmetic（加减常量）
    │   └── dictionary substitution（已知 tokens）
    │
    ├── 执行 fuzz 函数
    │
    ├── 记录覆盖率
    │
    ├── 若触发新路径 → 保存到语料库
    │
    └── 若 crash/t.Errorf → 保存到 crashers 目录
</pre>

### Go fuzzing 的语料库管理

<pre>
testdata/fuzz/FuzzReverse/
    ├── seed0/           # 初始种子
    │   └── input        # "hello"
    ├── seed1/
    │   └── input        # "world"
    ├── crashers/        # 发现的 crash
    │   ├── 0a3b4c5d/
    │   │   ├── input    # crash 输入字节
    │   │   └── log      # crash 日志
    │   └── ...
    └── minimize/
        └── ...          # 最小化后的 crash

go test -fuzz=FuzzReverse：
    ├── 首次运行：使用 seed 语料库
    ├── 运行中发现 crash → 保存到 crashers/
    └── -fuzzcontinue：继续上次的 fuzzing
</pre>

### crashers 目录的数据流

<pre>
Crash 发现
    │
    ├── 保存输入到 crashers/<hash>/
    │       │
    │       ├── input：原始 crash 输入
    │       └── log：panic 信息 / 测试失败日志
    │
    └── 后续复现
            │
            ├── go test -run=FuzzReverse/<crasher_name>
            │       └── 重新运行该特定输入
            │
            └── go test -fuzz=FuzzReverse -fuzz=.
                    └── 继续 fuzzing（包括已知的 crashers）
</pre>

## 机制

### 为什么 fuzzing 能发现传统测试发现不了的 bug？

```
传统测试的问题：
  - 已知输入 → 验证输出
  - 输入由人工构造（有限的想象力）
  - 难以覆盖边界条件

Fuzzing 的优势：
  - 随机/变异输入 → 自动探索
  - 能发现：
    1. 整数溢出（INT_MIN - 1）
    2. 空指针解引用（空字符串、nil slice）
    3. 缓冲区溢出（超长输入）
    4. 格式化字符串漏洞（%s vs %x）
    5. 编码问题（UTF-8 截断、多字节字符）

本质：穷举输入空间的"角角落落"
```

### 内存泄漏的防护

```
Fuzzing 循环中的内存问题：

错误模式：
  func FuzzBad(f *testing.F) {
      var largeData [][]byte  // 错误：累积

      f.Fuzz(func(t *testing.T, data []byte) {
          largeData = append(largeData, data)  // 永不释放
      })
  }

正确模式：
  func FuzzGood(f *testing.F) {
      f.Fuzz(func(t *testing.T, data []byte) {
          process(data)  // 每次处理完即释放
      })
  }

关键约束：
  - Fuzz 函数必须是无状态的
  - 每次调用处理完应释放所有资源
  - 避免在函数外声明累积性变量
```

### 并行 fuzzing 的约束

```
go test -fuzz=FuzzA -fuzz=B 不支持：
  一次只能 fuzz 一个函数

正确方式：
  go test -v -fuzz=FuzzReverse -fuzztime=30s -parallel=4
    │
    ├── -parallel=4 只影响单元测试并行
    ├── Fuzz 测试始终单线程
    └── 多个 fuzzing 需要启动多个进程
```

## 参考存根

```go
// 基本 fuzzing
func Reverse(s string) string {
    runes := []rune(s)
    for i, j := 0, len(runes)-1; i < j; i, j = i+1, j-1 {
        runes[i], runes[j] = runes[j], runes[i]
    }
    return string(runes)
}

func FuzzReverse(f *testing.F) {
    f.Add("hello")
    f.Add("world")
    f.Add("")

    f.Fuzz(func(t *testing.T, orig string) {
        rev := Reverse(orig)
        revRev := Reverse(rev)
        if revRev != orig {
            t.Errorf("Reverse(Reverse(%q)) = %q", orig, revRev)
        }
    })
}

// 边界条件覆盖
func FuzzStringToInt(f *testing.F) {
    f.Add("0")
    f.Add("9")
    f.Add("2147483647")   // int32 max
    f.Add("-2147483648")  // int32 min
    f.Add("2147483648")   // overflow

    f.Fuzz(func(t *testing.T, s string) {
        got, err := strconv.Atoi(s)
        if err == nil {
            back := strconv.Itoa(got)
            if back != got {  // 注意：itoa 有符号问题
                t.Errorf("itoa(atoi(%q)) = %d", s, got)
            }
        }
    })
}

// JSON fuzzing
func FuzzJSONDecode(f *testing.F) {
    f.Add([]byte(`{"name":"test"}`))
    f.Add([]byte(`[1,2,3]`))
    f.Add([]byte(`"string"`))

    f.Fuzz(func(t *testing.T, data []byte) {
        var v any
        if err := json.Unmarshal(data, &v); err != nil {
            return
        }
        encoded, err := json.Marshal(v)
        if err != nil {
            t.Errorf("re-encode failed: %v", err)
        }
        var v2 any
        if err := json.Unmarshal(encoded, &v2); err != nil {
            t.Errorf("re-decode failed: %v", err)
        }
    })
}
```

## 最佳实践

### 识别应该 panicking 的情况

```go
func FuzzSafeParser(f *testing.F) {
    f.Add("valid input")
    f.Add("")

    f.Fuzz(func(t *testing.T, input string) {
        defer func() {
            if r := recover(); r != nil {
                t.Errorf("parser panicked on %q: %v", input, r)
            }
        }()
        result := Parse(input)
        _ = result
    })
}
```

### 结合 Property-Based Testing

```go
func FuzzReverser(f *testing.F) {
    // 属性 1：双重反转等于自身
    f.Fuzz(func(t *testing.T, s string) {
        if len(s) > 1000 {
            t.Skip("too long")
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
}
```

## 常见问题与解决方案

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 内存泄漏 | 累积性变量在 fuzz 函数外 | 每次 fuzz 函数内处理完即释放 |
| 超时 | 处理太慢 | 设置内部 ctx 超时，t.Skip |
| 假阳性 | 边界条件误报 | 调整属性验证逻辑 |
| 语料库爆炸 | 保留太多输入 | go test -fuzzminimize |

## 性能优化

```
并行 fuzzing：
  # 使用多核加速
  go test -fuzz=FuzzReverse -fuzztime=1m -parallel=4

  注意：-parallel 只影响单元测试，Fuzz 测试单线程

持续 fuzzing：
  nohup go test -fuzz=FuzzReverse -fuzztime=24h > fuzz.log 2>&1 &

覆盖率引导：
  go test -fuzz=FuzzReverse -fuzzcoverage
  go tool cover -html=fuzzcov.out
```

## 与 CI/CD 集成

```yaml
# GitHub Actions
- name: Run Fuzz Test
  run: |
    go test -fuzz=FuzzReverse -fuzztime=10m -v
  continue-on-error: true

- name: Upload Crashers
  if: failure()
  uses: actions/upload-artifact@v4
  with:
    name: fuzz-crashers
    path: testdata/fuzz/FuzzReverse/crashers/
```

## 适用场景

Fuzzing 特别适合：
- 边界条件和异常输入（parser、validator）
- 安全敏感代码（序列化/反序列化）
- 协议实现（HTTP、WebSocket、JSON）
- 数据转换（编码/解码）
