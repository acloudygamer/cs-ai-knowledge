# Gradle

> 前置：[Maven](./01-Maven.md) · 后续：[模块系统 JPMS](./03-模块系统JPMS.md)

> **版本基准**：Gradle 9.8.0（gradle.org 现行版本，2026 年口径）；Gradle 9 起运行守护进程要求 JVM 17+（编译目标仍可到更低版本）。本机无 Gradle，构建脚本示例为**骨架，未实测**，但 DSL API、配置名与版本均已网查核实。脚本一律用 Kotlin DSL（`build.gradle.kts`）——Gradle 官方自 2023 年起以 Kotlin DSL 为新建项目默认。

Gradle 是任务图驱动的构建工具：构建脚本是一段可执行的程序，它在**配置阶段**构造出一张任务有向无环图（DAG），**执行阶段**按依赖拓扑序调度这张图。这与 Maven（[01-Maven](./01-Maven.md)）的本质差异在于骨架的形状：Maven 的生命周期是钉死的线性阶段序列，插件目标挂在固定槽位上；Gradle 没有这条骨架，只有任务与任务间的依赖边，阶段概念被"任务依赖"取代。形状差异回应的约束不同：Maven 押注"所有项目构建方式相同"换可维护性，Gradle 押注"构建即代码"换表达力与性能。

## 三阶段：初始化、配置、执行

每次 `gradle build` 都走三段：

1. **初始化**：读 `settings.gradle.kts`，确定本次构建包含哪些 project（单模块或子模块列表）。
2. **配置**：执行各模块的 `build.gradle.kts`，注册任务、连依赖边，产出任务 DAG。这一阶段是纯图构造，不执行任何任务动作。
3. **执行**：从请求的任务出发沿依赖边回溯，按拓扑序执行图中被需要的子集。

一个最小 Java 项目的构建脚本：

```kotlin
// build.gradle.kts —— 骨架，未实测（本机无 Gradle）
plugins {
    `java-library`
}

repositories {
    mavenCentral()
}

dependencies {
    implementation("com.google.guava:guava:33.5.0-jre")
    testImplementation("org.junit.jupiter:junit-jupiter:5.13.4")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

tasks.test {
    useJUnitPlatform()
}
```

上下游连接：`plugins` 块引入的 `java-library` 插件是任务图的来源——它注册了 `compileJava`、`processResources`、`classes`、`test`、`jar`、`build` 等任务并连好边（`jar` 依赖 `classes`，`classes` 依赖 `compileJava`）；`gradle build` 请求 `build` 任务，引擎沿边回溯出整条链。

## 性能机制：守护进程、增量、缓存

Gradle 相对 Maven 的性能优势来自三个机制，全部围绕"不重复干活"：

- **守护进程（Daemon）**：构建跑在一个常驻 JVM 里，后续构建复用它——JVM 启动费、JIT 热身、类加载只付一次。配置缓存（configuration cache，Gradle 8 起逐步转正）进一步把配置阶段的图构造结果序列化复用。
- **增量构建**：每个任务声明自己的 inputs（源文件、配置参数）与 outputs（产物目录）。执行前对输入做内容哈希指纹，与上次记录比对：不变则任务标记 `UP-TO-DATE` 直接跳过。与 Make 的 mtime 时间戳相比，内容哈希不受时钟漂移与 `touch` 误触发影响。
- **构建缓存（Build Cache）**：任务输出按输入指纹的哈希值存入缓存（本地或远程节点），指纹命中时直接从缓存取产物而不执行。换台机器、CI 换 agent，只要输入指纹一致就能命中。

这三个机制能成立，前提正是"任务图 + 显式输入输出声明"的形状——Maven 的固定阶段模型里插件各自为政，没有统一的输入输出声明面，这是两者性能差距的结构根源。

## 依赖配置：implementation 与 api 的分界线

Gradle 的依赖声明挂在**配置**（configuration，一条具名 classpath）上，常用配置与 Maven scope 的对应：

| Gradle 配置 | 编译主代码 | 打包/运行时 | 暴露给消费者 | 对应 Maven scope |
|---|---|---|---|---|
| `implementation` | 是 | 是 | 否 | 无精确对应（最接近 `compile` 但不泄漏） |
| `api`（java-library 插件） | 是 | 是 | 是 | `compile` |
| `compileOnly` | 是 | 否 | 否 | `provided` |
| `runtimeOnly` | 否 | 是 | 否 | `runtime` |
| `testImplementation` | 测试代码 | 测试 | — | `test` |

`implementation` 与 `api` 的分界随 java-library 插件在 Gradle 3.4（2017-02）引入；Gradle 6（2019）弃用了旧 `compile` 配置（Gradle 7 移除），此后这条分界成为唯一正道：库的内部依赖用 `implementation`，不出现在消费者的编译 classpath 上——这既防止了依赖泄漏（消费者意外引用到库的内部类型），也让 Gradle 能跳过无关模块的重编译（内部依赖变化不影响消费者的编译指纹）。只有当库把自己的依赖类型写进公开 API 签名时，才必须用 `api`。

版本冲突调解规则与 Maven 相反：Gradle 默认**最新版本优先**（highest wins），无论路径深浅。强制钉版本用 `resolutionStrategy`：

```kotlin
// 骨架，未实测
configurations.all {
    resolutionStrategy {
        force("org.slf4j:slf4j-api:2.0.17")
    }
}
```

排查入口是 `gradle dependencies --configuration runtimeClasspath`（对应 Maven 的 `dependency:tree`）。多模块项目的版本集中管理用 version catalog（`gradle/libs.versions.toml`），角色对应 Maven 的 BOM。

## Gradle Wrapper：把工具版本钉进仓库

`gradlew` / `gradlew.bat` 是随项目提交的启动脚本，`gradle/wrapper/gradle-wrapper.properties` 里钉死发行版 URL：

```properties
distributionUrl=https\://services.gradle.org/distributions/gradle-9.8.0-bin.zip
```

首次执行时按 URL 下载并缓存到 `~/.gradle/wrapper/dists/`，此后所有人、所有 CI 节点跑的是同一 Gradle 版本——构建工具的版本不再是环境变量，而是项目的一部分。可追加 `distributionSha256Sum` 字段校验下载完整性，防 CDN 污染与中间人篡改。

## 版图与边界

Gradle 的版图：Android 与 Kotlin 生态的事实标准，大型多模块项目与对构建速度敏感的团队的常见选择；Maven 与 Gradle 在 Spring 生态里是并列的一等公民。选择口径：

- 团队大、项目形态标准、求稳求一致 → Maven 的强约定是资产；
- 构建慢已成为瓶颈、需要自定义构建逻辑、Android/Kotlin 项目 → Gradle 的任务图与缓存是资产；
- 代价要认：Gradle 脚本是代码，自由度即复杂度来源，DSL 写法随版本演进快（Groovy DSL 存量、Kotlin DSL 现行），升级大版本有迁移成本（Gradle 9 清理了大量弃用 API）。

两者共同的边界：它们管理编译与打包期的依赖，不管运行期的封装与裁剪——把模块路径交给 JVM 的事，见 [03-模块系统JPMS](./03-模块系统JPMS.md)。

---

> 前置：[Maven](./01-Maven.md) · 后续：[模块系统 JPMS](./03-模块系统JPMS.md)——构建工具的下游：运行时模块图
