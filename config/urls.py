from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

def root_redirect(request):
    if not request.user.is_authenticated:
        return redirect('login')  # 未登入導向登入頁
    return redirect('courses:course_list')  # 已登入導向課程清單

urlpatterns = [
    path('', root_redirect, name='index'),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('courses/', include('course.urls')),  # 👈 這裡原本寫成 'courses.urls'，請改成 'course.urls'
    path('users/', include('users.urls')),
]