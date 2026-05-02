# Maven 基础

## 定义

Maven 是基于项目对象模型（POM）的构建自动化工具，核心是将项目构建定义为有向无环图（DAG）的拓扑排序过程。POM 声明依赖、插件、属性，Maven 通过依赖传递解析和生命周期阶段绑定，将声明转化为可执行的构建任务序列。

## 数学模型

### 依赖解析的最短路径算法

Maven 使用最近声明优先（Nearest Definition）策略解析版本冲突。设依赖图 $G = (V, E)$，$V$ 为 artifact，$E$ 为依赖关系边。

对于 artifact $a$，其版本 $\text{ver}(a)$ 按以下规则确定：

$$\text{ver}(a) = \begin{cases}
\text{from\_dependencyManagement}(a) & \text{if defined} \\
\text{nearest}(a) & \text{else}
\end{cases}$$

其中 $\text{nearest}(a)$ 返回从根节点（当前项目）到 $a$ 的**最短路径**上的最后一个声明版本。若存在等长路径，选择声明顺序靠前的。

**形式化**：设 $P = \{p_1, p_2, ..., p_k\}$ 为所有从根到 $a$ 的路径，$|p_i|$ 为路径长度，$v_i$ 为 $p_i$ 末端的版本。则：

$$\text{nearest}(a) = v_j \text{ where } j = \arg\min_i |p_i|$$

**归约终点**：依赖冲突解决本质上是图论中的最短路径问题，路径长度定义为边数而非权重。

### DAG 拓扑排序的构建顺序

Maven 生命周期阶段（validate → compile → test → package → install → deploy）构成线性序。插件 goal 绑定到阶段，构建时按阶段顺序执行。

多模块项目的模块构建顺序由 reactor 决定：

$$O = \text{topological\_sort}(M, D)$$

其中 $M$ 为模块集合，$D$ 为模块间依赖关系（`<module>` 声明）。若存在环形依赖，reactor 失败并报错。

### 依赖传递的图收缩

传递依赖构成完全依赖图 $G_T$。排除（`exclusion`）操作将图中某些边移除：

$$G_T' = (V, E_T \setminus \{ (u, v) \mid u \in \text{exclusions} \})$$

收缩后重新计算 $\text{nearest}$，可能导致原本被排除的 artifact 重新被解析（若存在其他路径）。

## 数据流

<pre>
Maven 构建数据流：

    pom.xml 解析
         │
         ▼
    ┌────────────────────────────────────┐
    │  Project / Reactor                  │
    │  - 当前项目                         │
    │  - 模块列表（若有）                   │
    │  - dependencyManagement            │
    └────────────────────────────────────┘
         │
         ▼
    依赖解析（Dependency Resolution）
         │
         ▼
    ┌────────────────────────────────────┐
    │  Artifact 节点                      │
    │  [groupId:artifactId:version]       │
    └────────────────────────────────────┘
         │
         ├──────────────────┬──────────────┐
         ▼                  ▼              ▼
    本地仓库缓存      远程仓库下载    依赖传递
    (~/.m2/repository)  (Maven Central)  (transitive)

         │
         ▼
    Reactor 拓扑排序
         │
         ▼
    生命周期执行
    ┌────────────────────────────────────┐
    │  validate → compile → test          │
    │  → package → verify → install      │
    │  → deploy                          │
    └────────────────────────────────────┘
         │
         ▼
    构建产物（target/）
</pre>

**资源流转**：
- `pom.xml` → 内存中的 Project 对象
- 依赖坐标 → 本地仓库路径（`groupId/artifactId/version/artifactId-version.jar`）
- 插件 goal → 绑定到生命周期的具体执行类

## 机制

### dependencyManagement 的作用域提升

`<dependencyManagement>` 的作用是将版本号从子模块提升到父 POM：

```xml
<!-- 父 POM -->
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>org.springframework</groupId>
            <artifactId>spring-core</artifactId>
            <version>6.1.0</version>
        </dependency>
    </dependencies>
</dependencyManagement>

<!-- 子模块 POM（无需声明 version） -->
<dependencies>
    <dependency>
        <groupId>org.springframework</groupId>
        <artifactId>spring-core</artifactId>
        <!-- 版本从 dependencyManagement 继承 -->
    </dependency>
</dependencies>
```

