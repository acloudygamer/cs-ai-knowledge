# Docker 与 Kubernetes

## 定义

**Docker** 是容器化 runtime，其本质是通过 Linux Namespace 实现进程级资源隔离，通过 cgroup 实现资源限制，通过 UnionFS 实现分层镜像。**Kubernetes** 是容器编排引擎，其本质是 **声明式状态机**——用户声明期望状态（YAML），Kubernetes 控制器不断调谐（reconcile）实际状态直到与期望状态一致。

**核心价值**：
- **容器化**：一致性环境，消除"在我机器上能跑"
- **编排**：多容器自动调度、扩缩容、自愈
- **声明式**：基础设施即代码，可版本化、可复现

---

## 数学模型

### cgroup 资源限制的约束模型

cgroup v2 的资源约束可建模为不等式组：

| 资源类型 | 约束形式 | 说明 |
|---------|---------|------|
| CPU | $\text{CPU}_{\text{quota}} / \text{CPU}_{\text{period}} \leq N$ | 容器最多使用 N 个 CPU |
| 内存 | $\text{memory.max} = X$ | 超过则 OOM Kill |
| I/O | $\text{IOPS}_{\text{throttle}} \leq Y$ | 限制磁盘吞吐量 |

**CPU 权重模型**：cgroup 按权重分配 CPU 时间片。设容器 A 权重 $w_A$ ，容器 B 权重 $w_B$ ，则 CPU 时间片比例为：
$\frac{T_A}{T_B} = \frac{w_A}{w_B}$

权重是相对值，不是绝对值。若只有一个容器，即使权重很低也能使用全部空闲 CPU。

**归约视角**：cgroup 资源限制可归约为**令牌桶模型的资源配额分配**——每个 cgroup 按权重或配额获得资源份额。

### Kubernetes 调度器的装箱算法（Bin Packing）

Pod 调度 = 将 Pod 放入最优节点，本质是 **多维装箱问题（Multi-dimensional Bin Packing）**：

- 资源维度：CPU、内存、GPU、临时存储
- 约束：节点资源容量、亲和性/反亲和性、污点容忍

装箱目标是 **资源利用率最大化**，通常使用 **First Fit Decreasing (FFD)** 或 **Best Fit** 启发式算法。

**优先级函数**（simplified）：
$Score_i = w_1 \cdot \frac{\text{CPU\_used}}{\text{CPU\_allocatable}} + w_2 \cdot \frac{\text{Mem\_used}}{\text{Mem\_allocatable}}$

得分最高的节点被选中调度。

**FFD 算法的不变量**：
$\text{装箱后的平均利用率} \geq \frac{1}{\text{OPT} + 1} \cdot 100\%$

其中 OPT 为最优装箱的箱数。FFD 的近似比为 $\frac{11}{9} \cdot \text{OPT}$ 。

### Pod QoS 的优先级建模

Kubernetes 为 Pod 分配 QoS 类别：**Guaranteed > Burstable > BestEffort**

| QoS 级别 | 资源请求/限制 | OOM Score |
|---------|-------------|-----------|
| Guaranteed | both set and equal | -999（最后被 kill） |
| Burstable | requests < limits | 中间值 |
| BestEffort | neither set | 正值（最先被 kill） |

**OOM Score 计算**（Linux 内核）：
$\text{oom\_score} = \text{base\_score} + \frac{\text{memory\_usage}}{\text{memory\_limit}}$

**OOM Kill 的数学保证**：OOM Killer 选择 $\max(\text{oom\_score})$ 的进程杀死。Guaranteed Pod 的 oom_score_adj 为 -999，保证其最后被考虑。

---

## 数据流

<pre>
Docker 镜像层与容器层
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌──────────────────────────────────────────────────────────┐
│ Container Layer (可写层，thin R/W)                       │
│  对容器文件系统的修改在此层                                │
└──────────────────────────────────────────────────────────┘
         ▲ copy-on-write（写入时才复制）
         │
