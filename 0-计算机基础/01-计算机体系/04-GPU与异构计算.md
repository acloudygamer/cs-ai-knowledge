# GPU 与异构计算

## 解决什么问题
CPU适合灵活的单线程控制，GPU适合高吞吐量数据并行计算。异构计算通过CPU+GPU协同，实现两种架构优势互补，适用于深度学习、科学计算等场景。

## 核心概念
- 异构计算使用不同类型处理器（CPU+GPU/FPGA）协同完成计算
- GPU拥有数千个小核心，擅长数据并行的高吞吐量计算
- CPU灵活单线程控制强，适合复杂逻辑和串行任务
- CUDA/OpenCL是主流GPU编程框架
- CPU-GPU数据传输带宽（PCIe/NVLink）是性能关键

## GPU 架构

### CPU vs GPU 设计理念

| 特性 | CPU | GPU |
|------|-----|-----|
| 核心数 | 4-128+ (少)，取决于定位 | 数千到数万（取决于具体型号） |
| 设计目标 | 低延迟，单线程性能 | 高吞吐，数据并行 |
| 缓存 | 大型分层缓存 | 较小，高带宽 |
| 控制逻辑 | 复杂，分支预测 | 简单，线程束(Warp) |
| 内存 | DDR | GDDR/HBM |

### GPU 架构层级

```
GPU
 ├── 计算单元 (SM - Streaming Multiprocessor)
 │    ├── 大量 CUDA Core (执行单元)
 │    ├── 共享内存 (Shared Memory)
 │    ├── 寄存器文件
 │    └── 调度器/发射单元
 │
 └── 全局内存 (Global Memory) - VRAM
```

**NVIDIA GPU 架构演进**：

| 架构 | 代号 | 特点 |
|------|------|------|
| Fermi | GF100 | 首个完整 CUDA 架构 |
| Kepler | GK110 | 动态并行，GPU 直接启动 kernel |
| Maxwell | GM204 | 效率优化，SM设计改进，每SM性能提升 |
| Pascal | GP100 | NVLink，HBM2 内存 |
| Volta | GV100 | Tensor Core，混合精度 |
| Turing | TU102 | RT Core，光线追踪 |
| Ampere | GA100 | 第三代 Tensor Core，结构化稀疏 |
| Ada | AD102 | 第四代 Tensor Core，DLSS 3超分辨率技术 |
| Hopper | GH100 | Transformer 引擎，更大共享内存 |
| Blackwell | GB100 | 第五代 Tensor Core，FP8 支持，专为大规模 AI 推理设计 |

### CUDA 编程模型

```python
# CUDA Python (使用 Numba)
from numba import cuda
import numpy as np

@cuda.jit
def kernel_add(a, b, result):
    idx = cuda.grid(1)  # 全局线程索引
    if idx < len(result):
        result[idx] = a[idx] + b[idx]

# 主程序
n = 1000000
a = np.random.rand(n).astype(np.float32)
b = np.random.rand(n).astype(np.float32)
result = np.zeros(n, dtype=np.float32)

# 传输到 GPU
d_a = cuda.to_device(a)
d_b = cuda.to_device(b)
d_result = cuda.to_device(result)

# 配置线程块
threads_per_block = 256
blocks_per_grid = (n + threads_per_block - 1) // threads_per_block

# 执行 kernel
kernel_add[blocks_per_grid, threads_per_block](d_a, d_b, d_result)

# 复制回 CPU
result = d_result.copy_to_host()
```

### CUDA 线程层级

```
Grid
 └── Block (线程块)
      └── Thread (线程)
           - threadIdx.x: 块内线程索引
           - blockIdx.x: 全局块索引
           - blockDim.x: 每块线程数
```

```python
# 二维示例
@cuda.jit
def matrix_add(A, B, C, N, M):
    row = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    col = cuda.blockIdx.y * cuda.blockDim.y + cuda.threadIdx.y
    
    if row < N and col < M:
        C[row * M + col] = A[row * M + col] + B[row * M + col]

# 配置 2D 线程结构
threads = (16, 16)
blocks = (N // 16 + 1, M // 16 + 1)
matrix_add[blocks, threads](d_A, d_B, d_C, N, M)
```

