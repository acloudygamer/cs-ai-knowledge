---
name: go-patterns-pro
description: Go 最佳实践技能。当编写或审查 Go 代码、设计 Go 项目、使用 Goroutines/Channels、错误处理、并发模式或依赖管理时激活。确保代码符合惯用 Go（idiomatic Go）最佳实践。
---

# Go Patterns Pro

## 核心工程实践

### 1. 惯用 Go

**必须掌握**：
- 错误处理：`if err != nil { return err }`
- 短变量声明：`:=`
- 多返回值（尤其是 error）
- 切片和映射字面量
- `go fmt` / `goimports` 格式化

### 2. 并发
- Goroutine：`go func()`
- Channel：`<-ch`、`ch <-`
- `select` 多路复用
- `sync.WaitGroup`
- `context.Context` 取消和超时
- 避免共享内存，用 channel 通信

### 3. 错误处理
- 自定义错误：`fmt.Errorf("wrap: %w", err)`
- Sentinel errors：`var ErrNotFound = errors.New("not found")`
- 避免 panic（仅真正异常）
- 错误包装和检查链

### 4. 内存管理
- 切片容量：`make([]int, 0, 10)`
- `append` 超过容量自动扩容
- 避免全局可变状态
- `sync.Map` 只用于特定场景

## 代码质量

- 包名小写、无下划线
- getter 不需要 Get 前缀
- Receiver 命名统一（通常 `r` 或 `t`）
- 接口尽量小（单一职责）

## 常见错误

1. 切片引用同一个底层数组
2. Goroutine 泄漏
3. 迭代变量闭包问题
4. 不关闭资源（defer）
