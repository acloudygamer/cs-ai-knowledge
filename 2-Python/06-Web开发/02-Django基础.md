# Django 基础

## 定义

Django 是一个遵循"batteries included"原则的 MTV（Model-Template-View）Web 框架，通过三层职责分离（数据持久化、展示渲染、业务编排）实现 Web 开发各层面的解耦。核心哲学是"不要重复自己"（DRY）——数据模型单次定义后，表单、Admin、API 自动从同一模型派生，而非各自重复声明。

**归约视角**：Django 的 MTV 架构可归约为**模型-视图-模板**的三层分离，每层通过明确定义的接口通信。Model 层抽象数据库操作，View 层执行业务逻辑，Template 层负责展示渲染，三者通过 Context 字典传递数据，无直接依赖。

## 数学模型

### 请求处理队列模型

Django 请求处理可建模为 M/G/1 队列系统。设请求到达率为 $\lambda$ （请求/秒），服务时间分布为 $G$ （处理时长分布），则：

**Little 定律**：系统中平均请求数
$L = \lambda W$
其中 $W$ 是平均响应时间。

稳态下，服务利用率 $\rho = \lambda \mathbb{E}[S]$ （ $\mathbb{E}[S]$ 为平均服务时间），当 $\rho \to 1$ 时响应时间急剧增长（Django 请求堆积）。这解释了为何 Django 应用需关注：
- 数据库查询的 $\mathbb{E}[S]$ （慢查询拖慢整个请求）
- 中间件链的 $N_{\text{mw}}$ （每个中间件增加 $\mathbb{E}[S]$ ）
- 连接池大小 $K$ （当 $\rho > 0.7$ 时应扩容）

**队列饱和分析**：M/G/1 队列的平均响应时间公式：
$W = \frac{\lambda \mathbb{E}[S^2]}{2(1-\rho)} + \mathbb{E}[S]$

其中 $\mathbb{E}[S^2]$ 是服务时间的二阶矩。当 $\rho \to 1$ 时，分母 $1-\rho \to 0$ ，响应时间 $W \to \infty$——这是队列饱和的数学表述。

### ORM 查询代价的形式化分析

Django ORM 查询代价由三部分构成：解析代价 + 网络代价 + 计算代价。

设查询计划为有向无环图（DAG），节点 $i$ 的代价为 $c_i$ ：

$T_{\text{total}} = \sum_{i \in \text{DAG}} c_i + \underbrace{(n_{\text{query}} - 1) \cdot t_{\text{rtt}}}_{\text{网络往返代价}}$

其中 $t_{\text{rtt}}$ 是数据库往返延迟（约 0.5-5ms，同一机房）。

**N+1 问题**：若未使用 `select_related`/`prefetch_related`，遍历 $N$ 条结果的关联字段触发 $N$ 次额外查询，总代价：
$T_{\text{N+1}} = T_{\text{initial}} + N \cdot T_{\text{related}}$

预加载后降至 $T_{\text{prefetch}} = T_{\text{initial}} + T_{\text{related}}$ （常数次往返，与 $N$ 无关）。

**JOIN 复杂度**：设关联深度为 $d$ ，每层最多 $m_i$ 个关联模型，最坏 JOIN 数：
$N_{\text{JOIN}} \le \prod_{i=0}^{d} (1 + m_i) - 1$

对于单层 $m$ 个外键： $N_{\text{JOIN}} \le m$ 。这就是为何深度嵌套的 `select_related` 会生成臃肿 SQL。

### URL 模式匹配

Django URL 分派使用正则匹配，路径表达式编译为以下优先序列：

| 模式类型 | 匹配顺序 | 匹配复杂度 |
|----------|----------|------------|
| 精确路径 | 最先 | $O(1)$ （字典查找） |
| 路径转换器 | 其次 | $O(P)$ （前缀树，P=路径段数） |
| 正则捕获组 | 最后 | $O(R)$ （线性扫描，R=路由数） |

匹配算法从 URLconf 列表头部扫描，**首次匹配即停止**，不进行最优匹配。因此更具体的路径必须放在更宽泛的路径之前。

