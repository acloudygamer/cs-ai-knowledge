# 模块系统（JPMS）

> 前置：[Gradle](./02-Gradle.md) · 后续：[测试理论](../07-测试与质量/01-测试理论.md)

> **版本基准**：JPMS 自 Java 9（2017）引入，本篇示例实测环境为 Temurin JDK 25.0.4.1（Windows），编译命令 `javac -encoding UTF-8 --release 21`。全部命令行示例均已实测。

JPMS（Java Platform Module System，Java 平台模块系统）是给 JVM 增加的一层**模块级封装与依赖声明**：每个模块用一份 `module-info.java` 声明自己叫什么、依赖谁、导出哪些包，编译器和运行时据此检查访问合法性。它回应的约束是 classpath 的扁平结构：classpath 把所有 JAR 的所有包倒进同一个命名空间，public 即全局可见，依赖关系只在运行到 `NoClassDefFoundError` 那一刻才暴露。模块系统把"哪些包是 API、哪些是实现"从约定升格为编译期与运行期双重强制的边界。

## module-info：模块的接口声明

一个最小模块（本节全部命令实测于 Temurin 25.0.4.1）：

```java
// src/com.example.lib/module-info.java
module com.example.lib {
    exports com.example.lib.api;   // 只有这个包对外可见
}
```

指令全集按职责分四组：

| 指令 | 作用 | 连接的下游 |
|---|---|---|
| `requires M` | 依赖模块 M（可读其导出包） | 编译期与启动期校验 M 必须存在 |
| `requires transitive M` | 依赖 M 并转授可读性 | 依赖我的模块自动可读 M——用于"我的公开 API 签名里出现了 M 的类型" |
| `requires static M` | 编译期需要 M，运行期可选 | 注解处理、可选集成 |
| `exports p` / `exports p to M` | 开放包 p 的编译期与运行期访问 | 限定 `to` 时仅指定模块可见 |
| `opens p` / `opens p to M` | 开放包 p 的运行时**深反射** | Spring/Hibernate 等框架反射私有字段所需 |
| `uses I` / `provides I with C` | 服务消费/提供声明 | `ServiceLoader` 在模块图上发现实现 |

`exports` 与 `opens` 的分界是编译期访问与运行期反射的分界：`exports` 开放的包可以被正常 import 和调用，但私有成员的反射访问仍需 `opens`。

## 实测：编译、运行与强封装

两模块项目：`com.example.lib` 导出 `api` 包（接口 `Greeting` 与工厂 `Greetings`），实现类 `DefaultGreeting` 放在未导出的 `internal` 包；`com.example.app` 依赖 lib 并调用工厂。

```bash
# 编译（--module-source-path 让 javac 按模块组织源码树）
javac -encoding UTF-8 --release 21 --module-source-path src -d out $(find src -name '*.java')

# 运行（模块路径取代 classpath，-m 指定 模块/主类）
java --module-path out -m com.example.app/com.example.app.Main
# 输出：hello, jpms
```

**强封装的实测证据**：让 app 模块 `import com.example.lib.internal.DefaultGreeting`，编译直接失败：

```text
错误: 程序包 com.example.lib.internal 不可见
  (该程序包已在模块 com.example.lib 中声明, 但该模块未导出它)
```

对比 classpath 世界：只要类是 public，`internal` 包名只是君子协定；模块世界里它是编译器强制。运行时反射越界同样被拦——`setAccessible` 访问未 `opens` 包的私有成员会抛 `InaccessibleObjectException`。JDK 自身是这套机制的最大用户：`jdk.internal.*`、`sun.misc.Unsafe` 等内部 API 正是靠模块封装在 Java 9 之后关上了门。

**拆包（split package）约束**：同一个包不允许出现在两个模块中。模块图解析时发现两个模块含同名包即报错——这是"一个包一个归属"的强制，也是老代码迁移时最常见的撞墙点（典型：一个包被切成 api/impl 两个 JAR 的历史项目）。

## 实测：jlink 定制运行时

模块图的确定性带来一个 classpath 给不了的能力：既然每个模块声明了全部依赖，就能算出运行一个应用所需的最小 JDK 子集。`jdeps` 先分析，jlink 再裁剪：

```bash
# 打成模块化 JAR
jar --create --file mods/com.example.lib.jar -C out/com.example.lib .
jar --create --file mods/com.example.app.jar --main-class com.example.app.Main -C out/com.example.app .

# jdeps 分析模块依赖（实测输出）
jdeps --module-path mods -s -m com.example.app
# com.example.app -> com.example.lib
# com.example.app -> java.base

# jlink 定制运行时镜像（--launcher 生成启动脚本 app）
jlink --module-path mods;$JAVA_HOME/jmods --add-modules com.example.app \
      --launcher app=com.example.app --output img \
      --strip-debug --no-man-pages --no-header-files
./img/bin/app   # 输出：hello, jpms
```

实测体积账（Temurin 25.0.4.1，Windows）：完整 JDK 291 MB，只含 `java.base` 加两个应用模块的定制镜像 **45 MB**。本例应用只用 `java.base`；需要 `java.sql`、`java.net.http` 等模块时按需 `--add-modules` 追加，体积随模块数增长。45 MB 里不含 `jmods`、不包含 javac——镜像是纯运行时，这正对容器部署场景（与 [11-GraalVM与云原生](../08-生态与框架/11-GraalVM与云原生.md) 的 AOT 路线是同一约束的两种解法）。

## 迁移路径：unnamed module 与 automatic module

JPMS 设计了兼容层，让未模块化的存量 JAR 与模块化代码共存：

- **无名模块（unnamed module）**：classpath 上的一切归入一个无名模块，它可读所有模块、导出全部包——classpath 行为原样保留，老应用不改一行也能跑在 JDK 9+ 上。
- **自动模块（automatic module）**：把普通 JAR 放上**模块路径**，它自动成为模块：导出全部包、可读所有其他模块，模块名从文件名推导（或由 JAR 清单的 `Automatic-Module-Name` 指定）。实测：

```bash
jar --file plain-old-lib-1.0.jar --describe-module
# plain.old.lib@1.0 automatic      ← 文件名 plain-old-lib-1.0.jar 推导出模块名
# requires java.base mandated
# contains plainlib
```

文件名推导的名字不稳定（改名即断依赖），库作者的正确做法是先在清单里钉 `Automatic-Module-Name` 再发布。迁移的标准顺序是**自下而上**：用 `jdeps` 分析依赖图 → 叶子库先模块化（加 module-info）→ 上层应用最后迁移；拆包冲突在这一过程中逐一消除。

## 版图与边界

版图之内：JDK 自身的模块化（9 起 JDK 被切成约 70 个模块，`java --list-modules` 可见）、jlink 运行时裁剪、库作者的强封装。版图之外是现实：**应用侧采用率始终不高**——多数业务应用的全部价值在 classpath 上也能拿到，模块化的收益（封装、裁剪）抵不过迁移成本（拆包、反射框架的 opens 配置、生态依赖未模块化），Spring Boot 应用的主流交付形态仍是 classpath 上的 fat JAR。这是历史路径依赖，不是设计失败：JPMS 钉死了 JDK 内部封装与 jlink 这两个确定性收益，应用侧留作可选项。

---

> 前置：[Gradle](./02-Gradle.md) · 后续：[测试理论](../07-测试与质量/01-测试理论.md)——构建期之后是验证期
