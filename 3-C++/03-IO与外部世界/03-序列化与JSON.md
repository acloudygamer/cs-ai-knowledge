# 03-序列化与JSON

> 前置：[01-文件操作](01-文件操作.md)、[02-网络编程](02-网络编程.md)（字节从哪来到哪去） · 后续：[04-正则表达式](04-正则表达式.md)

> **版本基准**：C++20；C++23/26 特性行内标注。标准库示例实测环境：GCC 14.2（MinGW-w64，Windows）；第三方库示例为骨架示意，未实测。

文件与网络给的都是无结构的字节流，程序要的是有类型的对象。序列化（serialization）是两者之间的映射：把内存中的对象图展平成字节序列，反序列化是逆映射。C++ 没有运行时反射，这个映射无法自动完成——每个字段的读写代码必须有人显式写出：手写、宏生成，或由 schema 编译器（protobuf 的 `protoc`）生成。

## 本质

序列化的全部困难集中在两条约束上：

- **跨平台一致性**：字节离开本机内存后，接收方可能是另一种 CPU、另一个编译器。内存布局三要素都不可移植——对齐填充、字节序、类型宽度——所以线格式必须与内存布局解耦，逐字段显式编码。
- **版本演进**：数据活得比代码久。去年写入磁盘的文件要被今年的程序读，新旧版本必须能在同一份字节上共存。

文本格式（JSON）与二进制格式（protobuf 等）是同一映射的两种编码选择：JSON 把可读性与零配置押在前面，二进制把体积与速度押在前面。

## 机制

### JSON 三库与选型轴

| 库 | 解析形态 | 速度（典型口径） | 易用性 | 选型位置 |
|---|---|---|---|---|
| nlohmann/json | DOM | 够用 | 最高：`j["k"]` 直取，容器自动互转 | 默认答案，开发速度优先 |
| RapidJSON | DOM + SAX，支持原位解析 | 快（公开基准口径常为 nlohmann 的数倍） | 中：allocator、类型 API 偏显式 | 吞吐敏感但要可改的 DOM |
| simdjson | on-demand 遍历（另有 DOM），SIMD 指令解析 | 极致（官方口径 GB/s 级） | 按字段名直取，只读友好 | 大 JSON 只读消费，吞吐优先 |

选型轴是一条线：**开发速度 ↔ 吞吐**。轴上还有一票否决项——simdjson 的强项是只读场景，要增删改 JSON 树还得回 DOM 库。

### DOM vs SAX：两种解析形态

- **DOM**（Document Object Model）：整份 JSON 解析成内存里的树，之后随机访问、修改、再写回。内存代价与文档大小成正比。
- **SAX**（流式/事件回调）：解析器边读边回调（"遇到对象开始""遇到键""遇到值"），应用层在回调里当场消费。内存只占 O(嵌套深度)，但不能回头、不能随机访问。

判据：需要"文档"这个概念（整树在手、要改要写回）用 DOM；文档只是过路的数据流（读完字段就扔、文档远大于内存）用 SAX。

### 手写二进制序列化的三个陷阱

1. **对齐填充**：编译器为对齐在结构体字段间插入填充字节，`sizeof(Header)`（`uint8_t` + `uint32_t`）实测是 8 而非 5（GCC 14.2）。`memcpy` 整个结构体上线 = 把内容未定的填充字节也写进了格式。
2. **字节序**：x86-64 是小端，`0x01020304` 在内存里是 `04 03 02 01`。线格式必须固定一种端序，编码端显式逐字节移位，解码端反向组合——见示例。
3. **类型宽度**：`long` 在 Linux（LP64）是 8 字节、Windows（LLP64）是 4 字节。线格式只用 `<cstdint>` 的固定宽度类型（`uint32_t` 等），平台相关类型（`long`、`size_t`）禁止上线。

### protobuf 与 flatbuffers：schema 路线的两种取舍

两者都由 schema 文件编译出 C++ 类，把上面三个陷阱全部接管：

- **Protocol Buffers（protobuf）**：编码为 varint 压缩的 tag-length-value 流，体积小；读写都要经过生成的对象。schema 演进纪律由 tag 编码支撑——**只加字段、字段编号（tag）永不复用、字段类型不改**；旧代码遇到未知 tag 直接跳过，新代码读旧数据时缺失字段取默认值，前后向兼容由此而来。
- **FlatBuffers**：序列化产物本身带偏移表，**不解包就能随机访问字段**（零拷贝读），适合读多写少、大 buffer 只取少数字段（游戏资源、模型文件）；代价是构建缓冲区的 API 绕一层 builder，不适合频繁改写的对象。

### 版本演进纪律（与具体库无关）

能加不能删、不能改；删除字段的正确做法是新版本停止使用它但保留编号占位；未知内容必须跳过而非报错。违反任意一条，旧数据或旧程序就会在某天静默读错。

## 连接

字节落地走 [01-文件操作](01-文件操作.md) 的二进制模式，上线走 [02-网络编程](02-网络编程.md) 的字节流；JSON 文本的进一步模式抽取见 [04-正则表达式](04-正则表达式.md)。

## 示例

**实测**（GCC 14.2 MinGW，`-std=c++20`）：对齐陷阱的实测证据 + 端序安全的手写编解码——

```cpp
#include <cstdint>
#include <cstdio>
#include <vector>

struct Header { std::uint8_t tag; std::uint32_t len; };  // 对齐填充：sizeof 不是 5

void put_u32(std::vector<std::uint8_t>& v, std::uint32_t x) {
    for (int i = 0; i < 4; ++i)
        v.push_back(static_cast<std::uint8_t>(x >> (i * 8)));  // 线格式固定小端
}
std::uint32_t get_u32(const std::uint8_t* p) {
    std::uint32_t x = 0;
    for (int i = 0; i < 4; ++i)
        x |= static_cast<std::uint32_t>(p[i]) << (i * 8);
    return x;
}

int main() {
    std::printf("%zu\n", sizeof(Header));        // 8：填充字节的实证
    std::vector<std::uint8_t> buf;
    put_u32(buf, 0x01020304);
    std::printf("%02x %02x %02x %02x\n", buf[0], buf[1], buf[2], buf[3]);
    std::printf("%08x\n", get_u32(buf.data()));  // 01020304：往返无损
}
```

实测输出：

```text
8
04 03 02 01
01020304
```

**骨架示意（未实测）**：nlohmann/json 的 DOM 形态——

```cpp
#include <nlohmann/json.hpp>
using nlohmann::json;

json j = json::parse(R"({"name":"alice","tags":["a","b"]})");
std::string name = j["name"];            // DOM：解析成树后随机访问
j["age"] = 30;                           // 树可改
std::string out = j.dump();              // 写回文本
```
