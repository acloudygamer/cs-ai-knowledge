# Java 简介

## 诞生背景

1995年，由 Sun Microsystems 的 **James Gosling** 领导的团队正式发布了 Java 语言。最初的设计目标是解决消费性电子产品（如微波炉、遥控器等小型设备）的软件跨平台运行问题。

## 发展历程

| 年份 | 里程碑 |
|------|--------|
| 1991 | James Gosling 启动 "Green Project" |
| 1995 | Java 1.0 正式发布，提出 "Write Once, Run Anywhere" |
| 2006 | Sun 开源 Java（OpenJDK） |
| 2010 | Oracle 收购 Sun，Java 进入 Oracle 时代 |
| 2017 | Java 9 开启每6个月发布一个新版本的节奏 |
| 2021 | Java 17 LTS 发布，现代特性集大成 |
| 2023 | Java 21 LTS 发布，虚拟线程正式加入 |
| 2025 | Java 25 发布，Instance Main Methods 和模块导入简化 |

## 核心理念：Write Once, Run Anywhere

Java 之所以能 "一次编写，到处运行"，得益于 **JVM（Java Virtual Machine，Java 虚拟机）**：

1. **源代码（.java）**：程序员编写的 Java 代码
2. **字节码（.class）**：编译器将源代码编译成的中间代码
3. **JVM**：在各种操作系统上运行字节码的"软件计算机"

只要为目标平台安装 JVM，同样的 `.class` 文件就能在 Windows、macOS、Linux 上运行，无需重新编译。

## Java 的优缺点

### 优点

1. **跨平台能力**: JVM 是跨平台的，真正实现 "一次编写，到处运行"。

2. **面向对象**: 纯面向对象的编程语言（除基本类型外），设计良好。

3. **自动内存管理**: 垃圾回收机制（Garbage Collection）自动管理内存，减少内存泄漏。

4. **丰富的生态系统**:
   - Spring 生态系统（Spring Boot、Spring Cloud）
   - 企业级应用框架（Hibernate、MyBatis）
   - Android 开发
   - 大数据处理（Hadoop、Spark）

5. **强大的安全机制**: 字节码验证、沙箱安全模型。

6. **多线程支持**: 内置多线程支持，Thread 类和 Runnable 接口。

7. **丰富的标准库**: JDK 提供了大量实用的类库。

### 缺点

1. **语法较冗长**: 相比 Python、Ruby 等语言，Java 代码较为繁琐。

2. **学习曲线**: 对于初学者来说，概念较多（类、对象、继承、接口、泛型等）。

3. **性能一般**: 虽然比脚本语言快，但不如 C/C++。

4. **GUI 开发不便**: 桌面 GUI 开发不如 Electron 等框架方便。

## 与其他语言的对比

| 特性 | Java | Python | JavaScript | C++ |
|------|------|--------|------------|-----|
| 类型系统 | 静态类型 | 动态类型 | 动态类型 | 静态类型 |
| 执行方式 | 编译为字节码 | 解释执行 | 解释执行 | 编译为机器码 |
| 主要应用 | 企业/Android/大数据 | AI/数据科学/脚本 | Web前端/全栈 | 系统/游戏开发 |
| 学习曲线 | 中等 | 低 | 低 | 高 |
| 运行速度 | 中等 | 慢 | 慢 | 快 |
| 内存管理 | GC自动回收 | GC自动回收 | GC自动回收 | 手动管理 |
| 多继承 | 不支持（接口替代） | 不支持 | 不支持 | 支持 |
| 全局变量 | 不支持 | 支持 | 支持 | 支持 |
| 指针 | 不支持 | 支持 | 支持 | 支持 |

## 著名项目和应用

使用 Java 开发的一些著名项目：

- **Android 应用**: 虽然 Kotlin 现在是首选，但大部分 Android 应用仍是 Java
- **Hadoop**: 大数据处理框架
- **Spark**: 大数据计算引擎
- **Elasticsearch**: 搜索引擎
- **Kafka**: 消息队列系统
- **Minecraft**: Minecraft Java 版
- **IntelliJ IDEA**: JetBrains 出品的 Java IDE
- **Spring 框架**: 改变 Java 开发方式的框架

## Java 开发工具

### IDE

- **IntelliJ IDEA**: 最流行的 Java IDE，功能强大，智能提示优秀
- **Eclipse**: 开源免费，适合大型企业项目
- **VS Code + Extension Pack for Java**: 轻量级选择

### 构建工具

- **Maven**: 使用 pom.xml 配置，依赖管理成熟稳定
- **Gradle**: 使用 build.gradle，更灵活，性能更好

### 相关技术栈

```
后端: Java → Spring Boot → Spring Cloud
数据库: MySQL / PostgreSQL / Oracle
缓存: Redis / Memcached
消息队列: Kafka / RabbitMQ
容器: Docker / Kubernetes
CI/CD: Jenkins / GitLab CI
```

