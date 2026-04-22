# Django 基础

Django 是高级 Python Web 框架，遵循 "batteries included" 原则。MTV 架构：Model（模型）、Template（模板）、View（视图）。

## 核心特性

## 环境准备

`pip install django` 安装，`django-admin startproject` 创建项目，`python manage.py startapp` 创建应用。

### 参考样例

```bash
pip install django
django-admin startproject myproject
cd myproject
python manage.py startapp myapp
```

## 项目结构

```
myproject/
├── manage.py
├── myproject/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── myapp/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── models.py
    ├── views.py
    ├── urls.py
    └── tests.py
```

Django ORM 通过 `models.Model` 子类定义模型，字段类型对应数据库列。

### 参考样例

```python
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Category(models.Model):
    """商品分类"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    """商品模型"""
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products"
    )
    description = models.TextField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="products/", blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["price", "is_active"]),
        ]

    def __str__(self):
        return self.name

    @property
    def avg_rating(self) -> float:
        """计算商品平均评分"""
        from django.db.models import Avg
        result = self.reviews.aggregate(Avg("rating"))["rating__avg"]
        return result or 0.0

    def decrease_stock(self, quantity: int):
        """减少库存"""
        if self.stock < quantity:
            raise ValueError("Insufficient stock")
        self.stock -= quantity
        self.save()


class Review(models.Model):
    """商品评论"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reviews"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ["product", "user"]
        ordering = ["-created_at"]


class Order(models.Model):
    """订单模型"""
    class Status(models.TextChoices):
        PENDING = "pending", "待处理"
        PROCESSING = "processing", "处理中"
        SHIPPED = "shipped", "已发货"
        DELIVERED = "delivered", "已送达"
        CANCELLED = "cancelled", "已取消"

    order_number = models.CharField(max_length=20, unique=True)
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="orders"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.TextField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.order_number}"


class OrderItem(models.Model):
    """订单项"""
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        return self.quantity * self.unit_price
```

Django 视图处理请求并返回响应。Class-based views（CBV）如 `ListView`、`DetailView` 提供通用功能。

### 参考样例

```python
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from .models import Product, Category, Review, Order, OrderItem
from .forms import ReviewForm, OrderCreateForm


class ProductListView(ListView):
    """商品列表"""
    model = Product
    template_name = "myapp/product_list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)
        category_slug = self.kwargs.get("category_slug")
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(Q(name__icontains=search))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        return context


class ProductDetailView(DetailView):
    """商品详情"""
    model = Product
    template_name = "myapp/product_detail.html"
    context_object_name = "product"
    slug_field = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["reviews"] = self.object.reviews.annotate(
            avg_rating=Avg("rating")
        ).order_by("-created_at")[:5]
        context["review_form"] = ReviewForm()
        return context


class AddReviewView(View):
    """添加评论"""
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, "Review added successfully")
        return redirect("myapp:product_detail", pk=pk)


class OrderCreateView(CreateView):
    """创建订单"""
    model = Order
    form_class = OrderCreateForm
    template_name = "myapp/order_create.html"
    success_url = "/orders/"

    def form_valid(self, form):
        cart = self.request.session.get("cart", {})
        if not cart:
            form.add_error(None, "Cart is empty")
            return self.form_invalid(form)
        # 计算总价
        total = 0
        for product_id, quantity in cart.items():
            product = get_object_or_404(Product, pk=product_id)
            total += product.price * quantity
        form.instance.user = self.request.user
        form.instance.total_amount = total
        messages.success(self.request, "Order created successfully")
        return super().form_valid(form)


class DashboardView(TemplateView):
    """用户仪表板"""
    template_name = "myapp/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["total_orders"] = Order.objects.filter(user=user).count()
        context["pending_orders"] = Order.objects.filter(
            user=user, status="pending"
        ).count()
        context["recent_orders"] = Order.objects.filter(user=user)[:5]
        return context
```

URL 配置通过 `urls.py` 中的 `path()` 和 `include()` 组织路由。

### 参考样例

```python
# myproject/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("myapp.api_urls")),
    path("", include("myapp.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

```python
# myapp/urls.py
from django.urls import path
from . import views

app_name = "myapp"

urlpatterns = [
    path("", views.ProductListView.as_view(), name="product_list"),
    path(
        "category/<slug:category_slug>/",
        views.ProductListView.as_view(),
        name="category_products"
    ),
    path(
        "product/<int:pk>/",
        views.ProductDetailView.as_view(),
        name="product_detail"
    ),
    path(
        "product/<int:pk>/review/",
        views.AddReviewView.as_view(),
        name="add_review"
    ),
    path("order/create/", views.OrderCreateView.as_view(), name="order_create"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
]
```

Django 表单通过 `forms.ModelForm` 或 `forms.Form` 定义，提供验证和渲染。

### 参考样例

```python
from django import forms
from django.core.validators import MinValueValidator
from .models import Review, Order


class ReviewForm(forms.ModelForm):
    """评论表单"""
    rating = forms.IntegerField(
        widget=forms.HiddenInput(),
        validators=[MinValueValidator(1)]
    )

    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 4}),
        }


