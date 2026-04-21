# GraalVM 与 Native Image

## 概述

GraalVM 是 Oracle 开发的高性能运行时，支持 Java、Kotlin 等语言编译为原生可执行文件，显著提升启动速度和内存效率。

### 核心优势

| 特性 | JVM | Native Image |
|------|-----|--------------|
| 启动时间 | 1-10 秒 | <100 毫秒 |
| 内存占用 | 100-500 MB | 10-50 MB |
| 预热时间 | 需要 | 无需 |
| 即时编译 | 需要 | AOT 编译 |

## 安装配置

### 下载安装

```bash
# 下载 GraalVM (JDK 17)
curl -sL https://github.com/graalvm/graalvm-ce-builds/releases/download/vm-22.3.2/graalvm-ce-java17-linux-amd64-22.3.2.tar.gz | tar xz

# 设置环境变量
export GRAALVM_HOME=/path/to/graalvm-ce-java17-22.3.2
export PATH=$GRAALVM_HOME/bin:$PATH

# 验证安装
java -version
native-image --version
```

### 安装 Native Image 组件

```bash
# 使用 gu 安装 native-image
gu install native-image

# 更新到最新版本
gu update native-image
```

## Spring Boot 3 + Native Image

### 项目配置

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.4.0</version>
    </parent>

    <groupId>com.example</groupId>
    <artifactId>native-demo</artifactId>
    <version>1.0.0</version>

    <properties>
        <java.version>21</java.version>
        <native.maven.plugin.version>0.9.24</native.maven.plugin.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        <dependency>
            <groupId>com.h2database</groupId>
            <artifactId>h2</artifactId>
            <scope>runtime</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
            <plugin>
                <groupId>org.graalvm.buildtools</groupId>
                <artifactId>native-maven-plugin</artifactId>
                <version>${native.maven.plugin.version}</version>
                <executions>
                    <execution>
                        <id>build-native</id>
                        <goals>
                            <goal>compile-no-fork</goal>
                        </goals>
                        <phase>package</phase>
                    </execution>
                    <execution>
                        <id>test-native</id>
                        <goals>
                            <goal>test-no-fork</goal>
                        </goals>
                        <phase>test</phase>
                    </execution>
                </executions>
                <configuration>
                    <imageName>native-demo</imageName>
                    <buildArgs>
                        --no-fallback
                    </buildArgs>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
```

### application.yml

```yaml
spring:
  application:
    name: native-demo
  datasource:
    url: jdbc:h2:mem:testdb
    driver-class-name: org.h2.Driver
  jpa:
    hibernate:
      ddl-auto: create-drop

management:
  endpoints:
    web:
      exposure:
        include: health,info

logging:
  level:
    root: INFO
```

## 快速启动示例

### 简单 REST 控制器

```java
package com.example.nativedemo;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.*;

@SpringBootApplication
@RestController
@RequestMapping("/api")
public class NativeDemoApplication {

    public static void main(String[] args) {
        SpringApplication.run(NativeDemoApplication.class, args);
    }

    @GetMapping("/hello")
    public String hello(@RequestParam(defaultValue = "World") String name) {
        return "Hello, " + name + "!";
    }

    @GetMapping("/health")
    public HealthStatus health() {
        return new HealthStatus("UP", System.currentTimeMillis());
    }

    record HealthStatus(String status, long timestamp) {}
}
```

### 构建原生镜像

```bash
# Maven 构建
./mvnw -Pnative package

# 或使用 Gradle
./gradlew nativeCompile

# 直接运行
./target/native-demo
```

## GraalVM 配置详解

### native-image.properties

```properties
# src/main/resources/META-INF/native-image/native-image.properties
Args=--verbose \
     --initialize-at-build-time=org.slf4j.LoggerFactory \
     --initialize-at-build-time=ch.qos.logback \
     --initialize-at-build-time=org.hibernate \
     --no-fallback \
     --install-exit-handlers \
     -H:+ReportExceptionStackTraces \
     -H:+AddAllCharsets \
     -H:EnableURLProtocols=http,https
```

### 资源文件配置

```properties
# META-INF/native-image/resource-config.json
{
  "resources": {
    "includes": [
      {
        "pattern": ".*\\.properties$"
      },
      {
        "pattern": ".*\\.xml$"
      },
      {
        "pattern": ".*\\.yml$"
      },
      {
        "pattern": "org/springframework/boot/logback/.*"
      }
    ],
    "excludes": [
      {
        "pattern": ".*/test/.*"
      }
    ]
  }
}
```

### 反射配置

```json
// META-INF/native-image/reflection-config.json
[
  {
    "name": "com.example.nativedemo.model.User",
    "allDeclaredConstructors": true,
    "allDeclaredMethods": true,
    "allDeclaredFields": true,
    "fields": [
      {
        "name": "id",
        "type": "long"
      },
      {
        "name": "name",
        "type": "java.lang.String"
      }
    ]
  },
  {
    "name": "java.time.LocalDateTime",
    "methods": [
      {
        "name": "now",
        "parameterTypes": []
      }
    ]
  }
]
```

### 动态代理配置

```json
// META-INF/native-image/proxy-config.json
[
  [
    "java.lang.reflect.InvocationHandler",
    "org.springframework.http.client.ClientHttpRequestFactory"
  ]
]
```

## 动态类加载处理

### 示例：Class.forName

```java
@Service
public class PluginService {

