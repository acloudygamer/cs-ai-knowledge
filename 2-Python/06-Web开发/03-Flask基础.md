# Flask 基础

> **版本基准**：Python 3.12 stable（latest=3.14，新特性章节保留并标注）

## 本质

Flask 是核心极简但扩展生态丰富的 Python WSGI Web 框架，通过松耦合设计让开发者按需选择组件，而非强制捆绑。核心只提供路由、请求/响应对象和上下文本地代理；数据库、会话、认证等功能由扩展按需引入。这与 Django 的"batteries included"哲学形成鲜明对比。

**归约视角**：Flask 的本质是**基于上下文局部变量的请求-响应分派器**——通过 LocalStack 维护请求级上下文，URL 映射表将请求路由到处理函数，处理函数通过上下文代理访问请求数据和会话信息。

## 数学模型

### 请求上下文栈（LocalStack）

Flask 上下文管理基于 `werkzeug.local.LocalStack`，其数学模型是**线程/协程隔离的词法作用域**，可归约为线程局部存储（TLS）的变体。

设 $\text{LS}$ 为 LocalStack， $\text{tid}$ 为当前线程/协程 ID， $\text{stack}[\text{tid}]$ 为该 ID 对应的对象栈： 为 LocalStack， $\text{tid}$ 为当前线程/协程 ID， $\text{stack}[\text{tid}]$ 为该 ID 对应的对象栈： 为当前线程/协程 ID， $\text{stack}[\text{tid}]$ 为该 ID 对应的对象栈： 为该 ID 对应的对象栈：

 $\text{LS.push}(x) \triangleq \text{stack}[\text{tid}].\text{append}(x)$ 
 $\text{LS.pop}() \triangleq \text{stack}[\text{tid}].\text{pop}()$ 
 $\text{LS.top}() \triangleq \text{stack}[\text{tid}][-1]$ 

**隔离性**：若 $\text{tid}_1 \neq \text{tid}_2$，则 $\text{stack}[\text{tid}_1] \cap \text{stack}[\text{tid}_2] = \emptyset$。这保证了不同请求并发执行时，上下文完全隔离。 ，则 $\text{stack}[\text{tid}_1] \cap \text{stack}[\text{tid}_2] = \emptyset$。这保证了不同请求并发执行时，上下文完全隔离。 。这保证了不同请求并发执行时，上下文完全隔离。

**归约链**：LocalStack → contextvars（Python 3.7+） → threading.local（Python 2+） → OS-managed TLS 寄存器。Flask 的上下文隔离最终归约到操作系统层面的线程局部存储机制，是这一基础原语在 Web 框架中的具体实现。

### 会话签名（HMAC-SHA256）

Flask session 本质是经密钥签名的 Cookie。设会话数据为 $D$，密钥为 $k$，时间戳为 $t$： ，密钥为 $k$，时间戳为 $t$： ，时间戳为 $t$： ：

 $\text{session} = \text{base64}(D) \cdot \text{SEP} \cdot \text{base64}(\text{HMAC-SHA256}(k, \text{base64}(D) \cdot t \cdot \text{salt}))$ 

服务端验证时，重新计算 HMAC 并与传输值比对：**若不等，则数据被篡改**。

**恒定时间比对**（`hmac.compare_digest`）防止时序攻击：攻击者通过测量响应时间猜测密钥。

**为什么这样设计**：签名 Cookie 方案使服务端完全无状态——所有会话数据存在客户端，只有一个签名防止篡改。这使得 Flask 应用可以水平扩展，多个实例共享同一签名密钥即可。

安全性取决于：
- 密钥 $k$ 的熵（应 $\ge 128$ bit 随机数） 的熵（应 $\ge 128$ bit 随机数） bit 随机数）
- HMAC-SHA256 的抗碰撞性（ $2^{256}$ 攻击代价） 攻击代价）

**约束**：数据以明文存储在 Cookie 中，仅签名防篡改，不加密保密。因此 session 中只能存用户 ID 等引用符，不得存密码或敏感信息。

**违反约束的后果**：Cookie 数据可被客户端查看和修改（但签名验证会失败）。若存入会话敏感信息（如用户角色），攻击者可通过修改明文数据提升权限。

### 路由匹配复杂度

Flask 按定义顺序线性扫描路由列表。设路由数为 $R$，最坏情况匹配复杂度： ，最坏情况匹配复杂度：

 $T_{\text{match}} = O(R)$ 

Blueprint 注册后，Werkzeug 的 `Map` 维护一个按路径前缀构建的字典跳表（radix trie），典型路径查找均摊 $O(1)$，但 Blueprint 内部仍按注册顺序扫描。 ，但 Blueprint 内部仍按注册顺序扫描。