## 内存层级

GPU 有复杂的内存层级：

```
GPU 内存层级:
─────────────────────────
寄存器 (Register)
  ↓ 极低延迟
本地内存 (Local Memory) - 每个线程私有
  ↓ 低延迟，高带宽
共享内存 (Shared Memory) - 每个 block 共享
  ↓ 低延迟
L1/L2 Cache
  ↓ 高带宽
全局内存 (Global Memory / VRAM) - 所有线程共享
  ↓
CPU 内存 (通过 PCIe)
```

### 内存合并 (Coalescing)

GPU 访问全局内存时，合并的访问可以大幅提升带宽：

```python
# 好: 合并访问
@cuda.jit
def coalesced_access(arr):
    idx = cuda.grid(1)
    if idx < len(arr):
        arr[idx] = arr[idx] * 2  # 相邻线程访问相邻地址

# 差: 步长访问
@cuda.jit
def strided_access(arr):
    idx = cuda.grid(1)
    if idx * 4 < len(arr):
        arr[idx * 4] = arr[idx * 4] * 2  # 访问不连续
```

## GPU 计算场景

### 深度学习

GPU 是深度学习训练的基础：

```python
# PyTorch GPU 操作
import torch

# 检查 GPU
print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0))

# 将数据移到 GPU
x = torch.randn(1000, 1000).to('cuda')
y = torch.randn(1000, 1000).to('cuda')
z = torch.matmul(x, y)  # GPU 矩阵运算

# Tensor Core 混合精度
with torch.cuda.amp.autocast():
    z = torch.matmul(x, y)
```

**Tensor Core**：专门用于矩阵乘法的硬件单元

| 计算精度 | 用途 |
|----------|------|
| FP64 | 科学计算 |
| FP32 | 通用深度学习 |
| TF32 | Ampere 新精度 |
| FP16 | 加速训练 |
| BF16 | 梯度计算 |
| INT8 | 量化推理 |

### CUDA C++ 基础

```cpp
// CUDA C++ kernel
__global__
void vectorAdd(const float *a, const float *b, float *c, int n) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < n) {
        c[idx] = a[idx] + b[idx];
    }
}

int main() {
    // 主机端数据
    float *h_a, *h_b, *h_c;
    // 设备端数据
    float *d_a, *d_b, *d_c;
    
    // 分配 GPU 内存
    cudaMalloc(&d_a, n * sizeof(float));
    cudaMalloc(&d_b, n * sizeof(float));
    cudaMalloc(&d_c, n * sizeof(float));
    
    // 复制数据到 GPU
    cudaMemcpy(d_a, h_a, n * sizeof(float), cudaMemcpyHostToDevice);
    cudaMemcpy(d_b, h_b, n * sizeof(float), cudaMemcpyHostToDevice);
    
    // 启动 kernel
    int threadsPerBlock = 256;
    int blocksPerGrid = (n + threadsPerBlock - 1) / threadsPerBlock;
    vectorAdd<<<blocksPerGrid, threadsPerBlock>>>(d_a, d_b, d_c, n);
    
    // 复制结果回 CPU
    cudaMemcpy(h_c, d_c, n * sizeof(float), cudaMemcpyDeviceToHost);
    
    // 释放 GPU 内存
    cudaFree(d_a); cudaFree(d_b); cudaFree(d_c);
}
```

## 异构系统

### CPU-GPU 异构

```
CPU (主机)                    GPU (设备)
─────────                    ─────────
控制逻辑                     数据并行
复杂分支判断                 规则数据操作
串行任务                     并行任务
────                        ─────
内存: DDR5 (Windows 11 / Ubuntu 24.04 典型)  内存: GDDR6X / HBM3 / HBM3e
带宽: 76.8-102.4 GB/s (DDR5-4800 双通道约 76.8 GB/s，DDR5-6400 双通道约 102.4 GB/s）  带宽: GDDR6X: ~1000 GB/s；HBM3: ~1024 GB/s；HBM3e: 2048-2560 GB/s
延迟: 低                     延迟: 高
```

