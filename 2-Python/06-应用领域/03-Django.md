# 03-Django

> 前置：[01-Web开发总览](01-Web开发总览.md)（全栈 vs 微的选型轴）、[07-面向对象](../01-语言核心/07-面向对象.md)（模型层地基）、[06-数据库操作](../02-IO与工程实践/06-数据库操作.md)（ORM 判据） · 后续：[04-Flask](04-Flask.md)（另一极）

Django 的差异化机制是**全家桶 + 约定**：ORM、迁移、Admin、Auth、表单、模板一箱出齐，"Django way" 优先于自由组装。代价是结构重量，收益是**全队默认一致**——新人到岗即知道代码在哪。本篇按它的四层骨架讲，重点在别处没有的件（Admin、迁移）。

## 本质

- MVT 分层：**Model**（数据层，ORM）→ **View**（业务处理）→ **Template**（展示）；URLconf 把路径映射到 view。与 MVC 同构，命名不同。
- 一切围绕 `settings.py` 的**约定树**：app（可插拔功能包）→ `models.py` / `views.py` / `admin.py` / `migrations/` 每个文件名都有框架语义——约定即架构（对照 [10-模块与导入系统](../01-语言核心/10-模块与导入系统.md) 的包语义，Django 把它制度化到文件名级）。

## 机制

### Model 与迁移：数据库的版本化

```python
# models.py —— 定义即 schema
from django.db import models

class Article(models.Model):
    title = models.CharField(max_length=200)
    published_at = models.DateTimeField()
    tags = models.ManyToManyField("Tag", related_name="articles")

    class Meta:
        ordering = ["-published_at"]        # 默认排序进元数据（查询默认值的正确位置）
```

- 迁移是 **schema 的 git**：`makemigrations`（自动 diff 模型变化生成迁移文件）→ `migrate`（应用到库）。迁移文件**进版本库**——生产 schema 由代码历史完整表达（[06-数据库操作](../02-IO与工程实践/06-数据库操作.md) 末尾"迁移管理"的承诺在此兑现）。
- ORM 查询构造：`Article.objects.filter(tags__name="py").exclude(published_at=None)`——`__` 穿透关系；N+1 的解药是 `select_related`（JOIN 外键）/`prefetch_related`（批量取多对多），配合 `queryset.query` 或日志验证实际 SQL（[02-性能优化与剖析](../03-运行时与性能/02-性能优化与剖析.md) 的"先测后改"对 ORM 同样成立）。

### Admin：全家桶里最独家的件

`admin.site.register(Article)` 一行，得到完整后台（列表/筛选/表单/权限）。它是 Django 的"买一送一"：内部工具、运营后台经常一行不用写。定制度阶梯：`list_display`/`search_fields`（一行）→ `ModelAdmin` 方法（中级）→ 覆写模板（重）——Admin 适合内部与中低复杂度，复杂工作流仍走业务前端。

### View 的两代形态

- 函数视图 + 装饰器（`@login_required`）：轻逻辑直白。
- 类视图（CBV）：`ListView`/`DetailView`/`CreateView` 继承即得 CRUD 骨架——继承层次深时的查找成本（[07-面向对象](../01-语言核心/07-面向对象.md) 的深继承判据）是它的争议点，**团队定一档**（只用浅层通用视图）比摇摆好。
- DRF（Django REST Framework）：API 化的标配扩展——`Serializer` 是 pydantic 的 Django 方言，`ViewSet` + Router 把 REST 路由自动化；FastAPI 式的注解驱动在 DRF 里换成 Serializer 声明（两条路线对照 [02-FastAPI](02-FastAPI.md)）。

### Auth、表单与中间件

- Auth 全家：User 模型、session、密码哈希、权限组——自研鉴权的冲动在 Django 项目里应被克制（除非有硬理由）。
- 表单层：`Form`/`ModelForm` 声明字段与校验，服务端渲染——传统多页应用的组件；纯 API 项目跳过它。
- 中间件：责任链（[04-行为型模式](../05-设计模式/04-行为型模式.md)）的 Django 实例，`MIDDLEWARE` 列表即洋葱顺序，session/auth/CORS 都在这层挂。

### 异步与 Django

ASGI 支持（[01-Web开发总览](01-Web开发总览.md) 的双协议语境）已覆盖 view/中间件/ORM 的 async 形态（`async def view`、`aget()`），但生态同步件居多——**Django 选型时把"高并发长连接"让给 ASGI 原生框架**，Django 的甜区仍是经典请求-响应业务系统。

## 连接

| 需求 | 去 |
|---|---|
| ORM 深入与 raw 判据 | [06-数据库操作](../02-IO与工程实践/06-数据库操作.md) |
| 测试 | `TestCase`（事务回滚隔离）/ pytest-django、fixture 策略（[02-Fixture](../04-测试与质量/02-Fixture.md)） |
| 部署 | ASGI/WSGI 服务器（[01-Web开发总览](01-Web开发总览.md) 部署表） |
| 前后分离 | DRF（本篇）+ 前端框架；契约测试见 [05-覆盖率与测试策略](../04-测试与质量/05-覆盖率与测试策略.md) |

## 示例

```python
# admin.py —— 三行拿到可用的内容后台
from django.contrib import admin
from .models import Article, Tag

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "published_at", "tag_count")
    search_fields = ("title",)
    list_filter = ("published_at",)

    def tag_count(self, obj: Article) -> int:
        return obj.tags.count()

# 迁移工作流（schema 即版本史）
# python manage.py makemigrations && python manage.py migrate
```