## 应用场景

### 1. 企业级应用开发

Java 是企业软件的事实标准，尤其在大型系统中：

- **Spring 全家桶**：Spring Boot、Spring Cloud、Spring Security
- **企业级应用服务器**：Tomcat、Jetty、JBoss、WebLogic
- **银行、证券、保险**等金融系统核心系统

典型特征：高并发、大数据量、强一致性要求

### 2. Android 应用开发

虽然 Android 官方推荐的开发语言是 Kotlin，但 Java 一直是 Android 开发的主要语言：

- Android SDK 大量 API 使用 Java 编写
- 许多大型 Android 应用（如淘宝、微信早期版本）使用 Java
- 现有 Android 代码库中有大量 Java 代码

> 目前 Google 官方同时支持 Java 和 Kotlin，Kotlin 语法更简洁，但学会 Java 能更好地理解 Android 底层。

### 3. Web 后端服务

Java 在 Web 后端领域地位稳固：

- **电商平台**：天猫、京东后端大量使用 Java
- **SaaS 服务**：各种在线办公、管理系统
- **RESTful API**：Spring Boot 让创建微服务变得极为简单

### 4. 大数据技术栈

大数据领域的核心框架多以 Java 为基础：

| 框架 | 用途 | 语言基础 |
|------|------|----------|
| Hadoop | 分布式存储与计算 | Java |
| Spark | 大数据计算引擎 | Scala（JVM 之上） |
| Flink | 流处理引擎 | Java |
| Kafka | 消息队列 | Java |

### 5. 微服务架构

Java 是微服务架构的热门选择：

- **Spring Boot**：简化微服务创建，打包成 JAR 即可运行
- **Spring Cloud**：完整的微服务解决方案（配置中心、负载均衡、服务熔断等）
- **Quarkus**：新一代 Kubernetes 原生 Java 框架，更轻量、启动更快

### 适用场景总结

| 场景 | Java 适合度 | 原因 |
|------|-------------|------|
| 企业后台 | ★★★★★ | 成熟框架、丰富生态、稳定可靠 |
| Android 开发 | ★★★★☆ | 主流选择之一，但 Kotlin 正在崛起 |
| Web 全栈 | ★★★★☆ | Spring Boot 大幅提升开发效率 |
| 大数据 | ★★★★★ | Hadoop 生态核心语言 |
| 嵌入式/移动端 | ★★☆☆☆ | 资源受限场景略显笨重 |
| 快速脚本 | ★★☆☆☆ | 不如 Python 轻便 |

## 你好，世界！

让我们编写并运行第一个 Java 程序。

### 完整代码

```java
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("你好，世界！");
    }
}
```

### 逐行解释

#### `public class HelloWorld`

- `class` 是 Java 的核心概念——**类**是面向对象的基本构件
- `public` 表示这个类是公开的，可以被其他类访问
- 类名 `HelloWorld` 必须与文件名**完全一致**（Java 大小写敏感）
- 源文件名必须是 `HelloWorld.java`

#### `public static void main(String[] args)`

这是 Java 程序的**入口方法**。程序启动时，JVM 会首先调用这个方法。

| 关键字 | 含义 |
|--------|------|
| `public` | 公开的，任何地方都可以调用 |
| `static` | 静态方法，属于类而非对象，无需创建实例就能运行 |
| `void` | 返回类型为空，方法执行完毕后不返回任何值 |
| `main` | 方法名，JVM 约定的入口方法名 |
| `String[] args` | 命令行参数数组 |

#### `System.out.println("你好，世界！");`

- `System` — Java 标准库提供的系统类
- `out` — 标准输出流（通常是屏幕）
- `println` — 打印一行内容，并自动换行

### 运行程序

#### 步骤一：编写源代码

将代码保存为 `HelloWorld.java`（注意文件名大小写）。

#### 步骤二：编译

```bash
javac HelloWorld.java
```

编译后会生成 `HelloWorld.class` 文件（字节码）。

#### 步骤三：运行

```bash
java HelloWorld
```

你会看到输出：

```
你好，世界！
```

### 新手常见错误

| 错误 | 原因 | 解决方法 |
|------|------|----------|
| `Error: Could not find or load main class` | 类名与文件名不一致 | 确保文件名为 `HelloWorld.java`，类名为 `HelloWorld` |
| `'javac' is not recognized...` | PATH 未配置好 | 参考 [安装与环境](../01-基础/01-安装与环境.md) 配置环境变量 |
| 大小写错误 | Java 区分大小写 | `system.out.println` 是不对的，必须是 `System.out.println` |

### 进阶练习

尝试修改代码，实现以下输出：

```
你好，世界！
Java 版本：21
```

提示：`System.out.println` 可以打印任意字符串，字符串可以拼接（用 `+` 符号）。