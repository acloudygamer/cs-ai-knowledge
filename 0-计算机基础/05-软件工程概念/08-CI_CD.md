# CI/CD

## 概念

**CI (持续集成)** 频繁地将代码合并到主分支,自动构建和测试。**CD (持续交付/部署)** 自动将通过测试的代码部署到生产环境。

```
┌─────────────────────────────────────────────────────────┐
│                    CI/CD 流程                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  代码提交 ──► CI 服务器 ──► 构建 ──► 测试 ──► 部署     │
│      │           │           │         │         │       │
│      ▼           ▼           ▼         ▼         ▼       │
│   触发钩子   拉取代码    编译/打包  单元/集成  Staging │
│                                                     或    │
│                                                   Prod   │
└─────────────────────────────────────────────────────────┘
```

## 关系

**关键连接**:
- 代码提交 → **触发 CI**: Git 钩子触发构建
- 构建 → **测试**: 自动化测试验证
- 测试通过 → **部署**: 自动部署到目标环境
- 监控 → **反馈**: 部署后监控和报警

## 持续集成 (CI)

### CI 工作流程

```
┌─────────────────────────────────────────────────────────┐
│                    CI 工作流程                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  开发者 ──► push 代码 ──► Webhook ──► CI 服务器         │
│                                             │            │
│                                             ▼            │
│                                      ┌──────────┐       │
│                                      │ 检出代码  │       │
│                                      └────┬─────┘       │
│                                           ▼            │
│                                      ┌──────────┐       │
│                                      │ 安装依赖  │       │
│                                      └────┬─────┘       │
│                                           ▼            │
│                                      ┌──────────┐       │
│                                      │  运行测试 │       │
│                                      └────┬─────┘       │
│                                           ▼            │
│                                      ┌──────────┐       │
│                                      │ 代码扫描 │       │
│                                      └────┬─────┘       │
│                                           ▼            │
│                                      ┌──────────┐       │
│                                      │  构建 artifact│   │
│                                      └────┬─────┘       │
│                                           ▼            │
│                                    成功/失败通知        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Git 钩子

```bash
# .git/hooks 目录
# pre-commit: 提交前检查
# commit-msg: 提交信息格式
# pre-push: 推送前检查
# post-receive: 接收推送后触发 CI

# pre-commit 示例
#!/bin/bash
set -e

echo "Running pre-commit checks..."

# 运行 lint
npm run lint

# 运行测试
npm test

# 检查代码格式
npm run format:check

echo "All checks passed!"
```

### GitHub Actions 示例

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run linter
        run: npm run lint

      - name: Run tests
        run: npm test
        with:
          coverage: true

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Build Docker image
        run: docker build -t myapp:${{ github.sha }} .

      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_TOKEN }} | docker login -u ${{ secrets.DOCKER_USER }} --password-stdin
          docker push myapp:${{ github.sha }}
```

### GitLab CI 示例

```yaml
# .gitlab-ci.yml
stages:
  - build
  - test
  - deploy

variables:
  DOCKER_IMAGE: registry.example.com/myapp

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $DOCKER_IMAGE:$CI_COMMIT_SHA .
    - docker push $DOCKER_IMAGE:$CI_COMMIT_SHA

test:
  stage: test
  image: node:20
  script:
    - npm ci
    - npm run lint
    - npm test
  coverage: '/All files[^|]*\|[^|]*\s+([\d\.]+)/'

deploy:
  stage: deploy
  script:
    - echo "Deploying..."
  only:
    - main
  environment:
    name: production
```

## 持续交付 vs 持续部署

| 阶段 | 持续交付 | 持续部署 |
|------|----------|----------|
| 自动化构建 | 是 | 是 |
| 自动化测试 | 是 | 是 |
| 自动化部署到 Staging | 是 | 是 |
| 自动化部署到 Production | 否 | 是 |

## 部署策略

### 蓝绿部署

```
┌─────────────────────────────────────────────────────────┐
│                    蓝绿部署                             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  负载均衡器                                            │
│      │                                                 │
│   ┌──┴──┐                                            │
│   │     │                                             │
│   ▼     ▼                                             │
│ ┌───┐ ┌───┐                                         │
│ │蓝 │ │绿 │                                         │
│ │环境│ │环境│                                         │
│ └───┘ └───┘                                         │
│   │      │                                             │
│ 旧版本  新版本                                         │
│                                                         │
│  切换时: 负载均衡器指向绿环境即可                       │
│  回滚时: 负载均衡器指向蓝环境即可                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 金丝雀发布

```yaml
# Kubernetes 金丝雀部署
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  selector:
    app: myapp