**约束**：若路径 `/items/<int:id>/delete` 放在 `/items/<int:id>` 之后，由于线性扫描的首次匹配原则，删除路径永远不会被匹配到——因为泛型路径已先匹配。

### 中间件的格代数

Django 中间件链构成一个**格（lattice）结构**。设中间件集合 $M = \{M_1, M_2, \ldots, M_n\}$ ，定义偏序关系：

$M_i \prec M_j \iff i < j \text{（在 settings.py 中的注册顺序）}$

`process_request` 沿此偏序向下传播，`process_response` 逆序向上返回。这个结构形成一个**有界格**——顶为最末注册的中间件，底为最先注册的中间件。

## 数据流

<pre>
HTTP 请求字节流
    │
    ▼
WSGI Handler（django/core/handlers/wsgi.py）
    │  解析 environ dict：METHOD, PATH, QUERY_STRING, BODY
    ▼
URL Resolver ──匹配──▶ URLconf 路由表（urls.py）
    │  正则编译 + 线性扫描，首次匹配即停止
    │  匹配结果：视图函数/类 + kwargs（路径参数）
    │                  │
    ▼                  ▼
Middleware.process_request ──▶ 视图
    │（按 settings.py 声明顺序向下）  │
    │                              ▼
    │                         ORM 查询（惰性求值）
    │                         首次遍历/求值才触发 SQL
    │                         QuerySet 持有 SQL 描述 + 缓存
    │                              │
    │                              ▼
    │                         模板渲染（Jinja2）
    │                         Context dict + 模板文件 → HTML
    │                              │
    │                              ▼
    │                         HttpResponse 对象
    │                              │
    ▼                              ▼
Middleware.process_response ◀──
    │（按逆序向上，形成洋葱模型）
    ▼
WSGI Response（bytes 流）
</pre>

**所有权变换**：
- HTTP 字节流 → `HttpRequest`（解析后持有 GET/POST/META/COOKIES）
- 路由 kwargs → 视图函数的输入参数（值拷贝，非引用）
- ORM QuerySet → **惰性求值**：首次遍历才触发 SQL，结果缓存于 QuerySet 内部
- 模板 Context → 模板引擎持有，渲染完成后释放
- `HttpResponse` → 最终字节流，写入 WSGI 输出缓冲

**关键中间态**：QuerySet 是查询的**描述对象**而非结果集。它持有 SQL 字符串和参数，直到首次求值（遍历、切片、`count()`、`list()`）时才真正执行查询。

## 对比参照

| 维度 | Django MTV | Flask | FastAPI |
|------|-----------|-------|---------|
| **数据模型** | ORM（主动记录，类=表） | SQLAlchemy（数据映射，声明式） | Pydantic（验证，非持久化） |
| **模板** | Jinja2（继承+组件） | Jinja2 | 无（返回 JSON） |
| **路由** | 正则 URLconf | 装饰器路径 | 类型注解路径 |
| **中间件语义** | 可中断的洋葱模型 | 请求上下文栈 | 依赖注入 |
| **DB 迁移** | 迁移系统（版本化） | 无内置（Alembic） | 无内置 |
| **请求模型** | 隐式 request 参数 | 显式 request 全局代理 | 显式 request 参数 |
| **ORM 模式** | 主动记录（Active Record） | 数据映射（Data Mapper） | 无（外部库如 SQLModel） |

## 机制

### MTV 架构的耦合分析与设计选择

MTV 三层之间的耦合关系决定了 Django 的设计边界：

**Model ↔ Database 的耦合**：
Model 层直接映射数据库表结构，字段类型绑定特定数据库列类型（Django ORM 对此做抽象）。这意味着：
- 数据库迁移必须与 Model 定义同步（`makemigrations`）
- 换数据库（如 PostgreSQL → MySQL）需检查字段兼容性（Django ORM 做大部分兼容）
- Model 层**不持有数据库连接**，连接由 `DATABASES` 配置决定，由 `DatabaseWrapper` 管理连接池

**为什么这样设计**：Django 的 ORM 抽象了数据库细节，使开发者可以用 Python 对象操作数据库，无需写 SQL。但 ORM 无法表达所有 SQL 特性（窗口函数、复杂聚合），所以保留了 `raw()` 和 `cursor.execute()` 作为逃生舱。

