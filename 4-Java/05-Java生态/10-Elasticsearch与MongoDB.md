# Elasticsearch 与 MongoDB

## 定义

**Elasticsearch** 是基于 **倒排索引（Inverted Index）** 的全文搜索引擎，本质是将文本切分为词项（Term），建立词项到文档的映射，实现 $O(1)$ 词项查找。**MongoDB** 是 **文档数据库**，本质是将 JSON 文档作为存储单元，通过 MMAP 内存映射文件实现磁盘读写的高性能。两者代表了检索型存储与文档型存储的两个极端。

**Elasticsearch 核心价值**：
- 全文搜索：TF-IDF、BM25 相关性算法
- 日志分析：ELK Stack
- 实时分析：聚合计算

**MongoDB 核心价值**：
- 灵活 schema：无固定结构，字段可增删
- 文档模型：天然的对象映射
- 水平扩展：分片集群

---

## 数学模型

### 倒排索引的查找复杂度

**正排索引**：Document → Terms（文档包含哪些词）
- 查找包含词 "Spring" 的文档：需要扫描所有文档

**倒排索引**：Term → Documents（词出现在哪些文档）
- 查找包含词 "Spring" 的文档：直接查倒排表，$O(1)$

倒排索引的存储结构：
```
倒排表（Posting List）：
Spring → [doc1, doc3, doc5, doc7, ...]  (每个 doc 以 docID 形式存储)
Boot   → [doc1, doc9, ...]
```

词项越多，倒排表越长。内存受限场景下可压缩：
- **FOR（Frame of Reference）**：压缩 docID 差值
- **Roaring Bitmap**：按块压缩 docID

### Elasticsearch 分片分配的负载均衡

ES 集群的 **分片分配（Shard Allocation）** 遵循 **磁盘使用率 + 分片数均衡** 策略：

设节点 $N_i$ 的分片数为 $s_i$，磁盘使用率为 $d_i$，目标函数：
$$\min \sum_i |s_i - \bar{s}| + \lambda \cdot |d_i - \bar{d}|$$

其中 $\bar{s}$ 为平均分片数，$\bar{d}$ 为平均磁盘使用率，$\lambda$ 为权重因子。

ES 默认优先均衡分片数，新索引优先分配到分片数最少的节点。

### MongoDB 聚合管道的延迟求值

MongoDB 聚合管道是 **延迟求值（Lazy Evaluation）**：
```
db.orders.aggregate([
    { $match: { status: "completed" } },  // Stage 1
    { $group: { _id: "$customer", total: { $sum: "$amount" } } }, // Stage 2
    { $sort: { total: -1 } }               // Stage 3
])
```

管道不会一次性加载所有数据到内存，而是 **流式处理**：每个 document 依次通过所有 stage，按需产出结果。这允许处理远大于内存的数据集。

### 倒排索引的压缩算法

**Frame of Reference (FOR)**：存储 docID 的增量，而非绝对值。

```
原始 docIDs: [1003, 1004, 1005, 1006, 1007]
增量存储:    [1003, 1, 1, 1, 1]  // 第一个存绝对值，后续存差值
```

差值越小，所需 bit 数越少。设平均差值为 $d$：
$$\text{bits\_per\_doc} = \lceil \log_2(d) \rceil$$

**Roaring Bitmap**：按块（2^16）存储，每块用不同策略。

### 分布式一致性的向量时钟模型

MongoDB 分片集群的副本集使用 **向量时钟（Vector Clock）** 追踪版本：

设副本节点集合 $R = \{r_1, r_2, ..., r_n\}$，向量时钟：
$$VC = \langle c_1, c_2, ..., c_n \rangle$$

其中 $c_i$ 为节点 $r_i$ 看到的版本号。

**写入版本号**：写入时 $c_i = c_i + 1$
**比较规则**：$VC_1 < VC_2$ 当且仅当 $\forall i: VC_1[i] \leq VC_2[i]$ 且 $\exists j: VC_1[j] < VC_2[j]$

---

## 数据流

<pre>
Elasticsearch 写入流程
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌──────────────────────────────────────────────────────────────┐
│  Client                                                      │
│   │                                                          │
│   ▼                                                          │
│  Coordinating Node（接收请求的节点）                          │
│   │                                                          │
│   ├─▶ 写入请求转发到 Primary Shard                            │
│   │                                                          │
│   │   Primary Shard ──▶ 写入内存 Buffer                       │
│   │                        │                                 │
│   │                        ▼                                 │
│   │                   写入 Translog（持久化）                 │
│   │                        │                                 │
│   │                        ▼                                 │
│   │                   refresh() → Segment                    │
│   │                        │                                 │
│   │                        ▼                                 │
│   │                   可被搜索                                          │
│   │                                                          │
│   │   异步：Segment 合并 → 写入磁盘（fsync）                   │
│   │                                                          │
│   └──▶ 副本同步（Replicas）                                  │
└──────────────────────────────────────────────────────────────┘

Elasticsearch 搜索流程
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌──────────────────────────────────────────────────────────────┐
│  Client → Query                                              │
│   │                                                          │
│   ▼                                                          │
│  Coordinating Node →广播查询到所有相关 Shard                   │
│   │                                                          │
│   ├─▶ Primary Shard 1 → 返回 Top-K 结果                      │
│   ├─▶ Primary Shard 2 → 返回 Top-K 结果                      │
│   └─▶ Primary Shard 3 → 返回 Top-K 结果                      │
│   │                                                          │
│   ▼                                                          │
│  Coordinating Node 合并所有 Shard 结果 → 返回最终 Top-K         │
└──────────────────────────────────────────────────────────────┘

