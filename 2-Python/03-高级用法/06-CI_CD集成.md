# CI/CD 集成

## 定义

CI/CD 是软件交付流水线的两个阶段：CI（持续集成）将代码变更自动构建、测试并验证；CD（持续交付/部署）将验证后的产物自动部署到目标环境。GitHub Actions 通过声明式工作流文件（YAML）在云端 runner（虚拟机容器）中执行，与 Git 事件（push、PR）绑定实现自动化。

## 数学模型

### 工作流执行图

工作流是有向无环图（DAG），节点为 jobs，边为 `needs` 依赖：

 $\text{Workflow} = (J, E),\ J = \{\text{job}_i\},\ E \subseteq J \times J$ 

并行 jobs 满足 $j_a \nrightarrow j_b \land j_b \nrightarrow j_a$ ；串行 jobs 满足偏序关系。Job 内各 step 按声明顺序执行。 ；串行 jobs 满足偏序关系。Job 内各 step 按声明顺序执行。

**DAG 的拓扑排序**：工作流调度器对 DAG 进行拓扑排序，确定 jobs 的执行顺序。拓扑排序结果不唯一，但必须满足所有偏序约束。

**并行度的数学约束**：设 DAG 中无依赖的 jobs 集合为 $U$ （即 $\forall j \in U, \nexists i \in J: i \to j$ 或所有前驱已完成）。则最大并行度为 $|U|$——同一时刻最多可运行 $|U|$ 个 job。 （即 $\forall j \in U, \nexists i \in J: i \to j$ 或所有前驱已完成）。则最大并行度为 $|U|$——同一时刻最多可运行 $|U|$ 个 job。 或所有前驱已完成）。则最大并行度为 $|U|$ ——同一时刻最多可运行 $|U|$ 个 job。——同一时刻最多可运行 $|U|$ 个 job。 个 job。

### 缓存命中率

CI 缓存的目的是减少重复依赖下载。缓存 key 的设计直接影响命中率：

 $\text{hit} \iff \text{cache-key}_\text{generated} = \text{cache-key}_\text{stored}$ 

Key 生成公式（GitHub Actions 缓存 action）：

 $\text{key} = \text{prefix} + \text{hash}(\text{dependencies-files})$ 

常见的缓存 key 策略：

| 策略 | key 格式 | 命中率 |
|------|----------|--------|
| 精确版本 | ` ${{ runner.os }}-pip-$ {{ hashFiles('**/requirements.txt') }}` | 高（依赖不变时完全命中） |{{ hashFiles('**/requirements.txt') }}` | 高（依赖不变时完全命中） |
| 回退匹配 | `${{ runner.os }}-pip-` | 中（依赖变化但 OS 相同时部分命中） |
| 锁文件 | ` ${{ runner.os }}-poetry-$ {{ hashFiles('**/poetry.lock') }}` | 高（锁文件变化才失效） |{{ hashFiles('**/poetry.lock') }}` | 高（锁文件变化才失效） |

**回退匹配（restore-keys）的语义**：当精确 key 未命中时，restore-keys 按前缀匹配恢复缓存。例如 key `pip-A1B2C3` 的 restore-keys 为 `pip-` 和 `pip-A`，若存在 `pip-A1B2` 则命中恢复。这允许同一 OS 下依赖小幅更新时复用已有缓存层。

### 覆盖率门禁

覆盖率检查在 CI 中作为质量门禁：

 $\text{gate}(coverage, threshold) = \begin{cases} \text{pass} & coverage \geq threshold \\ \text{fail} & coverage < threshold \end{cases}$ 

`--cov-fail-under=80` 表示覆盖率低于 80% 时 CI 任务失败。

### Matrix 策略的组合数学

Matrix 是笛卡尔积展开：

 $\text{jobs} = |python-version| \times |os| \times |custom-vars|$ 

```yaml
strategy:
  matrix:
    python-version: ["3.12", "3.14"]
    poetry-version: ["1.7", "1.8"]
```

产生 $2 \times 2 = 4$ 个并行 job 实例，每个消耗独立虚拟机实例和配额。 个并行 job 实例，每个消耗独立虚拟机实例和配额。

