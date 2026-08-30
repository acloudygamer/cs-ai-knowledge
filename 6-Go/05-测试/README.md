# 测试

## 目录

| 文件 | 主题 |
|------|------|
| [01-单元测试](./01-单元测试.md) | testing 包、表驱动测试、Mock、覆盖率 |
| [02-集成测试](./02-集成测试.md) | httptest、Testcontainers、事务回滚 |
| [03-Fuzz测试](./03-Fuzz测试.md) | 覆盖引导模糊测试、语料库、crashers |

## 主题简介

### 单元测试

基于 Go 标准库 testing 包的单元测试机制。核心概念包括：表驱动测试的惯用模式、Mock 接口隔离模型、TestMain 的包级别 setup/teardown、子测试并行控制、覆盖率衡量。

### 集成测试

通过真实依赖验证组件协作正确性。涵盖 httptest 模拟 HTTP、Testcontainers 启动真实容器、数据库事务回滚隔离策略。分析集成测试比单元测试慢的数量级原因及 CI 分阶段执行方案。

### Fuzz 测试

Go 1.18 引入的覆盖引导模糊测试。深入讲解语料库管理、crashers 目录、内存泄漏防护、并行 fuzzing 约束。涵盖 JSON/Parser/FuzzReverse 等典型场景与 CI/CD 集成实践。
