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

GAV: GroupId, ArtifactId, Version。

## 依赖范围（scope）

| scope | 编译时可用 | 打包时包含 | 测试可用 |
|-------|-----------|-----------|---------|
| `compile` | ✓ | ✓ | ✓ |
| `provided` | ✓ | ✗ | ✓ |
| `runtime` | ✗ | ✓ | ✓ |
| `test` | ✗ | ✗ | ✓ |

## 依赖版本管理

Maven 采用"最短路径"和"声明顺序"原则解决版本冲突。

## Maven 仓库

本地仓库位置 `~/.m2/repository`。

## Spring Boot 的父 POM

Spring Boot 项目继承 `spring-boot-starter-parent`，获得统一版本管理。

## 多模块项目

父 pom.xml 使用 `<modules>` 声明子模块，`<dependencyManagement>` 统一版本管理。

## 常用插件

### Maven Compiler Plugin

### Spring Boot Maven Plugin

## 构建生命周期

```
validate → compile → test → package → verify → install → deploy
```

## 参考样例

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.example</groupId>
    <artifactId>my-app</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>

    <dependencies>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <version>5.10.0</version>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.11.0</version>
                <configuration>
                    <source>21</source>
                    <target>21</target>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
```

```bash
# 常用命令
mvn compile           # 编译项目
mvn test              # 运行测试
mvn package           # 打包
mvn clean package     # 清理并重新构建
mvn dependency:tree    # 查看依赖树
mvn clean install -DskipTests  # 跳过测试安装
```

```xml
<!-- 依赖排除 -->
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

```xml
<!-- Spring Boot 父 POM -->
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

```xml
<!-- 多模块项目父 POM -->
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
        <name>Aliyun Maven</name>
        <url>https://maven.aliyun.com/repository/public</url>
        <mirrorOf>central</mirrorOf>
    </mirror>
</mirrors>
```
