# CI/CD 集成

## GitHub Actions

### 基础工作流

```yaml
# .github/workflows/test.yml
name: Test

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.14", "3.15"]

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Cache pip packages
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests
        run: pytest --cov=src tests/

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
```

### 完整工作流示例

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.14"

      - name: Install lint tools
        run: pip install ruff mypy

      - name: Run ruff
        run: ruff check .

      - name: Run mypy
        run: mypy src/

  test:
    needs: lint
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.14", "3.15"]
        poetry-version: "1.7"

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Setup Poetry
        uses: abatilo/actions-poetry@v3
        with:
          poetry-version: ${{ matrix.poetry-version }}

      - name: Cache Poetry packages
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-poetry-${{ matrix.poetry-version }}-${{ hashFiles('**/poetry.lock') }}
          restore-keys: |
            ${{ runner.os }}-poetry-

      - name: Install dependencies
        run: poetry install --all-extras

      - name: Run tests
        run: poetry run pytest --cov --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          fail_ci_if_error: true

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build package
        run: |
          python -m pip install build
          python -m build

      - name: Upload package
        uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  publish:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_TOKEN }}
```

## pre-commit

### 安装与配置

```bash
pip install pre-commit
pre-commit install
```

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: debug-statements

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### 自定义钩子

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: pytest-changed
      name: pytest (changed files only)
      entry: pytest --changed-in-HEAD-vs
      language: system
      pass_filenames: true
      stages: [push]

    - id: security-scan
      name: Security scan
      entry: python scripts/security_scan.py
      language: system
      always_run: true
      pass_filenames: false
```

## Tox（多环境测试）

### 安装与配置

```bash
pip install tox
```

```ini
# tox.ini
[tox]
envlist = py312,py313,py314,lint,type
isolated_build = True

[testenv]
deps =
    pytest
    pytest-cov
    pytest-asyncio
commands =
    pytest tests/ {posargs}

[testenv:lint]
deps =
    ruff
commands =
    ruff check .

[testenv:type]
deps =
    mypy
    types-requests
commands =
    mypy src/

[testenv:security]
deps =
    bandit
commands =
    bandit -r src/
```

```bash
# 运行所有环境
tox

# 运行特定环境
tox -e py312

# 只运行 lint
tox -e lint
```

## Docker 集成

### Dockerfile 示例

```dockerfile
# 构建阶段
FROM python:3.14-slim as builder

WORKDIR /app
COPY pyproject.toml poetry.lock* ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-root --without dev

# 运行阶段
FROM python:3.14-slim

WORKDIR /app
COPY --from=builder /app /app
COPY src/ /app/src/

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 非 root 用户运行
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

CMD ["python", "-m", "src.main"]
```

### Multi-stage 构建

```dockerfile
FROM python:3.14-slim as base
WORKDIR /app
COPY pyproject.toml poetry.lock* ./

FROM base as builder
RUN pip install poetry
COPY src/ /app/src/
RUN poetry install --no-root --only main

FROM base as development
RUN pip install poetry
COPY src/ /app/src/
RUN poetry install --no-root --with dev
CMD ["poetry", "run", "fastapi", "dev", "src/main.py"]

FROM builder as test
RUN poetry install --with test
COPY tests/ /app/tests/
CMD ["poetry", "run", "pytest"]

FROM builder as production
RUN poetry install --only main --no-dev
COPY --from=builder /app/src/ /app/src/
CMD ["python", "-m", "src.main"]
```

## 依赖管理

### pip-compile（锁定依赖）

```bash
pip install pip-tools
```

```bash
# requirements.in
requests>=2.28
click>=8.0
```

```bash
pip-compile requirements.in  # 生成 requirements.txt（锁定版本）
pip-compile --upgrade requirements.in  # 升级依赖
```

### poetry.lock

```bash
poetry lock --no-update    # 更新锁文件（不升级版本）
poetry lock --update-all   # 升级所有依赖
poetry check               # 检查依赖有效性
```

## 发布到 PyPI

### 配置

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "mypackage"
version = "0.1.0"
description = "A short description"
readme = "README.md"
requires-python = ">=3.14"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "you@example.com"}
]
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT",
]
```

```bash
# 本地构建测试
python -m pip install build
python -m build
twine check dist/*

# 上传到 Test PyPI
twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ mypackage

# 上传到正式 PyPI
twine upload dist/*
```

## 常见问题

| 问题 | 解决方案 |
|------|----------|
| Action 缓存失效 | 使用 `actions/cache@v4` 并正确配置 key |
| 并行任务冲突 | 使用数据库 migrations 时加锁或串行化 |
| Docker 构建慢 | 使用 multi-stage 减少镜像体积，利用缓存 |
| 秘密信息泄露 | 使用 GitHub Secrets，不在日志中打印敏感值 |
| 多 Python 版本兼容 | 使用 `matrix` 策略，`requires-python` 正确设置 |
