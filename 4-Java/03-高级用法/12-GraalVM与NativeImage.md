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

Spring Boot 3 对 Native Image 有完整支持。

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

```json
// META-INF/native-image/resource-config.json
{
  "resources": {
    "includes": [
      { "pattern": ".*\\.properties$" },
      { "pattern": ".*\\.xml$" },
      { "pattern": ".*\\.yml$" },
      { "pattern": "org/springframework/boot/logback/.*" }
    ],
    "excludes": [
      { "pattern": ".*/test/.*" }
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
      { "name": "id", "type": "long" },
      { "name": "name", "type": "java.lang.String" }
    ]
  }
]
```

## 动态类加载处理

### Class.forName 处理

GraalVM Native Image 需要预知要加载的类。动态类加载场景需要预注册。

```java
@Service
public class PluginService {

    public Object loadPlugin(String className) {
        try {
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
```

## 性能对比

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

COPY mvnw pom.xml ./
COPY .mvn .mvn
COPY src src

RUN ./mvnw dependency:go-offline
RUN ./mvnw -Pnative package -DskipTests

FROM ghcr.io/graalvm/native-image:ol9-java17
WORKDIR /app
COPY --from=builder /app/target/native-demo /app/native-demo
EXPOSE 8080
ENTRYPOINT ["/app/native-demo"]
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

## 常见问题与解决

### 反射问题

运行时反射失败，需要注册反射配置。

```json
// META-INF/native-image/reflect-config.json
[
  {
    "name": "com.example.ReflectionIssue",
    "fields": [
      { "name": "userName", "type": "java.lang.String" }
    ]
  }
]
```

### 资源加载问题

资源文件找不到，需要注册资源模式。

```json
// META-INF/native-image/resource-config.json
{
  "resources": {
    "includes": [{ "pattern": "/config.json" }]
  }
}
```

### 类初始化顺序

类在错误的时间初始化，通过 --initialize-at-build-time 指定。

```properties
# native-image.properties
Args =--initialize-at-build-time=com.example.StaticInit
```

## Quarkus 与 GraalVM

Quarkus 是为 GraalVM 优化的框架，Native Image 支持开箱即用。

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
```

## 迁移指南

### 从传统 JVM 迁移

1. 测试优先：先在 JVM 模式确保测试通过
2. 添加配置：注册反射、资源、代理配置
3. 迭代构建：使用 --verbose 定位问题
4. 性能调优：根据实际情况调整参数

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

## 参考样例

```bash
# 安装 GraalVM
curl -sL https://github.com/graalvm/graalvm-ce-builds/releases/download/vm-22.3.2/graalvm-ce-java17-linux-amd64-22.3.2.tar.gz | tar xz
export GRAALVM_HOME=/path/to/graalvm-ce-java17-22.3.2
gu install native-image
```

```bash
# 构建 Native Image
./mvnw -Pnative package

# 或使用 Gradle
./gradlew nativeCompile

# 直接运行
./target/native-demo
```

```bash
# 调试构建
native-image --verbose \
              -H:+VerboseSupport \
              -H:+TraceClassInitialization \
              -jar target/app.jar
```

```xml
<!-- Spring Boot Native Image Maven 配置 -->
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

```properties
# native-image.properties
Args=--verbose \
     --initialize-at-build-time=org.slf4j.LoggerFactory \
     --initialize-at-build-time=ch.qos.logback \
     --no-fallback
```

```json
// reflection-config.json
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

```dockerfile
# 多阶段构建
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

```java
// GraalVM 检测
String version = System.getProperty("java.vm.version");
if (version.contains("GraalVM")) {
    System.out.println("Running on GraalVM");
}
```

```yaml
# Kubernetes 部署配置
apiVersion: apps/v1
kind: Deployment
metadata:
  name: native-demo
spec:
  replicas: 3
  template:
    spec:
      containers:
        - name: native-demo
          image: native-demo:1.0.0
          resources:
            limits:
              memory: "128Mi"
              cpu: "500m"
```

```java
// 启动基准测试
@SpringBootApplication
public class StartupBenchmark {
    public static void main(String[] args) {
        long start = System.currentTimeMillis();
        var app = new SpringApplication(StartupBenchmark.class);
        app.setBannerMode(Banner.Mode.OFF);
        var context = app.run(args);
        System.out.println("Startup time: " + (System.currentTimeMillis() - start) + "ms");
        context.close();
    }
}
```
