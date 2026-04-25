# Node.js运行时

## 定义

**Node.js是基于V8引擎的事件驱动JavaScript运行时，通过非阻塞I/O和单线程事件循环实现高并发。**

$$
T_{响应} = T_{事件循环遍历} + T_{回调执行} + T_{下次轮询等待}
$$

$$
\text{并发数} \approx \frac{T_{I/O等待}}{T_{回调执行}} \times \text{线程池大小}
$$

## 数学模型

### 事件循环调度模型

<pre>
每阶段执行: 该阶段所有回调直到队列清空或达到slice(默认6ms)
         ↓
阶段顺序: timers → pending callbacks → idle/prepare → poll → check → close
         ↓
吞吐量 = 1 / (单回调平均执行时间 + 阶段切换开销)
      ≈ 1 / (1μs + 1μs) ≈ 500K ops/s (理想情况)
</pre>

### 线程池排队模型

<pre>
请求到达 → 线程池有空闲? → 是 → 执行 → 返回
              ↓ 否
         入队等待 → 空闲时执行
              ↓
UV_THREADPOOL_SIZE = 512 (默认)
最大并发阻塞I/O = 线程池大小 + epoll异步I/O数
</pre>

### V8优化/去优化模型

<pre>
Ignition (解释器): 字节码执行，启动快
Turbofan (优化编译器): 热点代码 → 机器码
         ↓
假设检验: 类型变化 / 隐藏类变更 / 计数器溢出
         ↓
去优化: 回退到字节码，重新积累热点信息
</pre>

## 数据流

### Node.js整体架构

<pre>
JavaScript 源代码
    ↓ [V8 Parser]
AST (抽象语法树)
    ↓ [V8 Ignition]
字节码 (Ignition bytecode)
    ↓ [热点检测]
Turbofan JIT → 优化机器码
    ↓
Node.js API 调用
    ↓
libuv (事件循环 + 线程池)
    ↓
操作系统 (epoll/kqueue/IOCP)
</pre>

### V8编译流水线

<pre>
源代码
    ↓ [Parser]
AST
    ↓ [Full-codegen / Ignition]
字节码 (Bytecode) 或 快速机器码
    ↓ [热函数检测]
Turbofan优化编译器
    ↓
优化机器码 (Speculative Optimization)
    ↓
类型反馈 (Type Feedback)
    ↓
假设失败 → Deoptimizer → 回退字节码
</pre>

### 事件循环详细阶段

<pre>
   ┌─────────────────────────────────────┐
   │            timers 阶段               │
   │  执行 setTimeout / setInterval 回调  │
   └─────────────┬───────────────────────┘
                 ↓
   ┌─────────────────────────────────────┐
   │       pending callbacks 阶段          │
   │  执行延迟到下次循环的I/O回调          │
   └─────────────┬───────────────────────┘
                 ↓
   ┌─────────────────────────────────────┐
   │       idle, prepare 阶段             │
   │  libuv内部使用                       │
   └─────────────┬───────────────────────┘
                 ↓
   ┌─────────────────────────────────────┐
   │            poll 阶段                 │
   │  获取新I/O事件 / 若无回调则阻塞等待   │
   └─────────────┬───────────────────────┘
                 ↓
   ┌─────────────────────────────────────┐
   │            check 阶段                 │
   │  执行 setImmediate 回调              │
   └─────────────┬───────────────────────┘
                 ↓
   ┌─────────────────────────────────────┐
   │        close callbacks 阶段          │
   │  执行关闭回调 (如 socket.on('close'))│
   └─────────────┬───────────────────────┘
                 ↓
                 └──────→ 返回 timers 阶段
</pre>

### 宏任务与微任务调度

<pre>
主线程同步代码
    ↓
微任务 (Promise.then / queueMicrotask / process.nextTick)
    ↓
宏任务 (setTimeout / setImmediate / I/O回调)
    ↓
下一事件循环 tick
</pre>

