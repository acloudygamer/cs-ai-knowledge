# Gradle

## 定义

Gradle 构建逻辑由**有向无环图（DAG）**驱动，每个 Task 节点代表一个原子构建操作（有输入、执行逻辑、输出），边代表任务依赖关系（有向边 $T_A \rightarrow T_B$ 表示 $T_B$ 依赖 $T_A$ 的输出）。执行引擎按 DAG 的拓扑排序决定任务并行度：无依赖或依赖已满足的任务可并行执行。

## 数学模型

### 任务 DAG 的拓扑排序

设任务集合 $T = \{t_1, t_2, \ldots, t_n\}$，依赖关系构成偏序集合 $(T, \prec)$，其中 $t_a \prec t_b$ 表示 $t_b$ 依赖 $t_a$ 的输出。拓扑排序保证：
$$\forall (t_a, t_b) \in \prec: \text{position}(t_a) < \text{position}(t_b)$$

并行执行度上界：
$$\text{maxParallelism} = \min(|T|, \text{CPU\_cores})$$

实际上由于任务间存在文件锁、端口占用等资源竞争，实际并行度可能低于上界。

### 增量构建的指纹算法

设任务 $t$ 的输入指纹为 $F_{in}(t) = \text{hash}(\text{content\_hash}(f_1), \text{content\_hash}(f_2), \ldots)$，输出指纹为 $F_{out}(t) = \text{hash}(\text{content\_hash}(o_1), \text{content\_hash}(o_2), \ldots)$。

任务跳过条件：
$$F_{in}(t) = F_{in}^{\text{cached}} \land F_{out}(t) = F_{out}^{\text{cached}} \land \text{cacheValid}(t)$$

若任一条件不满足，任务重新执行。

### cacheValid(t) 的判断逻辑

`cacheValid(t)` 是任务缓存有效性的附加约束，由 Gradle 的构建缓存（Build Cache）决定：

$$\text{cacheValid}(t) = \text{buildCacheEnabled} \land \text{outputLocationsValid}(t)$$

其中 `outputLocationsValid(t)` 检查输出目标位置是否满足以下全部条件：

1. **输出不存在冲突**：任务的输出文件未被其他任务声明为输入（防止输出污染）
2. **构建缓存可访问**：本地构建缓存或远程构建缓存（Gradle Enterprise/Develocity）可读
3. **输出完整性**：任务的全部输出文件均已就位（无部分写入）

**远程构建缓存的场景**：当 `buildCacheEnabled=true` 且配置了远程缓存时，`cacheValid(t)` 还需满足：
$$\text{remoteCacheHit}(t) = \text{true} \land \text{artifactUpToDate}(t)$$

即 Gradle 从远程缓存下载产物后，会验证下载文件的 SHA-256 校验和与元数据中记录的值是否一致：

$$\text{verify}(artifact) = \text{SHA256}(\text{artifact}) \stackrel{?}{=} \text{meta.expectedHash}$$

指纹碰撞概率（SHA-256）：
$$P(\text{collision}) \approx 2^{-256} \approx 10^{-77}$$

### 依赖解析的版本冲突解决

Maven 使用"最短路径优先"（nearest-first）原则：若 A→B→C→D@1.0 且 A→X→D@2.0，则选择 D@2.0（路径长度 2 < 3）。

Gradle 使用"最新版本优先"（最新策略），但允许通过 `resolutionStrategy` 强制指定版本。

**归约终点**：Gradle 的 DAG 执行模型可归约为**拓扑排序 + 并行调度**，是最优构建顺序的存在性证明。

## 数据流

<pre>
构建初始化阶段:
settings.gradle
    │
    ▼ 解析
Project 对象树
    │
    ▼ 配置
Task DAG 构建
    │
    ▼
┌─────────────────────────────────────────────┐
│                  Task DAG                     │
│                                              │
│   :compileJava ──► :processResources ──► :classes │
│        │                                       │       │
│        │     ┌────────────────────────────────┘       │
│        ▼     ▼                                        │
│   :compileTestJUnit ──► :test ──► :build              │
│                              │                         │
│                              ▼                         │
│                       :bootJar (Spring Boot)           │
└─────────────────────────────────────────────┘
        │
        ▼ 执行引擎按拓扑序调度
任务并行执行（无依赖任务同时运行）
        │
        ▼
构建缓存 (.gradle/caches/) 或 产物输出 (build/)
</pre>

### 增量构建数据流

```
输入文件 ──► 哈希计算 ──► 对比缓存指纹
                              │
                              ├── 匹配 ──► 跳过任务，跳过输出检查
                              │
                              └── 不匹配 ──► 执行任务 ──► 计算输出指纹 ──► 写入缓存
```