**资源消耗的数学约束**：总资源消耗为 $O(\prod |dim_i|)$ 。若维度过多，job 数量指数增长可能导致配额耗尽。设 $d$ 个维度，每个维度平均 $|v|$ 个值，则 job 总数： 。若维度过多，job 数量指数增长可能导致配额耗尽。设 $d$ 个维度，每个维度平均 $|v|$ 个值，则 job 总数： 个维度，每个维度平均 $|v|$ 个值，则 job 总数： 个值，则 job 总数：

 $N_{jobs} = \prod_{i=1}^{d} |v_i|$ 

若 $d=4$ 、每个维度 3 个值， $N_{jobs} = 81$ ，可能耗尽 GitHub Actions 并发配额。 、每个维度 3 个值， $N_{jobs} = 81$ ，可能耗尽 GitHub Actions 并发配额。 ，可能耗尽 GitHub Actions 并发配额。

## 数据流

<pre>
代码 Push / PR
    │
    ▼
GitHub 事件触发
    │
    ├── push to main ──→ Workflow 启动
    └── PR opened ─────→ Workflow 启动
              │
              ▼
        Matrix Strategy（并行 job 生成）
        python-version: [3.12, 3.14]
              │
              ▼
        ┌─────────────────────────────────┐
        │  Job: lint                      │
        │  ┌──────────┐  ┌──────────────┐ │
        │  │ checkout │→│ setup-python │ │
        │  └──────────┘  └──────────────┘ │
        │  ┌──────────────────────────┐    │
        │  │ pip install ruff mypy   │    │
        │  └──────────────────────────┘    │
        │  ┌─────────┐  ┌─────────────┐   │
        │  │ruff check│→│ mypy src/   │   │
        │  └─────────┘  └─────────────┘   │
        └─────────────────────────────────┘
              │ needs
              ▼
        ┌─────────────────────────────────┐
        │  Job: test                     │
        │  ...                            │
        └─────────────────────────────────┘
              │ needs
              ▼
        ┌─────────────────────────────────┐
        │  Job: build                    │
        │  python -m build               │
        └─────────────────────────────────┘
              │ needs
              ▼
        ┌─────────────────────────────────┐
        │  Job: publish (if main branch) │
        └─────────────────────────────────┘
</pre>

## 机制

### GitHub Actions 执行模型

GitHub Actions 工作流运行在云端虚拟机（runner）中，每个 job 在独立的虚拟机实例上执行，虚拟机在 job 完成后销毁。Job 之间通过 artifacts 网络传递数据（压缩包、日志、构建产物），而非共享文件系统。

**Job 与 Step 的执行语义**：
- Job 内的 step 按声明顺序串行执行（除非使用 `continue-on-error`）
- Job 之间按 `needs` 依赖偏序执行：无依赖的 job 并行启动
- 每个 step 的退出码决定后续行为：零→成功，非零→失败

**触发条件的精确语义**：
- `push` + `branches: [main]`：仅 main 分支的 push 触发，包含 tag push（因 tag 属于 refs/heads 外）
- `pull_request` + `branches: [main]`：仅 PR 目标为 main 时触发，包含 PR opened、synchronized、reopened
- `workflow_dispatch`：允许手动从 GitHub UI 或 API 触发，需提供输入参数

### Matrix 策略

Matrix 是笛卡尔积展开，产生 $2 \times 2 = 4$ 个并行 job 实例，每个消耗独立虚拟机实例和配额。Matrix 的每个维度独立展开，总实例数为各维度基数的乘积。 个并行 job 实例，每个消耗独立虚拟机实例和配额。Matrix 的每个维度独立展开，总实例数为各维度基数的乘积。

**约束**：Matrix 维度过多会导致 job 数量指数增长。例如 4 个维度各 3 个值产生 81 个 job，可能耗尽 GitHub Actions 的并发配额。

### 缓存机制

GitHub Actions 缓存是内容寻址存储（CAS）：

1. 计算缓存内容的 hash 作为 key
2. 上传时：content → hash → 存储（按 key 索引）
3. 下载时：计算当前内容 hash，查找匹配 key，存在则恢复

**约束**：缓存有 10GB 容量限制和 2 周过期（LRU 驱逐）。缓存 key 的哈希范围必须是确定性的（`hashFiles` 必须在文件存在时求值）。回退 key（`restore-keys`）允许缓存 key 部分匹配时恢复。

