# Maven 基础

## 概述

Maven 是 Java 主流的构建工具和依赖管理工具，通过 `pom.xml` 声明项目依赖和构建配置。

核心功能：
- **依赖管理**：自动下载、更新、解决依赖冲突
- **构建自动化**：编译、打包、测试、部署
- **项目模板**：使用 Archetype 创建标准项目结构
- **统一构建**：保证团队构建一致性问题

## 项目结构

```
my-project/
├── pom.xml              # 项目配置
├── src/
│   ├── main/
│   │   ├── java/        # Java 源码
│   │   └── resources/   # 资源文件
│   └── test/
│       ├── java/        # 测试源码
│       └── resources/   # 测试资源
└── target/              # 编译输出目录
```

## pom.xml 基础

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>

    <!-- GAV: GroupId, ArtifactId, Version -->
    <groupId>com.example</groupId>
    <artifactId>my-app</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>

    <name>My Application</name>
    <description>A sample Maven project</description>

    <!-- 依赖 -->
    <dependencies>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <version>5.10.0</version>
            <scope>test</scope>
        </dependency>

        <dependency>
            <groupId>com.google.guava</groupId>
            <artifactId>guava</artifactId>
            <version>32.1.3-jre</version>
        </dependency>
    </dependencies>

    <!-- 构建配置 -->
    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.11.0</version>
                <configuration>
                    <source>25</source>
                    <target>25</target>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
```

## 依赖范围（scope）

| scope | 编译时可用 | 打包时包含 | 测试可用 |
|-------|-----------|-----------|---------|
| `compile` | ✓ | ✓ | ✓ |
| `provided` | ✓ | ✗ | ✓ |
| `runtime` | ✗ | ✓ | ✓ |
| `test` | ✗ | ✗ | ✓ |
| `import` | - | - | - |

```xml
<!-- servlet-api 在编译时需要，但部署容器已提供 -->
<dependency>
    <groupId>jakarta.servlet</groupId>
    <artifactId>jakarta.servlet-api</artifactId>
    <version>6.0.0</version>
    <scope>provided</scope>
</dependency>
```

## 常用命令

```bash
# 编译项目
mvn compile

# 运行测试
mvn test

# 打包（生成 jar）
mvn package

# 跳过测试打包
mvn package -DskipTests

# 清理并重新构建
mvn clean package

# 运行主类
mvn exec:java -Dexec.mainClass="com.example.Main"

# 查看依赖树
mvn dependency:tree

# 解决依赖冲突：查看哪些依赖引入了特定包
mvn dependency:tree -Dincludes=com.google.guava

# 跳过测试运行
mvn clean install -DskipTests

# 只构建指定模块（多模块项目）
mvn clean install -pl module-a -am
```

## 依赖版本管理

### 依赖仲裁（Conflict Resolution）

Maven 采用"最短路径"和"声明顺序"原则解决版本冲突：

```bash
# 查看依赖冲突
mvn dependency:tree -Dverbose
```

### 版本变量

```xml
<project>
    <properties>
        <java.version>17</java.version>
        <spring.version>6.1.0</spring.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.springframework</groupId>
            <artifactId>spring-core</artifactId>
            <version>${spring.version}</version>
        </dependency>
    </dependencies>
</project>
```

### 依赖排除

```xml
<dependency>
    <groupId>com.example</groupId>
    <artifactId>some-library</artifactId>
    <version>1.0.0</version>
    <exclusions>
        <exclusion>
            <groupId>org.unwanted</groupId>
            <artifactId>unwanted-artifact</artifactId>
        </exclusion>
    </exclusions>
</dependency>
```

## Maven 仓库

```bash
# 本地仓库位置
~/.m2/repository

# 配置阿里云镜像（加速国内下载）
# 编辑 ~/.m2/settings.xml
```

```xml
<mirrors>
    <mirror>
        <id>aliyun</id>
        <name>Aliyun Maven</name>
        <url>https://maven.aliyun.com/repository/public</url>
        <mirrorOf>central</mirrorOf>
    </mirror>
</mirrors>
```

## Spring Boot 的父 POM

Spring Boot 项目继承 `spring-boot-starter-parent`，获得：
- 默认 Java 版本（当前是 17）
- 资源编码配置
- 测试框架配置
- 依赖版本管理

```xml
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.4.0</version>
</parent>

<dependencies>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
</dependencies>
```

## 创建 Spring Boot 项目

```bash
# 使用官方模板创建
mvn archetype:generate \
    -DgroupId=com.example \
    -DartifactId=demo \
    -DarchetypeArtifactId=maven-archetype-quickstart \
    -DinteractiveMode=false

# 或者使用 Spring Initializr（推荐）
# 访问 https://start.spring.io/
```

## 多模块项目

```xml
<!-- 父 pom.xml -->
<project>
    <groupId>com.example</groupId>
    <artifactId>parent-project</artifactId>
    <version>1.0.0</version>
    <packaging>pom</packaging>

    <modules>
        <module>module-a</module>
        <module>module-b</module>
    </modules>

    <!-- 统一版本管理 -->
    <dependencyManagement>
        <dependencies>
            <dependency>
                <groupId>com.google.guava</groupId>
                <artifactId>guava</artifactId>
                <version>32.1.3-jre</version>
            </dependency>
        </dependencies>
    </dependencyManagement>
</project>
```

## 常用插件

### Maven Compiler Plugin

```xml
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-compiler-plugin</artifactId>
    <version>3.11.0</version>
    <configuration>
        <source>25</source>
        <target>25</target>
        <encoding>UTF-8</encoding>
    </configuration>
</plugin>
```

### Spring Boot Maven Plugin

```xml
<plugin>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-maven-plugin</artifactId>
</plugin>
```

## 构建生命周期

```
validate → compile → test → package → verify → install → deploy
```

| 阶段 | 说明 |
|------|------|
| `validate` | 验证项目结构是否正确 |
| `compile` | 编译源代码 |
| `test` | 运行单元测试 |
| `package` | 打包成 jar/war |
| `verify` | 运行集成测试 |
| `install` | 安装到本地仓库 |
| `deploy` | 部署到远程仓库 |
