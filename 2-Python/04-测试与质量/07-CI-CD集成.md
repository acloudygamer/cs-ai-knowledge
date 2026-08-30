# 07-CI-CD集成

> 前置：[06-代码质量工具](06-代码质量工具.md)（要挂进流水线的工具）、[04-打包与分发](../03-运行时与性能/04-打包与分发.md)（构建与发布）、[02-开发环境与工具链](../00-概览/02-开发环境与工具链.md)（环境与锁） · 后续：[06-应用领域](../06-应用领域/README.md)（部署形态）

CI/CD 把前六篇的所有纪律（lint、类型、测试、构建、版本）固化成**机器执行的流水线**——纪律不进流水线就会退化成口头约定。本篇以 GitHub Actions 为载体讲三件事：工作流解剖、阶段设计（PR 门禁 → 主干 → 发布）、发布自动化。

## 本质

- 工作流三段：**workflow**（触发器 + 并行的 job）→ **job**（独立虚拟机，可矩阵展开）→ **step**（命令序列）。job 间默认无共享（各自全新环境），显式传物用 artifacts/cache。
- 设计主线：**PR 快速反馈（分钟级）→ 主干全量验证 → tag 触发发布**。三层各自要什么、不要什么，由反馈延迟与成本权衡决定。

## 机制

### 骨架与高频件

```yaml
# .github/workflows/ci.yml
name: ci
on:
  pull_request:
  push:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4          # uv：解释器+依赖一步到位（见 02-开发环境与工具链）
      - run: uv sync --frozen                 # 严格按锁安装——可复现是 CI 的前提
      - run: uv run ruff check . && uv run ruff format --check .
      - run: uv run mypy src/

  test:
    strategy:
      fail-fast: false                        # 一个版本失败不取消其余——全貌优先
      matrix:
        os: [ubuntu-latest, windows-latest]   # 跨平台差异真实存在（路径/编码/进程模型）
        python-version: ["3.12", "3.13"]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --frozen
      - run: uv run pytest -m "not slow" --cov=mylib --cov-branch
```

要点：`uv sync --frozen` / `pip sync`（按锁精确安装）让 CI 与本地同构——"本地绿 CI 红"的第一嫌疑人就是环境漂移；矩阵覆盖 `requires-python` 承诺的**边界版本**（[04-打包与分发](../03-运行时与性能/04-打包与分发.md)），不是所有版本；缓存依赖（`setup-uv` 内建 / `actions/cache` 键含锁文件哈希）把分钟级安装压到秒级。

### 分层跑测试

- PR 门禁：lint + 类型 + 快速测试（`-m "not slow"`，[01-pytest基础](01-pytest基础.md) 的 marker 分层）——目标是分钟内给结论。
- 主干/夜间：全量（含 slow、集成、[03-Mock与替身](03-Mock与替身.md) 的契约测试、容器真库——`services:` 或 `containers:` 起依赖服务）。
- 覆盖率上报与 diff 覆盖门禁的落点见 [05-覆盖率与测试策略](05-覆盖率与测试策略.md)。

### 发布流水线：tag 驱动

```yaml
  release:
    if: startsWith(github.ref, 'refs/tags/v')
    needs: [lint, test]
    environment: pypi            # 受环境保护的发布环境
    permissions:
      id-token: write            # Trusted Publishing：OIDC 免长期令牌
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv build && uv publish    # wheel+sdist 构建+上传（见 04-打包与分发）
```

发布纪律落到机器：**版本号只来自 git tag**（手工改文件与 tag 双轨必打架）；`needs` 保证测试绿才有发布；`environment` 加人工审批位（prod 级别的最后一道）；**Trusted Publishing（OIDC）**取代长期 PyPI token——令牌泄漏面归零。扩展形态：含 C/Rust 扩展的包用 cibuildwheel 矩阵出全平台 wheel（[04-打包与分发](../03-运行时与性能/04-打包与分发.md)）；应用类交付走容器镜像构建 + 推送（[02-开发环境与工具链](../00-概览/02-开发环境与工具链.md) 的 Docker 档）。

### 分支保护与依赖安全

- 分支保护规则把 CI 从"信息"变"门禁"：required checks + 禁止直推 main + PR 必须最新——这套配置是流程的最后一环，缺失则一切 lint 都是建议。
- 依赖安全：`pip-audit` / `uv lock --audit`（锁文件对 OSV 漏洞库）、`dependabot`/`renovate`（升级 PR 自动化）周期任务；密钥只进 GitHub Secrets（[03-序列化与配置格式](../02-IO与工程实践/03-序列化与配置格式.md) 的密钥纪律在 CI 侧的镜像）。

## 连接

| 需求 | 去 |
|---|---|
| 门禁工具的配置 | [06-代码质量工具](06-代码质量工具.md)（本篇只管"何时跑"） |
| 构建产物与入口点 | [04-打包与分发](../03-运行时与性能/04-打包与分发.md) |
| 测试分层与 marker | [01-pytest基础](01-pytest基础.md)、[05-覆盖率与测试策略](05-覆盖率与测试策略.md) |
| 部署目标（Web 服务） | [01-Web开发总览](../06-应用领域/01-Web开发总览.md)（容器/平台的下游） |
| 其他 CI 平台 | GitLab CI 同构（stages/jobs）；Actions 是本篇的示例载体而非绑定 |

## 示例

```bash
# 本地等价性检查：提交前手动模拟整条 PR 流水线
uv sync --frozen &&
uv run ruff check . && uv run ruff format --check . &&
uv run mypy src/ &&
uv run pytest -m "not slow" -n auto

# 发布一条龙（手工触发路径；自动路径是打 tag）
git tag v0.3.1 && git push origin v0.3.1   # → release job: build → trusted publish
```
