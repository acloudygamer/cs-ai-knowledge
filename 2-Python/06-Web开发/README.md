# Web 开发

## 目录

- [FastAPI 快速入门](01-FastAPI快速入门.md)
- [Django 基础](02-Django基础.md)
- [Flask 基础](03-Flask基础.md)

## 概述

Python Web 框架分为三类核心范式，每种范式代表了对 Web 开发不同层面的抽象：

| 框架 | 架构范式 | 核心特点 | 适用场景 |
|------|----------|----------|----------|
| **FastAPI** | ASGI + 类型驱动 | 原生 async/await，Pydantic 验证，OpenAPI 自动生成 | 高性能 API，微服务 |
| **Django** | MTV + batteries included | 全功能 ORM，Admin 自动生成，迁移系统 | 企业级 Web 应用 |
| **Flask** | WSGI + 极简核心 | 轻量扩展，LocalStack 上下文，按需组装 | 中小型项目，灵活定制 |

## 核心范式对比

### 同步 vs 异步

| 维度 | Flask（同步） | Django（同步为主） | FastAPI（异步优先） |
|------|-------------|------------------|-------------------|
| **并发模型** | 多 worker 进程 | 多 worker 进程 | 单进程事件循环 |
| **I/O 等待** | 阻塞 worker | 阻塞 worker | 让出控制权给其他任务 |
| **适用场景** | CPU 密集型 | CPU 密集型 | I/O 密集型（高并发） |

### 状态管理

| 框架 | 会话存储 | 上下文隔离 | 认证机制 |
|------|----------|------------|----------|
| Flask | 签名 Cookie（服务端无状态） | LocalStack（线程/协程隔离） | 扩展（如 Flask-Login） |
| Django | 数据库/缓存/Cookie | 请求参数传递 | 内置 Session + Auth |
| FastAPI | 外部存储（Redis 等） | 依赖注入（显式参数） | 依赖注入（OAuth2 等） |

### 请求处理的数学抽象

**Flask 请求处理**：
- LocalStack 实现上下文隔离，数学本质是线程/协程局部存储
- 路由匹配：Radix Trie 查找，均摊 $O(1)$ ；Blueprint 内部线性扫描， $O(R)$ ；Blueprint 内部线性扫描， $O(R)$ 

**Django 请求处理**：
- M/G/1 队列模型： $\rho = \lambda \mathbb{E}[S]$ ， $\rho \to 1$ 时响应时间爆炸 ， $\rho \to 1$ 时响应时间爆炸 时响应时间爆炸
- 中间件链：格代数结构，`process_request` 向下、`process_response` 逆序

**FastAPI 请求处理**：
- 依赖注入：DAG 拓扑排序，Kahn 算法 $O(N+E)$ 
- 路径匹配：DFA 状态转移， $O(|\text{path}|)$ 
- Pydantic 验证：约束满足问题（CSP）

## 学习路径

**推荐顺序**：FastAPI（现代类型驱动）→ Flask（理解底层）→ Django（企业级完整框架）

- **FastAPI**：适合作为首个框架入门，类型系统强制契约，文档自动生成，async/await 原生支持
- **Flask**：理解上下文局部变量（LocalStack）、装饰器路由、会话签名（HMAC）、Gunicorn 多进程模型
- **Django**：深入 MTV 架构、ORM 惰性求值与 N+1 问题、中间件洋葱模型、迁移状态机

## 版本说明

Python 3.14 为前沿版本（`latest`），Python 3.12 为稳定版本（`stable`）。本目录内容基于 Python 3.12+ 标准库和框架通用特性编写，框架特定版本特性按需标注。