### 异构编程框架

| 框架 | 描述 | 适用场景 |
|------|------|----------|
| CUDA | NVIDIA 专用 | NVIDIA GPU |
| OpenCL | 跨平台开放标准 | 多厂商 GPU/FPGA |
| ROCm | AMD GPU 计算 | AMD GPU |
| oneAPI | Intel 统一编程 | CPU/GPU/FPGA |
| OpenMP | 编译器指令 | CPU多线程（GPU支持需扩展） |

### oneAPI Data Parallel C++

```cpp
// oneAPI DPC++ 示例
#include <CL/sycl.hpp>

using namespace sycl;

void vector_add(queue &q, const std::vector<float> &a,
                const std::vector<float> &b, std::vector<float> &c) {
    buffer buf_a(a), buf_b(b), buf_c(c);
    
    q.submit([&](handler &h) {
        auto acc_a = buf_a.get_access<access::mode::read>(h);
        auto acc_b = buf_b.get_access<access::mode::read>(h);
        auto acc_c = buf_c.get_access<access::mode::write>(h);
        
        h.parallel_for(range<1>(a.size()), [=](id<1> idx) {
            acc_c[idx] = acc_a[idx] + acc_b[idx];
        });
    });
}
```

## GPU 性能优化

### 内存合并与对齐

```python
# 确保内存对齐到 256 字节
d_data = cuda.aligned_array(1024, dtype=np.float32)  # 256 字节对齐
```

### 共享内存银行冲突

```python
# 共享内存访问优化
@cuda.jit
def shared_memory_kernel():
    # 声明共享内存
    shared_data = cuda.shared.array(256, dtype=np.float32)
    
    tid = cuda.threadIdx.x
    # 避免银行冲突：使用padding
    shared_data[tid * 2] = ...
```

### 指令优化

```python
# 使用 fastmath 优化
@cuda.jit(fastmath=True)
def fast_math_kernel(a, b, c):
    c[cuda.grid(1)] = math.sqrt(a[cuda.grid(1)]**2 + b[cuda.grid(1)]**2)
```

## FPGA 异构计算

FPGA (现场可编程门阵列) 用于特定场景，通过OpenCL或RTL设计实现定制化计算。

## GPU 技术趋势

### NVLink 与 C2C

| 互联技术 | 带宽（单向） | 说明 |
|----------|-------------|------|
| PCIe 4.0 x16 | 32 GB/s | 标准 CPU-GPU 互联 |
| PCIe 5.0 x16 | 128 GB/s | 标准 CPU-GPU 互联 |
| NVLink (Volta/Ampere) | 300-600 GB/s | 多 GPU 互联（Ada 达 600 GB/s） |
| NVLink (Ada/Hopper) | 450-900 GB/s | 多 GPU 或 CPU-GPU 直连（Hopper 达 900 GB/s） |
| NVLink C2C | 900 GB/s | 芯片间互联（Grace Hopper 超级芯片采用） |

### 统一内存

```python
# CUDA Python (Numba) 统一内存
from numba import cuda
import numpy as np

# 分配统一内存 - CPU/GPU 都可以访问
data = cuda.device_array(shape, dtype=np.float32)  # 自动在 CPU/GPU 间迁移

# 或使用 cuda.pinned_array for page-locked内存
# OS 和驱动自动在 CPU/GPU 之间迁移数据
```

### 多实例 GPU (MIG)

```bash
# 将单个 GPU 分割成多个独立实例
nvidia-smi mig -cgi 19,19 -C
```

## 常见问题

### GPU 利用率低

```python
# 检查 GPU 利用率
# NVIDIA: nvidia-smi
# PyTorch: torch.cuda.utilization()
```

可能原因：
- 数据传输瓶颈 (PCIe 带宽)
- 内存访问不合并
- 线程块太小
- 同步过多

### 显存不足 (OOM)

```python
# 减小 batch size
batch_size = 8  # 减小

# 使用梯度累积
accumulation_steps = 4
effective_batch = batch_size * accumulation_steps

# 混合精度训练
with torch.cuda.amp.autocast():
    outputs = model(inputs)
```