**Model ↔ View 的耦合**：
View 通过 `Model.objects` 管理器操作 Model，完全通过 Python API 而非 SQL。这形成约束：
- 复杂查询（窗口函数、多层聚合）超出 ORM 表达能力的，用 `raw()` 或 `cursor.execute()` 绕道
- View 层不知道 SQL 长什么样，调试时用 `connection.queries` 查看实际 SQL

**为什么这样设计**：将数据访问抽象为 Python API，使得 View 层与数据库解耦——换数据库只需改配置，View 代码无需修改。但这个抽象有代价：某些复杂查询无法表达。

**View ↔ Template 的耦合**：
Template 只接收 Context dict，不持有任何数据引用。Template 层的 `{% for %}` 是纯 Python 迭代，不触发查询。这意味着：
- N+1 问题在 View 层控制（预加载关联），Template 层无法感知
- 循环中的查询（模板内查 Model）是**反模式**——应该从 View 预加载后传入 Template

**为什么这样设计**：Template 层的纯迭代设计避免了模板引擎本身执行数据库查询的复杂性，保持了 MTV 的清晰边界——View 负责数据准备，Template 负责展示。

**三层联合约束**（DRY 的物理实现）：
- `ModelForm` 自动从 Model 字段推导表单字段——Model 是单一事实来源
- `Admin` 从 Model Meta 信息生成管理界面——Model 是唯一需要维护元信息的地方
- 换 Model 字段，表单和 Admin 自动更新——无需三处重复修改

**违反约束的后果**：若在 Template 层查询 Model（如 `{% for item in items %}{{ item.category.name }}{% endfor %}` 而未预加载），每次迭代触发一次数据库查询。对于 $N$ 个 item，触发 $N+1$ 次查询（1 次主查询 + $N$ 次关联查询），性能急剧下降。

### ORM 的抽象代价：形式化分析

Django ORM 采用**主动记录模式**（Active Record）。每个 Model 实例内部持有 `__dict__`（实例数据）和对 Manager 的引用（类级别查询接口）。

**QuerySet 惰性求值**是理解 Django ORM 性能的关键。QuerySet 是**查询描述的持久化对象**，而非查询结果：

```python
qs = Product.objects.filter(price__gt=100).select_related('category')
# 此时：仅构造了 SQL 字符串，未发送任何请求
# SQL = "SELECT ... FROM product JOIN category ..."
```

`list(qs)` 或 `qs[0]` 触发**求值**，结果被缓存，后续遍历不重复查询。

**为什么这样设计**：惰性求值允许链式构造复杂查询而不立即执行，减少网络往返。例如 `filter().exclude().select_related()` 可以组合多个查询条件，最终只执行一条 SQL。

**代价模型**：

| 操作 | 触发 SQL | 缓存 |
|------|----------|------|
| 构造 QuerySet（不过滤） | 否 | - |
| `filter/exclude/annotate` | 否 | 返回新 QuerySet |
| `count/sum/exists` | 是（聚合查询） | 否（直接返回值） |
| `list(qs)` / `qs[0]` | 是 | 是（QuerySet 内部缓存） |
| 遍历 `for x in qs` | 是 | 是（缓存已求值部分） |

**违反约束的后果**：
- 在 Template 层循环查 Model：每次迭代触发一次查询（N+1）
- `queryset.count()` 前调用 `list(queryset)`：先拉全部数据再内存计数，极慢
- `select_related` 嵌套过深：生成巨大的 JOIN，数据库 CPU 时间反而更高

### 中间件链的执行顺序与短路语义

Django 中间件的 `process_request` 按 **settings.py 中注册的顺序**执行，`process_response` 按**逆序**。这形成严格对称的洋葱模型：

```
请求进入 ↓
Middleware1.process_request  ── 可返回 HttpResponse 短路
Middleware2.process_request  ── 可返回 HttpResponse 短路
Middleware3.process_request  ── 可返回 HttpResponse 短路
           ↓
      视图函数
           ↑
Middleware3.process_response
Middleware2.process_response
Middleware1.process_response
响应发出 ↓
```