**约束**：只有直接匹配的 `groupId:artifactId` 才从 `dependencyManagement` 继承版本，传递依赖不自动应用。

### scope 的传递闭包

依赖 scope 在传递时按以下规则变换：

| 依赖的 scope | 传递到依赖于该项目的 scope |
|--------------|---------------------------|
| `compile` | `compile` |
| `provided` | `compile` |
| `runtime` | `runtime` |
| `test` | 不传递 |

**关键约束**：`provided` 和 `test` 不传递。这意味着若 `A → B → C`，且 `B` 的 `spring-core` 为 `provided`，则 `A` 不会获得 `spring-core`（除非 `A` 直接声明）。

### 插件 goal 的阶段绑定语义

`mvn <phase>` 执行该阶段及之前的所有阶段。每个阶段绑定零个或多个插件 goal：

```
compile 阶段默认绑定:
  └── maven-compiler-plugin:compile → 编译 src/main/java

test 阶段默认绑定:
  └── maven-compiler-plugin:testCompile → 编译 src/test/java
  └── maven-surefire-plugin:test → 运行测试
```

自定义绑定通过 `<executions><execution>` 声明：

```xml
<plugin>
    <executions>
        <execution>
            <id>my-goal</id>
            <phase>package</phase>
            <goals><goal>myGoal</goal></goals>
        </execution>
    </executions>
</plugin>
```

### reactor 的环形依赖检测

Maven reactor 在构建前检测模块依赖图中的环。若存在环形依赖：

```
A → B → C
    └── D → C
```

构建顺序通过拓扑排序确定。若添加 `D → A` 形成环，reactor 抛出 `ProjectCycleException`。

**检测算法**：深度优先搜索（DFS）+ 回溯标记，复杂度 $O(|V| + |E|)$。

### 依赖解析的冲突解决实例

考虑以下依赖图：

```
项目 A
  ├── B:1.0
  └── C:2.0
       └── B:2.0
```

从 A 到 B 的路径：
- A → B:1.0（长度 1）
- A → C:2.0 → B:2.0（长度 2）

按最近路径优先原则，选择 B:1.0。若 A 的 dependencyManagement 声明了 B:3.0，则优先使用 dependencyManagement 的版本。

### 传递依赖的版本覆盖

传递依赖的版本覆盖规则：

1. 若直接在当前 POM 声明 → 使用当前 POM 的版本（无论 dependencyManagement 是否存在）
2. 否则，若在 dependencyManagement 中声明 → 使用 dependencyManagement 的版本
3. 否则，选择路径最近的传递依赖版本
4. 若存在等长路径，选择 POM 中声明顺序靠前的

这形成了一个优先级序列：

$$\text{direct} > \text{dependencyManagement} > \text{transitive (nearest)}$$

## 参考存根

```xml
<!-- 多模块 reactor（≤20行）-->
<project>
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>parent</artifactId>
    <version>1.0</version>
    <packaging>pom</packaging>
    <modules>
        <module>api</module>
        <module>impl</module>
    </modules>
</project>
```

```bash
# 依赖树分析（定位冲突）
mvn dependency:tree -Dverbose \
    -Dincludes=com.example:problematic-artifact
# 输出显示哪些路径引入该 artifact
```

```xml
<!-- 阿里云镜像配置（settings.xml）-->
<mirrors>
    <mirror>
        <id>aliyun</id>
        <url>https://maven.aliyun.com/repository/public</url>
        <mirrorOf>central</mirrorOf>
    </mirror>
</mirrors>
```

```xml
<!-- dependencyManagement 版本锁定 -->
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>com.google.guava</groupId>
            <artifactId>guava</artifactId>
            <version>32.1.3-jre</version>
        </dependency>
    </dependencies>
</dependencyManagement>
```

```xml
<!-- 传递依赖排除 -->
<dependency>
    <groupId>com.example</groupId>
    <artifactId>legacy-lib</artifactId>
    <version>1.0</version>
    <exclusions>
        <exclusion>
            <groupId>org.slf4j</groupId>
            <artifactId>slf4j-api</artifactId>
        </exclusion>
    </exclusions>
</dependency>
```
