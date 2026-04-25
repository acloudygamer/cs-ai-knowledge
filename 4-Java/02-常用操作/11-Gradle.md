# Gradle

> **本质断言**：Gradle 构建逻辑由有向无环图（DAG）驱动，每个 Task 节点代表一个原子构建操作，边代表任务依赖关系，执行引擎按拓扑排序决定任务并行度和执行顺序。

## 构建 DAG

<pre>
应用构建任务图:

:compileJava ──► :processResources ──► :classes
      │                                    │
      │         ┌─────────────────────────┘
      │         ▼
:compileTestJUnit ──► :test ──► :build
                          │
                          ▼
                   :bootJar (Spring Boot)
</pre>

**增量构建原理**：每个 Task 记录 `lastBuildSuccessTimestamp` 和输入指纹（input file hash）、输出指纹（output file hash）。构建时比较当前指纹与记录指纹，仅在指纹变化时重新执行任务。这使 Gradle 在大多数增量修改后跳过 90%+ 的任务。

## Gradle vs Maven 核心差异

| 特性 | Gradle | Maven |
|------|--------|-------|
| 构建语言 | Groovy/Kotlin DSL | XML |
| 依赖解析 | DAG + 传递依赖智能解析 | 最短路径 + 声明顺序 |
| 增量构建 | 基于任务指纹 | 基于时间戳 |
| 并行执行 | 任务级并行 | Reactor 模式 |
| 配置方式 | 声明式 + 代码式 | 纯声明式 |

**为什么 Gradle 更快**：Maven 的 Reactor 只决定模块构建顺序，每个模块内部仍是顺序执行。Gradle 的任务级并行（`--parallel`）允许 DAG 中无依赖的任务同时执行，现代多核 CPU 上显著提速。

## 依赖配置

<pre>
implementation vs api vs compileOnly:

implementation: 编译时可用，传递依赖不暴露给消费者
               A → B(implementation) → C  → C 对 A 不可见

api (≈ compile): 编译时可用，传递依赖暴露给消费者
               A → B(api) → C     → C 对 A 可见

compileOnly: 仅编译时，不打包、不运行
</pre>

`api` 配置解决了"依赖泄漏"问题：库作者希望某些传递依赖对使用者可见（用于进一步扩展），但 `implementation` 会阻断传递性。

## Gradle Wrapper

`gradlew` 脚本在用户首次执行时下载指定版本的 Gradle，然后所有团队成员使用相同的 Gradle 版本，消除"在我机器上能构建"的兼容性问题。

## 参考样例

```groovy
// settings.gradle（≤20行）
rootProject.name = 'my-app'
include 'app', 'library'
```

```groovy
// build.gradle (Groovy DSL)
plugins {
    id 'java'
    id 'application'
}
group = 'com.example'
version = '1.0.0'
repositories { mavenCentral() }
dependencies {
    implementation 'com.google.guava:guava:32.1.3-jre'
    testImplementation 'org.junit.jupiter:junit-jupiter:5.10.1'
}
java {
    sourceCompatibility = JavaVersion.VERSION_25
    targetCompatibility = JavaVersion.VERSION_25
}
application { mainClass = 'com.example.App' }
test { useJUnitPlatform() }
```

```kotlin
// build.gradle.kts (Kotlin DSL)
plugins { java; application }
group = "com.example"
version = "1.0.0"
repositories { mavenCentral() }
dependencies {
    implementation("com.google.guava:guava:32.1.3-jre")
    testImplementation("org.junit.jupiter:junit-jupiter:5.10.1")
}
java { sourceCompatibility = JavaVersion.VERSION_25 }
application { mainClass.set("com.example.App") }
```

```groovy
// 依赖冲突解决
configurations.all {
    resolutionStrategy { force 'org.slf4j:slf4j-api:2.0.9' }
}
```

```groovy
// 自定义任务
tasks.register('hello') {
    doLast { println 'Hello, Gradle!' }
}
```

```groovy
// Spring Boot
plugins {
    id 'java'
    id 'org.springframework.boot' version '3.4.0'
    id 'io.spring.dependency-management' version '1.1.4'
}
dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web'
}
```

```bash
# 常用命令
gradle build          # 编译测试
gradle test           # 运行测试
gradle bootRun        # 运行 Spring Boot
gradle dependencies   # 查看依赖树
```

```properties
# gradle.properties
org.gradle.jvmargs=-Xmx2g -XX:+HeapDumpOnOutOfMemoryError
org.gradle.daemon=true
org.gradle.parallel=true
org.gradle.caching=true
```
