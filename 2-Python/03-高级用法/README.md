# 高级用法

Python 进阶主题，深入语言底层机制与工程化实践：并发模型、内存分配器、性能分析、类型系统现代化、打包分发、CI/CD 流水线、上下文协议，以及前沿版本新特性。

## 目录

### 底层与性能
- [01-并发与异步](01-并发与异步.md) - GIL、线程/进程/协程、asyncio、TaskGroup
- [02-内存管理](02-内存管理.md) - 引用计数、GC 分代、obmalloc、循环引用
- [03-性能优化](03-性能优化.md) - Amdahl 定律、cProfile、`__slots__`、Faster CPython

### 语言工程化
- [04-类型提示深入](04-类型提示深入.md) - TypeVar/Protocol/NewType/TypedDict、结构子类型
- [05-打包与分发](05-打包与分发.md) - pyproject.toml、wheel/sdist、CSP 依赖解析
- [06-CI_CD集成](06-CI_CD集成.md) - GitHub Actions、缓存策略、Docker 多阶段构建

### 协议与前沿
- [07-上下文管理器](07-上下文管理器.md) - `__enter__`/`__exit__`、`@contextmanager`、事务原子性
- [08-Python3.14新特性](08-Python3.14新特性.md) - t-string、惰性类型提示、子解释器、尾调用
