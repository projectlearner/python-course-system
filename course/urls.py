from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('<int:course_id>/', views.course_detail, name='course_detail'),
    path('<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    path('<int:course_id>/drop/', views.drop_course, name='drop_course'),
    path('my-courses/', views.my_courses, name='my_courses'),
    path('teacher/', views.teacher_courses, name='teacher_courses'),
    path('<int:course_id>/roster/', views.course_roster, name='course_roster'),
    path('<int:course_id>/edit/', views.edit_course, name='edit_course'),
]