┌──────────────────────────────────────────────────────────┐
│ Image Layer 3 (Tomcat)                                   │
│ Image Layer 2 (JRE)                                       │
│ Image Layer 1 (OS Base: alpine)                           │
│ Boot Layer (bootfs)                                       │
└──────────────────────────────────────────────────────────┘

Kubernetes 控制器调谐循环
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

用户声明: spec.replicas = 3
         │
         ▼
┌─────────────────┐
│  Controller    │ ──▶ 比较期望状态 vs 实际状态
│  (Control Loop) │
└────────┬────────┘
         │ 发现差距
         ▼
┌─────────────────┐
│  ReplicaSet     │ ──▶ 创建/删除 Pod
│  Controller     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Scheduler     │ ──▶ 为 Pod 选择最优节点
│                 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Kubelet       │ ──▶ 在节点上创建/停止容器
│                 │
└────────┬────────┘
         │
         ▼
      实际状态 → (再次调谐) → 期望状态

Kubelet 状态上报循环
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Kubelet                    Kubernetes API Server
    │                              │
    │◀─── 心跳（每 10s）────────────│ 报告节点状态
    │                              │
    │◀─── Pod 创建请求（若需要）────│
    │                              │
    │───→ Pod 状态更新──────────────▶│
</pre>

---

## 机制

### UnionFS 的写时复制（Copy-on-Write）语义

镜像层是只读的。当容器向某文件写入时：
1. 若文件不在容器层（未修改过）→ 从下层镜像层复制到容器层
2. 在容器层执行写入操作
3. 读取时：容器层有则读容器层，无则读镜像层（按顺序向下查找）

这使得：
- 多个容器共享相同镜像层，节省磁盘空间
- 容器启动极快（只需创建薄的 R/W 层）
- 镜像构建可复用层缓存

**CoW 的性能代价**：首次写入时需要复制整个文件。若镜像是大文件（如数据库），首次写入延迟可能较高。

### Pod 的本质：共享命名空间

Pod 内的容器共享：
- **网络命名空间**：同一 IP、端口空间，`localhost` 互通
- **IPC 命名空间**：可通过 IPC 通信（System V IPC、POSIX 消息队列）
- **UTS 命名空间**：同一主机名
- **PID 命名空间**：容器 1 的进程在容器 2 中可见（Kubernetes 特有的 "shareProcessNamespace"）

**存储卷共享**：通过 `emptyDir` 或 `persistentVolumeClaim`，Pod 内多个容器可读写同一卷。

**归约视角**：Pod 可归约为**共享命名空间的进程组**——Pod 内的容器是同一网络/IPC/UTS 上下文中的独立进程。

### 探针机制的安全语义

| 探针类型 | 失败后果 | 适用场景 |
|---------|---------|---------|
| livenessProbe | kubelet 重启容器 | 确认进程僵死（无法自行恢复） |
| readinessProbe | 从 Service 摘除 | 确认未就绪（启动中/过载/依赖不可用） |
| startupProbe | 禁用 liveness/readiness 直到成功 | 确认启动完成（用于启动慢的应用） |

**约束条件**：
- `failureThreshold × periodSeconds` 应大于应用最大启动时间
- livenessProbe 不应检查外部依赖（否则依赖故障会触发无限重启）
- readinessProbe 失败时 Pod IP 从 Endpoints 移除，但容器不重启

**违反约束的后果**：
- livenessProbe 检查外部依赖：外部故障 → livenessProbe 失败 → kubelet 重启 → 外部仍故障 → 无限重启
- 启动时间超过 livenessProbe 容忍：Pod 被误杀

### Rolling Update 的数学保证

Rolling Update 策略参数：
```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1    # 最多不可用 Pod 数
      maxSurge: 1          # 最多超出期望 Pod 数
```

设 $N$ = 期望副本数， $S$ = maxSurge， $U$ = maxUnavailable：

**最小可用 Pod 数**： $N - U$
**最大总 Pod 数**： $N + S$