**Radix Trie 的结构**：每个节点包含 (prefix, handler, parameters) 三元组。匹配时从根开始，按路径段前缀递减查找，时间复杂度 $O(P)$ 其中 $P$ 为路径段数，与路由总数无关。 其中 $P$ 为路径段数，与路由总数无关。 为路径段数，与路由总数无关。

**约束**：当路由数超过 100 时，线性扫描的性能损耗开始显著。此时应使用 Blueprint 并确保高频路由在注册时排在前面。

**违反约束的后果**：路由数线性增长时，匹配时间也线性增长。500 个路由时，每次请求最多匹配 500 次才能找到处理器。

### 事件驱动的并发模型（归约）

Flask 本身是**同步阻塞 I/O** 模型。单个 worker 在同一时刻只能处理一个请求——其他请求必须排队等待。这意味着：

 $T_{\text{response}} = \sum_{i} T_i^{\text{CPU}} + \sum_{j} T_j^{\text{I/O}}$ 

其中 $T^{\text{I/O}}$ 包括数据库查询、外部 API 调用等。**若 $T^{\text{I/O}}$ 占比高（如等待数据库），worker 空闲率就高**。这是 Flask + 同步数据库驱动在高 I/O 场景下性能差的原因。 包括数据库查询、外部 API 调用等。**若 $T^{\text{I/O}}$ 占比高（如等待数据库），worker 空闲率就高**。这是 Flask + 同步数据库驱动在高 I/O 场景下性能差的原因。 占比高（如等待数据库），worker 空闲率就高**。这是 Flask + 同步数据库驱动在高 I/O 场景下性能差的原因。

**归约**：Flask (同步) → Gunicorn (多 worker) → OS 进程调度 → 时间片轮转。真正的并发来自多 worker 进程，而非 Flask 本身。

**并发度建模**：设 Gunicorn 配置 $N$ 个 worker 进程，每个 worker 处理一个请求。系统并发处理能力为 $N$。若请求到达率 $\lambda > N \cdot \mu$ （ $\mu$ 为单 worker 处理率），队列无限增长，响应时间爆炸。 个 worker 进程，每个 worker 处理一个请求。系统并发处理能力为 $N$。若请求到达率 $\lambda > N \cdot \mu$ （ $\mu$ 为单 worker 处理率），队列无限增长，响应时间爆炸。 。若请求到达率 $\lambda > N \cdot \mu$ （ $\mu$ 为单 worker 处理率），队列无限增长，响应时间爆炸。 （ $\mu$ 为单 worker 处理率），队列无限增长，响应时间爆炸。 为单 worker 处理率），队列无限增长，响应时间爆炸。

**为什么这样设计**：同步模型简化了开发——开发者无需担心竞态条件、锁、事务边界等并发问题。一切请求串行处理，状态在请求内是确定性的。

## 数据流

<pre>
HTTP 请求字节流
    │
    ▼
WSGI Server（Gunicorn / Werkzeug dev server）
    │
    ▼
Flask app.__call__(environ) ──▶ RequestContext 压栈
    │  environ: {REQUEST_METHOD, PATH_INFO, QUERY_STRING, ...}
    │  WSGI 规范：environ 是 PEP 3333 定义的标准接口
    │                              │
    │                              ▼
    │                         app.preprocess_request()
    │                         （执行 before_request 钩子）
    │                              │
    ▼                              ▼
URL Resolver（app.url_map）──匹配──▶ 路由处理函数
    │  Radix Trie 查找 / 线性扫描
    │  匹配结果：endpoint + view function
    │                              │
    │                              ▼
    │                         视图函数（业务逻辑）
    │                         通过 request/session/g 访问上下文
    │                              │
    │                              ▼
    │                         蓝图特定 before_request 钩子
    │                              │
    ▼                              ▼
Response 对象 ◀─── app.postprocess_request()
    │  （执行 after_request 钩子）
    ▼
RequestContext 弹栈
    │  触发 teardown_request 钩子
    │  上下文对象从 LocalStack 弹出
    ▼
WSGI Response（iterable of bytes）
</pre>

**所有权变换**：
- 字节流 → `environ` dict（WSGI 规范）→ `RequestContext`（Flask 封装）
- `g` 对象在请求结束时销毁，不跨请求保留
- `session` 数据经 HMAC 签名后存在客户端 Cookie（服务端无状态）

**关键中间态**：`RequestContext` 是请求上下文的持有者，包含 `request`（请求数据）和 `session`（会话数据）。上下文压栈后，`request`、`session`、`g` 等代理对象指向栈顶上下文的对应属性。

## 对比参照

