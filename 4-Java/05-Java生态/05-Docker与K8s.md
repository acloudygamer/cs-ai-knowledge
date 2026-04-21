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

### Gradle 构建插件

```groovy
plugins {
    id 'com.google.cloud.tools.jib' version '3.3.2'
}

jib {
    from {
        image = 'eclipse-temurin:25-jre-alpine'
    }
    to {
        image = 'docker.io/myuser/myapp'
        tags = ['${project.version}', 'latest']
    }
    container {
        jvmFlags = ['-Xmx512m']
        ports = ['8080']
    }
}
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
    networks:
      - mynet

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=mydb
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - mynet

  redis:
    image: redis:7-alpine
    networks:
      - mynet

volumes:
  postgres_data:

networks:
  mynet:
    driver: bridge
```

### 完整微服务配置

```yaml
version: '3.8'

services:
  gateway:
    build: ./gateway
    ports:
      - "8080:8080"
    depends_on:
      - user-service
      - order-service

  user-service:
    build: ./user-service
    environment:
      - SPRING_PROFILES_ACTIVE=prod
      - SPRING_DATASOURCE_URL=jdbc:postgresql://postgres:5432/users
    depends_on:
      postgres:
        condition: service_healthy

  order-service:
    build: ./order-service
    environment:
      - SPRING_PROFILES_ACTIVE=prod
      - SPRING_DATASOURCE_URL=jdbc:postgresql://postgres:5432/orders
      - SPRING_REDIS_HOST=redis
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started

  postgres:
    image: postgres:15-alpine
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
```

## Kubernetes

### Pod

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
          env:
            - name: SPRING_PROFILES_ACTIVE
              value: "prod"
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

### Service

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
---
# Pod 引用
spec:
  containers:
    - name: myapp
      volumeMounts:
        - name: config
          mountPath: /app/config
  volumes:
    - name: config
      configMap:
        name: myapp-config
```

### Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: myapp-secret
type: Opaque
data:
  DB_PASSWORD: cGFzc3dvcmQ=  # base64 编码
stringData:
  SPRING_DATASOURCE_USERNAME: admin
---
# Pod 引用
env:
  - name: DB_PASSWORD
    valueFrom:
      secretKeyRef:
        name: myapp-secret
        key: DB_PASSWORD
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

```yaml
# Chart.yaml
apiVersion: v2
name: myapp
version: 1.0.0
appVersion: "1.0.0"

# values.yaml
replicaCount: 3

image:
  repository: myuser/myapp
  tag: "1.0.0"
  pullPolicy: IfNotPresent

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

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
```

### Kubernetes Java Client

```xml
<dependency>
    <groupId>io.kubernetes</groupId>
    <artifactId>client-java</artifactId>
    <version>18.0.0</version>
</dependency>
```

```java
@Configuration
public class KubernetesConfig {

    @Bean
    public CoreV1Api coreV1Api() throws IOException {
        return new ClientBuilder().build()
            .runtimeClient(CoreV1Api.class);
    }
}

@Service
public class PodService {

    @Autowired
    private CoreV1Api coreV1Api;

    public String getCurrentNamespace() throws IOException {
        String context = new DefaultKubernetesClient().getContext();
        return context != null ? context : "default";
    }

    public List<Pod> listPods(String namespace) throws IOException {
        return coreV1Api.listNamespacedPod(namespace)
            .getItems();
    }
}
```

## 最佳实践

### 镜像优化

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
    memory: "256Mi"    # 调度依据
    cpu: "250m"
  limits:
    memory: "512Mi"    # 超过后 OOM
    cpu: "500m"        # CPU 限制
```

### 健康检查

```yaml
livenessProbe:
  httpGet:
    path: /actuator/health/liveness
    port: 8080
  failureThreshold: 3
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /actuator/health/readiness
    port: 8080
  failureThreshold: 1
  periodSeconds: 5
  initialDelaySeconds: 30
```

### 优雅关闭

```yaml
spec:
  terminationGracePeriodSeconds: 60  # 等待时间
  containers:
    - name: myapp
      lifecycle:
        preStop:
          exec:
            command: ["sh", "-c", "sleep 10"]
```

### Pod 中断预算

```yaml
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
