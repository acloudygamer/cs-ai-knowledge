# 常用操作

Python 日常开发中的高频工具操作，覆盖文件 I/O、网络通信、数据序列化、错误处理、时间计算、文本匹配、模块管理、持久化、日志、调试和配置等 13 个核心场景。

## 目录

### 基础工具
- [01-文件操作](01-文件操作.md) - 文件描述符、页缓存、mmap、文件锁
- [02-网络请求](02-网络请求.md) - HTTP/websocket、连接池、超时、重试
- [03-JSON处理](03-JSON处理.md) - 序列化/反序列化、词法分析、流式解析
- [04-错误处理](04-错误处理.md) - 异常传播链、自定义异常、RAII 模式
- [05-日期时间](05-日期时间.md) - naive/aware datetime、时区转换、timedelta 算术
- [06-正则表达式](06-正则表达式.md) - FSA/NFA、Thompson 构造、回溯灾难

### 模块与数据
- [07-模块与包](07-模块与包.md) - import 机制、sys.modules、循环导入、虚拟环境
- [08-数据库操作](08-数据库操作.md) - SQLite/ORM、事务 ACID、WAL、连接池
- [09-日志记录](09-日志记录.md) - Logger 树、Handler 链、Formatter 解耦、ELK 集成

### 调试与工具
- [10-调试技术](10-调试技术.md) - pdb、断点、cProfile、tracemalloc
- [11-CLI应用](11-CLI应用.md) - argparse/click/typer、FST 状态机、子命令
- [12-f-string格式化](12-f-string格式化.md) - 编译期 AST、FORMAT_VALUE 字节码、`__format__` 协议
- [13-配置文件处理](13-配置文件处理.md) - TOML/YAML/JSON、层叠合并、环境变量覆盖
