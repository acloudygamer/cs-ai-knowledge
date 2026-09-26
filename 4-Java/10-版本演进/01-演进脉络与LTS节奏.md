# 演进脉络与 LTS 节奏

> 前置：[01-Java全景](../00-概览/01-Java全景.md) · 后续：[02-Java21](./02-Java21.md)

> **版本基准**：Java 21 stable / Java 25 latest（均为 LTS）。本篇事实口径：JEP 号与归属版本均以 OpenJDK JEP 索引（openjdk.org/jeps/0）为准。

Java 的版本演进是一台**发布列车**（release train）：车次按日历发车，特性造好才上车，没造好等下一班。本篇交代这台列车的三个机构——发车节奏、特性的三级上车闸口（孵化/预览/转正）、以及上游 OpenJDK 与各厂商发行版的供应链关系——然后沿 8→11→17 的 LTS 主线清点特性，为后续两篇（[02-Java21](./02-Java21.md)、[03-Java22至25](./03-Java22至25.md)）建立坐标系。

## 发布列车模型

### 节奏：从"憋大招"到半年一版

1996–2017 年，Java 按特性完备度发版，间隔不可预期：Java 7 等了 5 年（2006→2011），Java 9 因模块系统（Jigsaw）两度跳票（2015→2016→2017-09）。延期一次，全平台的特性交付都被绑架。

2017-09 Java 9 发布后，Oracle 宣布改为**时间驱动**：每年 3 月、9 月各发一个特性版本，版本号随之为时间基（JEP 322，Java 10 起生效，2018-03）。列车化把"特性延期"的代价从"全版延期"降为"该特性等半年后的下一班"——这是预览机制存在的前提：特性可以先上半成品车厢。

### LTS：从三年一版到两年一版

**LTS**（Long-Term Support，长期支持版）不是技术版本而是商业承诺：厂商对该版本提供多年安全与缺陷修复更新，非 LTS 版本的支持在下个版本发布即终止。LTS 最初三年一版（8→11→17）；2021-09 随 Java 17 发布，Oracle 宣布改为**两年一版**（17→21→25），理由是半年列车让特性成熟速度足够支撑更密的 LTS。

| 版本 | 发布 | 类别 | 标志性特性（详见下文主线） |
|---|---|---|---|
| Java 8 | 2014-03 | LTS | Lambda（JEP 126）、Stream API（JEP 107） |
| Java 9 | 2017-09 | — | 模块系统（JEP 261） |
| Java 11 | 2018-09 | LTS | HttpClient（JEP 321）、单文件源码运行（JEP 330） |
| Java 17 | 2021-09 | LTS | 密封类转正（JEP 409）、Security Manager 弃用（JEP 411） |
| Java 21 | 2023-09 | LTS | 虚拟线程转正（JEP 444） |
| Java 25 | 2025-09 | LTS | 简化 main 转正（JEP 512）、Scoped Values 转正（JEP 506） |

非 LTS 版本（12–16、18–20、22–24）是通往下一个 LTS 的试验田：生产上几乎没人部署，但每个转正特性都在它们身上预览过。

## 特性的三级闸口：孵化、预览、转正

列车要跑得快，又不能让半成品炸掉生产代码，OpenJDK 给特性设了两道隔离闸口，均为 JEP 流程内的正式身份：

- **孵化**（incubator）：API 形态未定，放在 `jdk.incubator.*` 包下，明确不承诺兼容。典型是 Vector API——从 Java 16（JEP 338）孵化到 Java 26 仍是第十一次孵化（JEP 529），等 Valhalla 的值类型落地才敢转正。
- **预览**（preview）：语言/JVM 特性已基本定型，收最后一轮反馈。编译运行必须显式加 `--enable-preview`，且预览 class 文件的版本号绑定当次 JDK——换版本必须重编译，从机制上阻止预览特性流入生产依赖。
- **转正**（permanent）：进入 JLS/JVMS/SE API，承诺向后兼容。

预览不是走形式，真会改、真会死：

- record：Java 14 预览（JEP 359）→ 15 二次预览（JEP 384）→ 16 转正（JEP 395）。
- switch 表达式：Java 12 预览（JEP 325）→ 13 二次预览并引入 `yield`（JEP 354）→ 14 转正（JEP 361）。
- String Templates：Java 21 预览（JEP 430）→ 22 二次预览（JEP 459）→ 因模板注入的安全设计缺陷无法收敛，Java 23 起**撤回**——预览机制最成功的案例恰恰是这次撤回。

## OpenJDK 与发行版供应链

