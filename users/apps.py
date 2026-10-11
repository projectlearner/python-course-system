from django.apps import AppConfig
import os

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(s):
        # 避免在 migrates 等指令執行期間過早呼叫
        import sys
        if 'runserver' in sys.argv or 'gunicorn' in sys.argv:
            from django.contrib.auth.models import User
            username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
            email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
            password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123456')
            
            if not User.objects.filter(username=username).exists():
                User.objects.create_superuser(username=username, email=email, password=password)
                print(f"--> 自動建立管理員成功: {username} / {password}")