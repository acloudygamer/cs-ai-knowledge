# GraalVM与Native Image

> GraalVM Native Image的本质是AOT编译（提前编译）——在构建时将Java应用编译为本地机器码的可执行文件，省去JVM启动和JIT编译的运行时开销，从而实现毫秒级启动和极低内存占用。

---

## AOT vs JIT：编译模型对比

### 数学模型

设应用启动阶段的有效工作时间为 $T_{\text{useful}}$，JVM启动开销为 $T_{\text{jvm}}$，JIT编译时间为 $T_{\text{jit}}$：

$$
\text{JVM总启动时间} = T_{\text{jvm}} + T_{\text{jit}} + T_{\text{useful}}
$$

$$
\text{Native Image启动时间} = T_{\text{aot\_compilation}} + T_{\text{useful}}
$$

其中 $T_{\text{aot\_compilation}}$ 是构建时开销，不影响运行时启动性能。

### JIT编译的运行时开销

JIT（即时编译）将字节码在运行时编译为本地机器码：

$$
T_{\text{jit}} = \sum_{i=1}^{n} \underbrace{T_{\text{detect}}(h_i)}_{\text{热点检测}} + \underbrace{T_{\text{compile}}(h_i)}_{\text{编译耗时}}
$$

热点检测依赖采样或计数器，需积累足够调用才能触发编译，导致应用启动阶段无法达到峰值性能。

### AOT编译的优势

Native Image在构建时：
1. 执行所有类的静态初始化
2. 通过静态分析（+动态追踪）确定可达代码
3. 生成包含所有已编译代码的本地可执行文件

$$
\text{启动时无需 JIT} \implies \text{即时进入峰值性能}
$$

---

## Native Image 构建过程

### 两阶段架构

<pre>
构建时阶段（Build Time）
    │
    ├── 1. 静态分析：从入口点出发，递归遍历所有可达类/方法
    ├── 2. 动态追踪（可选）：运行 agent 追踪运行时反射/资源/类加载
    │       生成：reflection-config.json、resource-config.json、proxy-config.json
    └── 3. AOT 编译：生成ELF/PE/Mach-O本地可执行文件

运行时阶段（Runtime）
    │
    ├── Substrate VM（极简运行时）：无垃圾回收器、无JIT、无字节码解释器
    └── 直接执行编译后的本地代码
</pre>

### 镜像堆（Image Heap）

Native Image在构建时分配并初始化一个**镜像堆**——包含应用启动时所有可达对象的预初始化快照。启动时无需类加载和对象分配，直接使用预分配内存：

$$
\text{Memory}_{\text{image}} = \text{预初始化对象} + \text{类元数据} + \text{GC元数据}
$$

### 子strateVM组件

Substrate VM是极简运行时，仅包含：

| 组件 | Native Image | Hotspot JVM |
|------|-------------|-------------|
| GC | 无（或G1/Serial提前配置） | ZGC/Shenandoah/... |
| JIT | 无 | 有（C1/C2） |
| 解释器 | 无 | 有 |
| 类加载 | 仅运行时需要的类 | 按需动态加载 |
| 反射 | 需预注册 | 原生支持 |

---

## 反射配置

### 必要性

静态分析无法处理所有反射场景（如`Class.forName(name)`），因此需要运行时配置文件声明必须保留的反射元数据。

### 配置模型

```json
[
  {
    "name": "com.example.model.User",
    "allDeclaredConstructors": true,
    "allDeclaredMethods": true,
    "fields": [
      { "name": "id", "type": "long" },
      { "name": "name", "type": "java.lang.String" }
    ]
  }
]
```

字段`type`使用JVM内部签名格式（`Ljava/lang/String;`）。

### Native Image Agent

Agent在试运行（test run）阶段自动生成配置文件：

```bash
native-image-agent -jar target/app.jar -agentlib:native-image-agent=config-output-dir=.
./target/app      # 触发各种代码路径
# 生成 reflection-config.json, resource-config.json, jni-config.json
```

---

## 动态类加载

### 约束

Native Image在构建时需要预知所有运行的代码。`Class.forName()`等动态加载场景必须在配置文件中预注册：

