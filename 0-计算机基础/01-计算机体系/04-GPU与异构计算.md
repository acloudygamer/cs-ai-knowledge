# GPU 与异构计算

> **版本基准**: universal

## 定义

异构计算是使用不同类型处理器（CPU+GPU/FPGA）协同完成计算，通过各自擅长的任务类型实现优势互补。CPU 设计追求低延迟（Latency-optimized），擅长复杂分支和串行任务；GPU 设计追求高吞吐（Throughput-optimized），擅长大规模数据并行任务。

两者核心差异在于缓存层级和运算单元数量的取舍：CPU 用大缓存弥补内存延迟（以延迟换带宽），GPU 用海量线程掩盖内存延迟（以吞吐换延迟）。GPU 的设计哲学是：如果有足够多的线程在运行，总有一个线程的内存访问不阻塞，因此可以持续利用计算单元。

**归约终点**：GPU 的计算模型可归约为"大规模同步数据流"——所有线程执行相同代码（SIMT），通过硬件屏障实现同步，数据级并行（Data-Level Parallelism，DLP）转化为吞吐率。

## 数学模型

### GPU 理论吞吐

GPU 的峰值浮点吞吐取决于流式多处理器（SM）数量、时钟频率和每周期指令发射数：

$$
TP_{GPU} = \text{SM}_{数量} \times \frac{\text{Warp}_{大小}}{\text{周期}} \times f_{GPU} \times \text{IPC}_{warp}
$$

典型值：80 SM × 32 线程/warp × 1.4 GHz × 2 FLOPs/周期 = 7.2 TFLOP/s（FP32）。

### Warp 调度与隐藏延迟

GPU 的计算延迟隐藏机制通过快速切换 Warp 实现。当一个 Warp 等待内存访问时，调度器切换到另一个 Warp 继续执行：

$$
T_{总周期} = \frac{T_{计算} + T_{内存等待}}{\text{活跃 Warp 数}}
$$

理想情况下，当 Warp 切换无代价且活跃 Warp 数足够多时，内存等待时间被计算时间完全隐藏。

### 内存带宽饱和模型

$$
U_{bw} = \frac{B_{实际}}{B_{理论}} = \frac{\text{活跃 warp 数} \times \text{每 warp 带宽需求}}{B_{理论}}
$$

当 $U_{bw} < 50\\%$ 时，计算单元饥饿（memory bound）；当 $U_{bw} > 80\\%$ 时，计算单元饱和（compute bound）。

### Roofline 模型

算术强度（Arithmetic Intensity，AI）决定 kernel 是 compute-bound 还是 memory-bound：

$$
\text{性能} = \min(\text{AI}_{实际} \times \text{带宽}, \text{峰值性能})
$$

其中算术强度 $AI = \frac{\text{浮点运算数}}{\text{字节传输量}}$ 。

```
        TFLOP/s
          ▲
    峰值  ┤        ● 矩阵乘 (AI=200)
    性能  │             ● GEMM
          │                ●
          │            ●
          │        ●
    Roofline ●─────────────● AI
          │    / (AI × 带宽)
          │ /
          └──────────────────► AI (FLOPs/Byte)
```

### L2 Cache 命中率对内存流量影响

$$
B_{实际} = B_{DRAM} \times (1 - H_{L2}) + B_{global} \times H_{L2}
$$

其中 $H_{L2}$ 为 L2 命中率， $B_{global}$ 为全局内存带宽。当 $H_{L2}$ 提升时，实际内存流量降低， $U_{bw}$ 降低。

### Warp 调度优先级数学

Warp Scheduler 采用 oldest-ready-first 策略：扫描所有 Warp，选择等待最久且操作数已就绪的 Warp 发射。调度延迟 $L_{schedule}$ 近似为：

$$
L_{schedule} = \frac{N_{warp}}{W_{dispatch\\_width}}
$$

其中 $N_{warp}$ 是活跃 Warp 数， $`W_{dispatch\_width}`$ 是每周期发射的 Warp 数（通常为 2）。当 $`N_{warp} \gg W_{dispatch\_width}`$ 时，调度器始终有选择余地，流水线保持满载。

### 共享内存 Bank Conflict 的量化

共享内存分为 32 个 bank（每个 bank 4 字节宽度）。当 $N$ 个线程访问 $N$ 个不同 bank 且地址差为 4 字节的倍数时，并发访问；否则发生冲突，最坏串行化：

$$
T_{bank} = \begin{cases}
1 \text{ 周期} & \text{无冲突} \\
N \text{ 周期} & \text{所有线程访问同一 bank} \\
\end{cases}
$$

Bank conflict 比率 $r_{conflict} = \frac{T_{实际} - 1}{N - 1}$ 。

