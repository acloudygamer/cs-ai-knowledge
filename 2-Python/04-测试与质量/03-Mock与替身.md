# 03-Mock与替身

> 前置：[02-Fixture](02-Fixture.md)（monkeypatch 同族）、[09-上下文管理器](../01-语言核心/09-上下文管理器.md)（patch 是上下文管理器）、[10-模块与导入系统](../01-语言核心/10-模块与导入系统.md)（patch 的目标解析） · 后续：[05-覆盖率与测试策略](05-覆盖率与测试策略.md)（何时该写集成测试而不是 mock）

替身（test double）解决的问题是：被测代码的依赖在测试环境里不存在、太慢、太贵或有副作用。本篇先立**替身分类学**（mock 只是其中一种），再讲 `unittest.mock` 与 pytest 的 `monkeypatch` 两套工具，最后给出最重要的内容——**什么时候不该 mock**。

## 本质

| 替身 | 语义 | 用于 |
|---|---|---|
| dummy | 只占位、从不被使用 | 填参数表 |
| stub | 给预设返回值 | 让流程走通（假时钟返回固定时间） |
| spy | 真实现 + 记录调用 | 验证"是否发了通知" |
| fake | 可用的简化实现 | 内存版仓储、内存版文件系统 |
| mock | 预设期望 + 校验交互 | 断言"以什么参数调了什么" |

`unittest.mock.Mock` 实际上是 stub+spy+mock 的合体。选择的判据：**关心输出用 stub/fake，关心交互用 mock**——交互断言（"调了什么"）比输出断言更脆，能少用就少用。

## 机制

### Mock 基础与 spec 安全带

```python
from unittest.mock import Mock

mailer = Mock(spec=Mailer)         # spec：只允许存在的方法/签名 —— 防止拼错方法名还绿
mailer.send.return_value = 42      # stub 面：预设返回
mailer.send.side_effect = TimeoutError   # 或预设抛异常（故障注入）
```

无 spec 的 `Mock()` 对任何属性访问都返回新 Mock——`mailer.sned(...)`（拼错）静默通过，测试形同虚设。**`spec=`（或 `autospec=True` 的 patch）是 mock 的安全带**，两条纪律：生产代码里的替身一律带 spec；断言前先让 mock 只暴露真实接口。

### patch：临时替换的三个落点

```python
from unittest.mock import patch

# 形态一：上下文管理器（首选，作用域显式）
with patch("mylib.service.Mailer") as MockMailer:
    svc = Service()
    svc.notify("hi")
MockMailer().send.assert_called_once_with("hi")

# 形态二：装饰器（整个测试期间）
@patch("mylib.service.Mailer")
def test_notify(MockMailer): ...

# 形态三：pytest 原生 monkeypatch fixture（无 mock 对象，纯替换）
def test_env(monkeypatch):
    monkeypatch.setenv("APP_MODE", "test")       # 测后自动还原
    monkeypatch.setattr("mylib.service.RETRIES", 1)
```

**patch 的目标是"使用处"而不是"定义处"**：`patch("mailer.Mailer")` 改的是 mailer 模块的名字绑定，而 `mylib.service` 里 `from mailer import Mailer` 已经把名字拷进了自己的命名空间——必须 patch `mylib.service.Mailer`（名字绑定机制见 [10-模块与导入系统](../01-语言核心/10-模块与导入系统.md)，这也是"导入即执行"的测试面代价）。`monkeypatch` 的 `delattr/setattr/setenv/chdir` 覆盖环境类替换，测试结束自动还原——比裸 patch 少一层"忘记还原"的事故面。

### 交互断言的克制

`assert_called_once_with(args)` 最严格也最脆（参数多一个关键字就红）；`assert_called_once()` 只验次数；`call_args` 事后检查最宽松。顺序：**能断行为结果就别断交互**（输出优于调用），必须断交互时取满足意图的最弱断言——重构不该因为参数从位置改成关键字而打红一片测试。

### fake 的构造：更耐用的替身

```python
class InMemoryRepo:                       # fake：真语义、假存储
    def __init__(self): self._items: dict[int, Item] = {}
    def save(self, item): self._items[item.id] = item; return item.id
    def get(self, id): return self._items.get(id)
```

fake 让测试走**真实逻辑路径**（异常、边界都由 fake 真实触发），对重构免疫（不依赖调用细节）；代价是要维护 fake 与真实现的一致性（契约测试守护：同一套测试既跑真库又跑 fake，行为必须一致——见 [05-覆盖率与测试策略](05-覆盖率与测试策略.md) 的组合策略）。

### 什么时候不该 mock

1. **mock 你不拥有的东西的内部**：mock 第三方库的私有行为，库升级即碎。自有薄封装层隔离第三方（防腐层），mock 封装层。
2. **mock 出的"现实"从不为真**：mock 数据库返回固定行，查询语义错了测试照样绿——数据访问层用真库测（容器起 Postgres，见 [07-CI-CD集成](07-CI-CD集成.md)），别 mock SQL。
3. **被测值就是协作过程本身**：序列化/反序列化、编解码两端，用 roundtrip 测试而不是 mock 中间件。
判据浓缩：mock 是给"边界外依赖"（时钟、随机、网络、通知）的；**领域逻辑内部依赖用真实现或 fake**。

## 连接

| 需求 | 去 |
|---|---|
| 时间/随机数的确定性 | 注入 Clock/RNG 到构造函数（设计层解法，优于全局 patch） |
| 外部 HTTP 服务 | `respx`（httpx 专属）或本地 fake server（[05-网络请求](../02-IO与工程实践/05-网络请求.md)） |
| 文件系统 | `tmp_path`（[02-Fixture](02-Fixture.md)）优于 mock open |
| 数据库 | 事务回滚 / 容器真库（[06-数据库操作](../02-IO与工程实践/06-数据库操作.md)） |
| 交互断言失效排查 | 本篇"克制"一节 + [05-覆盖率与测试策略](05-覆盖率与测试策略.md) |

## 示例

```python
from unittest.mock import patch

def test_retry_then_success():
    calls = []
    def flaky(url):
        calls.append(url)
        if len(calls) < 3:
            raise TimeoutError(url)
        return "ok"

    with patch("mylib.fetcher.httpx_get", side_effect=flaky) as mocked:
        assert fetch_with_retry("https://x") == "ok"
    assert mocked.call_count == 3            # 恰好三次：交互断言的最弱充分形式
```
