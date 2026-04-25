# Maven 基础

> **本质断言**：Maven 通过约定优于配置（Convention over Configuration）和依赖传递图解析，将项目构建定义为一个有向无环图（DAG）的拓扑排序过程。

## 依赖解析算法

<pre>
依赖图构建：
A → B:1.0
A → C:2.0
B → D:1.5
C → D:2.0  (冲突)

Maven 最短路径原则：
A → B → D:1.5  (路径长度2)
A → C → D:2.0  (路径长度2) → 声明顺序/Circular选择

冲突解决：选择路径最短的版本；若等长，选择声明靠前的
</pre>

`dependencyManagement` 节点的作用是将版本号提升到父 POM，作为所有子模块引用的版本约束来源，避免版本信息散落在各子模块。

## 项目结构约定

<pre>
my-project/
├── pom.xml
├── src/main/java/        ← 编译输出到 target/classes
├── src/main/resources/   ← 资源文件复制到 target/classes
├── src/test/java/        ← 测试编译输出到 target/test-classes
└── target/               ← 所有构建产物
</pre>

约定优于配置意味着：如果遵循标准目录结构，`pom.xml` 可以极简；如果自定义源码目录（如将 Java 源码放在 `src/java`），则需显式配置 `<sourceDirectory>`。

## 构建生命周期

<pre>
validate → compile → test → package → verify → install → deploy
  │         │        │       │         │        │        │
  │         │        │       │         │        │        └── 推送到远程仓库
  │         │        │       │         │        └── 安装到本地 .m2
  │         │        │       │         └── 运行集成测试
  │         │        │       └── jar/war/zip
  │         │        └── 运行单元测试（surefire）
  │         └── 编译 src/main/java
  └── 验证项目结构正确
</pre>

每个阶段（phase）绑定一个或多个插件目标（goal）。`mvn package` 实际执行 `process-classes → jar:jar` 等。

## 依赖范围（scope）

| scope | 编译可见 | 打包包含 | 测试可见 | 典型用途 |
|-------|---------|---------|---------|---------|
| `compile` | ✓ | ✓ | ✓ | 默认，主代码依赖 |
| `provided` | ✓ | ✗ | ✓ | JDK/容器提供的 API |
| `runtime` | ✗ | ✓ | ✓ | 实现类，如 JDBC 驱动 |
| `test` | ✗ | ✗ | ✓ | 仅测试代码依赖 |

## 参考样例

```xml
<!-- 最小 pom.xml（≤20行）-->
<project>
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>my-app</artifactId>
    <version>1.0.0</version>
    <dependencies>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <version>5.10.0</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>
```

```xml
<!-- 依赖排除（解决冲突）-->
<dependency>
    <groupId>com.example</groupId>
    <artifactId>some-lib</artifactId>
    <version>1.0.0</version>
    <exclusions>
        <exclusion>
            <groupId>org.unwanted</groupId>
            <artifactId>unwanted-artifact</artifactId>
        </exclusion>
    </exclusions>
</dependency>
```

```xml
<!-- Spring Boot 父 POM -->
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.4.0</version>
</parent>
```

```xml
<!-- 多模块父 POM -->
<project>
    <groupId>com.example</groupId>
    <artifactId>parent-project</artifactId>
    <version>1.0.0</version>
    <packaging>pom</packaging>
    <modules>
        <module>module-a</module>
        <module>module-b</module>
    </modules>
</project>
```

```xml
<!-- 阿里云镜像 -->
<mirrors>
    <mirror>
        <id>aliyun</id>
        <url>https://maven.aliyun.com/repository/public</url>
        <mirrorOf>central</mirrorOf>
    </mirror>
</mirrors>
```

```bash
# 常用命令
mvn compile        # 编译
mvn test            # 运行测试
mvn package         # 打包
mvn dependency:tree  # 查看依赖树
```
