from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', include('pages.urls')),  # 把 pages/urls.py 引進來
    path('', include('course.urls')),
    path('users/', include('users.urls')),
    path('accounts/', include('django.contrib.auth.urls')), # 引入 Django 內建登入/登出路由
]