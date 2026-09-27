# 03-IO与外部世界

程序与外部世界的接口：文件、网络、文本格式、数据库。C++ 标准库只覆盖文件与正则，其余靠第三方库——每篇先给选型判据再给用法。主线见 [3-C++/README](../README.md)。

| 篇目 | 一句话 |
|---|---|
| [01-文件操作](01-文件操作.md) | fstream 与 std::filesystem（C++17）：路径、遍历、原子写 |
| [02-网络编程](02-网络编程.md) | 标准库无网络：Asio、cpp-httplib、cpr/libcurl 的选型与形态 |
| [03-序列化与JSON](03-序列化与JSON.md) | JSON（nlohmann/json）与二进制序列化（protobuf/flatbuffers）的取舍轴 |
| [04-正则表达式](04-正则表达式.md) | std::regex 的语法族与性能现实；何时换 RE2 |
| [05-数据库操作](05-数据库操作.md) | 原生 C API（sqlite3）与封装层（sqlite_modern_cpp/soci/sqlpp11）的分工 |