| 维度 | Flask | Django | FastAPI |
|------|-------|--------|---------|
| **架构哲学** | 极简核心 + 扩展 | batteries included | 现代类型优先 |
| **上下文模型** | LocalStack（线程/协程隔离） | 请求对象（参数传递） | 依赖注入（显式） |
| **路由定义** | 装饰器（声明式） | URLconf（集中式） | 路径装饰器 + 类型注解 |
| **数据绑定** | 无内置 ORM | ORM 内置 | Pydantic 模型 |
| **异步支持** | 需扩展（Flask 2.3+） | 有限 | 原生 async/await |
| **会话存储** | 签名 Cookie（默认） | 数据库/缓存/Cookie | 无内置 |
| **请求对象** | 全局代理 `request` | 显式参数 `request` | 显式参数 `Request` |

## 机制

### 上下文局部变量的实现原理

`werkzeug.local.LocalStack` 的实现依赖于 Python 的 `contextvars`（Python 3.7+）：

```python
from contextvars import ContextVar
_request_ctx_stack = ContextVar('request_ctx_stack')
```

**为什么这样设计**：传统的线程局部存储（`threading.local`）无法跨协程隔离——同一线程内的多个协程共享同一线程 ID。`contextvars.ContextVar` 为每个协程维护独立的上下文副本，实现了更细粒度的隔离。

这意味着：
- 同一进程内，不同请求访问同名变量而互不干扰
- 协程切换时（`asyncio`）上下文自动隔离，无需手动管理
- 上下文栈在请求结束时必须显式 pop，否则 ctx stack 不被 GC（内存泄漏）

**contextvars 的语义**：每个 `ContextVar` 维护一个上下文局部值。当执行流进入新上下文（如新协程）时，继承当前上下文变量的拷贝；修改仅在当前上下文内有效，不影响父上下文。这提供了比 `threading.local` 更精细的隔离粒度。

**违反约束的后果**：若 `pop()` 未被调用（如 early return、异常未捕获），栈顶上下文对象不会被垃圾回收。每次请求都会 push 新上下文但不 pop，内存会持续增长直到进程崩溃。

**归约视角**：Flask 的 LocalStack 是以下原语链的具体实现：
1. **OS TLS**（`pthread_getspecific`）：操作系统提供的线程局部存储
2. **Python threading.local()**：在 TLS 上封装的 Python 接口
3. **contextvars.ContextVar**：协程安全的上下文隔离（Python 3.7+）
4. **LocalStack**：在 ContextVar 上封装的栈结构

每一层都在前一层的基础上增加了抽象，最终提供了"线程/协程内共享，跨线程/协程隔离"的分层语义。

### 会话签名的安全约束

Flask session 是签名 Cookie——数据以 pickle 序列化后，经 HMAC-SHA256 签名，服务端不存储任何内容。签名验证流程：

```
客户端 Cookie
    │
    ▼  base64 解码 → (data, timestamp, mac_received)
    │
    ▼  重新计算 mac = HMAC-SHA256(secret_key, data + timestamp)
    │
    ▼  恒定时间比对 mac == mac_received ？
    │    是 → session 数据有效
    │    否 → 签名验证失败（数据被篡改）
```

**恒定时间比对**（`hmac.compare_digest`）防止时序攻击：攻击者通过测量响应时间猜测密钥。

**为什么这样设计**：HMAC 签名提供了数据完整性保护——任何对 Cookie 数据的修改都会导致签名验证失败。由于服务端不存储会话数据，多个 Flask 实例可以共享同一密钥，实现无状态水平扩展。

**约束**：HMAC 签名只保证完整性（防篡改），不加密内容。Cookie 中的 session 数据是 base64 编码的明文，任何能看到 Cookie 的人都能读取内容。

**违反约束的后果**：会话数据以明文存在 Cookie 中。若会话中存储了敏感信息（如用户邮箱、权限），攻击者可通过 XSS 或网络窃听获取。

### Jinja2 模板引擎的核心机制

Jinja2 模板编译为 Python 代码执行。每条模板语句对应一段 Python 代码块：

```jinja2
{% for item in items %}
  <li>{{ item.name }}</li>
{% endfor %}
```

编译后本质上是：
```python
for item in items:
    write('<li>')
    write(str(item.name))
    write('</li>')
```

**为什么这样设计**：将模板编译为 Python 代码，复用了 Python 解释器的执行效率（字节码缓存），同时保持了模板语法的简洁性。模板引擎本身只需要解析模板语法、生成 Python 代码，无需实现自己的执行引擎。

**编译流程**：模板字符串 → 词法分析（Token） → 语法分析（AST） → Python 源代码 → compile → 代码对象。

**归约视角**：模板引擎本质上是一个**从 DSL（模板语法）到 Python 可执行代码的编译器**。模板中的 `{{ }}` 是插值表达式，`{% %}` 是控制流语句——两者共同构成了一套受限的 Python 子集。这使得模板渲染可以复用 Python 的所有执行优化（字节码缓存、解释器复用）。