**OpenJDK** 是 Java SE 的上游开源项目（GPLv2 + Classpath 例外）：语言、HotSpot、类库的源码与参考实现都在这里，JEP 在这里立项。它发布的是源码和参考构建，不是面向企业的产品。

各厂商从 OpenJDK 源码构建自己的**发行版**，通过 TCK（兼容性测试套件）认证后都可称"Java SE 兼容"：

| 发行版 | 提供方 | 定位 |
|---|---|---|
| Eclipse Temurin | Adoptium 工作组 | 社区主流免费发行版，本库实测环境 |
| Amazon Corretto | Amazon | 免费、AWS 场景长期支持 |
| Oracle JDK | Oracle | 商业发行版，含 Oracle 专属支持服务 |

三家跑同一份字节码，差异在构建选项、支持年限与许可。许可的变迁本身就是一条约束链：Java 8 及以前 Oracle JDK 用 BCL 许可（开发免费、部分商用场景付费）；Java 11–16 改为 OTN 许可（生产使用须订阅付费），直接催生了 Temurin/Corretto 的用户迁移潮；Java 17 起改为 NFTC（No-Fee Terms and Conditions）——免费含商用，但免费更新只到"下一个 LTS 发布后一年"为止（如 Oracle JDK 21 的免费更新止于 2024-09 后一年），长期停留仍需订阅或转向开源发行版。

## LTS 主线：8 → 11 → 17

三个 LTS 各奠定一层后续演进的基石。

### Java 8（2014-03）：函数式入场

- **Lambda 表达式**（JEP 126）与 **Stream API**（JEP 107）：行为参数化与集合批量操作，依赖接口默认方法（同为 JEP 126 一部分）才能给既有接口加 `stream()` 而不破坏兼容。
- Date & Time API（JEP 150）：`java.time` 取代可变的 `Date`/`Calendar`。
- 删除永久代（JEP 122）：类元数据移入本地内存的 Metaspace。

### Java 9（2017-09）：模块化

- **模块系统**（JEP 261，Jigsaw 项目）：JDK 自身被切成 `java.base` 等模块（JEP 200），`module-info.java` 声明依赖与导出，强封装内部 API（JEP 260）。配套 jlink（JEP 282，定制运行时镜像）与 jshell（JEP 222）。
- 集合工厂方法 `List.of(...)`（JEP 269）、Compact Strings（JEP 254，拉丁字符串内部存储从 char[] 改 byte[]）、G1 成为默认 GC（JEP 248）。
- 代价：模块路径与类路径并存的过渡期，是 8→11 升级的主要摩擦源。

### Java 10–11（2018-03 / 2018-09 LTS）：列车头两班

- Java 10：`var` 局部变量类型推断（JEP 286）——编译期推断，不改变静态类型本质。
- Java 11：HttpClient 转正（JEP 321，自 Java 9 以 JEP 110 孵化）；单文件源码直接 `java Hello.java` 运行（JEP 330）；`var` 可用于 Lambda 参数（JEP 323）；ZGC 实验性登场（JEP 333）；删除 Java EE 与 CORBA 模块（JEP 320）——这些在 Java 9 已弃用，列车节奏让"弃用→删除"周期制度化。

### Java 12–17（2021-09 LTS）：模式匹配的铺垫期

这五个版本的主线是**类型系统替程序员干活**，全部走预览闸口：

- switch 表达式转正（Java 14，JEP 361），switch 从语句变为有值的表达式，为穷尽性检查铺路。
- instanceof 模式匹配转正（Java 16，JEP 394）：类型检查、转换、绑定三步合一。
- record 转正（Java 16，JEP 395）：不可变数据载体，编译器合成 `equals`/`hashCode`/`toString`。
- 文本块转正（Java 15，JEP 378）：多行字符串字面量。
- Java 17 收口：**密封类转正**（JEP 409）——`permits` 声明有限子类集，编译器可对 switch 做穷尽性证明。record + sealed + switch 表达式三件齐备，后续 Java 21 的 record patterns 与 switch 模式匹配只是把它们接起来（见 [02-Java21](./02-Java21.md)）。
- 平台侧：强封装 JDK 内部 API（JEP 403，`sun.misc.Unsafe` 等默认不可反射访问）、Security Manager 弃用待删（JEP 411）、macOS/AArch64 移植（JEP 391）。

至此坐标系建立：19→21 的虚拟线程线、14→17 的模式匹配线在 Java 21 汇合（[02-Java21](./02-Java21.md)），22→25 是这两条线的收尾与新线开启（[03-Java22至25](./03-Java22至25.md)）。

---

> 前置：[01-Java全景](../00-概览/01-Java全景.md) · 后续：[02-Java21](./02-Java21.md)——LTS 主线的第一个汇合点
