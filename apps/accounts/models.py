from django.contrib.auth.models import AbstractUser
from django.db import models


class UserInfo(AbstractUser):
    """自定义用户模型"""
    phone = models.CharField('手机号', max_length=20, blank=True)
    avatar = models.ImageField('头像', upload_to='avatars/', blank=True, null=True)

    notification_enabled = models.BooleanField('启用通知', default=True)
    theme = models.CharField('主题', max_length=20, default='light',
                             choices=[('light', '浅色'), ('dark', '深色')])

    # 时间戳
    last_login_ip = models.GenericIPAddressField('最后登录IP', blank=True, null=True)
    last_login_device = models.CharField('最后登录设备', max_length=200, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.username} ({self.email})"

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return '/static/images/default-avatar.png'

class UserLoginHistory(models.Model):
    """用户登录历史"""
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE, related_name='login_history')
    login_time = models.DateTimeField('登录时间', auto_now_add=True)
    ip_address = models.GenericIPAddressField('IP地址')
    user_agent = models.TextField('用户代理', blank=True)
    success = models.BooleanField('登录成功', default=True)

    class Meta:
        db_table = 'user_login_history'
        ordering = ['-login_time']
        verbose_name = '用户登录历史'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.user.username} - {self.login_time}"