### libuv线程池流程

<pre>
Node.js API (fs.readFile)
    ↓
libuv任务入队 (线程池)
    ↓
工作线程执行阻塞I/O (或同步调用系统API)
    ↓
完成 → 回调入队到事件循环
    ↓
事件循环执行回调
</pre>

## 机制

### 为什么单线程能处理高并发

**约束条件**：
- I/O操作（磁盘、网络）相比CPU计算慢几个数量级
- 线程阻塞在I/O上是极大浪费
- 事件循环通过回调机制让线程在等待I/O时处理其他任务

**违规后果**：
- CPU密集型任务阻塞事件循环 → 所有请求卡顿
- 长同步循环 → 事件循环无法推进

### 事件循环设计原理

**阶段划分**：
- timers：定时器回调（setTimeout/setInterval）
- poll：获取I/O事件（最重要的阶段）
- check：setImmediate回调
- close：关闭事件回调

**阶段切换**：
- 每个阶段执行完所有可用回调或达到slice限制
- process.nextTick在当前阶段结束后立即执行，优先于其他微任务

### 非阻塞I/O原理

<pre>
同步阻塞模型:
  线程请求I/O → 阻塞等待 → 返回
  (线程在等待期间无法处理其他请求)

异步非阻塞模型:
  线程请求I/O → 注册回调 → 返回
  (线程可处理其他请求)
  ↓
I/O完成 → epoll/kqueue通知 → 事件循环执行回调
</pre>

### libuv线程池机制

**哪些操作使用线程池**：
- 文件系统操作（fs.readFile等）
- DNS查询（dns.lookup）
- 加密操作（crypto.pbkdf2等）
- 压缩操作（zlib.deflate等）

**为什么不所有I/O都用线程池**：
- 网络I/O本身已异步（epoll/kqueue/IOCP）
- 线程池用于模拟无法异步化的阻塞操作

**配置**：
```bash
UV_THREADPOOL_SIZE=8 node app.js  # 必须在启动前设置
```

### V8引擎机制

**隐藏类（Hidden Classes）**：
- 同一构造函数创建的对象共享隐藏类
- 属性访问通过偏移量直接定位
- 属性添加顺序影响隐藏类

**内联缓存（Inline Cache）**：
- 记录热点调用的类型信息
- 相同类型时直接使用缓存的偏移量
- 类型变化时失效

**去优化（Deoptimization）**：
- 优化假设不成立时回退到字节码
- 触发条件：类型变化、分支干扰、计数器溢出
- 去优化开销：~10-100ms

### Node.js模块系统

**CommonJS模块加载**：
```
require('module')
    ↓
Module.resolve() → 查找模块路径
    ↓
读取文件 / 执行雪橇
    ↓
module.exports 包装
    ↓
缓存 (require.cache)
```

**ES模块加载**：
```
import → 静态分析 → 构建依赖图
    ↓
所有模块加载完成 → 执行
    ↓
import() 动态导入 → 按需加载
```

### 约束与违规后果

**事件循环阻塞**：
- CPU密集型任务应用worker_threads
- 大数据处理应分片或流式处理

**内存泄漏**：
- 累积的监听器未移除
- 闭包引用大对象
- 缓存无界限增长

**回调地狱**：
- 嵌套过深用async/await或Promise解决

## 参考存根

### 事件循环示例（≤20行）

```javascript
console.log('1');
setTimeout(() => console.log('2'), 0);
Promise.resolve().then(() => console.log('3'));
console.log('4');
// 输出: 1 → 4 → 3 → 2
```

### HTTP服务器（≤20行）

```javascript
const http = require('http');
http.createServer((req, res) => {
    res.writeHead(200);
    res.end('ok');
}).listen(3000);
```

### 文件异步读取（≤20行）

```javascript
const fs = require('fs').promises;
async function read() {
    const data = await fs.readFile('test.txt', 'utf8');
    return data;
}
```
