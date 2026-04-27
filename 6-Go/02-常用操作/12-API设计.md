# API 设计

**定义**：RESTful API 是"资源即 URL、方法即动名词"的无状态 HTTP 接口，约束是**客户端-服务器**分离、**无状态**交互、**统一接口**——这些约束使得缓存和横向扩展成为可能。

## 资源命名核心约束

### 定义
REST 的核心原则之一是**幂等性**：GET（读取）、PUT（完整替换）、DELETE（删除）是幂等操作，POST（创建）和 PATCH（部分更新）是非幂等。幂等性使重试安全，是可靠 HTTP 交互的基础。

### 数学模型

**幂等性形式化**：操作 $f$ 是幂等的，当且仅当：
$$\forall x: f(f(x)) = f(x)$$

在 HTTP 语义中，这意味着一旦操作成功，后续重试不会改变服务器状态（对于读操作：返回相同结果；对于写操作：最终状态相同）。

**幂等性 vs 安全性**：
- 安全性：操作不改变服务器状态（GET, HEAD, OPTIONS）
- 幂等性：多次执行与一次执行效果相同（GET, PUT, DELETE）

### 机制

**POST vs PUT 的本质差异**：
- PUT 是幂等的"完整替换"：客户端提供资源的完整表示，服务器用其覆盖
- POST 是非幂等的"创建/动作"：服务器决定资源 ID（新创建）或执行动作

**PATCH 的非幂等性来源**：PATCH 只发送部分字段，服务器通常使用 merge patch（保留未提及字段）或 replace patch（未提及字段置零）。两者语义不同，重试可能导致不同结果。

**嵌套 URL 的深层问题**：如 `/users/1/orders/2/items/3`：
1. URL 长度随嵌套层级线性增长
2. 移动资源位置可能导致所有子资源 URL 失效
3. 缓存键必须包含完整路径，缓存利用率低

建议：使用扁平的 ID 导航（`/items/3`），父资源关系通过响应中的 `user_id`/`order_id` 字段表达。

## 分页数学模型

### 定义
游标分页（Cursor Pagination）适合实时数据流，偏移分页（Offset Pagination）适合随机访问场景。前者无重复/遗漏风险，后者存在数据变更时的统计不准确问题。

### 数学模型

**偏移分页的页码公式**：
$$N_{pages} = \left\lceil \frac{N_{total}}{page\_size} \right\rceil$$

**偏移分页的问题**：当 $N_{total}$ 在分页过程中增加时：
- 假设总页数 $N_{pages} = 10$，用户在第 5 页时新增 2 条记录
- 原第 5 页的最后一条记录可能滑落到新第 6 页
- 用户可能看到重复记录或遗漏记录

**游标分页的数学保证**：游标分页基于"最后一条记录的排序键值"：
- 下一页：`WHERE created_at < {cursor} ORDER BY created_at DESC LIMIT page_size`
- 游标值本身就是书签，不依赖全局偏移量

### 数据流

<pre>
偏移分页（存在数据变更问题）：

时刻 T0（总记录数 N=100）：
  第1页: records[0:20]     ← 返回 20 条
  第2页: records[20:40]   ← 返回 20 条
  ...
  第5页: records[80:100]

时刻 T1（用户请求第5页时，新增2条，总N=102）：
  第5页: records[80:100] ← 返回 18 条（原20条-2条前移）

时刻 T2（用户再次请求第5页）：
  第5页: records[80:100] ← 同样的18条，但部分记录与T0不同

游标分页（无数据变更问题）：

时刻 T0（cursor="rec_80"）：
  首页: 0-20, last_cursor="rec_80"
  第2页: WHERE id < "rec_80" → 返回 rec_60-79, last_cursor="rec_60"

时刻 T1（用户持有 cursor="rec_80"，此时新增记录）：
  继续使用 WHERE id < "rec_80" → 不受新增记录影响
</pre>

### 分页选型决策树

```
数据是否实时变化（如聊天记录、订单）？
├─ 是 → 游标分页（使用 created_at 或 ID 作为游标）
└─ 否 → 随机访问？
       ├─ 是 → 偏移分页（用户可跳页、点击页码）
       └─ 否 → 游标分页
```

## 错误处理策略

### 定义
API 错误的响应结构应**始终一致**：`{ "code": 400, "message": "human readable", "data": null }`。客户端应基于 `code`（而非 `message` 字符串）做分支处理，因为 `message` 可能本地化或变更。

### 数学模型

**错误码的层次设计**：
- 第一位：类别（1=客户端错误，2=服务器错误，3=认证错误，...）
- 后三位：具体错误类型

例如：
- `1001`: 客户端错误 - 参数验证失败
- `1002`: 客户端错误 - 资源不存在
- `2001`: 服务器错误 - 数据库连接失败

### 机制

**为什么基于 code 而非 message 做分支**：message 是给人看的，可能因为：
1. 国际化而变化（英文→中文）
2. 措辞调整（"Not found" → "Resource not found"）
3. 不同 API 版本返回不同 message

**错误响应的一致性约束**：无论错误发生在哪一层（路由层、service 层、repository 层），最终响应格式必须统一。这要求统一的错误转换中间件或错误封装类型。

## 版本控制

### 定义
URL 版本控制（`/api/v1/`）是最显式、最易缓存的方案；Header 版本控制（`Accept: application/vnd.api+json; version=2`）更 RESTful 但调试困难。两者都是有效方案，URL 版本更常用。

### 机制

**URL 版本的缓存优势**：HTTP 缓存基于 URL。`/api/v1/users` 和 `/api/v2/users` 是完全不同的缓存键，可以独立设置 TTL、单独失效。Header 版本控制的缓存键是 URL + Accept header，CDN 配置更复杂。

**版本共存策略**：
```
/api/v1/*  →  旧版本（维护期，允许只读访问）
/api/v2/*  →  新版本（活跃开发）
```

维护期结束后，v1 下线，v2 成为默认。旧客户端渐进迁移，而非一次性切换。

### 参考存根

```go
// chi 路由版本控制
r.Route("/api/v1", func(r chi.Router) {
    r.Use(middleware.V1Auth)
    v1Handlers.apply(r)
})
r.Route("/api/v2", func(r chi.Router) {
    r.Use(middleware.V2Auth)
    v2Handlers.apply(r)
})

// 或基于 Header 的版本协商
r.Route("/api", func(r chi.Router) {
    r.Use(versionNegotiator)
    r.Route("/{version}", func(r chi.Router) {
        r.Route("/v1", v1Handlers.apply)
        r.Route("/v2", v2Handlers.apply)
    })
})
```
