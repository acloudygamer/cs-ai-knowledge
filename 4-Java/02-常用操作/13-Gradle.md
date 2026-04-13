# Gradle

## 概述

Gradle 是现代化的构建工具，使用 Groovy 或 Kotlin DSL 定义构建逻辑。

### vs Maven

| 特性 | Gradle | Maven |
|------|--------|-------|
| 语言 | Groovy/Kotlin DSL | XML |
| 构建速度 | 更快（增量构建） | 较慢 |
| 依赖管理 | 传递依赖智能解析 | 依赖冲突手动解决 |
| 灵活性 | 高 | 中 |
| 生态 | Spring Boot 优先支持 | Apache 生态优先 |

## 项目结构

```
project/
├── build.gradle           # 构建脚本（Groovy DSL）
├── build.gradle.kts       # 构建脚本（Kotlin DSL）
├── settings.gradle        # 项目设置
├── settings.gradle.kts
├── gradle.properties      # Gradle 属性
├── app/
│   ├── build.gradle
│   └── src/
│       ├── main/
│       │   ├── java/
│       │   └── resources/
│       └── test/
│           ├── java/
│           └── resources/
├── src/                   # 源码目录（单项目时）
└── lib/                   # 库目录
```

## 基础构建脚本

### settings.gradle

```groovy
// settings.gradle
rootProject.name = 'my-app'

// 包含子项目
include 'app', 'library'
```

### build.gradle（Groovy DSL）

```groovy
plugins {
    id 'java'
    id 'application'
    id 'java-library'
}

// 项目属性
group 'com.example'
version '1.0.0'

// 仓库配置
repositories {
    mavenCentral()
    google()
    maven { url 'https://jitpack.io' }
}

// 依赖配置
dependencies {
    // 编译时依赖
    implementation 'com.google.guava:guava:32.1.3-jre'

    // 测试依赖
    testImplementation 'org.junit.jupiter:junit-jupiter:5.10.1'
    testRuntimeOnly 'org.junit.platform:junit-platform-launcher'

    // API（编译和运行时可用，但不会传递）
    api 'org.apache.commons:commons-lang3:3.14.0'

    // 仅编译时实现
    compileOnly 'org.projectlombok:lombok:1.18.30'
    annotationProcessor 'org.projectlombok:lombok:1.18.30'
}

// Java 编译配置
java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17

    // 源码编码
    withJavadocJar()
}

// 任务配置
application {
    mainClass = 'com.example.App'
}

// 测试配置
test {
    useJUnitPlatform()
    testLogging {
        events 'passed', 'skipped', 'failed'
    }
}
```

### build.gradle.kts（Kotlin DSL）

```kotlin
// build.gradle.kts
plugins {
    java
    application
}

group = "com.example"
version = "1.0.0"

repositories {
    mavenCentral()
    google()
}

dependencies {
    implementation("com.google.guava:guava:32.1.3-jre")
    testImplementation("org.junit.jupiter:junit-jupiter:5.10.1")
}

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}

application {
    mainClass.set("com.example.App")
}
```

## 依赖管理

### 依赖配置

```groovy
dependencies {
    // 编译时依赖（传递依赖不会暴露给消费者）
    implementation 'com.google.guava:guava:32.1.3-jre'

    // API 依赖（传递依赖会暴露给消费者，等同于 compile）
    api 'org.apache.commons:commons-lang3:3.14.0'

    // 仅编译时
    compileOnly 'org.projectlombok:lombok:1.18.30'

    // 运行时依赖
    runtimeOnly 'com.fasterxml.jackson.core:jackson-databind:2.16.1'

    // 测试依赖
    testImplementation 'org.junit.jupiter:junit-jupiter:5.10.1'
    testRuntimeOnly 'org.junit.platform:junit-platform-launcher'
}
```

### 依赖冲突解决

```groovy
// 排除传递依赖
implementation('com.example:library:1.0') {
    exclude group: 'org.slf4j', module: 'slf4j-api'
}

// 强制使用特定版本（解决冲突）
configurations.all {
    resolutionStrategy {
        force 'org.slf4j:slf4j-api:2.0.9'
    }
}

// 依赖版本变量
ext {
    guavaVersion = '32.1.3-jre'
}
dependencies {
    implementation "com.google.guava:guava:$guavaVersion"
}
```

## 多项目构建

### settings.gradle

```groovy
rootProject.name = 'multi-project'

include 'app', 'library', 'web-service'

// 项目别名
project(':app').name = 'application'
```

