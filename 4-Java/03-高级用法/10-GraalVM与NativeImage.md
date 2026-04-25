# GraalVM与Native Image

> GraalVM Native Image的本质是AOT编译（提前编译）——在构建时将Java应用编译为本地机器码的可执行文件，省去JVM启动和JIT编译的运行时开销，从而实现毫秒级启动和极低内存占用。

## 核心优势

| 特性 | JVM | Native Image |
|------|-----|--------------|
| 启动时间 | 1-10秒 | <100毫秒 |
| 内存占用 | 100-500MB | 10-50MB |
| 预热时间 | 需要 | 无需 |
| 编译方式 | JIT编译 | AOT编译 |

<pre>
JVM启动流程:
  JVM启动 → 类加载 → 字节码解释 → JIT编译热点代码 → 全速运行
              ↑
          这段延迟 Native Image 完全消除

Native Image启动流程:
  直接执行机器码 → 全速运行
</pre>

## 安装配置

```bash
curl -sL https://github.com/graalvm/graalvm-ce-builds/releases/download/vm-22.3.2/graalvm-ce-java17-linux-amd64-22.3.2.tar.gz | tar xz
export GRAALVM_HOME=/path/to/graalvm-ce-java17-22.3.2
export PATH=$GRAALVM_HOME/bin:$PATH
gu install native-image
```

## 构建过程

**Native Image构建分为分析阶段和编译阶段——分析阶段通过静态和动态分析遍历所有可达代码，编译阶段生成机器码。**

<pre>
构建命令 ──> 分析（agent追踪反射/资源/类加载）
    │
    ├── 生成 reflection-config.json
    ├── 生成 resource-config.json
    └── 生成 proxy-config.json
    │
    └──> AOT编译生成可执行文件
</pre>

### Spring Boot + Native Image

```xml
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.4.0</version>
</parent>
<artifactId>native-demo</artifactId>
```

```xml
<plugin>
    <groupId>org.graalvm.buildtools</groupId>
    <artifactId>native-maven-plugin</artifactId>
    <version>0.9.24</version>
    <configuration>
        <imageName>native-demo</imageName>
        <buildArgs>--no-fallback</buildArgs>
    </configuration>
</plugin>
```

```bash
./mvnw -Pnative package
./target/native-demo
```

## 配置文件

### native-image.properties

```properties
Args=--verbose \
     --initialize-at-build-time=org.slf4j.LoggerFactory \
     --initialize-at-build-time=ch.qos.logback \
     --no-fallback
```

### 反射配置

```json
[
  {
    "name": "com.example.model.User",
    "allDeclaredConstructors": true,
    "allDeclaredMethods": true,
    "fields": [
      { "name": "id", "type": "long" },
      { "name": "name", "type": "java.lang.String" }
    ]
  }
]
```

### 资源文件配置

```json
{
  "resources": {
    "includes": [
      { "pattern": ".*\\.properties$" },
      { "pattern": ".*\\.xml$" }
    ]
  }
}
```

## 动态类加载

**Native Image在构建时需要预知所有运行的代码。Class.forName()等动态加载场景需要预注册。**

```java
public Object loadPlugin(String className) {
    Class<?> clazz = Class.forName(className);
    return clazz.getDeclaredConstructor().newInstance();
}
```

## 常用构建选项

| 选项 | 说明 |
|------|------|
| --no-fallback | 不使用fallback解释器 |
| -O<level> | 优化级别(1-4) |
| --initialize-at-build-time | 构建时初始化类 |
| -H:+ReportExceptionStackTraces | 报告异常堆栈 |

## 性能对比

$$
\text{启动时间提升} \approx \frac{\text{JVM启动时间}}{\text{Native启动时间}} \approx 10-100\text{x}
$$

| 指标 | JVM | Native Image |
|------|-----|--------------|
| 启动时间 | 2.5s | 85ms |
| 内存占用 | 256MB | 32MB |
| 首次响应 | 800ms | 12ms |

## 容器集成

### Dockerfile

```dockerfile
FROM ghcr.io/graalvm/native-image:ol9-java17 as builder
WORKDIR /app
COPY mvnw pom.xml ./
RUN ./mvnw dependency:go-offline
COPY src src
RUN ./mvnw -Pnative package -DskipTests
FROM ghcr.io/graalvm/native-image:ol9-java17
WORKDIR /app
COPY --from=builder /app/target/native-demo /app/native-demo
ENTRYPOINT ["/app/native-demo"]
```

### Kubernetes资源建议

```yaml
resources:
  requests:
    memory: "32Mi"
    cpu: "100m"
  limits:
    memory: "128Mi"
    cpu: "500m"
```

## 迁移检查清单

1. 先在JVM模式确保测试通过
2. 使用Native Image Agent追踪反射/资源
3. 注册所需反射配置
4. 迭代构建，使用--verbose定位问题
5. 性能调优

## GraalVM检测

```java
String version = System.getProperty("java.vm.version");
if (version.contains("GraalVM")) {
    System.out.println("Running on GraalVM");
}
```