    public Object loadPlugin(String className) {
        try {
            // GraalVM 需要预知要加载的类
            Class<?> clazz = Class.forName(className);
            return clazz.getDeclaredConstructor().newInstance();
        } catch (ClassNotFoundException e) {
            throw new PluginLoadException("Plugin not found: " + className, e);
        }
    }

    // 预注册可能加载的类
    private static final Set<String> KNOWN_PLUGINS = Set.of(
        "com.example.plugins.EmailPlugin",
        "com.example.plugins.SmsPlugin",
        "com.example.plugins.PaymentPlugin"
    );
}
```

### ConditionalOnClass 处理

```java
@Configuration
@ConditionalOnClass(value = com.fasterxml.jackson.databind.ObjectMapper.class)
public class JacksonAutoConfiguration {
    // 只有当 Jackson 在类路径中时才加载
}
```

## Native Image 构建选项

### 常用选项

| 选项 | 说明 |
|------|------|
| `--no-fallback` | 不使用 fallback 解释器 |
| `-O<level>` | 优化级别 (1-4) |
| `-H:+ReportExceptionStackTraces` | 报告异常堆栈 |
| `-H:+AddAllCharsets` | 添加所有字符集 |
| `-H:Path` | 输出路径 |
| `--initialize-at-build-time` | 构建时初始化类 |

### 镜像分析

```bash
# 生成构建报告
native-image --features=NativeImageAgent \
             -H:+DashboardAll \
             -H:DashboardPath=build/dashboard \
             -jar target/app.jar

# 查看分析结果
ls -la build/dashboard/
```

### 调试构建

```bash
# 详细输出
native-image --verbose \
              -H:+VerboseSupport \
              -H:+TraceClassInitialization \
              -jar target/app.jar

# 检查镜像内容
native-image-inspect target/app
```

## 性能对比

### 启动时间对比

```java
@SpringBootApplication
public class StartupBenchmark {

    public static void main(String[] args) {
        // 记录启动时间
        long start = System.currentTimeMillis();

        var app = new SpringApplication(StartupBenchmark.class);
        app.setBannerMode(Banner.Mode.OFF);

        ConfigurableApplicationContext context = app.run(args);

        long duration = System.currentTimeMillis() - start;

        System.out.println("Startup time: " + duration + "ms");
        System.out.println("Memory used: " +
            Runtime.getRuntime().totalMemory() -
            Runtime.getRuntime().freeMemory() + " bytes");

        context.close();
    }
}
```

### 典型对比数据

| 指标 | JVM | Native Image | 提升 |
|------|-----|--------------|------|
| 启动时间 | 2.5s | 85ms | 30x |
| 内存占用 | 256MB | 32MB | 8x |
| 首次响应 | 800ms | 12ms | 67x |
| 打包大小 | 50MB | 45MB | 1.1x |

## 与容器集成

### Dockerfile

```dockerfile
FROM ghcr.io/graalvm/native-image:ol9-java17 as builder

WORKDIR /app

# 复制 Maven 依赖
COPY mvnw pom.xml ./
COPY .mvn .mvn
COPY src src

# 下载依赖
RUN ./mvnw dependency:go-offline

# 构建
RUN ./mvnw -Pnative package -DskipTests

