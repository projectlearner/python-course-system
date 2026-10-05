# course/urls.py
from django.urls import path
from . import views
from users import views as users_views

app_name = 'courses'

urlpatterns = [
    path('', views.course_list, name='course_list'),                            # 課程列表頁
    path('<int:course_id>/', views.course_detail, name='course_detail'),         # 課程詳情頁
    path('<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),   # 執行選課動作
    path('<int:course_id>/drop/', views.drop_course, name='drop_course'),        # 退選動作
    path('my-courses/', views.my_courses, name='my_courses'),                   # 個人課表
    path('profile/', users_views.student_profile, name='student_profile'),      # 個人主頁
    
    # 教師端功能
    path('teacher/courses/', views.teacher_courses, name='teacher_courses'),
    path('teacher/course/<int:course_id>/roster/', views.course_roster, name='course_roster'),
]