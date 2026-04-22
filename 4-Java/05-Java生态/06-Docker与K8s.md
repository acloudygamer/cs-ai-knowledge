# Docker 与 Kubernetes

## Docker

### Dockerfile 基本结构

```dockerfile
FROM openjdk:25-slim

WORKDIR /app

COPY target/myapp.jar /app/myapp.jar

EXPOSE 8080

ENV JAVA_OPTS="-Xmx512m"

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar /app/myapp.jar"]
```

### 多阶段构建

多阶段构建使用一个阶段构建，另一个阶段运行，优化镜像大小。

```dockerfile
# 阶段 1: 构建
FROM maven:3.9-eclipse-temurin-25 AS builder
WORKDIR /build
COPY pom.xml .
RUN mvn dependency:go-offline
COPY src ./src
RUN mvn package -DskipTests

# 阶段 2: 运行
FROM eclipse-temurin:25-jre-alpine
WORKDIR /app
COPY --from=builder /build/target/myapp.jar /app/myapp.jar

EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/myapp.jar"]
```

### Maven 构建插件

Jib 是 Google 提供的容器镜像构建插件，无需 Docker daemon。

```xml
<plugin>
    <groupId>com.google.cloud.tools</groupId>
    <artifactId>jib-maven-plugin</artifactId>
    <version>3.3.2</version>
    <configuration>
        <from>
            <image>eclipse-temurin:25-jre-alpine</image>
        </from>
        <to>
            <image>docker.io/myuser/myapp</image>
            <tags>
                <tag>${project.version}</tag>
                <tag>latest</tag>
            </tags>
        </to>
        <container>
            <jvmFlags>
                <jvmFlag>-Xmx512m</jvmFlag>
            </jvmFlags>
            <ports>
                <port>8080</port>
            </ports>
        </container>
    </configuration>
</plugin>
```

## Docker Compose

### 基本配置

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
      - SPRING_DATASOURCE_URL=jdbc:postgresql://db:5432/mydb
    depends_on:
      - db
      - redis

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=mydb
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

volumes:
  postgres_data:

networks:
  mynet:
    driver: bridge
```

## Kubernetes

### Pod

Pod 是 Kubernetes 的最小调度单元，包含一个或多个容器。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: myapp-pod
  labels:
    app: myapp
spec:
  containers:
    - name: myapp
      image: myuser/myapp:1.0.0
      ports:
        - containerPort: 8080
      env:
        - name: SPRING_PROFILES_ACTIVE
          value: "prod"
        - name: JAVA_OPTS
          value: "-Xmx512m"
      resources:
        requests:
          memory: "256Mi"
          cpu: "250m"
        limits:
          memory: "512Mi"
          cpu: "500m"
      livenessProbe:
        httpGet:
          path: /actuator/health/liveness
          port: 8080
        initialDelaySeconds: 60
        periodSeconds: 10
      readinessProbe:
        httpGet:
          path: /actuator/health/readiness
          port: 8080
        initialDelaySeconds: 30
        periodSeconds: 5
```

### Deployment

Deployment 管理 Pod 的副本数、滚动更新、回滚等。

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
        - name: myapp
          image: myuser/myapp:1.0.0
          ports:
            - containerPort: 8080
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
```

### Service

Service 为 Pod 提供稳定的访问入口。

```yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp-service
spec:
  selector:
    app: myapp
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
  type: ClusterIP
```

### Ingress

Ingress 提供 HTTP/HTTPS 路由。

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
    - host: myapp.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: myapp-service
                port:
                  number: 80
```

### ConfigMap

ConfigMap 存储非敏感配置。

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: myapp-config
data:
  application.yml: |
    spring:
      profiles:
        active: prod
    server:
      port: 8080
```

### Secret

Secret 存储敏感数据，如密码、密钥。

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: myapp-secret
type: Opaque
data:
  DB_PASSWORD: cGFzc3dvcmQ=
stringData:
  SPRING_DATASOURCE_USERNAME: admin
```

## Spring Boot on K8s

### 探针配置

```yaml
management:
  endpoint:
    health:
      probes: true
  health:
    livenessState:
      enabled: true
    readinessState:
      enabled: true
```

### Helm Chart

Helm 是 Kubernetes 的包管理器。

```yaml
# Chart.yaml
apiVersion: v2
name: myapp
version: 1.0.0

# values.yaml
replicaCount: 3
image:
  repository: myuser/myapp
  tag: "1.0.0"
service:
  type: ClusterIP
  port: 80
resources:
  requests:
    memory: 256Mi
    cpu: 250m
  limits:
    memory: 512Mi
    cpu: 500m
```

## 最佳实践

### 镜像优化

使用轻量级基础镜像、最小化层数、非 root 用户运行。

```dockerfile
# 使用轻量级基础镜像
FROM eclipse-temurin:25-jre-alpine

# 最小化层数
COPY target/myapp.jar /app/myapp.jar

# 非 root 用户
USER 1000

# 健康检查
HEALTHCHECK --interval=30s CMD wget -qO- http://localhost:8080/actuator/health || exit 1
```

### 资源配置

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### 优雅关闭

```yaml
spec:
  terminationGracePeriodSeconds: 60
  containers:
    - name: myapp
      lifecycle:
        preStop:
          exec:
            command: ["sh", "-c", "sleep 10"]
```

## 参考样例

```dockerfile
# 多阶段构建
FROM maven:3.9-eclipse-temurin-25 AS builder
WORKDIR /build
COPY pom.xml .
RUN mvn dependency:go-offline
COPY src ./src
RUN mvn package -DskipTests

FROM eclipse-temurin:25-jre-alpine
WORKDIR /app
COPY --from=builder /build/target/myapp.jar /app/myapp.jar
ENTRYPOINT ["java", "-jar", "/app/myapp.jar"]
```

```yaml
# Docker Compose 微服务
services:
  gateway:
    build: ./gateway
    ports:
      - "8080:8080"
  user-service:
    build: ./user-service
    depends_on:
      postgres:
        condition: service_healthy
  postgres:
    image: postgres:15-alpine
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
```

```yaml
# Kubernetes Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
        - name: myapp
          image: myuser/myapp:1.0.0
          ports:
            - containerPort: 8080
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
```

```yaml
# Kubernetes Service
apiVersion: v1
kind: Service
metadata:
  name: myapp-service
spec:
  selector:
    app: myapp
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
  type: ClusterIP
```

```yaml
# Ingress
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp-ingress
spec:
  rules:
    - host: myapp.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: myapp-service
                port:
                  number: 80
```

```yaml
# 探针配置
management:
  endpoint:
    health:
      probes: true
  health:
    livenessState:
      enabled: true
    readinessState:
      enabled: true
```

```yaml
# PodDisruptionBudget
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: myapp-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: myapp
```