### 根项目 build.gradle

```groovy
subprojects {
    // 所有子项目共享的配置
    plugins.apply('java')

    repositories {
        mavenCentral()
    }

    dependencies {
        testImplementation 'org.junit.jupiter:junit-jupiter:5.10.1'
    }

    test {
        useJUnitPlatform()
    }
}

// 子项目特定配置
project(':app') {
    dependencies {
        implementation project(':library')
    }
}

project(':web-service') {
    dependencies {
        implementation project(':library')
        implementation 'org.springframework.boot:spring-boot-starter-web:3.2.1'
    }
}
```

## 自定义任务

```groovy
// 创建任务
tasks.register('hello') {
    doLast {
        println 'Hello, Gradle!'
    }
}

// 任务依赖
tasks.register('buildAll') {
    dependsOn tasks.named('clean'), tasks.named('build')
}

// 任务分组
tasks.register('myTask') {
    group = 'Custom'
    description = 'A custom task'

    doLast {
        println 'Custom task executed'
    }
}

// 增量任务
tasks.register('processFiles', Copy) {
    from 'source'
    into 'target'

    // 增量配置
    filesMatching('*.txt') {
        expand(version: '1.0')
    }
}
```

## Gradle Wrapper

### 生成 Wrapper

```bash
# 生成 Gradle Wrapper
gradle wrapper --gradle-version=8.5

# 验证 Wrapper
./gradlew -v
```

### gradle/wrapper/gradle-wrapper.properties

```properties
distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\://services.gradle.org/distributions/gradle-8.5-bin.zip
networkTimeout=10000
validateDistributionUrl=true
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
```

## 常用命令

```bash
# 构建
gradle build              # 编译测试
gradle build -x test     # 跳过测试构建
gradle clean build       # 清理并重新构建

# 运行
gradle run               # 运行 application
gradle bootRun           # 运行 Spring Boot 应用

# 测试
gradle test              # 运行测试
gradle test --info       # 详细测试输出
gradle test --tests '*ServiceTest'  # 运行特定测试

# 依赖
gradle dependencies      # 查看依赖树
gradle dependencies --configuration runtimeClasspath  # 查看特定配置
gradle buildEnvironment   # 查看构建环境

# 其他
gradle projects          # 查看项目结构
gradle tasks            # 查看可用任务
gradle properties       # 查看项目属性
gradle wrapper --gradle-version=8.5  # 升级 Wrapper
```

## Spring Boot 集成

```groovy
plugins {
    id 'java'
    id 'org.springframework.boot' version '3.2.1'
    id 'io.spring.dependency-management' version '1.1.4'
}

dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web'
    implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
    runtimeOnly 'com.h2database:h2'
    testImplementation 'org.springframework.boot:spring-boot-starter-test'
}
```

## 发布配置

```groovy
plugins {
    id 'java-library'
    id 'maven-publish'
}

publishing {
    publications {
        mavenJava(MavenPublication) {
            from components.java

            pom {
                name = 'My Library'
                description = 'A sample library'
                url = 'https://github.com/example/library'

                licenses {
                    license {
                        name = 'MIT'
                        url = 'https://opensource.org/licenses/MIT'
                    }
                }

                developers {
                    developer {
                        id = 'developer'
                        name = 'Developer Name'
                    }
                }

                scm {
                    connection = 'scm:git:https://github.com/example/library.git'
                    developerConnection = 'scm:git:https://github.com/example/library.git'
                }
            }
        }
    }

    repositories {
        maven {
            url = version.endsWith('SNAPSHOT')
                ? 'https://oss.sonatype.org/content/repositories/snapshots/'
                : 'https://oss.sonatype.org/service/local/staging/deploy/maven2/'

            credentials {
                username = System.getenv('MAVEN_USERNAME')
                password = System.getenv('MAVEN_PASSWORD')
            }
        }
    }
}
```

## 常见问题

### 依赖下载慢

```groovy
repositories {
    maven {
        url 'https://maven.aliyun.com/repository/public'
        url 'https://maven.aliyun.com/repository/spring'
    }
}
```

### 内存不足

```properties
# gradle.properties
org.gradle.jvmargs=-Xmx2g -XX:+HeapDumpOnOutOfMemoryError
org.gradle.daemon=true
org.gradle.parallel=true
org.gradle.caching=true
```

### 构建缓存

```bash
# 清理缓存
gradle clean --refresh-dependencies

# 离线模式（使用本地缓存）
gradle build --offline
```
