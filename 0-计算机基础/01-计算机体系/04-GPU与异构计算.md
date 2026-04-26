# GPU 与异构计算

## 定义

异构计算是使用不同类型处理器（CPU+GPU/FPGA）协同完成计算，通过各自擅长的任务类型实现优势互补。CPU 设计追求低延迟（Latency-optimized），擅长复杂分支和串行任务；GPU 设计追求高吞吐（Throughput-optimized），擅长大规模数据并行任务。两者的核心差异在于缓存层级和运算单元数量的取舍：CPU 用大缓存弥补内存延迟，GPU 用海量线程掩盖内存延迟。

## 数学模型

**GPU 理论吞吐：**

$$
TP_{GPU} = \text{SM}_{数量} \times \frac{\text{Warp}_{大小}}{\text{周期}} \times f_{GPU} \times \text{IPC}_{warp}
$$

典型值：80 SM × 32 线程/warp × 1.4 GHz × 2 ops/周期 = 7.2 TFLOP/s（FP32）。

**内存带宽饱和模型：**

$$
U_{bw} = \frac{B_{实际}}}{B_{理论}}} = \frac{\text{活跃 warp 数} \times \text{每个 warp 的带宽需求}}{\text{理论带宽}}
$$

当 $U_{bw} < 50\%$ 时，计算单元饥饿（memory bound）；当 $U_{bw} > 80\%$ 时，计算单元饱和（compute bound）。

**Roofline 模型：**

$$
\text{性能} = \min(\text{AI}_{实际} \times \text{带宽}, \text{峰值性能})
$$

其中算术强度 $AI = \frac{\text{浮点运算数}}{\text{字节传输量}}$。AI 决定系统是 memory bound 还是 compute bound。

## 数据流

<pre>
CPU（主机）                              GPU（设备）
─────────                               ─────────
控制逻辑（复杂分支，low arithmetic intensity）
    │                                    ↑
    │ PCIe/NVLink                        │
    │ 32 GB/s / 300-900 GB/s            │
    │ 延迟：~1μs / ~100ns                │
    ↓                                    │
┌────────────────────────────┐          │
│ Host Memory (DDR)          │          │
│  │                         │          │
│  ↓ cudaMemcpy (同步/异步)   │          │
└────────────────────────────┘          │
    │ 复制到 Device Memory              │
    │ (H2D 或 D2H)                      │
    ↓                                    │
┌────────────────────────────┐          │
│ Device Memory (GDDR/HBM)  │          │
│  │ 带宽：500-1000 GB/s               │
│  延迟：~500ns                              │
│  ↓                                    │
│  L2 Cache（~6MB）                      │
│  ↓                                    │
│  SM (Streaming Multiprocessor)        │
│  ├──→ Warp Scheduler                  │
│  │    └──→ 32 线程并行执行            │
│  │         └──→ CUDA Core (ALU)       │
│  │                                   │
│  └──→ 共享内存 (64KB/SM)             │
│       └──→ Bank 冲突检测              │
└────────────────────────────────────┘
</pre>

## 机制

### GPU 架构

**SIMT（Single Instruction Multiple Thread）执行模型：**

GPU 不是传统 SIMD，而是 SIMT——32 线程组成一个 Warp，同一 Warp 内线程执行相同代码但处理不同数据。当分支发散时（if-else），Warp 内的线程会串行执行两个分支并屏蔽非活动线程。

**约束：**
- Warp（32 线程）是最小调度单元
- 共享内存在同一 block 线程可见
- 全局内存访问需要合并（Coalescing）

**违规后果：**
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

### Tensor Core

矩阵乘累加（MMA）专用单元，执行 $D = A \times B + C$：

- A: MXK 矩阵，B: KXN 矩阵，C/D: MXN 矩阵
- 混合精度：FP16 输入，FP32 累加（防止精度损失）
- 每个 Tensor Core 每周期执行 256 FLOPs（FP16）
- NVIDIA Hopper FP8 Tensor Core 每周期执行 4096 FLOPs

**约束：**
- 输入矩阵需满足维度对齐（M/N/K 为 8 的倍数）
- 需显式调用 `wmma` API 或使用 CUTLASS 库

### CUDA 编程模型

```
__global__ void kernel(float* C, float* A, float* B, int N) {
    int row = blockIdx.y * blockDim.y + threadIdx.y;
    int col = blockIdx.x * blockDim.x + threadIdx.x;
    float sum = 0.0f;
    for (int k = 0; k < N; k++)
        sum += A[row*N + k] * B[k*N + col];
    C[row*N + col] = sum;
}
```

**约束：**
- Grid/Block 维度需匹配算术强度
- 共享内存大小有限（64KB/SM）
- 全局内存延迟需被大量线程隐藏

## 参考存根

```python
# PyTorch GPU 矩阵乘法
import torch
x = torch.randn(1000, 1000, device='cuda')
y = torch.randn(1000, 1000, device='cuda')
z = x @ y  # GPU 执行
```

```python
# CUDA 内存层次
# 全局内存：500 GB/s，延迟 ~500ns
# 共享内存：~1.5 TB/s，延迟 ~1ns
# 寄存器：~8 TB/s，延迟 ~0.5ns
```