## 机制

### 增量构建 vs 传统时间戳检查

传统 Makefile：检查文件修改时间（mtime），精度为秒级，但存在时钟 skew 问题（ NFS 时钟不同步导致误判）。

Gradle 指纹：计算文件内容哈希，精度为位级，仅在内容真正变化时触发重构建。

### 任务并行执行的约束

- 任务间无读写冲突（无共同输入/输出文件）时可安全并行
- Gradle 的 worker API 提供进程隔离（`maxWorkers` 控制并发度）
- 文件锁（Project.fileLock）防止同一文件被并发读写

### 任务输出的文件锁机制

当多个任务可能写入同一文件时（如多个 sourceSet 编译到同一 classpath），Gradle 通过文件锁协调：

```groovy
// 文件锁确保同一时刻只有一个任务写入
fileLock.lock()  // 阻塞直到获取锁
try {
    // 写入操作
} finally {
    fileLock.unlock()
}
```

锁的粒度是文件级别，高并发时仍可能成为瓶颈。

### 依赖配置的作用域

- `implementation`：编译可见，传递依赖不暴露（消费者无法看到 B 的传递依赖 C）
- `api`（等价于旧 `compile`）：编译可见，传递依赖暴露（消费者可以看到 C）
- `compileOnly`：仅编译时存在，不打包不运行

`api` 配置解决的是"依赖泄漏"问题——库作者希望暴露某些传递依赖供消费者使用，但 `implementation` 会阻断这种传递性。

### Gradle Wrapper 的原理

`gradlew` 脚本在首次执行时检测本地是否有指定版本 Gradle，若无则从 `services.gradle.org` 下载。下载的 Gradle 安装在 `~/.gradle/wrapper/dists/` 目录下，所有后续构建使用统一的 Gradle 版本。

### gradlew 校验和验证机制

Gradle Wrapper 的校验和验证采用 SHA-256 哈希链机制，确保下载的 Gradle 发行版未被篡改：

**校验流程**：
1. `gradle/wrapper/gradle-wrapper.properties` 中记录了下载 URL 和校验和：
   ```properties
   distributionUrl=https\://services.gradle.org/distributions/gradle-8.5-bin.zip
   distributionSha256Sum=3168d2e0...  # Gradle 8.0+ 新增字段
   ```
2. `gradlew` 脚本首次下载 zip 后，计算本地文件的 SHA-256 摘要：
   ```bash
   sha256sum gradle-8.5-bin.zip
   ```
3. 将计算结果与 `distributionSha256Sum` 比对：
   $$\text{verify} = \begin{cases} \text{pass} & \text{SHA256}(\text{downloaded}) = \text{expected} \\ \text{fail} & \text{otherwise} \end{cases}$$
4. 校验失败时抛出异常，拒绝解压和使用该发行版

**校验和更新的原子性**：Gradle 升级时，校验和由官方在发布时写入 `gradle-wrapper.properties`。若校验和不匹配，说明下载被劫持（中间人攻击）或 CDN 被污染。Gradle 8.0+ 原生支持此字段；旧版本可通过 `wrapper` 任务自动添加校验和。

### 依赖解析的最新版本策略

Gradle 默认使用"最新版本优先"策略，与 Maven 的"最短路径优先"不同：

```groovy
// 强制指定版本（覆盖所有路径）
configurations.all {
    resolutionStrategy {
        force 'org.slf4j:slf4j-api:2.0.9'
    }
}

// 指定版本替换
configurations.all {
    resolutionStrategy {
        eachDependency { details ->
            if (details.requested.group == 'org.slf4j') {
                details.useVersion '2.0.9'
            }
        }
    }
}
```

**冲突示例**：
```
A → B:1.0 → C:2.0
A → X:1.0 → C:1.0
```

Maven 选择 C:1.0（路径长度 2 < 3）
Gradle 选择 C:2.0（最新版本）

## 参考存根

```groovy
// build.gradle 增量构建验证（≤20行）
tasks.register(' fingerprint') {
    inputs.file("src/main/java/Main.java")
    outputs.file("build/classes/java/main.class")
    doLast {
        println "Compiling..."
    }
}
```

```groovy
// 任务并行配置
org.gradle.parallel=true
org.gradle.workers.max=4  // 最多4个并行 worker
```

```groovy
// 依赖冲突解决
configurations.all {
    resolutionStrategy {
        force 'org.slf4j:slf4j-api:2.0.9'
    }
}
```
