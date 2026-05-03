# Fuzz Testing

## 定义

Fuzz testing（模糊测试）是 Go 1.18 引入的测试范式，其本质是**基于覆盖引导的随机输入生成**。Fuzzer 通过追踪代码覆盖路径，选择能触发新执行路径的输入进行变异，从而系统性探索输入空间。

与单元测试的本质区别在于**输入生成方式**：单元测试依赖人工构造的已知输入，fuzzing 依赖自动变异生成的随机输入。Fuzzing 能发现人工构造难以覆盖的边界条件——整数溢出、空指针解引用、缓冲区溢出、编码截断等。

## 数学模型

### 覆盖引导的输入生成

设输入空间为 $\mathcal{I}$ ，代码覆盖空间为 $\mathcal{C}$ ，覆盖映射：
$\text{Cov} : \mathcal{I} \rightarrow \mathcal{P}(B)$

其中 $B$ 是分支集合， $\mathcal{P}(B)$ 是 $B$ 的幂集。

**Fuzzer 的优化目标**：维护语料库 $C \subseteq \mathcal{I}$ ，最大化：
$|\bigcup_{c \in C} \text{Cov}(c)|$

即最大化覆盖的分支数。由于分支数有限（代码静态确定），该目标可达成，但需要海量迭代。

**覆盖引导算法**：
```
1. 从种子语料库开始
2. 选择一个输入执行 SUT
3. 记录覆盖的代码路径（分支覆盖率）
4. 若输入触发了新路径 → 保留，加入语料库
5. 变异输入（bit flip, byte swap, arithmetic...）
6. 重复 2-5
```

### 语料库最小化

给定 crash 输入集合 $\text{crashers} = \{c_1, c_2, \ldots, c_n\}$ ，最小化目标是找到最小的子集 $S \subseteq \text{crashers}$ 使得：
$\text{coverage}(S) = \text{coverage}(\text{crashers})$

即最小子集仍能覆盖相同的分支空间。最小化必要性：
- 未最小化的 crashers 包含冗余输入
- 导致复现测试时间长
- CI 资源浪费
- 难以分析根本原因

### 不变性谓词与 Fuzzing 本质

Fuzzing 测试基于不变性谓词 $P$ 。设 $f: X \rightarrow Y$ 为被测函数：

Fuzzer 搜索：
$\exists x \in X : \neg P(x, f(x))$

若找到则证明 $f$ 有 bug。

**不变性类型**：

| 不变性 | 形式化 | 示例 |
|--------|--------|------|
| Double-Reverse | $f(f(x)) = x$ | 字符串反转 |
| 解码-重新编码 | $\text{Decode}(\text{Encode}(x)) = x$ | JSON 序列化 |
| 交换律 | $a \oplus b = b \oplus a$ | 某些数值运算 |

### 变异操作符的形式化

| 操作 | 数学表示 | 描述 |
|------|----------|------|
| Bit flip | $\text{mut}(x, i) = x \oplus (1 \ll i)$ | 翻转第 i 位 |
| Byte swap | $\text{mut}(x, i) = x[i] \leftrightarrow x[i+1]$ | 交换相邻字节 |
| Arithmetic | $\text{mut}(x, i, \delta) = x + \delta$ | 在整数字节上做加减 |
| Dictionary | $\text{mut}(x, i, t) = x[:i] + t + x[i+1:]$ | 用已知 token 替换 |

每个变异操作的目标是探索"邻近"的输入空间。

### 时间-覆盖率权衡

设总 fuzzing 时间为 $T$ ，覆盖率 $C(T)$ 随 $T$ 增长但逐渐趋于平稳：
$\lim_{T \to \infty} C(T) = C_{\max}$

其中 $C_{\max}$ 是代码的可达分支数。实践中 $T = 24\text{h}$ 的覆盖率已足够发现大多数 bug。

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
    ├── 初始化语料库（f.Add 种子）
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
    ├── seed0/
    │       └── input        # 初始种子："hello"
    ├── seed1/
    │       └── input        # 初始种子："world"
    ├── crashers/           # 发现的 crash
    │       ├── 0a3b4c5d/
    │       │       ├── input    # crash 输入字节
    │       │       └── log      # crash 日志
    │       └── ...
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

