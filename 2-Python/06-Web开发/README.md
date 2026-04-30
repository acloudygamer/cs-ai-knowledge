# Web 开发

## 目录

- [FastAPI 快速入门](01-FastAPI快速入门.md)
- [Django 基础](02-Django基础.md)
- [Flask 基础](03-Flask基础.md)

## 概述

Python Web 框架分为三类核心范式：

| 框架 | 架构范式 | 核心特点 | 适用场景 |
|------|----------|----------|----------|
| **FastAPI** | ASGI + 类型驱动 | 原生 async/await，Pydantic 验证，OpenAPI 自动生成 | 高性能 API，微服务 |
| **Django** | MTV + batteries included | 全功能 ORM，Admin 自动生成，迁移系统 | 企业级 Web 应用 |
| **Flask** | WSGI + 极简核心 | 轻量扩展，LocalStack 上下文，按需组装 | 中小型项目，灵活定制 |

## 学习路径

**推荐顺序**：FastAPI（现代类型驱动）→ Flask（理解底层）→ Django（企业级完整框架）

- **FastAPI**：适合作为首个框架入门，类型系统强制契约，文档自动生成
- **Flask**：理解上下文局部变量、装饰器路由、会话签名等核心机制
- **Django**：深入 MTV 架构、ORM 惰性求值、中间件洋葱模型
