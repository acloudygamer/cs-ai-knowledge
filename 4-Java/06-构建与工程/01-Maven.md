# Maven

> 前置：[01-语言核心](../01-语言核心/) · 后续：[Gradle](./02-Gradle.md)

> **版本基准**：Maven 3.9.16（现行稳定版，maven.apache.org 2026 年口径；Maven 4.0 处于 RC 阶段）。插件版本以 Maven Central 现行稳定版为准：maven-compiler-plugin 3.16.0、maven-surefire-plugin 3.6.0。本机无 Maven，XML 示例为**骨架，未实测**，但坐标、生命周期阶段名、插件名与版本均已网查核实。

Maven 是约定驱动的构建工具：开发者用一份 `pom.xml`（POM，Project Object Model，项目对象模型）声明"这个项目是什么、依赖谁、怎么打包"，Maven 把声明翻译成一次具体构建——下载依赖、编译、跑测试、打 JAR。它要回应的约束是手工 `javac` 在多模块、多依赖下的失控：classpath 靠手工拼、依赖 JAR 靠手工下载、版本靠口头约定。Maven 的解法是三条约定——坐标寻址、固定生命周期、仓库缓存——本篇沿这三条展开。

## 坐标：依赖的寻址方案

每个构件（artifact，一次发布产出的 JAR/POM 等文件）由三元组唯一寻址：

- **groupId**：发布组织，约定为反向域名，如 `org.apache.commons`；
- **artifactId**：模块名，如 `commons-lang3`；
- **version**：版本号，`3.20.0` 这样的定版，或 `1.0-SNAPSHOT` 这样的开发中快照（默认按日检查远程更新，updatePolicy 可调；定版则永久缓存）。

坐标决定了两端的连接：对上游，`groupId:artifactId:version` 是在仓库里发起 HTTP 下载的路径；对下游，它映射到本地仓库的文件位置 `~/.m2/repository/org/apache/commons/commons-lang3/3.20.0/commons-lang3-3.20.0.jar`——groupId 的 `.` 展开为目录层级。本地仓库是缓存层：已下载的构件不再走网络，这是 Maven 离线可重复构建的基础。

```xml
<!-- 骨架，未实测（本机无 Maven） -->
<dependency>
    <groupId>org.junit.jupiter</groupId>
    <artifactId>junit-jupiter</artifactId>
    <version>5.14.4</version>   <!-- JUnit 5 维护线现行版（2026-04）；JUnit 6 已发布，见 07-02 -->
    <scope>test</scope>
</dependency>
```

## 依赖传递与冲突调解

声明一个依赖，得到的是一棵依赖树：A 依赖 B，B 又依赖 C，C 被**传递**进 A 的 classpath。这带来冲突——同一个 artifact 可能从多条路径被拉入，且版本不同。Maven 的调解规则是**最近优先**（nearest wins）：从项目根到该 artifact 的所有路径中，深度最浅的版本胜出；深度并列时，POM 中声明顺序靠前的胜出。

```text
项目 A
  ├── B:1.0            ← 深度 1，胜出
  └── C:2.0
       └── B:2.0       ← 深度 2，被淘汰
```

规则之上还有两个显式干预手段，优先级高于"最近优先"：

1. **直接声明**：当前 POM 里直接写的依赖，永远压过传递进来的版本（深度 0 vs 深度 ≥1，本质是最近优先的特例）。
2. **`<dependencyManagement>`**：在父 POM 中集中锁定版本号，子模块声明依赖时不写版本。它只钉版本、不引入依赖；典型用法是导入 BOM（Bill of Materials，如 `spring-boot-dependencies`）一次锁定整组生态版本。

排查冲突的标准工具是 `mvn dependency:tree`，它把整棵解析后的树连同"谁淘汰了谁"打印出来，是定位版本错位的入口。另一个常用手段是 `<exclusions>`：在某条依赖声明里排除掉它传递带入的特定 artifact，切断一条路径。

scope（作用域）决定依赖出现在哪条 classpath 上，也决定它是否传递：

| scope | 编译主代码 | 编译/跑测试 | 打入运行时 | 传递给下游 |
|---|---|---|---|---|
| `compile`（默认） | 是 | 是 | 是 | 是 |
| `provided` | 是 | 是 | 否（由运行环境提供，如 Servlet 容器） | 否 |
| `runtime` | 否 | 是 | 是 | 是（降为 runtime） |
| `test` | 否 | 是 | 否 | 否 |