### Tensor Core 矩阵乘法数学

矩阵乘累加（MMA）执行 $D = A \times B + C$ ，数学形式为：

$$
D_{m,n} = \sum_{k=0}^{K-1} A_{m,k} \times B_{k,n} + C_{m,n}
$$

每周期完成 $M \times N \times K$ 次乘累加。Tensor Core 将 $K$ 维度展开在流水线中，实现高吞吐。

## 数据流

<pre>
CPU（主机）                              GPU（设备）
─────────                               ─────────
控制逻辑（复杂分支，low arithmetic intensity）
    │                                    ↑
    │ PCIe/NVLink                        │
    │ 32 GB/s / 300-900 GB/s            │
    │ 延迟：~1μs / ~100ns               │
    ↓                                    │
┌────────────────────────────┐          │
│ Host Memory (DDR)         │          │
│  │                        │          │
│  ↓ cudaMemcpy (同步/异步)  │          │
└────────────────────────────┘          │
    │ 复制到 Device Memory              │
    │ (H2D 或 D2H)                     │
    ↓                                    │
┌────────────────────────────┐          │
│ Device Memory (GDDR/HBM)  │          │
│  带宽：500-1000 GB/s       │          │
│  延迟：~500ns             │          │
│  ↓                        │          │
│  L2 Cache（~6MB/SM）      │          │
│  ↓                        │          │
│  L1 Cache/共享内存        │          │
│  (128KB/SM)               │          │
│  ↓                        │          │
│  SM (Streaming Multiprocessor)        │
│  ├──→ Warp Scheduler（每个 SM 两个）  │
│  │    └──→ 发射 Ready Warp 到执行单元 │
│  │         └──→ 32 线程并行执行       │
│  │              └──→ CUDA Core (ALU) │
│  │                                   │
│  ├──→ 共享内存 (64KB/SM)            │
│  │    └──→ Bank 冲突检测             │
│  └──→ 寄存器文件 (64KB/SM)           │
│       └──→ 256KB 物理寄存器           │
└─────────────────────────────────────┘
</pre>

**数据所有权在 CPU-GPU 间的变换**：

<pre>
Host Memory (CPU 可访问)
    │
    │ cudaMemcpy H2D（同步：CPU 阻塞；异步：CUDA 流）
    ↓
Device Memory (GPU 可访问)
    │
    │ L2 Cache 命中检查
    ├──→ 命中 → 直接供 SM 使用
    └──→ 未命中 → 从 Device Memory 加载
              │
              ↓
         L1 Cache / 共享内存
              │
              ↓
         SM (执行计算)
              │
              ↓
         结果写回 Device Memory
              │
    │ cudaMemcpy D2H（GPU → CPU）
    ↓
Host Memory (CPU 可访问)
</pre>

**Warp 执行数据流**：

<pre>
Warp 0  [线程 0-31] ──► IFetch ──► Decode ──► EX ──► MEM ──► WB
  │                                                        ↑
  │  (当前 warp 停顿)                                       │
  ├─► Warp 1  [线程 32-63] ──► ...                        │
  │                                                        │
  ├─► Warp 2  [线程 64-95] ──► ...                        │
  │    (分支分歧：部分线程走 then，部分走 else)              │
  │                                                        │
  └─► 等待所有分支完成 ◄────────────────────────────────────┘
</pre>

**矩阵乘数据流（GEMM）**：

<pre>
矩阵 A (M×K)              矩阵 B (K×N)
    │                          │
    ↓ 分块到 共享内存           ↓ 分块到 共享内存
Block A (16×16)            Block B (16×16)
    │                          │
    ↓ 每个线程计算              ↓
    │  一个输出元素              │
    ↓                          ↓
结果矩阵 C (M×N) ←── 累加到 寄存器 → 写回
</pre>

**Tensor Core MMA 数据流**：

<pre>
矩阵 A (M×K, FP16) ──► Warp 级矩阵寄存器
矩阵 B (K×N, FP16) ──► Warp 级矩阵寄存器
矩阵 C (M×N, FP32) ──► 累加器寄存器
         │
         ▼
    8×4×4 子矩阵乘法（D= A×B + C）
         │
         ▼
    输出矩阵 D (M×N, FP16/FP32)
</pre>

## 机制

### GPU 架构

**SIMT（Single Instruction Multiple Thread）执行模型**：

GPU 不是传统 SIMD（数据并行），而是 SIMT（线程并行）。32 线程组成一个 Warp，同一 Warp 内所有线程执行相同指令但处理不同数据。当分支发散时（if-else），Warp 内的线程会串行执行两个分支，未执行分支的线程被屏蔽（Active Mask）。

**SIMT 与 SIMD 的本质区别**：