### 为什么 fuzzing 能发现传统测试发现不了的 bug

**传统测试的局限性**：
- 已知输入 → 验证输出
- 输入由人工构造（有限的想象力）
- 难以覆盖边界条件

**Fuzzing 发现的典型 bug 类型**：

| Bug 类型 | 示例 | 为什么传统测试会遗漏 |
|----------|------|---------------------|
| 整数溢出 | `INT_MIN - 1` | 人工难以想到 |
| 空指针解引用 | 空字符串、nil slice | 通常假设非空 |
| 缓冲区溢出 | 超长输入 | 通常用正常长度 |
| 格式化字符串 | `%s` vs `%x` | 通常假设格式正确 |
| 编码问题 | UTF-8 截断 | 通常用 ASCII |

**本质**：穷举输入空间的"角角落落"。人类倾向于构造"正常"输入，忽略极端情况。Fuzzer 通过系统性地变异字节，能够探索人工构造难以覆盖的边界区域。

### fuzzing 循环的内存泄漏防护

**错误模式**：
```go
// 错误：累积性变量在 fuzz 函数外声明
func FuzzBad(f *testing.F) {
    var largeData [][]byte  // 跨越多次 fuzz 调用的状态

    f.Fuzz(func(t *testing.T, data []byte) {
        largeData = append(largeData, data)  // 永不释放
    })
}
```

**正确模式**：
```go
// 正确：每次调用内处理完即释放
func FuzzGood(f *testing.F) {
    f.Fuzz(func(t *testing.T, data []byte) {
        process(data)  // 每次处理完即释放
    })
}
```

**关键约束**：Fuzz 函数必须是无状态的。每次调用处理完应释放所有资源。累积性变量会导致：
- 内存持续增长（最终 OOM）
- 测试间状态污染
- 并行执行时的数据竞争

**为什么无状态是必须的**：Fuzz 函数的每次调用可能运行在不同的 goroutine 中，状态共享会引入数据竞争。

### 并行 fuzzing 的约束

```bash
# 不支持：一次只能 fuzz 一个函数
go test -fuzz=FuzzA -fuzz=B  # 错误

# 正确方式：多个 fuzzing 需要启动多个进程
go test -v -fuzz=FuzzReverse -fuzztime=30s -parallel=4
```

**-parallel=4 只影响单元测试并行，Fuzz 测试始终单线程**。

**为什么 fuzzing 是单线程的**：Fuzzing 的覆盖引导算法需要维护全局语料库状态，多线程访问需要同步。单线程设计避免了锁竞争，简化了实现。

### crash 的分类与严重性

| 严重性 | 描述 | 后果 | 检测方式 |
|--------|------|------|----------|
| Panic | 触发 panic | 程序崩溃 | `t.Errorf` 或 panic |
| 断言失败 | 不变性被违反 | 程序继续 | `t.Errorf` |
| 超时 | 处理时间过长 | DoS 风险 | 内部超时检测 |
| 内存泄漏 | 内存持续增长 | 最终 OOM | 外部监控 |

### 适用场景

**特别适合 fuzzing 的场景**：

| 场景 | 原因 |
|------|------|
| Parser/Validator | 输入边界多样 |
| 序列化/反序列化 | 编解码对称性可验证 |
| 协议实现 | HTTP, WebSocket, JSON |
| 数据转换 | 编码/解码往返不变性 |

**不适用场景**：

| 场景 | 原因 |
|------|------|
| 需要特定前置条件的业务逻辑 | Fuzzer 无法构造前置状态 |
| 依赖外部状态的操作 | 外部状态不在 Fuzzer 控制范围 |
| 执行时间过长的函数 | Fuzzing 需要大量迭代 |

## 验证标准

- Fuzz 函数必须是无状态的（无外部累积性变量）
- 使用不变性谓词（如往返编码、Double-Reverse）
- 使用 `f.Add` 初始化种子语料库
- 使用 `defer recover()` 处理潜在的 panic
- 慢 fuzz 函数添加内部超时或 skip 逻辑
- crashers 定期最小化并分析

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
            if back != s {  // itoa 有符号问题
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

// panic 防护
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
