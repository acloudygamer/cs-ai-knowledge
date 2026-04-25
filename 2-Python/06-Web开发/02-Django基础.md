# Django 基础

Django 是遵循"batteries included"原则的高级 Python Web 框架，通过 MTV 架构将数据模型、业务逻辑和页面模板分离，实现 Web 开发各层面的解耦。

## 核心特性

## 环境准备

```bash
pip install django
django-admin startproject myproject
cd myproject
python manage.py startapp myapp
```

## 请求处理流程

<pre>
HTTP 请求
    │
    ▼
URLconf (urls.py)
    │
    ▼
中间件链 (Middleware)
    │
    ├─── process_request
    │
    ▼
路由匹配 (path/re_path)
    │
    ▼
视图函数/类
    │
    ├─── 业务逻辑
    │
    ├─── ORM 操作
    │
    ▼
模板渲染 (可选)
    │
    ▼
中间件链 (Middleware)
    │
    ├─── process_response
    │
    ▼
HTTP 响应
</pre>

### 机制：MTV 架构的职责分离

Model 负责数据结构和数据库映射，与持久化层耦合。Template 负责页面渲染，与展示层耦合。View 承载业务逻辑，居于两者之间。这种分离使各层可独立修改——换模板不影响数据逻辑，改 Model 不影响页面结构。

## 数据模型

```python
from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
```

### 机制：ORM 的抽象代价

ORM 将数据库表映射为 Python 对象，开发者无需写 SQL。但这种抽象有代价：复杂查询（多表关联、子查询）用 ORM 表达不直观，且生成的 SQL 未必最优。Django的设计选择是优先开发速度，在明确性能瓶颈时才写原生 SQL。

## 类视图

```python
from django.views.generic import ListView, DetailView
from .models import Product

class ProductListView(ListView):
    model = Product
    template_name = "myapp/product_list.html"
    context_object_name = "products"
    paginate_by = 12
```

### 机制：CBV vs FBV

函数视图（FBV）直观，适合简单逻辑。类视图（CBV）通过属性和方法复用，适合标准 CRUD 模式。Django 提供通用类视图（ListView、DetailView 等），封装了分页、上下文构建等重复模式，减少样板代码。

## URL 配置

```python
from django.urls import path
from . import views

urlpatterns = [
    path("products/", views.ProductListView.as_view()),
    path("products/<int:pk>/", views.ProductDetailView.as_view()),
]
```

### 机制：URL 解耦

URL 是客户端与服务器的契约。Django 将 URL 配置集中于 `urls.py`，业务逻辑不依赖特定 URL 格式。改 URL 只需在一处修改，视图无需改动——实现前后端解耦。

## 表单

```python
from django import forms

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment"]
```

### 机制：表单的双重职责

Django 表单同时处理验证规则和 HTML 生成。`ModelForm` 从模型字段推断验证规则，数据验证通过后才执行数据库操作——防止无效数据进入系统。

## Admin

```python
from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "stock"]
    search_fields = ["name"]
```

### 机制：Admin 的设计权衡

Django Admin 通过模型元信息自动生成管理界面，加速后台开发。但它是通用方案，定制化能力有限。Django 的设计选择是"先跑通，再优化"——后台原型用 Admin，后期有需求再自建视图。

## 中间件

```python
class RequestLoggingMiddleware:
    def process_request(self, request):
        return None

    def process_response(self, request, response):
        return response
```

### 机制：中间件链的顺序

中间件按声明顺序执行 `process_request`，按逆序执行 `process_response`。这意味着最后添加的中间件最接近视图——它的 `process_request` 最后执行，`process_response` 最先执行。设计 URL 路由时应考虑此顺序。