`provided` 与 `test` 不传递，是刻意收窄：Servlet API 该不该出现在运行时，由部署目标决定，不能顺着依赖链污染别人。

## 生命周期与插件：活都是插件干的

Maven 有三套互相独立的生命周期：**clean**（pre-clean → clean → post-clean）、**default**（构建主线）、**site**（生成站点文档，实践中很少用）。default 生命周期的主干阶段：

```text
validate → compile → test → package → verify → install → deploy
```

执行语义是线性前缀：`mvn package` 会顺序跑完 validate 到 package 的全部阶段。这里有一个容易误解的结构事实——**阶段本身只是空槽位，真正干活的是插件目标（goal）**。`compile` 阶段绑定了 `maven-compiler-plugin:compile`，`test` 阶段绑定了 `maven-surefire-plugin:test`，`package` 阶段按 packaging 类型绑定 `maven-jar-plugin:jar` 等。绑定关系由 packaging 默认值决定，也可以在 `<build><plugins>` 里显式声明插件版本与额外绑定：

```xml
<!-- 骨架，未实测；版本为 Maven Central 现行稳定版 -->
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-compiler-plugin</artifactId>
    <version>3.16.0</version>
    <configuration>
        <release>21</release>   <!-- 等价于 javac --release 21 -->
    </configuration>
</plugin>
```

这条链的上下游是清楚的：命令行给阶段名 → Maven 展开为前缀阶段序列 → 每个阶段查绑定表得到 goal 列表 → 插件读写 `src/main/java`、`target/` 等约定目录。约定优于配置的含义就在这里：目录结构、阶段顺序、默认绑定全是定死的，POM 只声明差异。

多模块项目用 parent POM 的 `<modules>` 聚合，Maven 的 **reactor** 对模块间依赖做拓扑排序决定构建顺序——被依赖的模块先构建；出现环（A 依赖 B、B 依赖 A）时 reactor 直接报错拒绝构建，因为拓扑序不存在。

## 仓库层级与 settings.xml

一次依赖下载沿三级查找：**本地仓库**（`~/.m2/repository`，命中即止）→ **settings.xml 配置的镜像/私服** → **Maven 中央仓库**（`repo.maven.apache.org`，默认远程）。`settings.xml`（位于 `~/.m2/`）是用户级配置，与项目无关：镜像、代理、私服凭证都在这里。国内常见配置是把中央仓库镜像到阿里云：

```xml
<!-- 骨架，未实测 -->
<mirrors>
    <mirror>
        <id>aliyun</id>
        <url>https://maven.aliyun.com/repository/public</url>
        <mirrorOf>central</mirrorOf>
    </mirror>
</mirrors>
```

`mirrorOf=central` 的含义：凡是本来要发往中央仓库的请求，改发到镜像。私服（Nexus、Artifactory）在同一层，承担企业内部构件的发布与代理缓存。

## 版图与边界

Maven 的版图：Java 后端企业开发的存量事实标准，Spring Boot 官方同时提供 Maven 与 Gradle 两套脚手架。它的强项恰是约束的产物——生命周期与目录约定钉死后，任何 Maven 项目的构建方式都一样，维护成本极低。

代价同样是约束的产物：

- **XML 声明式**表达不了条件逻辑与循环，复杂构建要靠堆插件配置绕；
- **生命周期是固定线性骨架**，阶段间无法自由编排 DAG，并行与增量构建弱于 Gradle（见 [02-Gradle](./02-Gradle.md) 的对比）；
- 传递依赖调解规则简单可预测，但"最近优先"在大依赖树下会选中出乎意料的版本，需要 `dependency:tree` 人工兜底。

模块级的封装与运行时裁剪不归 Maven 管——那是 Java 9 引入的模块系统（[03-模块系统JPMS](./03-模块系统JPMS.md)）的职责，Maven/Gradle 只负责把模块路径准备好。

---

> 前置：[01-语言核心](../01-语言核心/) · 后续：[Gradle](./02-Gradle.md)——同一问题的另一种解法：任务图驱动