---
apiVersion: v1
kind: Deployment
metadata:
  name: myapp-blue
spec:
  replicas: 10
  selector:
    matchLabels:
      app: myapp
      version: blue
  template:
    metadata:
      labels:
        app: myapp
        version: blue
---
apiVersion: v1
kind: Deployment
metadata:
  name: myapp-green
spec:
  replicas: 2  # 金丝雀: 少量新版本
  selector:
    matchLabels:
      app: myapp
      version: green
```

### 滚动更新

```bash
# Kubernetes 滚动更新
kubectl rollout status deployment/myapp
kubectl rollout undo deployment/myapp  # 回滚

# Docker Compose 滚动更新
docker-compose up -d --scale myapp=3 --interval 10s
```

## 自动化测试

### 测试金字塔

```
        ┌───────────┐
        │   E2E     │  少量,慢
        │   测试    │
        ├───────────┤
        │   集成    │
        │   测试    │  中等
        ├───────────┤
        │   单元    │
        │   测试    │  大量,快
        └───────────┘
```

### 测试类型

| 类型 | 覆盖面 | 速度 | 维护成本 |
|------|--------|------|----------|
| 单元测试 | 函数/类 | 毫秒级 | 低 |
| 集成测试 | 模块交互 | 秒级 | 中 |
| E2E 测试 | 完整流程 | 分钟级 | 高 |

```javascript
// 单元测试示例 (Jest)
describe('Calculator', () => {
    test('adds two numbers', () => {
        expect(add(2, 3)).toBe(5);
    });

    test('handles negative numbers', () => {
        expect(add(-1, -1)).toBe(-2);
    });
});

// 集成测试示例 (Supertest)
const request = require('supertest');
const app = require('../app');

describe('GET /api/users', () => {
    test('returns users list', async () => {
        const res = await request(app)
            .get('/api/users')
            .set('Authorization', `Bearer ${token}`);

        expect(res.status).toBe(200);
        expect(Array.isArray(res.body.data)).toBe(true);
    });
});
```

## 构建工具

### npm Scripts

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint . --ext .ts,.tsx",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "format": "prettier --write .",
    "prepare": "husky install"
  }
}
```

### Docker 构建

```dockerfile
# Dockerfile 示例
FROM node:20-alpine AS builder
WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules

RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

EXPOSE 3000
CMD ["node", "dist/index.js"]
```

```bash
# Docker 构建优化
# 1. 使用 .dockerignore
node_modules
.git
*.log

# 2. 多阶段构建减小镜像大小
# 3. 合并 RUN 指令减少层数
# 4. 顺序: 变化少的放前面
```

## 环境管理

### 环境类型

| 环境 | 用途 | 特点 |
|------|------|------|
| Development | 开发 | 本地,快速迭代 |
| Testing | 测试 | 自动化测试 |
| Staging | 预生产 | 接近生产,验证 |
| Production | 生产 | 真实用户访问 |

### 配置管理

```bash
# 环境变量
# .env.development
API_URL=http://localhost:3000
DEBUG=true

# .env.production
API_URL=https://api.example.com
DEBUG=false

# Kubernetes ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: myapp-config
data:
  API_URL: "https://api.example.com"
  LOG_LEVEL: "info"

# Kubernetes Secret
apiVersion: v1
kind: Secret
metadata:
  name: myapp-secret
type: Opaque
stringData:
  DATABASE_URL: "postgresql://..."
  JWT_SECRET: "your-secret"
```

## 监控与反馈

### 部署后检查

```bash
# 健康检查
curl https://myapp.example.com/health

# 响应
# { "status": "healthy", "version": "1.2.3" }

# 冒烟测试
npm run test:smoke

# 金丝雀分析
# 监控错误率,延迟,业务指标
```

### 监控指标

| 指标类型 | 示例 | 工具 |
|----------|------|------|
| 基础设施 | CPU, 内存, 磁盘 | Prometheus, Grafana |
| 应用 | 请求延迟, 错误率 | APM, Jaeger |
| 业务 | DAU, 转化率 | 业务监控 |
| 日志 | 错误日志, 访问日志 | ELK, Loki |

## 工具对比

| 工具 | 类型 | 特点 |
|------|------|------|
| Jenkins | CI/CD 服务器 | 插件丰富,自托管 |
| GitHub Actions | CI/CD | GitHub 集成 |
| GitLab CI | CI/CD | GitLab 集成 |
| CircleCI | CI/CD | 云托管 |
| ArgoCD | CD (Kubernetes) | GitOps |
| Spinnaker | CD | 多云支持 |