Rolling Update 过程可建模为状态机，确保任意时刻都有至少 $N-U$ 个 Pod 可用——这是 **始终保持服务可用** 的数学保证。

### 污点与容忍的调度控制

污点（Taint）应用于 Node，容忍（Toleration）应用于 Pod：

```
Node: 污点 key=value:Effect
       └── Effect: NoSchedule | PreferNoSchedule | NoExecute

Pod:  tolerations 配置容忍
```

**NoExecute 污点**：不仅不调度新 Pod，还会驱逐已有 Pod（除非 Pod 有对应容忍）。

**容忍的数学匹配**：
$\text{match}(t, \text{pod}) = \begin{cases} \text{true} & \text{若 } t \in \text{pod.tolerations} \\ \text{false} & \text{otherwise} \end{cases}$

---

## 参考存根

```dockerfile
# 多阶段构建示例：减小镜像体积
# 阶段 1：构建
FROM maven:3.9-eclipse-temurin AS builder
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline
COPY src ./src
RUN mvn package -DskipTests

# 阶段 2：运行（仅复制产物）
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
COPY --from=builder /app/target/myapp.jar ./myapp.jar
# 体积从 ~800MB 降到 ~200MB
ENTRYPOINT ["java", "-jar", "myapp.jar"]
```

```yaml
# Kubernetes Pod 探针配置
apiVersion: v1
kind: Pod
metadata:
  name: myapp
spec:
  containers:
  - name: myapp
    image: myapp:1.0
    livenessProbe:
      httpGet:
        path: /healthz
        port: 8080
      initialDelaySeconds: 30      # 启动 30s 后开始探测
      periodSeconds: 10             # 每 10s 探测一次
      failureThreshold: 3          # 连续 3 次失败则重启
    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 5
      failureThreshold: 2          # 连续 2 次失败则从 Service 摘除
    startupProbe:
      httpGet:
        path: /started
        port: 8080
      failureThreshold: 30         # 30 * 10s = 300s 最大启动时间
      periodSeconds: 10
```

---

## 深度：容器网络的命名空间隔离

### 网络命名空间的隔离模型

每个容器拥有独立的网络命名空间：

```
容器 A 网络命名空间                容器 B 网络命名空间
┌─────────────────────┐          ┌─────────────────────┐
│ eth0@if10 (veth)    │          │ eth0@if20 (veth)    │
│ IP: 10.1.1.2        │          │ IP: 10.1.1.3        │
│ MAC: 02:42:0a:01:01:02│          │ MAC: 02:42:0a:01:01:03│
│ 端口空间: 独立         │          │ 端口空间: 独立         │
└─────────────────────┘          └─────────────────────┘
```

**隔离保证**：
- IP 地址空间隔离（不同容器可使用相同IP）
- 端口空间隔离（不同容器可监听相同端口）
- 网络设备隔离（独立的 eth0、路由表、iptables）

### cgroup v2 资源限制的数学形式化

```bash
# CPU 限制：200ms CPU时间/100ms周期 = 2个CPU
echo "200000 100000" > /sys/fs/cgroup/system.slice/container.scope/cpu.max

# 内存限制：512MB
echo "536870912" > /sys/fs/cgroup/system.slice/container.scope/memory.max
```

**约束满足性**：
$\text{CPU}_{\text{usage}} \leq \frac{\text{CPU}_{\text{quota}}}{\text{CPU}_{\text{period}}}$

### 容器网络模型与主机网络的对比

| 维度 | 容器独立网络 | 主机网络（--network=host） |
|------|-------------|--------------------------|
| IP 地址 | 独立（veth pair） | 共享主机 IP |
| 端口空间 | 隔离（可重复监听相同端口） | 冲突（不可重复监听） |
| 网络栈 | 独立（eth0、路由表、iptables） | 共享主机网络栈 |
| 通信延迟 | 额外 veth 跳转 | 无额外跳转 |
| 安全性 | 隔离强 | 隔离弱 |