MongoDB 写入流程
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌──────────────────────────────────────────────────────────────┐
│  Client                                                      │
│   │                                                          │
│   ▼                                                          │
│  mongos（路由节点，分片集群）                                 │
│   │                                                          │
│   ▼                                                          │
│  Primary Replica Set                                         │
│   │                                                          │
│   ├─▶ 写入内存（WiredTiger Cache）                           │
│   │                                                          │
│   ├─▶ 写入 Journal（日志）                                    │
│   │                                                          │
│   └─▶ 返回 ACK（可配置 writeConcern）                         │
│                                                              │
│  异步：Checkpoint → 内存数据刷写到磁盘                        │
└──────────────────────────────────────────────────────────────┘
</pre>

---

## 机制

### Elasticsearch 的分片与副本一致性

ES 的 **写一致性** 通过 **quorum** 机制保证：
```yaml
wait_for_active_shards: 1  # 默认，等待 1 个 shard 就绪
# 可选：all（全部），quorum（多数）
```

写操作必须在 `wait_for_active_shards` 数量的 shard（包括 primary）写入成功后才返回。这确保了数据不丢失。

**副本同步机制**：ES 使用 **基于版本的复制（Version-based replication）**：
- Primary 写入后分配全局递增 version
- Replica 按 version 增量同步
- 若 replica 落后太多，Primary 发送全量 Lucene segment

### MongoDB 的写Concern 与 ReadConcern

**Write Concern** 控制写入确认级别：
```javascript
{ w: 0 }   // 不等待任何确认（最快，最不安全）
{ w: 1 }   // 等待 Primary 确认（默认）
{ w: "majority" } // 等待多数节点确认（最强一致性）
```

**Read Concern** 控制读取一致性级别：
```javascript
{ readConcern: "local" }        // 读取本地最新数据
{ readConcern: "available" }    // 分片集群：读取任意分片数据
{ readConcern: "majority" }     // 读取被多数节点确认的数据
{ readConcern: "snapshot" }      // 事务内读取快照
```

**组合效果**：`{ w: "majority", readConcern: "majority" }` 提供 **线性一致性（Linearizable）** 保证。

### 两者事务能力对比

| 维度 | Elasticsearch | MongoDB |
|------|--------------|---------|
| 单文档原子性 | ✅ Lucene 层面保证 | ✅ WiredTiger 层面保证 |
| 多文档事务 | ❌ 无（5.x+ 有，但有限制） | ✅ Replica Set 快照隔离 |
| 事务隔离级别 | 无 | 快照隔离（Snapshot） |

ES 通过外部事务管理器（如 Spring）实现跨系统事务，但这依赖外部补偿机制，非 ACID 事务。

### Elasticsearch 全文搜索的 BM25 排名算法

ES 使用 **BM25（Best Matching 25）** 作为默认相关性算法：

$$BM25(D, Q) = \sum_{i=1}^{n} \text{IDF}(q_i) \cdot \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \cdot (1 - b + b \cdot \frac{|D|}{\text{avgdl}})}$$

其中：
- $f(q_i, D)$ = 词项 $q_i$ 在文档 $D$ 中的词频
- $|D|$ = 文档长度
- $\text{avgdl}$ = 平均文档长度
- $k_1$ = 词频饱和参数（默认 1.2）
- $b$ = 文档长度归一化参数（默认 0.75）
- $\text{IDF}(q_i)$ = 逆文档频率

**饱和性**：BM25 解决了词频线性增长的问题——词频超过某阈值后，排名分数不再显著增加。

---

## 参考存根

```java
// 展示 Elasticsearch 批量写入
@Service
public class ElasticsearchService {
    private final ElasticsearchOperations esOps;

    public void bulkIndex(List<Product> products) {
        BulkOperations bulkOps = esOps.bulkOps(BulkOptions.defaultOptions(), Product.class);
        products.forEach(bulkOps::save);
        BulkResult result = bulkOps.index();
        if (result.hasErrors()) {
            result.getErrors().forEach(e ->
                System.err.println("Failed: " + e.getItem().getId()));
        }
    }
}

// 展示 MongoDB 聚合管道
public List<CityStats> getTopCities() {
    Aggregation agg = Aggregation.newAggregation(
        // Stage 1: 过滤已完成订单
        Aggregation.match(Criteria.where("status").is("COMPLETED")),
        // Stage 2: 按城市分组统计
        Aggregation.group("shippingAddress.city")
            .count().as("orderCount")
            .sum("totalAmount").as("revenue"),
        // Stage 3: 按收入排序取前 10
        Aggregation.sort(Sort.Direction.DESC, "revenue"),
        Aggregation.limit(10)
    );
    return mongoTemplate.aggregate(agg, "orders", CityStats.class)
        .getMappedResults();
}
```

---

## 深度：倒排索引的压缩数学

### Frame of Reference 编码

对于递增的 docID 序列 $[x_0, x_1, ..., x_{n-1}]$，存储差值 $[x_0, x_1-x_0, x_2-x_1, ...]$：

设最大差值为 $d_{\max}$，每个差值需要 $\lceil \log_2(d_{\max}) \rceil$ bits。

**压缩率**：
$$\text{compression} = \frac{\sum \lceil \log_2(\Delta_i) \rceil}{\sum \lceil \log_2(x_i) \rceil}$$

### Roaring Bitmap 的混合压缩

Roaring Bitmap 将 docID 空间划分为 $2^{16}$ 个桶（每个桶 65536 个 ID）：

| 桶类型 | 条件 | 存储方式 |
|--------|------|----------|
| 空桶 | 无 docID | 无存储 |
| 稀疏桶 | $< 4096$ 个 docID | 16位整数数组 |
| 稠密桶 | $\geq 4096$ 个 docID | Bitmap（65536 bits） |

**优势**：稀疏文档集节省大量空间，稠密文档集使用紧凑 Bitmap。
