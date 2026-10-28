# 计算机体系

> **版本基准**: universal

本章回答三个递进问题：软件与硬件之间的契约是什么，处理器怎样兑现契约，数据又怎样沿缓存、内存与设备供给执行。篇序先给 ISA，再进入微架构，避免用实现细节反推架构语义。

| 篇目 | 主链与消费的前置结论 |
| --- | --- |
| 01 硬件组成 | 取指/访存两路 → VPN→PFN → PA→通道与 DRAM 坐标 → 在途窗口与排队 → L3 域与 NUMA 放置 |
| 02 缓存与存储层次 | 01 的 VA/PA 与 64B 行 → VIPT 查询 → MSHR 与写缓冲 → MESI 权限 → TLB 覆盖 → SSD 重定向与 WAF |
| 03 指令集架构与 SIMD | ISA/微架构分界 → 执行模式与特权接口 → CISC/RISC 编码 → lane 与掩码 → 标量/向量汇编 |
| 04 指令执行 | 03 的 ISA 契约 → 预测与译码 → RAT/ROB → 端口乱序执行 → LSQ 与 Store Buffer → 顺序退休与精确异常；02 的 MSHR 用在途请求限制内存级并行 |
| 05 数据表示与字节序 | 模环与补码 → IEEE 754 字段 → 端序 → ABI 布局 → 位运算 → 宽度转换；03 的 ISA 分界解释同指令跨代代价，02 的 64B 行用于布局核算 |
| 06 GPU 与异构计算 | warp 供给 → SIMT 发散与驻留 → 输入精度与张量核 → sector 有效载荷 → BAR/DMA → 流依赖 → UM 驻留与迁移；消费 02 的缓存账、03 的掩码、04 的乱序窗口、05 的数值格式 |
| 07 并行与并发 | 强弱扩展 → SMT/L3/NUMA 放置 → 发布/获取 → CAS 条件更新 → futex 等待 → 安全回收 → 并发模型；消费 01/02/04 的拓扑、一致性与内存序 |

下游章的消费接口：02-操作系统使用 01 §二 的页表与 TLB、03 §一.3~§一.4 的执行模式与异常接口、04 §六 的精确异常、05 的端序与 ABI 布局、07 的 SMT 与拓扑；04-编程运行环境使用 03 的 ISA 与 SIMD 契约、04 的译码和退休机制；05-计算机网络使用 05 的网络序。

## 目录

### [01-硬件组成](./01-硬件组成.md)
存储程序模型、四级页表与 TLB、PCID、通道交织、DRAM 行列状态、带宽与在途窗口、L3 共享域和 NUMA

### [02-缓存与存储层次](./02-缓存与存储层次.md)
局部性与 AMAT、VIPT/PIPT、组相联、MSHR、写缓冲、MESI、TLB 覆盖与击落、FTL 和写放大

### [03-指令集架构与SIMD](./03-指令集架构与SIMD.md)
ISA/微架构契约、二进制兼容条件、执行模式与特权级、CISC/RISC 编码、向量寄存器、lane、掩码和汇编对照

### [04-指令执行](./04-指令执行.md)
顺序契约与乱序实现、预测与译码供给、寄存器重命名、ROB、执行端口、LSQ、Store Buffer、内存序和精确异常

### [05-数据表示与字节序](./05-数据表示与字节序.md)
定宽模环、补码、浮点字段、舍入、端序、结构体布局、位操作、饱和与重解释

### [06-GPU与异构计算](./06-GPU与异构计算.md)
warp 与 SIMT、驻留资源账、张量核与算术强度、sector 合并访存、PCIe DMA、流依赖和统一内存

### [07-并行与并发](./07-并行与并发.md)
强弱扩展、硬件拓扑、内存序、CAS、锁与 futex、RCU 与危险指针、消息传递和协程模型

## 学习路径

1. 先读 01，建立地址翻译和物理供给两条链。
2. 再读 02，看缓存如何过滤请求并维持多核副本权限。
3. 再读 03，分清 ISA 契约与微架构实现。
4. 再读 04，看顺序语义怎样由乱序引擎兑现。
5. 再读 05，把寄存器与内存中的位串还原成数值和布局。
6. 再读 06，比较 CPU 与 GPU 的指令和数据供给路径。
7. 最后读 07，把拓扑、内存序和原子操作落到并发模型。

## 本章术语表

