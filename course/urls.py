# courses/urls.py
from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.course_list, name='course_list'),                     # 課程列表頁
    path('<int:course_id>/', views.course_detail, name='course_detail'),  # 課程詳情頁
    path('<int:course_id>/enroll/', views.enroll_course, name='enroll'), # 執行選課動作
    path('my-courses/', views.my_courses, name='my_courses'),            # 已選課程（個人課表）
    path('<int:course_id>/drop/', views.drop_course, name='drop_course'),
]