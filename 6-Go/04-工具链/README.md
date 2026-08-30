# 工具链

## 目录

| 文件 | 主题 |
|------|------|
| [01-go命令专题](./01-go命令专题.md) | go build/test/vet/fmt/mod 等核心命令 |
| [02-代码质量工具](./02-代码质量工具.md) | golangci-lint/staticcheck/errcheck 等 |

## 主题简介

### Go 命令专题

涵盖 go 命令的核心子命令：环境管理（go env）、代码编译（go build）、测试运行（go test）、静态分析（go vet）、代码格式化（go fmt）、模块管理（go mod/go work）。深入讲解编译管道、覆盖率模型、MVS 算法等内部机制。

### 代码质量工具

覆盖三层检查体系：语法风格层（gofmt/goimports）、语义问题层（go vet/golangci-lint）、深度分析层（staticcheck）。详解各 linter 的检查维度、并行执行模型、--fix 限制与误报率对比。