class OrderCreateForm(forms.ModelForm):
    """订单创建表单"""
    class Meta:
        model = Order
        fields = ["shipping_address", "notes"]
        widgets = {
            "shipping_address": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }


class ProductSearchForm(forms.Form):
    """商品搜索表单"""
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Search products..."})
    )
    category = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="All Categories"
    )
    min_price = forms.DecimalField(required=False, min_value=0)
    max_price = forms.DecimalField(required=False, min_value=0)
    in_stock = forms.BooleanField(required=False)
```

Django Admin 通过 `@admin.register()` 装饰器配置模型管理界面。

### 参考样例

```python
from django.contrib import admin
from django.utils.html import format_html
from .models import Product, Category, Review, Order


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "product_count", "created_at"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = "Products"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "price", "stock", "is_active", "thumbnail"]
    list_filter = ["category", "is_active", "created_at"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ["price", "stock", "is_active"]

    fieldsets = (
        ("Basic Info", {"fields": ("name", "slug", "category", "image")}),
        ("Details", {"fields": ("description", "price", "stock")}),
        ("Status", {"fields": ("is_active",)}),
    )

    def thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" />',
                obj.image.url
            )
        return "-"
    thumbnail.short_description = "Image"


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["product", "user", "rating", "created_at"]
    list_filter = ["rating", "created_at"]
    search_fields = ["product__name", "user__username"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["order_number", "user", "status", "total_amount", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["order_number", "user__username"]
    readonly_fields = ["order_number", "total_amount", "created_at"]

    fieldsets = (
        ("Order Info", {"fields": ("order_number", "user", "status", "total_amount")}),
        ("Shipping", {"fields": ("shipping_address", "notes")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
```

Django 中间件通过 `MiddlewareMixin` 子类实现，`process_request/process_response` 处理请求/响应。

### 参考样例

```python
# myproject/settings.py
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "myapp.middleware.RequestLoggingMiddleware",
    "myapp.middleware.CartMiddleware",
]
```

```python
# myapp/middleware.py
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """请求日志中间件"""

    def process_request(self, request):
        logger.info(f"{request.method} {request.path}")
        return None

    def process_response(self, request, response):
        logger.info(f"Response: {response.status_code}")
        return response


class CartMiddleware(MiddlewareMixin):
    """购物车中间件"""

    def process_request(self, request):
        if not request.session.get("cart"):
            request.session["cart"] = {}
        return None
```

Django 信号通过 `@receiver` 装饰器监听模型事件，如保存后、删除前。

### 参考样例

```python
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import Order, OrderItem, Product




@receiver(pre_delete, sender=OrderItem)
def order_item_deleted(sender, instance, **kwargs):
    """订单项删除后退回库存"""
    instance.product.stock += instance.quantity
    instance.product.save()


@receiver(pre_delete, sender=OrderItem)
def order_item_deleted(sender, instance, **kwargs):
    """订单项删除后退回库存"""
    instance.product.stock += instance.quantity
    instance.product.save()
```

Django 测试通过 `django.test.TestCase` 子类编写，使用 `Client` 模拟请求。

### 参考样例

```python
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Product, Category, Order


class ProductModelTest(TestCase):
    """产品模型测试"""

    def setUp(self):
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            category=self.category,
            price=99.99,
            stock=10
        )

    def test_product_creation(self):
        self.assertEqual(self.product.name, "Test Product")
        self.assertEqual(self.product.stock, 10)

    def test_decrease_stock(self):
        self.product.decrease_stock(5)
        self.assertEqual(self.product.stock, 5)

    def test_decrease_stock_insufficient(self):
        with self.assertRaises(ValueError):
            self.product.decrease_stock(15)


class ProductViewTest(TestCase):
    """产品视图测试"""

    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            category=self.category,
            price=99.99,
            stock=10
        )

    def test_product_list_view(self):
        response = self.client.get(reverse("myapp:product_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Product")

    def test_product_detail_view(self):
        response = self.client.get(
            reverse("myapp:product_detail", kwargs={"pk": self.product.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Product")


class OrderViewTest(TestCase):
    """订单视图测试"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            category=self.category,
            price=99.99,
            stock=10
        )

    def test_order_creation_requires_login(self):
        response = self.client.get(reverse("myapp:order_create"))
        self.assertNotEqual(response.status_code, 200)
