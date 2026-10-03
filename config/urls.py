from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', include('pages.urls')),  # 把 pages/urls.py 引進來
    path('', include('course.urls')),
    path('users/', include('users.urls')),
]