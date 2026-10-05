from django.urls import path
from . import views
from .views import student_profile

app_name = 'users'

urlpatterns = [
    path('profile/', views.student_profile, name='profile'),
    path('profile/', student_profile, name='student_profile'),
]