**为什么这样设计**：洋葱模型确保中间件可以"包裹"整个请求处理过程——请求阶段从外到内，响应阶段从内到外。这使得中间件可以统一处理进入和离开的请求，例如日志中间件记录请求进入时间，在响应阶段计算总耗时。

**短路语义的形式化**：若 $M_i.\text{process\_request}$ 返回非 None，则执行序列在 $M_i$ 处截断，跳到所有已注册中间件的 `process_response`（从 $M_i$ 向上逆序）。这与短路求值（ $A \land B$ 中 $A$ 为 False 则不求  $B$）完全对应。

**违反约束的后果**：若 `process_request` 返回 HttpResponse 后忘记调用 `process_response`，响应不会正确返回给客户端（因为中间件的响应处理链未执行）。这是中间件开发的常见错误。

### 迁移系统的约束

Django 迁移是数据库架构的版本化描述，由 `makemigrations` 生成、`migrate` 应用。

**为什么这样设计**：迁移系统解决了"数据库 schema 与代码不同步"的问题。每次 Model 定义变更，生成迁移文件记录变更操作（创建表、添加字段等）。`migrate` 按顺序应用迁移，保证数据库 schema 与代码始终一致。

**约束**：
- 迁移文件是**自包含的 SQL 脚本序列**，必须能从未知旧状态应用
- 迁移文件中禁止引用模型方法（业务逻辑）——因为迁移可能在业务代码部署前运行
- `StateApps` 用于在迁移中临时操作模型（不需要真实数据库）

**版本化约束**：迁移必须可正向和反向应用。`migrate` 记录已应用的迁移版本，若回滚，Django 按记录逆向执行迁移序列。

**违反约束的后果**：
- 若迁移引用了模型方法，方法被修改或删除后，迁移无法运行
- 若迁移不是自包含的（依赖特定的初始数据），在新环境中创建数据库会失败

**迁移状态机**：迁移系统维护一个状态机，状态为已应用/未应用的迁移名称集合。`migrate` 命令执行时，系统根据当前状态计算需要应用或回滚的迁移序列，保证最终一致性。

### 会话与认证的解耦设计

Django 的会话框架与认证框架完全解耦：

- **会话**：存储用户状态（`request.session`），后端可配置（数据库/缓存/签名 Cookie）
- **认证**：处理用户密码哈希、登录/登出、权限检查，与会话通过 `request.user` 关联

**为什么这样设计**：解耦允许替换会话存储后端而不影响认证逻辑。例如从数据库会话切换到 Redis 会话，只需改配置，认证代码无需修改。

密码哈希使用 PBKDF2（默认）或 Argon2，通过 `make_password` / `check_password` 操作。这将用户提供的明文密码与存储的哈希比对，**不在任何地方存储明文密码**。

**PBKDF2 的安全性**：PBKDF2 通过迭代哈希 $H^n(\text{salt} + \text{password})$ 提供防护。默认配置（SHA256，360,000 次迭代）使每次密码验证计算代价约 100ms，难以暴力破解。

## 参考存根

```python
from django.db import connection, reset_queries
from django.conf import settings

# 开启查询日志
settings.DEBUG = True
reset_queries()

# 构造 QuerySet（未发 SQL）
qs = Product.objects.filter(price__gt=100).select_related('category')

print(f"构造后查询数: {len(connection.queries)}")  # 0 — 惰性

_ = list(qs)  # 求值，触发 SQL
print(f"求值后查询数: {len(connection.queries)}")  # 1

print(connection.queries[-1]['sql'])  # 打印实际 SQL

# 在模板中预加载 vs 循环查询的代价对比
# 预加载：SELECT ... JOIN category WHERE price > 100（1次）
# 循环：SELECT ... WHERE id=1; SELECT ... WHERE id=2; ...（N次）

# 中间件短路示例
class RateLimitMiddleware:
    def process_request(self, request):
        if self.is_rate_limited(request):
            return JsonResponse({'error': 'rate limited'}, status=429)
        # 返回 None 继续处理链
```
