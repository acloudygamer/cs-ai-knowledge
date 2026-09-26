# GraalVM 与云原生

> 前置：[10-响应式编程](10-响应式编程.md)、[01-Java全景](../00-概览/01-Java全景.md)（JIT 分层编译是本篇的对照系） · 后续：[12-安全编码](12-安全编码.md)

> **版本基准**：GraalVM 自 2023 年起版本号对齐 JDK——写作时（2026-09）Oracle GraalVM 25 LTS 为稳定线，25.1 为创新线（2026-06 发布）；Spring Boot 3.0（2022）起内置 Native Image 构建支持。性能数字采用官方宣称口径并标注，示例为**骨架，未实测**。

GraalVM Native Image 的本质是**把"边跑边编译"换成"构建时一次编译完"**：启动时不再有 JVM 引导、类加载、解释执行、JIT 热身这一串开销，产物是一个自包含的本地可执行文件。它回应的约束是云原生的计费与调度模型——按毫秒计费的函数计算、快速伸缩的副本——把 JVM 的"启动慢、热身慢"从可容忍变成了不可接受（JIT 的两笔账见 [01-Java全景](../00-概览/01-Java全景.md)）。

## 本质：封闭世界假设

AOT 编译器必须回答一个 JIT 永远不用回答的问题：**程序会执行的所有代码是哪些？** JIT 可以观望——跑到再编；AOT 必须构建时定案。Native Image 的答案是**封闭世界假设（closed-world assumption）**：从入口方法出发做**可达性分析（reachability analysis）**，把可达的类、方法、字段全部找出来编进可执行文件，**不可达的物理上不存在于产物中**。

这条假设直接划定了边界：

- **能的**：反射（只要登记）、动态代理（只要登记）、资源文件（只要登记）；
- **不能的**：运行时发现新代码——`Class.forName("运行时才知道的类名")`、动态加载 jar、运行时生成字节码（无法枚举的形式）。JVMTI agent、Attach API 这类"旁观 JVM"的调试/监控通道也不存在。

### 可达性元数据：告诉分析器"分析不出来的动态行为"

反射调用 `Class.forName(name)` 的目标在字符串里，静态分析看不见。解法是把这类动态行为登记成 **reachability metadata**（GraalVM 25 起各配置文件合并为统一的 `reachability-metadata.json`，旧的 `reflect-config.json` 等仍被识别）。两条来源：

1. **Tracing agent**：在普通 JVM 上挂 `-agentlib:native-image-agent` 跑一遍测试/典型路径，agent 把实际发生的反射、代理、资源加载记录下来生成元数据；
2. **共享元数据仓库**（graalvm-reachability-metadata）：主流库（Netty、Logback、Hibernate…）的元数据社区已备好，构建插件自动拉取——这是"Spring 应用能 native 化"的实际基础。

### 镜像堆：把初始化搬到构建时

Native Image 构建时还会执行类的静态初始化并把对象图**快照进可执行文件的镜像堆（image heap）**：启动时这些对象已经存在，无需再 new。启动快的一半功劳在这里；另一半约束也在这里——静态初始化里做"运行时才有意义的事"（开 socket、读环境）会在构建时炸出来，框架必须适配（Spring Boot 3 起通过 AOT 处理引擎把自动配置、Bean 定义在构建期固化，把条件评估从运行期挪到构建期）。

### 代价面：峰值与调试

- **峰值性能可能低于 JIT**：JIT 能用运行时画像（profile）做激进内联与去虚化，AOT 只有静态信息。Oracle GraalVM 的 PGO（Profile-Guided Optimization）用画像数据回补一部分，缩小差距。
- **构建慢且吃内存**：可达性分析 + 全量编译，分钟级、数 GB 内存，CI 成本显著高于 `mvn package`。
- **观测与诊断降级**：JFR、agent、heap dump 工具链大多不可用或受限——[08-可观测性](08-可观测性.md) 的指标/追踪仍可用（Micrometer 层面），JVM 内部诊断不行。

## 三条启动加速路线的对比

Native Image 不是唯一答案，2024-2026 年 HotSpot 阵营补齐了两条替代路线：

| 路线 | 机制 | 启动 | 动态性 | 代价 |
|---|---|---|---|---|
| **GraalVM Native Image** | AOT 编译为本地可执行文件 | 最快（官方口径：毫秒级启动、内存数倍于 JVM 的降幅，实测因应用而异） | 封闭世界，反射/代理需元数据 | 构建重、工具链降级、峰值可能略低 |
| **CRaC**（Coordinated Restore at Checkpoint） | JVM 热身后对进程做 checkpoint，启动 = 恢复快照 | 快（恢复通常百毫秒级） | 完整 JVM，动态性全保留 | checkpoint 前要关闭 socket/文件句柄并在 restore 后重建（框架需配合）；无跨机器架构可移植性 |
| **Project Leyden（AOT cache）** | HotSpot 把训练运行中已加载链接的类与方法画像存成缓存，下次启动直接映射（JEP 483，JDK 24；JEP 514/515，JDK 25 扩展） | 中等加速（数倍） | 完整 JVM，零适配 | 加速幅度小于前两者 |

选型的机制逻辑：能接受封闭世界、追求极限冷启动（函数计算、CLI）→ Native Image；要保留全部 JVM 生态（agent、反射自由）、有预热窗口 → CRaC；只想零成本吃掉一部分启动开销 → Leyden AOT cache（JDK 25 自带，`-XX:AOTCache` 系列开关）。

## Spring Boot 集成

Boot 3.0+ 内置 `native` profile，构建命令一句（骨架，未实测）：

```bash
mvn -Pnative spring-boot:build-image    # 或 ./mvnw -Pnative native:compile
```

背后是 Spring AOT 引擎在构建期运行自动配置评估、生成固化的 Bean 定义与反射元数据。适配负担真实存在：用到未登记反射的库会在运行时才抛 `ClassNotFoundException`/`MissingReflectionRegistrationError`——迁移纪律是"JVM 模式全测试通过 → tracing agent 补元数据 → native 模式重跑测试"，CI 里 native 测试应是独立一环。

---

> 前置：[10-响应式编程](10-响应式编程.md) · 后续：[12-安全编码](12-安全编码.md)——生态篇收官：把前面所有外部输入当不可信来源处理
