# 12-状态管理

> JavaScript 三大主流状态管理库的入门指南。

## 目录

| 编号 | 主题 | 说明 |
|------|------|------|
| [01-Redux入门](./01-Redux入门.md) | Redux | 可预测状态容器，单向数据流 + 纯函数 reducer |
| [02-MobX入门](./02-MobX入门.md) | MobX | 透明函数式响应式编程，自动依赖追踪 |
| [03-Pinia入门](./03-Pinia入门.md) | Pinia | Vue 3 组合式 API 状态管理，轻量最小化 |

## 概念总览

- **Redux**：拉模型（pull）—— UI 显式用 `useSelector` 声明需要什么数据
- **MobX**：推模型（push）—— Observable 变化时自动推送变更给观察者
- **Pinia**：响应式变量模型 —— 基于 Vue 3 Proxy，直接构建在 Vue 响应式系统之上

## 学习路径

```
Redux 基础概念 → MobX 响应式原理 → Pinia Vue3 集成
```

按需选择：
- 需要时间旅行调试 / 状态重放 → Redux
- 需要最小样板、最大自动化 → MobX
- 使用 Vue 3 / 喜欢组合式 API → Pinia