SIMD 中，数据元素严格按 lane 执行同一条指令，硬件实现简单但缺乏灵活性。SIMT 将 32 个线程编为一个 Warp，每个线程有独立的 PC 和寄存器状态，但同一 Warp 内必须执行相同指令——硬件上相当于 32 个并行执行单元由同一个指令流驱动，兼具 SIMD 的效率（单指令流）和 SIMT 的灵活性（线程级独立控制流）。

**Warp 分支分歧（Branch Divergence）**：

```cuda
if (threadIdx.x < 16) {
    // Warp 中线程 0-15 执行
    y = sqrt(x);
} else {
    // Warp 中线程 16-31 执行
    y = x * x;
}
// 两分支串行执行，部分线程空闲
```

**约束条件**：
- Warp（32 线程）是最小调度单元
- 共享内存在同一 block 线程可见
- 全局内存访问需要合并（Coalescing）以充分利用带宽

**违规后果**：
- **Warp 分支分歧**：if-else 导致一个 Warp 内线程执行两个分支，串行化降低有效并行度
- **Bank Conflict（银行冲突）**：共享内存分为 32 个 bank（每个 bank 4 字节），相邻线程访问相邻地址导致 bank 冲突，最坏情况串行化 32 倍
- **非合并访问（Non-Coalesced Access）**：线程访问全局内存不连续时，每个线程产生独立内存请求，带宽利用率骤降至 ~10%

### CPU-GPU 互联

PCIe 带宽是异构计算的阿克琉斯之踵。GPU 计算能力增长（每代 ~50%）远超 PCIe 带宽增长（每代 ~30%）。

| 互联 | 带宽 | 延迟 | 场景 |
|------|------|------|------|
| PCIe 4.0 x16 | 32 GB/s | ~1 μs | 单 GPU |
| PCIe 5.0 x16 | 64 GB/s | ~1 μs | 单 GPU |
| NVLink 4.0 | 900 GB/s | ~100 ns | 多 GPU/直连 |
| CXL | 256 GB/s | ~200 ns | CPU-GPU 共享内存 |

**PCIe 瓶颈的实际影响**：

对于 AI 推理场景，若模型参数为 7B（FP16，14GB）， PCIe 4.0 x16 传输需 ~0.5 秒，而实际推理可能只需 0.1 秒——数据传输成为主要瓶颈。

**NVLink 的拓扑优势**：

NVLink 不通过 PCIe 总线，而采用点对点高速互联（每链路 50 GB/s，双向 100 GB/s）。8-link NVLink 4.0 提供 900 GB/s 双向带宽，是 PCIe 5.0 x16 的 14 倍。多 GPU 系统使用 NVLink Mesh 拓扑，每 GPU 与其他 GPU 均有直接链路，避免了交换机瓶颈。

### Tensor Core

矩阵乘累加（MMA）专用单元，执行 $D = A \times B + C$ ：

- A: MXK 矩阵，B: KXN 矩阵，C/D: MXN 矩阵
- 混合精度：FP16 输入，FP32 累加（防止精度损失）
- 每个 Tensor Core 每周期执行 256 FLOPs（FP16），FP8 达 4096 FLOPs/周期
- NVIDIA Hopper FP8 Tensor Core 支持 Transformer 引擎加速

**Tensor Core 的数据流**：

Tensor Core 内部将 MXN 矩阵划分为 8×4×4 的子矩阵块（A、B 是 8×4，C/D 是 8×4），每个子矩阵块由一个 warp（32 线程）在 8 个时钟周期内完成乘累加。多个 Tensor Core 并行工作，实现高吞吐。

**WMMA API 的编程模型**：

```cuda
// 使用 WMMA API 显式调度 Tensor Core
wmma::fragment<wmma::matrix_a, m, n, k, half, wmma::row_major> a_frag;
wmma::fragment<wmma::matrix_b, m, n, k, half, wmma::col_major> b_frag;
wmma::fragment<wmma::accumulator, m, n, k, float> c_frag;
// 加载矩阵片段到 Tensor Core 寄存器
wmma::load_matrix_sync(a_frag, A_ptr, stride);
wmma::load_matrix_sync(b_frag, B_ptr, stride);
wmma::load_matrix_sync(c_frag, C_ptr, stride);
// 执行 MMA
wmma::mma_sync(c_frag, a_frag, b_frag, c_frag);
// 存储结果
wmma::store_matrix_sync(D_ptr, c_frag, stride, wmma::mem_row_major);
```

**约束条件**：
- 输入矩阵需满足维度对齐（M/N/K 为 8 的倍数）
- 需显式调用 `wmma` API 或使用 CUTLASS 库
- 累加器位宽必须大于等于输入位宽（防止溢出）

### CUDA 编程模型

