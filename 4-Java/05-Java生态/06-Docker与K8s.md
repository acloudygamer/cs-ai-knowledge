# Docker 与 Kubernetes

## 本质断言

容器的本质是进程隔离技术，通过 Linux Namespace 实现资源隔离（PID、网络、文件系统等），通过 cgroup 实现资源限制（CPU、内存），通过 UnionFS 实现分层镜像以节省存储。Kubernetes 的本质是容器编排引擎，通过声明式配置实现多容器 Pod 的自动化调度、扩缩容和自愈。

## Docker

### 镜像层叠机制

<pre>
Docker 镜像结构：
Container Layer（可写层）
    ↑
Image Layer 3（应用依赖）
Image Layer 2（运行时环境）
Image Layer 1（操作系统基础）
    ↓
Read-only 共享基础层
</pre>

每个镜像层是只读的，新容器在顶部添加可写层。相同基础层的多个镜像共享底层存储，实现空间节省。

### 多阶段构建原理

多阶段构建利用 Docker 镜像层共享机制：第一阶段构建产物（JAR/WAR）被复制到第二阶段，第二阶段仅包含运行时依赖，显著减小镜像体积。

<pre>
多阶段构建效果：
传统：构建工具 + 运行时 + 应用 = 800MB+
多阶段：仅运行时 + 应用 = 200MB+
</pre>

### Jib 的差异

Jib 直接将 Java 应用打包为 OCI 镜像，无需 Docker daemon，通过 Maven/Gradle 插件直接推送到 registry，实现无特权构建。

## Kubernetes

### Pod 的本质

<pre>
Pod 与容器的关系：
Pod = 共享网络 + 共享 IPC + 共享UTS命名空间的一个或多个容器
    ↓
同一 Pod 内的容器：
- 共享同一个 IP（localhost 互通）
- 共享同一个 PID 命名空间（可见彼此进程）
- 共享同一个 UTS（主机名相同）
</pre>

Pod 是 Kubernetes 的最小调度单元，而非容器。Pod 内的多个容器共享资源（内存卷、网络），共同调度。

### Deployment 的滚动更新

<pre>
滚动更新流程：
Deployment（replicas=3）
    ↓
ReplicaSet A：3 个旧版 Pod
    ↓
开始更新 → ReplicaSet B：1 个新版 Pod
    ↓
验证新版 Pod 就绪 → ReplicaSet A 缩容至 2
    ↓
循环直到全部替换
    ↓
最终：ReplicaSet B：3 个新版 Pod
</pre>

### Service 的服务发现

<pre>
Kubernetes 服务寻址流程：
Pod 访问 Service（clusterIP:port）
    ↓
kube-proxy 拦截流量
    ↓
负载均衡到后端 Pod（Endpoints）
    ↓
环境变量 / DNS 提供 Service 地址
</pre>

Service 通过 Label Selector 动态追踪后端 Pod 列表，Pod 的 IP 变化不影响 Service 地址。

### 探针机制

<pre>
存活探针（livenessProbe）vs 就绪探针（readinessProbe）：
livenessProbe 失败 → 重启容器（ kubelet 行为）
readinessProbe 失败 → 从 Service 移除（停止接收流量）
    ↓
应用启动慢 → 初始延迟（initialDelaySeconds）防止误杀
</pre>

## 资源配置

### 资源配额模型

<pre>
Kubernetes 资源配额：
requests：调度时预留的最小资源（调度依据）
limits：运行时不允许超过的最大资源（触发 OOM Kill）
    ↓
CPU：1 core = 1000m（millicores）
内存：1Gi = 1024Mi
</pre>

## 参考样例

```dockerfile
FROM eclipse-temurin:25-jre-alpine
COPY target/myapp.jar /app/myapp.jar
USER 1000
ENTRYPOINT ["java", "-jar", "/app/myapp.jar"]
```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
        - name: myapp
          image: myuser/myapp:1.0.0
          ports:
            - containerPort: 8080
```

```yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp-service
spec:
  selector:
    app: myapp
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
```

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp-ingress
spec:
  rules:
    - host: myapp.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: myapp-service
                port:
                  number: 80
```

```yaml
management:
  endpoint:
    health:
      probes: true
```

```yaml
spec:
  terminationGracePeriodSeconds: 60
  containers:
    - name: myapp
      lifecycle:
        preStop:
          exec:
            command: ["sh", "-c", "sleep 10"]
```
