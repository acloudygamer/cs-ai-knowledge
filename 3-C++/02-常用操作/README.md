# 常用操作

> 掌握 C++ 开发中常用的核心操作与工具链

## 核心概念

- **I/O 抽象**：流式 I/O、内存映射、文件锁
- **网络通信**：TCP/UDP、HTTP、Proactor 模式
- **数据格式**：JSON、正则表达式、二进制序列化
- **构建系统**：CMake、依赖图拓扑排序、包管理
- **持久化**：数据库操作、文件原子性

## 路由表

| 编号 | 文件 | 描述 |
|------|------|------|
| 01 | [文件操作](./01-文件操作.md) | 流式 I/O、mmap、文件锁、原子写入 |
| 02 | [网络请求](./02-网络请求.md) | TCP/UDP、HTTP、libcurl、Asio Proactor |
| 03 | [JSON处理](./03-JSON处理.md) | nlohmann/json、ADL 序列化、JSONPatch |
| 04 | [错误处理](./04-错误处理.md) | 异常安全、RAII、noexcept、移动语义 |
| 05 | [STL算法](./05-STL算法.md) | Introsort、erase-remove、执行策略、迭代器概念 |
| 06 | [日期时间](./06-日期时间.md) | Chrono 库、Duration、Time Point、时区转换 |
| 07 | [正则表达式](./07-正则表达式.md) | NFA/DFA、Kleene 代数、回溯机制、贪婪匹配 |
| 08 | [CMake构建](./08-CMake构建.md) | DAG 拓扑排序、生成器表达式、find_package |
| 09 | [包管理工具](./09-包管理工具.md) | vcpkg/Conan 依赖求解、SAT、vcpkg triplets |
| 10 | [数据库操作](./10-数据库操作.md) | ACID、2PL/MVCC、SQLite/SOCI/libpqxx、ORM |
| 11 | [序列化](./11-序列化.md) | Protocol Buffers、Varint 编码、版本兼容 |
| 12 | [预处理与宏](./12-预处理与宏.md) | Token 替换、do-while(0)、条件编译、VA_ARGS |