**自动转义**：Jinja2 对 HTML 内容默认转义，防止 XSS。转义由 `markupsafe.Markup` 实现——字符串被标记为"安全"后，跳过转义步骤。

**违反约束的后果**：若手动标记字符串为安全（`Markup(user_input)`）而其中包含恶意 JavaScript，会导致 XSS 漏洞。

### 蓝图（Blueprint）的命名空间隔离

Blueprint 在 Flask 中创建独立的 URL 命名空间和视图集合：

- `url_prefix` 为 Blueprint 下所有路由批量添加路径前缀
- `endpoint` 默认以蓝图名为前缀（如 `api.health`），避免不同蓝图之间的端点冲突
- Blueprint 可以有自己的 `before_request`/`after_request` 钩子，作用于该蓝图下所有路由

**为什么这样设计**：Flask 的极简核心没有模块化机制。Blueprint 是补充方案，将大型应用拆为多个 Blueprint，等价于将单体应用分解为多个松耦合的子应用——各 Blueprint 独立开发测试，最后注册到主应用。

**约束**：Blueprint 的 `before_request` 只在该 Blueprint 内的路由生效，不会跨 Blueprint 执行。这与 Django 中间件的全局拦截形成对比。

**违反约束的后果**：若期望某个 Blueprint 的 `before_request` 在另一个 Blueprint 的路由中执行，需要将钩子注册到主应用，而非 Blueprint 内部。

### 错误处理的解耦设计

Flask 的 `@app.errorhandler` 捕获 Werkzeug 的 HTTPException 或任意 Python 异常：

- `abort(404)` 抛出 `NotFound` 异常，由 `errorhandler(404)` 处理
- 业务逻辑错误（数据验证失败、权限不足）应返回 `jsonify({"error": "..."}, 400)`，而非 `abort`——因为 `abort` 会跳过视图函数的后续代码
- 未被捕获的异常最终由 `app.handle_exception()` 和 `app.handle_user_exception()` 处理

**为什么这样设计**：Flask 的错误处理机制将"返回错误响应"与"抛出异常"解耦。HTTPException 用于 HTTP 协议层面的错误（404、405、500），而业务逻辑错误通过 `jsonify` 直接返回响应，保持了 Handler 的正常执行流程。

**约束**：错误处理器中无法访问原始请求上下文（如 `request` 代理），因为错误可能在请求上下文弹出之后触发。若需要请求数据，必须在视图函数中保存到 `g` 对象。

**违反约束的后果**：在错误处理器中访问 `request` 会得到 `RuntimeError: Working outside of request context`，因为异常处理发生在请求上下文之外。

### Gunicorn 的多进程 worker 模型

Flask 作为 WSGI 应用本身是同步的，Gunicorn 通过 pre-fork worker 模型提供并发：

1. Master 进程监听端口，接受连接
2. 根据配置数量 fork 出 N 个 worker 进程
3. 每个 worker 独立处理请求（各自的事件循环/线程）
4. Worker 崩溃后，Master 自动重新 fork 新 worker

**为什么这样设计**：pre-fork 模式在请求到达前预先创建 worker，避免了请求到达时才 fork 的延迟。Master 进程只负责管理 worker，不处理请求，因此非常轻量。

**Sync worker 的执行流**：每个请求在单个 worker 内串行处理。请求到达 → worker 处理 → 响应 → 处理下一请求。若处理中涉及阻塞 I/O（如同步数据库驱动），worker 在 I/O 等待期间处于空闲状态。

**违反约束的后果**：若 worker 处理请求时间过长（同步 CPU 密集型），会独占 worker，导致其他请求排队。若 worker 崩溃（未捕获异常），Master 会自动 fork 新 worker，但正在处理的请求会丢失。

## 代码示例

```python
from flask import Flask, g, session, request, jsonify, abort
import hmac, hashlib
from contextvars import ContextVar

app = Flask(__name__)
app.secret_key = os.urandom(32)  # 密钥熵 ≥ 128 bit

@app.before_request
def before():
    g.db_conn = get_db_connection()

@app.teardown_request
def teardown(exc):
    if hasattr(g, 'db_conn'):
        g.db_conn.close()

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    session["user_id"] = data["username"]  # 签名 Cookie
    return jsonify({"status": "ok"})

@app.route("/protected")
def protected():
    if "user_id" not in session:
        abort(401)
    return jsonify({"user": session["user_id"]})

# 验证签名 cookie（在请求外测试）
with app.test_request_context("/"):
    print(session)

# HMAC 签名验证（防篡改）
def verify_mac(secret_key, data, mac):
    expected = hmac.new(secret_key, data, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, mac)  # 恒定时间比对，防时序攻击

# 蓝图示例
from flask import Blueprint
api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/health')
def health():
    return jsonify({'status': 'ok'})

app.register_blueprint(api)
```
