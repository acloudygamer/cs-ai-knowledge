# 12-状态管理

> JavaScript 三大主流状态管理库的入门指南。

## 目录

| 编号 | 主题 | 说明 |
|------|------|------|
| [12-状态管理](./12-状态管理.md) | Redux / MobX / Pinia | 三大状态管理库对比解析 |

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