**缓存失效原因**：
- 依赖文件内容变化（`hashFiles` 结果不同）
- 手动删除或达到容量上限被驱逐
- 超过 2 周未访问被清理

### Docker 多阶段构建

Docker 多阶段构建将构建环境与运行环境分离，通过 `FROM ... AS alias` 命名中间阶段，`COPY --from=alias` 引用：

```dockerfile
FROM python:3.14-slim as builder    # 阶段1：构建
WORKDIR /app
COPY requirements.txt .
RUN pip install --target=/app/deps -r requirements.txt

FROM python:3.14-slim as runtime    # 阶段2：运行
WORKDIR /app
COPY --from=builder /app/deps /app/deps
COPY --from=builder /app/src /app/src
USER appuser
CMD ["python", "src/main.py"]
```

**镜像层缓存机制**：
- Docker 按顺序逐层检查缓存：若指令和依赖未变，则复用已构建层
- `COPY requirements.txt` 层在 `RUN pip install` 前，当 requirements.txt 不变时 pip 层缓存命中
- 代码变更时：`COPY src/` 层失效，但 requirements.txt 未变所以依赖层仍可用

**非 root 运行的安全价值**：以 root 运行容器意味着攻击者成功逃逸后拥有宿主机 root 权限；非 root 用户将逃逸限制在容器命名空间。

### tox 多环境矩阵

tox 的 `envlist` 定义测试环境矩阵：

 $\text{envlist} = \{\text{py312}, \text{py313}, \text{py314}, \text{lint}, \text{type}\}$ 

每个环境在独立 virtualenv 中执行，隔离依赖。`isolated_build = True` 让 tox 为每个环境创建独立构建。

**tox 的隔离模型**：每个 testenv 环境有独立 virtualenv（`env/xxx/`），依赖安装和测试执行互不干扰。这与 GitHub Actions matrix 的区别在于：tox 在同一虚拟机内并行创建多个 virtualenv；matrix 为每个组合创建独立虚拟机（更高隔离但更高成本）。

### 依赖锁定的必要性

依赖解析的不确定性会导致"在我机器上能跑"问题：

| 工具 | 锁定机制 | 解析策略 |
|------|----------|----------|
| pip | requirements.txt（手动或 pip-compile） | 冻结精确版本 |
| poetry | poetry.lock | 求解 CSP，固定精确版本 |
| pdm | pdm.lock | 求解 CSP |

`pip-compile requirements.in` 将模糊约束（`requests>=2.28`）转化为精确约束（`requests==2.31.0`）。锁定后，即使上游发布新版本，安装的仍是锁定的精确版本。

### 违反约束的后果

- **并行 job 写入同一 artifact**：后写入覆盖先写入，导致部署版本不确定
- **缓存 key 过于宽泛**：依赖包小版本更新但缓存未失效，安装了过期依赖
- **跨 job 状态泄露**：依赖前序 job 的副作用状态，导致测试顺序依赖
- **秘密信息泄露**：将 `secrets.XXX` 打印到日志，或在矩阵 job 中将 secret 传给不信任的 action
- **Matrix job 数量过多**：超出 GitHub Actions 并发配额，部分 job 排队等待

## 参考存根

```yaml
# .github/workflows/test.yml
name: Test

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.14"
      - run: pip install ruff mypy
      - run: ruff check .
      - run: mypy src/

  test:
    needs: lint
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12", "3.14"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-$ {{ hashFiles('**/requirements.txt') }}{{ hashFiles('**/requirements.txt') }}
      - run: pip install -r requirements.txt
      - run: pytest --cov=src tests/
      - uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          fail_ci_if_error: true

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python -m pip install build
      - run: python -m build
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/
```

```dockerfile
# Multi-stage Dockerfile
FROM python:3.14-slim as builder
WORKDIR /app
COPY pyproject.toml poetry.lock* ./
RUN pip install poetry && poetry config virtualenvs.create false
COPY src/ /app/src/
RUN poetry install --no-root --without dev

FROM python:3.14-slim
WORKDIR /app
COPY --from=builder /app /app
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser
CMD ["python", "-m", "src.main"]
```