# 运行镜像
FROM ghcr.io/graalvm/native-image:ol9-java17
WORKDIR /app
COPY --from=builder /app/target/native-demo /app/native-demo
EXPOSE 8080
ENTRYPOINT ["/app/native-demo"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=prod
      - JAVA_OPTS=-Xmx64m
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/actuator/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 128M
```

### Kubernetes 部署

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: native-demo
spec:
  replicas: 3
  selector:
    matchLabels:
      app: native-demo
  template:
    metadata:
      labels:
        app: native-demo
    spec:
      containers:
        - name: native-demo
          image: native-demo:1.0.0
          ports:
            - containerPort: 8080
          resources:
            requests:
              memory: "32Mi"
              cpu: "100m"
            limits:
              memory: "128Mi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /actuator/health
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /actuator/health
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
```

## Spring Boot 3 特性

### AOT 编译插件

```xml
<plugin>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-aot-maven-plugin</artifactId>
    <version>3.4.0</version>
    <executions>
        <execution>
            <id>prepare-aot</id>
            <goals>
                <goal>prepare-aot</goal>
            </goals>
        </execution>
    </executions>
</plugin>
```

### 可推断的依赖

```java
// Spring Boot 3 可以自动推断某些依赖
@Configuration
public class AutoConfiguration {

    // 不需要显式指定数据源类
    @Bean
    public DataSource dataSource() {
        return DataSourceBuilder.create()
            .url("jdbc:h2:mem:testdb")
            .driverClassName("org.h2.Driver")
            .build();
    }
}
```

## 常见问题与解决

### 反射问题

```java
// 问题：运行时反射失败
public class ReflectionIssue {

    @JsonProperty("user_name")
    private String userName;

    // 解决：注册反射配置
}

// META-INF/native-image/reflect-config.json
[
  {
    "name": "com.example.ReflectionIssue",
    "fields": [
      {
        "name": "userName",
        "type": "java.lang.String"
      }
    ]
  }
]
```

### 资源加载问题

```java
// 问题：资源文件找不到
InputStream is = getClass().getResourceAsStream("/config.json");

// 解决：注册资源
// META-INF/native-image/resource-config.json
{
  "resources": {
    "includes": [{"pattern": "/config.json"}]
  }
}
```

### 类初始化顺序

```java
// 问题：类在错误的时间初始化
public class StaticInit {
    static {
        // 构建时运行可能出问题
    }
}

// 解决：指定初始化时机
// native-image.properties
Args =--initialize-at-build-time=com.example.StaticInit
```

## Quarkus 与 GraalVM

### Quarkus 配置

```xml
<dependency>
    <groupId>io.quarkus</groupId>
    <artifactId>quarkus-resteasy-reactive</artifactId>
</dependency>
<dependency>
    <groupId>io.quarkus</groupId>
    <artifactId>quarkus-hibernate-orm-panache</artifactId>
</dependency>
```

```properties
# application.properties
quarkus.native.additional-build-args=--initialize-at-build-time=org.hibernate
quarkus.http.port=8080
quarkus.datasource.db-kind=h2
quarkus.datasource.jdbc.url=jdbc:h2:mem:testdb
```

### 构建 Quarkus

```bash
./mvnw package -Pnative -Dquarkus.native.enabled=true
```

## 最佳实践

### 优化构建速度

```bash
# 使用构建缓存
native-image --libc=glibc \
             --enable-https \
             --strict-image-bounds \
             -jar target/app.jar

# 并行构建
native-image -jar target/app.jar \
             -H:NumberOfThreads=4
```

### 减小镜像体积

```bash
# 剥离调试信息
native-image --strip-debug-info \
             -jar target/app.jar

# 只包含需要的字符集
native-image -H:+AddAllCharsets \
             -jar target/app.jar
```

### 安全配置

```bash
# 安全加固
native-image --enable-svm \
             --install-exit-handlers \
             -jar target/app.jar

# 禁用不安全的功能
--allow-incomplete-classpath \
--report-unsupported-elements-at-runtime
```

### 内存配置

```bash
# 为 Native Image 配置内存
./target/native-demo -Xmx64m -Xms32m
```

## 与 JMH 集成

### 微基准测试

```java
@Warmup(iterations = 3, time = 1, timeUnit = TimeUnit.SECONDS)
@Measurement(iterations = 5, time = 1, timeUnit = TimeUnit.SECONDS)
@BenchmarkMode(Mode.Throughput)
@OutputTimeUnit(TimeUnit.MILLISECONDS)
public class NativeBenchmark {

    @Benchmark
    public void simpleOperation() {
        IntStream.range(0, 1000).sum();
    }

    @Benchmark
    public String stringConcat() {
        return "Hello" + " " + "World";
    }
}
```

### 运行基准测试

```bash
# 编译基准测试
javac -cp $JMH_HOME/jar/benchmarks.jar NativeBenchmark.java

# 运行
java -jar $JMH_HOME/jar/benchmarks.jar -prof gc NativeBenchmark
```

## 监控 Native Image

### JMX 配置

```bash
./target/native-demo \
    -Dcom.sun.management.jmxremote \
    -Dcom.sun.management.jmxremote.port=9999 \
    -Dcom.sun.management.jmxremote.authenticate=false
```

### Native Memory Tracking

```bash
./target/native-demo \
    -XX:NativeMemoryTracking=summary
```

## 迁移指南

### 从传统 JVM 迁移

1. **测试优先**：先在 JVM 模式确保测试通过
2. **添加配置**：注册反射、资源、代理配置
3. **迭代构建**：使用 `--verbose` 定位问题
4. **性能调优**：根据实际情况调整参数

### 兼容性检查

```java
@Component
public class GraalVMChecker implements ApplicationRunner {

    @Override
    public void run(ApplicationArguments args) {
        String version = System.getProperty("java.vm.version");
        if (version.contains("GraalVM")) {
            System.out.println("Running on GraalVM: " + version);
        } else {
            System.out.println("Running on JVM: " + version);
        }
    }
}
```

## 总结

GraalVM Native Image 是云原生 Java 的重要方向，特别适合：
- 无服务器函数 (Serverless)
- 容器化部署
- 边缘计算
- 需要快速启动的场景

通过合理的配置和优化，Native Image 可以显著提升应用的启动速度和资源效率。
