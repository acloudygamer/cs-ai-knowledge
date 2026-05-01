# 测试

Python 自动化测试体系：pytest 框架核心机制、测试替身（Mock/Fake）、Fixture 生命周期管理、参数化驱动测试、覆盖率量化分析。

## 目录

### 框架基础
- [01-pytest基础](01-pytest基础.md) - AST 断言重写、作用域格、Fixture DAG、raises 语义、Hook 插件架构

### 测试替身
- [02-Mock与Fake](02-Mock与Fake.md) - Mock 状态机、side_effect、@patch 命名空间替换、Fake 设计原则、Spy 区别、autospec

### Fixture 体系
- [03-Fixture](03-Fixture.md) - 作用域格、yield 清理、参数化 Fixture、autouse 隐式注入、工厂 Fixture 模式

### 测试驱动
- [04-参数化测试](04-参数化测试.md) - 笛卡尔积展开、节点 ID 生成、indirect 参数化、负向测试覆盖、等价类划分

### 质量度量
- [05-覆盖率](05-覆盖率.md) - 语句/分支/MC/DC 覆盖、AST 插桩原理、覆盖率盲区、增量覆盖、突变测试