**线程层次结构**：
- `thread`：最小执行单元
- `block`：一组线程（最多 1024），共享共享内存
- `grid`：所有 block，共享全局内存

**共享内存的物理本质**：

共享内存是 L1 Cache 的可编程版本，位于 SMX 片上，延迟 ~1ns，带宽 1.5 TB/s（是 L1D Cache 的 1/2，但远高于全局内存）。它的核心用途是作为用户管理的软件缓存，避免重复从全局内存加载数据。

**约束条件**：
- Grid/Block 维度需匹配算术强度
- 共享内存大小有限（64KB/SM）
- 全局内存延迟需被大量线程隐藏
- 寄存器溢出到局部内存会大幅降低性能

### GPU 内存层次详解

| 层次 | 带宽 | 延迟 | 作用域 |
|------|------|------|--------|
| 寄存器 | ~8 TB/s | ~0.5 ns | 线程私有 |
| 共享内存 | ~1.5 TB/s | ~1 ns | block 内线程 |
| L1 Cache | ~3 TB/s | ~10 ns | SM 内线程 |
| L2 Cache | ~2 TB/s | ~30 ns | 全 SM |
| 全局内存 | ~1 TB/s | ~500 ns | 所有线程 |

**L1/L2 缓存分配策略**：

GPU 的 L1D Cache 是读写合并的（write-through，无写分配）。Store 指令直接写 L1D，不分配新行。L2 Cache 是inclusive（全局一致），存储所有从全局内存加载的数据行。L1D 未命中时直接查 L2，无需广播。

**全局内存访问合并（Memory Coalescing）**：

当 Warp 内所有线程访问连续地址时（对齐到 32 字节或 64 字节边界），一次内存事务可以服务整个 Warp。合并访问模式下， $N$ 个线程的 $N$ 个请求合并为 $N/32$ 个 cache line 请求。

**非合并访问的带宽损失**：

$$
B_{实际} = B_{理论} \times \frac{\text{合并请求数}}{\text{总请求数}}
$$

最坏情况（每个线程独立请求不同 cache line）， $B_{实际} \approx B_{理论} / 32$ 。

**寄存器溢出（Register Spilling）**：

每个 SM 有 65536 个寄存器（物理）。若单个线程占用寄存器过多（如大型矩阵运算），超过限制的寄存器会被溢出到局部内存（本质上是全局内存），性能骤降 10-100 倍。CUDA 编译器通过 `-maxrregcount` 控制寄存器分配。

### GPU 与 CPU 的本质差异总结

**调度模型的差异**：

CPU 调度单元是线程，切换代价高（需保存/恢复完整上下文），因此每个线程执行长任务，通过大缓存弥补延迟。GPU 调度单元是 Warp，切换代价极低（仅切换 PC 和寄存器指针），因此每个 Warp 执行短任务，通过大量 Warp 掩盖延迟。

**延迟隐藏机制**：

CPU 的延迟隐藏依赖大缓存（L1D ~32KB + L2 ~256KB + L3 ~32MB），缓存命中率决定性能。GPU 的延迟隐藏依赖线程级并行（每个 SM 数十个 Warp），Warp 切换不占用额外周期，内存访问时自动切换到其他 Warp。

## 参考存根

```python
# PyTorch GPU 矩阵乘法
import torch
x = torch.randn(1000, 1000, device='cuda')
y = torch.randn(1000, 1000, device='cuda')
z = x @ y  # GPU 执行
print(f"Device: {z.device}")  # cuda:0
```

```python
# 测量 GPU 内存带宽
import torch
import time
x = torch.randn(8192, 8192, device='cuda')
torch.cuda.synchronize()
start = time.time()
for _ in range(100):
    y = x @ x
torch.cuda.synchronize()
print(f"Time: {(time.time()-start)/100*1000:.2f} ms")
```

```c
// CUDA 内存层次延迟对比
// 全局内存：500 GB/s，延迟 ~500ns
// L2 Cache：约 2 TB/s，延迟 ~200ns
// 共享内存：约 1.5 TB/s，延迟 ~1ns
// 寄存器：约 8 TB/s，延迟 ~0.5ns
```

```cuda
// Tensor Core WMMA 示例
#include <mma.h>
using namespace nvcuda::wmma;

fragment<matrix_a, m, n, k, half, row_major> a_frag;
fragment<matrix_b, m, n, k, half, col_major> b_frag;
fragment<accumulator, m, n, k, float> c_frag;

load_matrix_sync(a_frag, A, K);
load_matrix_sync(b_frag, B, N);
load_matrix_sync(c_frag, C, N);

mma_sync(c_frag, a_frag, b_frag, c_frag);

store_matrix_sync(C_out, c_frag, N, mem_row_major);
```