| 术语（最简形式） | 全称 | 首次出现的篇 |
| --- | --- | --- |
| PC | Program Counter | 01-硬件组成.md |
| CPU | Central Processing Unit | 01-硬件组成.md |
| DRAM | Dynamic Random-Access Memory | 01-硬件组成.md |
| VA | Virtual Address | 01-硬件组成.md |
| VPN | Virtual Page Number | 01-硬件组成.md |
| PA | Physical Address | 01-硬件组成.md |
| MMIO | Memory-Mapped I/O | 01-硬件组成.md |
| PFN | Physical Frame Number | 01-硬件组成.md |
| TLB | Translation Lookaside Buffer | 01-硬件组成.md |
| PMH | Page Miss Handler | 01-硬件组成.md |
| PCID | Process-Context Identifier | 01-硬件组成.md |
| IMC | Integrated Memory Controller | 01-硬件组成.md |
| DDR5 | Double Data Rate 5 | 01-硬件组成.md |
| CAS（内存列访问） | Column Access Strobe | 01-硬件组成.md |
| SSD | Solid-State Drive | 01-硬件组成.md |
| PCIe | Peripheral Component Interconnect Express | 01-硬件组成.md |
| DMA | Direct Memory Access | 01-硬件组成.md |
| UMA | Uniform Memory Access | 01-硬件组成.md |
| NUMA | Non-Uniform Memory Access | 01-硬件组成.md |
| SRAM | Static Random-Access Memory | 02-缓存与存储层次.md |
| AMAT | Average Memory Access Time | 02-缓存与存储层次.md |
| VIPT | Virtually Indexed, Physically Tagged | 02-缓存与存储层次.md |
| PIPT | Physically Indexed, Physically Tagged | 02-缓存与存储层次.md |
| MSHR | Miss Status Holding Register | 02-缓存与存储层次.md |
| MESI | Modified, Exclusive, Shared, Invalid | 02-缓存与存储层次.md |
| FTL | Flash Translation Layer | 02-缓存与存储层次.md |
| GC | Garbage Collection | 02-缓存与存储层次.md |
| ISA | Instruction Set Architecture | 03-指令集架构与SIMD.md |
| CISC | Complex Instruction Set Computer | 03-指令集架构与SIMD.md |
| RISC | Reduced Instruction Set Computer | 03-指令集架构与SIMD.md |
| CPL | Current Privilege Level | 03-指令集架构与SIMD.md |
| EL | Exception Level | 03-指令集架构与SIMD.md |
| SIMD | Single Instruction, Multiple Data | 03-指令集架构与SIMD.md |
| SVE | Scalable Vector Extension | 03-指令集架构与SIMD.md |
| RVV | RISC-V Vector | 03-指令集架构与SIMD.md |
| ROB | Reorder Buffer | 03-指令集架构与SIMD.md |
| RAT | Register Alias Table | 04-指令执行.md |
| PRF | Physical Register File | 04-指令执行.md |
| RS | Reservation Station | 04-指令执行.md |
| BF16 | bfloat16 | 05-数据表示与字节序.md |
| GPU | Graphics Processing Unit | 06-GPU与异构计算.md |
| SM | Streaming Multiprocessor | 06-GPU与异构计算.md |
| HBM | High Bandwidth Memory | 06-GPU与异构计算.md |
| SIMT | Single Instruction, Multiple Threads | 06-GPU与异构计算.md |
| TF32 | TensorFloat-32 | 06-GPU与异构计算.md |
| PTX | Parallel Thread Execution | 06-GPU与异构计算.md |
| BAR | Base Address Register | 06-GPU与异构计算.md |
| IOMMU | Input-Output Memory Management Unit | 06-GPU与异构计算.md |
| CUDA | Compute Unified Device Architecture | 06-GPU与异构计算.md |
| UVA | Unified Virtual Address Space | 06-GPU与异构计算.md |
| UM | Unified Memory | 06-GPU与异构计算.md |
| SMT | Simultaneous Multithreading | 07-并行与并发.md |
| CAS（比较并交换） | Compare-And-Swap | 07-并行与并发.md |
| futex | Fast Userspace Mutex | 07-并行与并发.md |
| RCU | Read-Copy-Update | 07-并行与并发.md |
| HP | hazard pointer | 07-并行与并发.md |
| CSP | Communicating Sequential Processes | 07-并行与并发.md |