```java
public Object loadPlugin(String className) {
    // 构建时 className 未知，静态分析无法发现该类
    Class<?> clazz = Class.forName(className);  // 必须在 reflection-config.json 中注册
    return clazz.getDeclaredConstructor().newInstance();
}
```

### 运行时类加载限制

即使注册了动态类，`Class.forName()`也只能加载：
1. 构建时已知超类的子类
2. 构建时已知接口的实现类

---

## 性能对比

### 启动时间模型

$$
\text{启动加速比} \approx \frac{T_{\text{jvm}}}{T_{\text{native}}}
\approx \frac{1-10\,\text{s}}{0.01-0.1\,\text{s}} \approx 10-100\text{x}
$$

### 内存占用模型

$$
\text{内存占用比} \approx \frac{M_{\text{jvm}}}{M_{\text{native}}}
\approx \frac{100-500\,\text{MB}}{10-50\,\text{MB}} \approx 10-20\text{x}
$$

JVM的内存占用包含：JVM堆、元空间、JIT编译缓存、线程栈（1MB/线程）。Native Image的线程栈按需增长（分页提交），无JIT缓存。

### 性能指标表

| 指标 | JVM Hotspot | Native Image | 提升 |
|------|-------------|--------------|------|
| 启动时间 | 2.5s | 85ms | ~30x |
| 内存占用 | 256MB | 32MB | ~8x |
| 首次响应 | 800ms（含JIT） | 12ms | ~67x |
| 峰值性能 | 最优（JIT优化后） | 略低（AOT优化有限） | ~5-10%差距 |

---

## 常用构建选项

| 选项 | 说明 | 使用场景 |
|------|------|----------|
| `--no-fallback` | 不使用fallback解释器（构建失败则报错） | 生产构建 |
| `-O<level>` | 优化级别（1-4） | 性能调优 |
| `--initialize-at-build-time` | 构建时初始化指定类 | SLF4J等静态初始化 |
| `-H:+ReportExceptionStackTraces` | 报告异常堆栈 | 调试 |
| `-H:NativeMemoryTracking=summary` | 跟踪本地内存 | 内存分析 |

---

## Spring Boot集成

Spring Boot 3.x原生支持Native Image，通过`spring-boot-starter-parent`自动配置`spring-aot-maven-plugin`：

```xml
<plugin>
    <groupId>org.graalvm.buildtools</groupId>
    <artifactId>native-maven-plugin</artifactId>
    <configuration>
        <imageName>native-demo</imageName>
        <buildArgs>--no-fallback</buildArgs>
    </configuration>
</plugin>
```

---

## 容器集成

### 镜像体积优势

Native Image的镜像极小，适合Serverless和容器化：

```dockerfile
FROM ghcr.io/graalvm/native-image:ol9-java17 as builder
WORKDIR /app
COPY mvnw pom.xml ./
RUN ./mvnw dependency:go-offline
COPY src src
RUN ./mvnw -Pnative package -DskipTests
FROM ghcr.io/graalvm/native-image:ol9-java17
WORKDIR /app
COPY --from=builder /app/target/native-demo /app/native-demo
ENTRYPOINT ["/app/native-demo"]
```

### Kubernetes资源建议

```yaml
resources:
  requests:
    memory: "32Mi"   # Native Image 极低内存
    cpu: "100m"
  limits:
    memory: "128Mi"  # 仍远低于 JVM
    cpu: "500m"
```

---

## 迁移检查清单

1. **JVM模式先行**：所有测试在JVM模式通过后再尝试Native Image
2. **Agent追踪**：使用native-image-agent捕获所有反射/资源/类加载
3. **注册反射**：将生成的reflection-config.json合并到项目
4. **迭代构建**：使用`--verbose`定位问题
5. **性能验证**：对比JVM与Native Image性能，确保关键路径无退化

---

## GraalVM检测

```java
String version = System.getProperty("java.vm.version");
if (version.contains("GraalVM")) {
    System.out.println("Running on GraalVM");
}
```

---

## 版本选择

| 场景 | 推荐版本 |
|------|----------|
| 生产环境 | GraalVM CE 22.x + Java 17 |
| 新项目（Native优先） | GraalVM CE 23.x + Java 21 |
| Spring Boot 3.x | GraalVM 22+ required |
