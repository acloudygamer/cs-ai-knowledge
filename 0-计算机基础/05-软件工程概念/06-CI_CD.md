# CI/CD

## 定义

CI/CD 是将代码变更从提交到生产的自动化流水线实践，包括持续集成（Continuous Integration）、持续交付（Continuous Delivery）和持续部署（Continuous Deployment）。CI 确认每次提交都通过质量门禁；CD 将代码变更自动推进到预生产环境；持续部署进一步自动化到生产环境。

**归约内核**：CI/CD 的本质是**软件交付的流水线自动化**。传统手动部署的每个步骤被编排为自动执行的管道，human-in-the-loop 被最小化，交付速度大幅提升。

## 数学模型

### 流水线执行时间模型

设流水线有 $n$ 个阶段，各阶段执行时间为 $T_i$，并发瓶颈导致的等待时间为 $W_j$：

$$
T_{pipeline} = \sum_{i=1}^{n} T_i + \sum_{j=1}^{m} W_j
$$

若各阶段可并行化，且测试可拆分为 $p$ 个并行 worker：

$$
T_{parallel} = \sum_{i=1}^{n} T_i + \frac{T_{test}}{p} + \sum_{j \neq test} W_j
$$

理想情况下，$T_{pipeline} \approx \max(T_i)$（最慢阶段决定总时间）。

### MTTR 与部署频率的关系

部署频率与平均恢复时间（MTTR）强相关：

$$
MTTR \propto \frac{1}{deployment\_frequency}
$$

高部署频率迫使团队建设快速恢复能力，形成正反馈循环。

### 构建缓存命中率模型

设依赖项数量为 $n$，每次构建的缓存命中概率：

$$
P_{cache\_hit} = \frac{\text{未变化依赖数}}{\text{总依赖数}}
$$

CI 缓存策略通过追踪依赖图的哈希，只对变化的依赖重新构建。

### 部署回滚的时间约束

蓝绿部署的回滚时间：

$$
T_{rollback} = T_{DNS\_switch} + T_{connection\_drain}
$$

通常为秒级，因为流量切换是 DNS 层面的操作。

## 数据流

<pre>
代码提交                         Git Hook                       CI Server                      构建环境                       部署目标
   │                               │                              │                              │                              │
   │─── git push ─────────────────►│                              │                              │                              │
   │      (触发钩子)                 │                              │                              │                              │
   │                               │─── Webhook 通知 ───────────►│                              │                              │
   │                               │                              │─── 检出代码 ────────────────►│                              │
   │                               │                              │─── 安装依赖 ────────────────►│                              │
   │                               │                              │─── 执行测试 ────────────────►│                              │
   │                               │                              │◄─── 测试结果 ───────────────│                              │
   │                               │                              │                              │─── 构建镜像 ──────────────►│
   │                               │                              │                              │◄─── 镜像产物 ─────────────│                              │
   │                               │                              │                              │─── 部署到 Staging ────────►│
   │                               │                              │                              │─── 部署到 Prod ───────────►│
</pre>

**数据形态变换链路**：

1. `代码提交（Commit）` → `Git 对象（blob/tree/commit）`
2. `Git 对象` → `Webhook Payload` → `CI 触发`
3. `CI 触发` → `代码检出（SHA 对应版本）`
4. `代码检出` → `依赖安装` → `构建产物`
5. `构建产物` → `镜像构建` → `OCI 镜像`
6. `OCI 镜像` → `部署到环境` → `容器/进程`

## 机制

### 幂等性的执行语义

幂等性（Idempotency）指：流水线任何步骤可重复执行且结果一致。形式化表述：

$$
\forall s, f(f(s)) = f(s)
$$

对于部署步骤，幂等性意味着**重复部署同一版本不会产生副作用**。实现机制：
- 声明式配置（如 Kubernetes Deployment）而非命令式脚本
- 不可变镜像：构建产物不可修改，直接部署

违反幂等性的后果是**环境漂移（Environment Drift）**：不同次部署产生不同的环境状态。

### 快速失败的质量门禁意义

快速失败（Fail Fast）的核心洞察是：**缺陷发现越晚，修复成本越高**。

| 阶段 | 修复成本倍数 |
|------|-------------|
| 需求/设计 | 1x |
| 编码 | 6x |
| 单元测试 | 10x |
| 集成测试 | 15x |
| 生产 | 30x-1000x |

### 不可变产物的一致性保障

不可变产物（Immutable Artifacts）指构建产物一旦创建，不应修改，直接部署。约束来自：
- **可审计性**：每个部署版本可精确关联到源码
- **可重现性**：给定相同源码，总是构建出相同产物
- **回滚确定性**：回滚到版本 V 就是部署版本 V 的产物

### 部署策略的可用性保障

| 策略 | 停机时间 | 回滚速度 | 资源成本 |
|------|----------|----------|----------|
| 蓝绿部署 | 零 | 秒级 | 双倍 |
| 金丝雀发布 | 零 | 分钟级 | 增量 |
| 滚动更新 | 零 | 分钟级 | 最小 |

### 特性开关的数学逻辑

特性开关（Feature Flag）将代码部署与功能发布解耦：

$$
\text{Enabled}(F, U, T) = \text{policy}(F, U) \geq T
$$

其中 $F$ 是特性名，$U$ 是用户，$T$ 是阈值。

### 构建缓存的依赖图分析

依赖项变化检测通过哈希链实现：

$$
H_{cache} = H(\text{file}_1, H(\text{file}_2, H(\text{file}_3, ...)))
$$

只要任一依赖变化，根哈希就变化，触发重新构建。

## 参考存根

```yaml
# GitHub Actions 示例
name: CI Pipeline
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.npm
          key: ${{ runner.os }}-npm-${{ hashFiles('**/package-lock.json') }}
      - run: npm ci && npm test
      - run: docker build -t app:${{ github.sha }} .
```

```yaml
# Kubernetes Deployment（声明式、幂等）
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    spec:
      containers:
      - name: app
        image: app:v1.2.3
        ports:
        - containerPort: 8080
```
