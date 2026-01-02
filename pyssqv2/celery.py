import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pyssqv2.settings')

app = Celery('pyssqv2')

# 使用Django的配置
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现任务
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))